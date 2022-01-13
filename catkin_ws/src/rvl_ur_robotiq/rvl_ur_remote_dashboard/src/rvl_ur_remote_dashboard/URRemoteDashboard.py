# rospy
import rospy
import rosservice
from rospy import ServiceException, ROSException
from rospy.exceptions import ROSInterruptException

# pretty logging
from rvl_utilities.CustomLogger import ColorLogger
from pprint import pprint

# Additional UR mappings
from rvl_ur_remote_dashboard.URInterfaceMapping import *

# Robotiq driver
from rvl_robotiq_controller.RobotiqController import Robotiq2FController

class URRemoteDashboard:
    def __init__(self, name = 'UR5e', using_gripper = False, using_urscript = False, service_timeout = 5) -> None:
        # custom logger
        self.logger = ColorLogger(name + ' Remote Dashboard')

        # default service timeout
        self.service_timeout = service_timeout

        # robot status tracking
        self.robot_mode = None
        self.safety_mode = None
        self.last_known_io_states = None
        self.loaded_program = None
        self.using_urscript = False

        # services
        self.services = self.define_services()

        # publisher/subscriber
        self.register_robot_status()

    # ---------------------------------------------------------------------------- #
    #                                 POWER CONTROL                                #
    # ---------------------------------------------------------------------------- #

    def power_on_arm(self, timeout = 30):
        success = self.trigger_service('power_on')
        if success:
            self.logger.log_warn(f'Waiting for arm to power on')
            try:
                elapsed = 0
                while self.robot_mode < 5 and elapsed < timeout and not rospy.is_shutdown():
                    rospy.sleep(1)
                    elapsed += 1
                    if elapsed > timeout:
                        raise ROSException
                self.logger.log_success('Arm powered on (brakes engaged)')
                return True
            except ROSException as e:
                self.logger.log_error(f'Wait time exceeded {timeout} seconds power on time. Aborted.')
                return False
        else:
            self.logger.log_error('Unable to power on robot arm')
            return False

    def power_off_arm(self, timeout = 30):
        success = self.trigger_service('power_off')
        if success:
            self.logger.log_warn(f'Waiting for arm to power off')
            try:
                elapsed = 0
                while self.robot_mode > 3 and elapsed < timeout and not rospy.is_shutdown():
                    rospy.sleep(1)
                    elapsed += 1
                    if elapsed > timeout:
                        raise ROSException
                self.logger.log_success('Arm powered off')
                return True
            except ROSException as e:
                self.logger.log_error(f'Wait time exceeded {timeout} seconds power off time. Aborted.')
                return False
        else:
            self.logger.log_error('Unable to power off robot arm')
            return False

    def system_shutdown(self):
        _ = self.trigger_service('shutdown')
        rospy.signal_shutdown('UR System shutdown requested. Shutting everything down.')
        self.logger.log_success('Goodbye!')
        exit(-1)

    def cold_boot(self):
        return self.release_brakes()

    # ---------------------------------------------------------------------------- #
    #                                SAFETY CONTROL                                #
    # ---------------------------------------------------------------------------- #

    def release_brakes(self, timeout = 30):
        success = self.trigger_service('brake_release')
        if success:
            self.logger.log_warn(f'Waiting for arm to power on and release brakes')
            try:
                elapsed = 0
                while self.robot_mode < 7 and elapsed < timeout and not rospy.is_shutdown():
                    rospy.sleep(1)
                    elapsed += 1
                    if elapsed > timeout:
                        raise ROSException
                self.logger.log_success('Arm powered and ready for planning!')
                return True
            except ROSException as _:
                self.logger.log_error(f'Wait time exceeded {timeout} seconds full powered on time. Aborted.')
                return False
        else:
            self.logger.log_error('Unable to fully initialized robot')
            return False

    def restart_safety(self):
        success = self.trigger_service('brake_release')
        if success:
            self.logger.log_warn(f'Safety fault/violation cleared')
            return True
        else:
            self.logger.log_error('Unable to clear safety violation')
            return False

    def clear_protective_stop(self, timeout = 30):
        success = self.trigger_service('unlock_protective_stop')
        if success:
            self.logger.log_warn(f'Waiting for protective stop to clear')
            try:
                elapsed = 0
                while self.safety_mode != 1 and elapsed < timeout and not rospy.is_shutdown():
                    rospy.sleep(1)
                    elapsed += 1
                    if elapsed > timeout:
                        raise ROSException
                self.logger.log_success('Protective stop cleared')
                return True
            except ROSException as _:
                self.logger.log_error(f'Wait time exceeded {timeout} seconds clearing time. Aborted.')
                return False
        else:
            self.logger.log_error('Unable to clear protective stop')
            return False

    def clear_operational_mode(self):
        success = self.trigger_service('clear_operational_mode')
        if success:
            self.logger.log_warn(f'Operational mode cleared')
            return True
        else:
            self.logger.log_error('Unable to clear operational mode')
            return False

    # ---------------------------------------------------------------------------- #
    #                                 POPUP CONTROL                                #
    # ---------------------------------------------------------------------------- #

    def close_popup(self, safety = False):
        if safety:
            success = self.trigger_service('close_safety_popup')
        else:
            success = self.trigger_service('close_popup')

        if success:
            self.logger.log_success(f'{"Safety popup" if safety else "Popup"} closed')
            return True
        else:
            self.logger.log_error('Unable to close popup')
            return False

    def send_popup(self, message):
        request = PopupRequest()
        request.message = message
        try:
            serv = self.services['popup']
            rospy.wait_for_message(serv, timeout = self.service_timeout)
            response = rospy.ServiceProxy(serv, Popup)(request)
            if not response.success: raise ServiceException('response.success returned False')
            self.logger.log_success('Popup sent to Teach Pendant')
        except (ROSException, ServiceException, KeyError) as e:
            self.logger.log_error('Unable to send popup')
            self.logger.log_error(e)
            return False

    # ---------------------------------------------------------------------------- #
    #                           DASHBOARD SERVER CONTROL                           #
    # ---------------------------------------------------------------------------- #

    def connect_dashboard(self, quiet = False):
        success = self.trigger_service('connect')
        if success:
            self.logger.log_success('Connection to dashboard established')
            return True
        else:
            if not quiet:
                self.logger.log_error('Unable to disconnect from dashboard server')
            return False

    def disconnect_dashboard(self):
        success = self.trigger_service('quit')
        if success:
            self.logger.log_success('Connection to dashboard terminated')
            return True
        else:
            self.logger.log_error('Unable to disconnect from dashboard server')
            return False

    def spam_connect(self, attempts = 10):
        for i in range(attempts):
            self.logger.log_warn(f'Reconnecting attempted ({attempts - i} remaining)', indent = 1)
            if self.connect_dashboard(quiet = True):
                return True
            rospy.sleep(1)
        self.logger.log_error('Reconnection attempts to dashboard server unsuccessful')
        return False

    # ---------------------------------------------------------------------------- #
    #                    POLYSCOPE PROGRAMS/INSTALLATION CONTROL                   #
    # ---------------------------------------------------------------------------- #

    def start_loaded_program(self):
        success = self.trigger_service('play')
        if success:
            self.logger.log_success(f'Program {self.loaded_program} is running')
            return True
        else:
            self.logger.log_error(f'Unable to start {self.loaded_progran}')
            return False

    def pause_loaded_program(self):
        success = self.trigger_service('pause')
        if success:
            self.logger.log_success(f'Program {self.loaded_program} is paused')
            return True
        else:
            self.logger.log_error(f'Unable to pause {self.loaded_progran}')

            return False

    def stop_loaded_program(self):
        success = self.trigger_service('stop')
        if success:
            self.logger.log_success(f'Program {self.loaded_program} is stopped')
            return True
        else:
            self.logger.log_error(f'Unable to stop {self.loaded_progran}')
            return False

    def is_program_running(self):
        try:
            response = rospy.ServiceProxy(self.services['program_running'], IsProgramRunning)()
            if not response.success: raise ServiceException('response.success returned False')
            self.logger.log_success(f'Program "{self.loaded_program}" is {"running" if response.program_running else "not running"}')
            return response.program_running
        except (ROSException, ServiceException, KeyError) as e:
            self.logger.log_error('Unable to query if program is running')
            self.logger.log_error(e)
            return False

    def is_program_saved(self):
        try:
            response = rospy.ServiceProxy(self.services['program_saved'], IsProgramSaved)()
            self.logger.log_success(f'Program "{response.program_name}" is {"saved" if response.program_saved else "not saved"}')
            if not response.success: raise ServiceException('response.success returned False')
            return response.program_saved
        except (ROSException, ServiceException, KeyError) as e:
            self.logger.log_error('Unable to query if program is saved')
            self.logger.log_error(e)
            return False

    def query_program_state(self):
        try:
            response = rospy.ServiceProxy(self.services['program_state'], GetProgramState)()
            if not response.success: raise ServiceException('response.success returned False')
            self.logger.log_success(f'Program "{response.program_name}" state is {response.state.state}')
        except (ROSException, ServiceException, KeyError) as e:
            self.logger.log_error('Unable to query if program is saved')
            self.logger.log_error(e)
            return False

    def terminate_external_control(self):
        success = self.trigger_service('hand_back_control')
        if success:
            self.logger.log_success('"External Control" program node terminated')
            return True
        else:
            self.logger.log_error('Unable to terminate external control node')
            return False

    def get_loaded_program(self):
        try:
            serv = self.services['get_loaded_program']
            response = rospy.ServiceProxy(serv, GetLoadedProgram)()
            if not response.success: raise ServiceException('response.success returned False')
            self.loaded_program = response.program_name
            return response.program_name
        except Exception as e:
            self.logger.log_error('Unable to request loaded program name')
            self.logger.log_error(str(e))

    def load_program(self, filename, ptype, wait = 10, attempts = 10):
        request = LoadRequest()
        request.filename = filename
        try:
            if ptype in ['prog', 'p', 'program', 'urp']:
                serv = self.services['load_program']
            elif ptype in ['inst', 'i', 'installation']:
                serv = self.services['load_installation']
            else:
                self.logger.log_error(f'{ptype} is invalid')
                self.logger.log_error(f'Expecting program [p, prog, program, urp] or installation [inst, i, installation]')
                return None
            rospy.wait_for_service(serv, timeout=self.service_timeout)
            response = rospy.ServiceProxy(serv, Load)(request)
            if not response.success: raise ServiceException('response.success returned False')
        except (ServiceException, ROSException) as _:
            self.logger.log_warn('Known dashboard server disconnection occured')
            self.logger.log_warn(f'Waiting for {wait} seconds for program/installation to load correctly')
            rospy.sleep(wait)
            self.logger.log_warn(f'Attempting to reconnect to dashboard server ({attempts} attempts)')
            self.spam_reconnect(attempts = attempts)
            self.close_popup()
        except KeyError as e:
            self.logger.log_error(str(e))
            return False
        self.last_known_installation = filename
        rospy.sleep(1)

    # ---------------------------------------------------------------------------- #
    #                                 ROBOT STATUS                                 #
    # ---------------------------------------------------------------------------- #

    def robot_status_callback(self, msg):
        self.robot_mode = msg.mode

    def robot_safety_callback(self, msg):
        self.safety_mode = msg.mode

    def robot_iostate_callback(self, msg):
        self.last_known_io_states = msg

    def get_robot_mode(self):
        try:
            serv = self.services['get_robot_mode']
            rospy.wait_for_service(serv, timeout = self.service_timeout)
            response = rospy.ServiceProxy(serv, GetRobotMode)()
            if not response.success: raise ServiceException('response.success returned False')
            mode = response.robot_mode.mode
            self.logger.log_success(f'Robot mode = {mode} ({RobotModeMapping(mode).name})')
            return mode
        except (ROSException, ServiceException, KeyError) as e:
            self.logger.log_error('Unable to request robot mode')
            self.logger.log_error(e)

    def get_safety_mode(self):
        try:
            serv = self.services['get_safety_mode']
            rospy.wait_for_service(serv, timeout = self.service_timeout)
            response = rospy.ServiceProxy(serv, GetSafetyMode)()
            if not response.success: raise ServiceException('response.success returned False')
            mode = response.safety_mode.mode
            self.logger.log_success(f'Robot safety mode = {mode} ({SafetyModeMapping(mode).name})')
            return mode
        except (ROSException, ServiceException, KeyError) as e:
            self.logger.log_error('Unable to request robot safety mode')
            self.logger.log_error(e)

    # ---------------------------------------------------------------------------- #
    #                               ADVANCED FEATURES                              #
    # ---------------------------------------------------------------------------- #

    def zero_force_torque_sensor(self):
        success = self.trigger_service('zero_ftsensor')
        if success:
            self.logger.log_success('Force/Torque sensor zero-ed')
            return True
        else:
            self.logger.log_error('Unable to zero force/torque sensor')
            return False

    def log_to_pendant(self, message):
        request = AddToLogRequest()
        request.message = message
        try:
            serv = self.services['add_to_log']
            rospy.wait_for_service(serv, timeout = self.service_timeout)
            response = rospy.ServiceProxy(serv, AddToLog)(request)
            if not response.success: raise ServiceException('response.success returned False')
        except (ROSException, ServiceException, KeyError) as e:
            self.logger.log_error('Unable to log message to Teach Pendant')
            self.logger.log_error(e)

    def raw_request(self, query):
        request = RawRequestRequest()
        request.query = query
        try:
            serv = self.services['raw_request']
            rospy.wait_for_service(serv, timeout = self.service_timeout)
            response = rospy.ServiceProxy(serv, RawRequest)(request)
            if not response.success: raise ServiceException('response.success returned False')
        except (ROSException, ServiceException, KeyError) as e:
            self.logger.log_error('Unable to log message to Teach Pendant')
            self.logger.log_error(e)

    def set_io(self, function, pin, state):
        request = SetIORequest()
        request.fun = function
        request.pin = pin
        request.state = state
        try:
            serv = self.services['set_io']
            rospy.wait_for_service(serv, timeout = self.service_timeout)
            response = rospy.ServiceProxy(serv, SetIO)(request)
            if not response.success: raise ServiceException('response.success returned False')
        except (ROSException, ServiceException, KeyError) as e:
            self.logger.log_error(f'Unable to set pin {pin} to {state} using {SetIOFunctionMapping(function).name}')
            self.logger.log_error(e)

    def set_payload(self, mass, cx, cy, cz):
        request = SetPayloadRequest()
        request.center_of_gravity = Vector3()
        request.center_of_gravity.x = cx
        request.center_of_gravity.y = cy
        request.center_of_gravity.z = cz
        request.mass = mass
        try:
            serv = self.services['set_payload']
            rospy.wait_for_service(serv, timeout = self.service_timeout)
            response = rospy.ServiceProxy(serv, SetPayload)(request)
            if not response.success: raise ServiceException('response.success returned False')
            self.logger.log_success(f'Setting payload successfully')
        except (ROSException, ServiceException, KeyError) as e:
            self.logger.log_error('Unable to set payload')
            self.logger.log_error(e)

    def set_speed_slider(self, fraction):
        request = SetSpeedSliderFractionRequest()
        request.speed_slider_fraction = clip(fraction, 0.0, 1.0)
        try:
            serv = self.services['set_speed_slider']
            rospy.wait_for_service(serv, timeout = self.service_timeout)
            response = rospy.ServiceProxy(serv, SetSpeedSliderFraction)(request)
            if not response.success: raise ServiceException('response.success returned False')
            self.logger.log_success(f'Setting speed slider successfully')
        except (ROSException, ServiceException, KeyError) as e:
            self.logger.log_error('Unable to set speed slider')
            self.logger.log_error(e)

    def set_robot_mode(self):
        raise NotImplementedError

    # ---------------------------------------------------------------------------- #
    #                             SUPPORTING FUNCTIONS                             #
    # ---------------------------------------------------------------------------- #

    def trigger_service(self, serv_alias):
        if serv_alias in self.services:
            serv_name = self.services[serv_alias]
            try:
                rospy.wait_for_service(serv_name, timeout = self.service_timeout)
                response = rospy.ServiceProxy(serv_name, Trigger)()
                if not response.success:
                    self.logger.log_error(response.message)
                    raise ServiceException('response.success returned False')
                return response.success
            except (ROSException, ROSInterruptException, KeyboardInterrupt, ServiceException) as e:
                self.logger.log_error(f'Unable to trigger {serv_name}')
                self.logger.log_error(e)
        else:
            self.logger.log_error(f'{serv_alias} is unknown/unsupported. Aborted.')
            return False

    def define_services(self):
        available = rosservice.get_service_list()
        filterted = [s for s in available if 'ur_hardware_interface' in s and 'logger' not in s]
        services = {s[s.rfind('/') + 1:] : s for s in filterted}
        return dict(sorted(services.items()))

    def register_robot_status(self) -> None:
        """Register necessary subscribers and callbacks to monitor robot operational status."""
        try:
            # wait for topics to show up
            self.robot_mode = rospy.wait_for_message('/ur_hardware_interface/robot_mode', RobotMode, timeout = self.service_timeout).mode
            self.safety_mode = rospy.wait_for_message('/ur_hardware_interface/safety_mode', SafetyMode, timeout = self.service_timeout).mode
            self.last_known_io_states = rospy.wait_for_message('/ur_hardware_interface/io_states', IOStates, timeout = self.service_timeout)

            # register robot status tracking with callbacks
            self.robot_mode_sub = rospy.Subscriber('/ur_hardware_interface/robot_mode', RobotMode, self.robot_status_callback)
            self.robot_safety_sub = rospy.Subscriber('/ur_hardware_interface/safety', SafetyMode, self.robot_safety_callback)
            self.robot_io_sub = rospy.Subscriber('/ur_hardware_interface/io_states', IOStates, self.robot_iostate_callback)

            # verify if services are available
            self.verify_services()

            # get program name
            self.get_loaded_program()

            self.logger.log_success('Registered robot status subscribers')
        except ROSException as error:
            self.logger.log_error('Unable to register status subscriber')
            self.logger.log_error('Remote Dashboard terminated')
            self.logger.log_error(error)
            exit(-1)

    def verify_services(self):
        self.logger.log_warn('Validating if all services are available')
        for _, serv in self.services.items():
            rospy.wait_for_service(serv, timeout = self.service_timeout)
        self.logger.log_success('All supported services are available')