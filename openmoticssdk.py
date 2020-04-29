## Depends on 3.x and requests (http://www.python-requests.org/)

import random
import time
import traceback

import requests

try:
    import simplejson as json
except ImportError:
    import json

class AuthenticationException(Exception):
    """ This Exception is raised when the user credentials are not valid. """

    def __init__(self):
        self.msg = "The provided credentials are not valid."

    def __str__(self):
        return self.msg


class MaintenanceModeException(Exception):
    """ This Exception is raised when the gateway is currently in maintenance mode. """

    def __init__(self):
        self.msg = "The gateway is currently in maintenance mode."

    def __str__(self):
        return self.msg


class ApiException(Exception):
    """ This Exception is raised when a non successful message was returned. """

    def __init__(self, msg):
        self.msg = f"Non successful api call: {msg} "

    def __str__(self):
        return self.msg


class OpenMoticsApi:
    """ Connector for the OpenMotics Gateway API. """

    def __init__(self, username, password, hostname, verify_https=False, port=443):
        """
        Create a new connector. This constructor requires the gateway username and password.
        These credentials are not the same as the username and password on the OpenMotics cloud.
        """
        self.auth = { "username" : username, "password" : password }
        self.hostname = hostname
        self.verify_https = verify_https
        self.port = port
        self.token = None

    def get_url(self, action):
        """ Get the url for an action. """
        return f"https://{self.hostname}:{self.port}/{action}"

    def get_post_data(self, post_data):
        """ Get the full post data dict, this method adds the token to the dict. """
        d = post_data.copy()
        if self.token != None:
            d["token"] = self.token
        return d

    def fetch_url(self, action, post_data={}, get_params={}, json_decode=True):
        """ Fetch an url. The url and post data are created based on the action and post_data. """
        url = self.get_url(action)
        post_data = self.get_post_data(post_data)

        # print(f"Fetching url: {url}")

        r = requests.post(url, params=get_params, data=post_data, verify=self.verify_https)
        if r.status_code == 401:
            self.token = None
            raise AuthenticationException()
        elif r.status_code == 503:
            raise MaintenanceModeException()
        elif r.status_code == 200:
            if json_decode:
                msg = r.json()
                if 'success' in msg and msg['success'] is False:
                    raise ApiException(msg)
                else:
                    return msg
            else:
                return r.text
        else:
            raise Exception(f"Unknown status code: {r.status_code}. Text: {r.text}" )

    def login(self):
        """ Login to the gateway: sets the token in the connector. """
        self.token = self.fetch_url("login", self.auth)["token"]

    def exec_action(self, action, post_data={}, get_params={}, json_decode=True):
        """ Execute an action: this method also performs the login if required. """
        if self.token == None:
            self.login()

        try:
            ## Try to execute the action.
            return self.fetch_url(action, post_data, get_params, json_decode)
        except AuthenticationException:
            ## Get a new token and retry the action.
            self.login()
            return self.fetch_url(action, post_data, get_params, json_decode)

    ######### Below are the actaul API actions #########

    def get_version(self):
        """ Get the version of the openmotics software.
        :returns: 'version': String (a.b.c).
        """
        return self.exec_action('get_version')

    ######### Master actions #########

    def get_status(self):
        """ Get the status of the Master.
        :returns: dict with 'time' (HH:MM), 'date' (DD:MM:YYYY), 'mode', 'version' (a.b.c)
                  and 'hw_version' (hardware version)
        """
        return self.exec_action('get_status')

    def get_outputs_status(self):
        """ Get the status of the outputs.
        :returns: 'status': list of dictionaries with the following keys: id,\
        status, dimmer and ctimer.
        """
        return self.exec_action('get_output_status')

    def get_output_status(self, id):
        """ Get the status of an output.
        :returns: 'status': list of dictionaries with the following keys: id,\
        status, dimmer and ctimer.
        """
        post_data = {'id' : id}
        return self.exec_action('get_output_status', post_data=post_data)


    def get_thermostats_status(self):
        """ Get the status of the thermostats.
        :returns: global status information about the thermostats: 'thermostats_on', \
        'automatic' and 'setpoint' and 'status': a list with status information for all \
        thermostats, each element in the list is a dict with the following keys: \
        'id', 'act', 'csetp', 'output0', 'output1', 'outside', 'mode'.
        """
        return self.exec_action('get_thermostat_status')

    def get_thermostat_status(self, id):
        """ Get the status of an thermostat.
        :returns: global status information about the thermostats: 'thermostats_on', \
        'automatic' and 'setpoint' and 'status': a list with status information for all \
        thermostats, each element in the list is a dict with the following keys: \
        'id', 'act', 'csetp', 'output0', 'output1', 'outside', 'mode'.
        """
        post_data = {'id' : id}
        return self.exec_action('get_thermostat_status', post_data=post_data)


    def get_sensor_brightness_status(self):
        """ Get the current brightness of all sensors.
        :returns: 'status': List of 32 bytes, 1 for each sensor.
        """
        return self.exec_action('get_sensor_brightness_status')

    def get_sensor_humidity_status(self):
        """ Get the current humidity of all sensors.
        :returns: 'status': List of 32 bytes, 1 for each sensor.
        """
        return self.exec_action('get_sensor_humidity_status')

    def get_sensor_temperature_status(self):
        """ Get the current temperature of all sensors.
        :returns: 'status': list of 32 temperatures, 1 for each sensor.
        """
        return self.exec_action('get_sensor_temperature_status')

    def set_output(self, id, on, dimmer=None, timer=None):
        """ Set the status, dimmer and timer of an output.
        :param id: The id of the output to set
        :type id: Integer [0, 240]
        :param is_on: Whether the output should be on
        :type is_on: Boolean
        :param dimmer: The dimmer value to set, None if unchanged
        :type dimmer: Integer [0, 100] or None
        :param timer: The timer value to set, None if unchanged
        :type timer: Integer in (150, 450, 900, 1500, 2220, 3120)
        """
        post_data = {'id' : id, 'is_on' : on}
        if dimmer is not None:
            post_data['dimmer'] = dimmer
        if timer is not None:
            post_data['timer'] = timer
        return self.exec_action('set_output', post_data=post_data)

    def set_all_lights_off(self):
        """ Turn all lights off. """
        return self.exec_action('set_all_lights_off')

    def set_all_lights_floor_off(self, floor):
        """ Turn all lights on a given floor off.
        :param floor: The id of the floor
        :type floor: Byte
        """
        return self.exec_action('set_all_lights_floor_off', post_data={'floor': floor})

    def set_all_lights_floor_on(self, floor):
        """ Turn all lights on a given floor on.
        :param floor: The id of the floor
        :type floor: Byte
        """
        return self.exec_action('set_all_lights_floor_on', post_data={'floor': floor})

    def set_current_setpoint(self, thermostat, temperature):
        """ Set the current setpoint of a thermostat.
        :param thermostat: The id of the thermostat to set
        :type thermostat: Integer [0, 24]
        :param temperature: The temperature to set in degrees Celcius
        :type temperature: float
        :return: 'status': 'OK'.
        """
        return self.exec_action('set_current_setpoint', post_data={'thermostat': thermostat, 'temperature': temperature})

    def set_thermostat_mode(self, on, automatic, setpoint):
        """ Set the mode of the thermostats. Thermostats can be on or off, automatic or manual
        and is set to one of the 6 setpoints.
        :param thermostat_on: Whether the thermostats are on
        :type thermostat_on: Boolean
        :param automatic: Automatic mode (True) or Manual mode (False)
        :type automatic: Boolean
        :param setpoint: The current setpoint
        :type setpoint: Integer [0, 5]
        :return: 'status': 'OK'.
        """
        return self.exec_action('set_thermostat_mode', post_data={'thermostat_on': on, 'automatic': automatic, 'setpoint': setpoint})

    def do_group_action(self, group_action_id):
        """ Execute a group action.
        :param group_action_id: The id of the group action
        :type group_action_id: Integer [0, 159]
        """
        return self.exec_action('do_group_action', post_data={'group_action_id': group_action_id})

    def module_discover_start(self):
        """ Start the module discover mode on the master.
        :returns: 'status': 'OK'.
        """
        return self.exec_action('module_discover_start')

    def module_discover_stop(self):
        """ Stop the module discover mode on the master.
        :returns: 'status': 'OK'.
        """
        return self.exec_action('module_discover_stop')

    def get_modules(self):
        """ Get a list of all modules attached and registered with the master.
        :returns: 'output': list of module types (O,R,D) and 'input': list of input module \
        types (I,T,L).
        """
        return self.exec_action('get_modules')

    def flash_leds(self, type, id):
        """ Flash the leds on the module for an output/input/sensor.

        :type type: Integer
        :param type: The module type: output/dimmer (0), input (1), sensor/temperatur (2).
        :type id: Integer
        :param id: The id of the output/input/sensor.
        :returns: 'status': 'OK'.
        """
        return self.exec_action('flash_leds', post_data={'type': type, 'id': id})

    def get_last_inputs(self):
        """ Get the 5 last pressed inputs during the last 5 minutes.
        :returns: 'inputs': list of tuples (input, output).
        """
        return self.exec_action('get_last_inputs')

    ######### Pulse counter actions #########

    def get_pulse_counter_status(self):
        """ Get the pulse counter values.
        :returns: 'counters': array with the 8 pulse counter values.
        """
        return self.exec_action('get_pulse_counter_status')

    ######### Master errors #########

    def get_errors(self):
        """ Get the number of seconds since the last successul communication with the master and
        power modules (master_last_success, power_last_success) and the error list per module
        (input and output modules). The modules are identified by O1, O2, I1, I2, ...
        :returns: 'errors': list of tuples (module, nr_errors), 'master_last_success': UNIX \
        timestamp of the last succesful master communication and 'power_last_success': UNIX \
        timestamp of the last successful power communication.
        """
        return self.exec_action('get_errors')

    def master_clear_error_list(self):
        """ Clear the number of errors. """
        return self.exec_action('master_clear_error_list')

    def reset_master(self):
        """ Perform a cold reset on the master.

        :returns: 'status': 'OK'.
        """
        return self.exec_action('reset_master')

    ######### Power actions #########

    def get_power_modules(self):
        """ Get information on the power modules.
        :returns: dict with key 'modules' (List of dictionaries with the following keys: 'id', \
            'name', 'address', 'input0', 'input1', 'input2', 'input3', 'input4', 'input5', \
            'input6', 'input7', 'times0', 'times1', 'times2', 'times3', 'times4', 'times5', \
            'times6', 'times7'.
        """
        return self.exec_action('get_power_modules')

    def set_power_modules(self, modules):
        """ Set information (module and input names) for the power modules.
        :param modules: list of dicts with as 'keys': 'id', 'name', 'input0', 'input1', 'input2', \
            'input3', 'input4', 'input5', 'input6', 'input7', 'times0', 'times1', 'times2', \
            'times3', 'times4', 'times5', 'times6', 'times7'.
        """
        return self.exec_action('set_power_modules', post_data={'modules': json.dumps(modules)})

    def get_realtime_power(self):
        """ Get the realtime power measurements.
        :returns: dict with the module id as key and the follow array as value: \
        [voltage, frequency, current, power].
        """
        return self.exec_action('get_realtime_power')

    def get_total_energy(self):
        """ Get the total energy (kWh) consumed by the power modules.
        :returns: dict with the module id as key and the following array as value: [day, night].
        """
        return self.exec_action('get_total_energy')

    def set_power_voltage(self, module_id, voltage):
        """ Set the voltage for a given module.
        :param module_id: The id of the power module.
        :type module_id: int
        :param voltage: The voltage to set for the power module.
        :type voltage: float
        :returns: empty dict
        """
        return self.exec_action('set_power_voltage', post_data={'module_id': module_id, 'voltage': voltage})

    def start_power_address_mode(self):
        """ Start the address mode on the power modules. """
        return self.exec_action('start_power_address_mode')

    def stop_power_address_mode(self):
        """ Stop the address mode on the power modules. """
        return self.exec_action('stop_power_address_mode')

    def in_power_address_mode(self):
        """ Check if the power modules are in address mode.

        :returns: 'address_mode': Boolean
        """
        return self.exec_action('in_power_address_mode')

    ######### Timezone actions #########

    def set_timezone(self, timezone):
        """ Set the timezone for the gateway.
        :param timezone: in format 'Continent/City'.
        :returns: dict with 'msg' key.
        """
        return self.exec_action('set_timezone', post_data={'timezone': timezone})

    def get_timezone(self):
        """ Get the timezone for the gateway.
        :returns: dict with 'timezone' key containing the timezone in 'Continent/City' format.
        """
        return self.exec_action('get_timezone')

    ######### URL actions #########

    def do_url_action(self, url, method='GET', headers=None, data=None, auth=None, timeout=10):
        """ Execute an url action.
        :param url: The url to fetch.
        :param method: (optional) The http method (defaults to GET).
        :param headers: (optional) The http headers to send (format: json encoded dict)
        :param data: (optional) Bytes to send in the body of the request.
        :param auth: (optional) Json encoded tuple (username, password).
        :param timeout: (optional) Timeout in seconds for the http request (default = 10 sec).
        :returns: dict with 'success' (boolean), 'headers' (dict) and 'data' (string) keys.
        """
        return self.exec_action('do_url_action',
                                 post_data={ 'url':url, 'method':method, 'headers':headers, 'data':data,
                                        'auth':auth, 'timeout':timeout })

    ######### Scheduled actions #########

    def schedule_action(self, timestamp, action):
        """ Schedule an action at a given point in the future. An action can be any function of the
        OpenMotics webservice. The action is JSON encoded dict with keys: 'type', 'action', 'params'
        and 'description'. At the moment 'type' can only be 'basic'. 'action' contains the name of
        the function on the webservice. 'params' is a dict maps the names of the parameters given to
        the function to their desired values. 'description' can be used to identify the scheduled
        action.
        :param timestamp: UNIX timestamp (integer)
        :param action: dict
        """
        return self.exec_action('schedule_action', post_data = { 'timestamp' : timestamp,
                                                             'action' : json.dumps(action) })

    def list_scheduled_actions(self):
        """ Get a list of all scheduled actions.
        :returns: dict with key 'actions' containing a list of dicts with keys: 'timestamp',
        'from_now', 'id', 'description' and 'action'. 'timestamp' is the UNIX timestamp when the
        action will be executed. 'from_now' is the number of seconds until the action will be
        scheduled. 'id' is a unique integer for the scheduled action. 'description' contains a
        user set description for the action. 'action' contains the function and params that will be
        used to execute the scheduled action.
        """
        return self.exec_action('list_scheduled_actions')

    def remove_scheduled_action(self, id):
        """ Remove a scheduled action when the id of the action is given.
        :param id: the id of the scheduled action to remove.
        :returns: { 'success' : True }
        """
        return self.exec_action('remove_scheduled_action', post_data = { 'id' : id })

    def set_output_delayed(self, timestamp, description, output_nr, on, dimmer=None, timer=None):
        """ Delayed version of set_output. """
        action = { 'type' : 'basic', 'action' : 'set_output', 'description' : description,
                   'params' : { 'output_nr' : output_nr, 'is_on' : on,
                                'dimmer': dimmer, 'timer' : timer } }
        return self.schedule_action(timestamp, action)

    def set_all_lights_off_delayed(self, timestamp, description):
        """ Delayed version of set_all_lights_off_delayed. """
        return self.schedule_action(timestamp, { 'type' : 'basic', 'action' : 'set_all_lights_off',
                                                 'description' : description })

    def set_all_lights_floor_off_delayed(self, timestamp, description, floor):
        """ Delayed version of set_all_lights_floor_off. """
        action = { 'type' : 'basic', 'action' : 'set_all_lights_floor_off',
                   'description' : description, 'params' : { 'floor' : floor } }
        return self.schedule_action(timestamp, action)

    def set_all_lights_floor_on_delayed(self, timestamp, description, floor):
        """ Delayed version of set_all_lights_floor_on. """
        action = { 'type' : 'basic', 'action' : 'set_all_lights_floor_on',
                   'description' : description, 'params' : { 'floor' : floor } }
        return self.schedule_action(timestamp, action)

    def set_current_setpoint_delayed(self, timestamp, description, thermostat, temperature):
        """ Delayed version of set_current_setpoint. """
        action = { 'type' : 'basic', 'action' : 'set_current_setpoint',
                   'description' : description,
                   'params' : { 'thermostat': thermostat, 'temperature': temperature } }
        return self.schedule_action(timestamp, action)

    def set_mode_delayed(self, timestamp, description, on, automatic, setpoint):
        """ Delayed version of set_mode. """
        action = { 'type' : 'basic', 'action' : 'set_thermostat_mode',
                   'description' : description,
                   'params' : { 'thermostat_on': on, 'automatic': automatic, 'setpoint': setpoint } }
        return self.schedule_action(timestamp, action)

    def do_group_action_delayed(self, timestamp, description, group_action_id):
        """ Delayed version of do_group_action. """
        action = { 'type' : 'basic', 'action' : 'do_group_action',
                   'description' : description,
                   'params' : { 'group_action_id': group_action_id } }
        return self.schedule_action(timestamp, action)

    ######### Master configuration api functions #########

    def get_output_configuration(self, id):
        """
        Get a specific output_configuration defined by its id.

        :param id: The id of the output_configuration
        :type id: Id
        :returns: output_configuration dict: contains 'id' (Id), 'floor' (Byte), 'module_type' (String[1]), 'name' (String[16]), 'timer' (Word), 'type' (Byte)
        """
        return self.exec_action("get_output_configuration", post_data = { "id" : id })

    def get_output_configurations(self):
        """
        Get all output_configurations.

        :returns: list of output_configuration dict: contains 'id' (Id), 'floor' (Byte), 'module_type' (String[1]), 'name' (String[16]), 'timer' (Word), 'type' (Byte)
        """
        return self.exec_action("get_output_configurations")

    def set_output_configuration(self, config):
        """
        Set one output_configuration.

        :param config: The output_configuration to set
        :type config: output_configuration dict: contains 'id' (Id), 'floor' (Byte), 'name' (String[16]), 'timer' (Word), 'type' (Byte)
        """
        return self.exec_action("set_output_configuration", post_data = { "config" : json.dumps(config) })

    def set_output_configurations(self, config):
        """
        Set multiple output_configurations.

        :param config: The list of output_configurations to set
        :type config: list of output_configuration dict: contains 'id' (Id), 'floor' (Byte), 'name' (String[16]), 'timer' (Word), 'type' (Byte)
        """
        return self.exec_action("set_output_configurations", post_data = { "config" : json.dumps(config) })

    def get_input_configuration(self, id):
        """
        Get a specific input_configuration defined by its id.

        :param id: The id of the input_configuration
        :type id: Id
        :returns: input_configuration dict: contains 'id' (Id), 'action' (Byte), 'basic_actions' (Actions[15]), 'invert' (Byte), 'module_type' (String[1]), 'name' (String[8])
        """
        return self.exec_action("get_input_configuration", post_data = { "id" : id })

    def get_input_configurations(self):
        """
        Get all input_configurations.

        :returns: list of input_configuration dict: contains 'id' (Id), 'action' (Byte), 'basic_actions' (Actions[15]), 'invert' (Byte), 'module_type' (String[1]), 'name' (String[8])
        """
        return self.exec_action("get_input_configurations")

    def set_input_configuration(self, config):
        """
        Set one input_configuration.

        :param config: The input_configuration to set
        :type config: input_configuration dict: contains 'id' (Id), 'action' (Byte), 'basic_actions' (Actions[15]), 'invert' (Byte), 'name' (String[8])
        """
        return self.exec_action("set_input_configuration", post_data = { "config" : json.dumps(config) })

    def set_input_configurations(self, config):
        """
        Set multiple input_configurations.

        :param config: The list of input_configurations to set
        :type config: list of input_configuration dict: contains 'id' (Id), 'action' (Byte), 'basic_actions' (Actions[15]), 'invert' (Byte), 'name' (String[8])
        """
        return self.exec_action("set_input_configurations", post_data = { "config" : json.dumps(config) })

    def get_thermostat_configuration(self, id):
        """
        Get a specific thermostat_configuration defined by its id.

        :param id: The id of the thermostat_configuration
        :type id: Id
        :returns: thermostat_configuration dict: contains 'id' (Id), 'auto_fri' ([temp_n(Temp),start_d1(Time),stop_d1(Time),temp_d1(Temp),start_d2(Time),stop_d2(Time),temp_d2(Temp)]), 'auto_mon' ([temp_n(Temp),start_d1(Time),stop_d1(Time),temp_d1(Temp),start_d2(Time),stop_d2(Time),temp_d2(Temp)]), 'auto_sat' ([temp_n(Temp),start_d1(Time),stop_d1(Time),temp_d1(Temp),start_d2(Time),stop_d2(Time),temp_d2(Temp)]), 'auto_sun' ([temp_n(Temp),start_d1(Time),stop_d1(Time),temp_d1(Temp),start_d2(Time),stop_d2(Time),temp_d2(Temp)]), 'auto_thu' ([temp_n(Temp),start_d1(Time),stop_d1(Time),temp_d1(Temp),start_d2(Time),stop_d2(Time),temp_d2(Temp)]), 'auto_tue' ([temp_n(Temp),start_d1(Time),stop_d1(Time),temp_d1(Temp),start_d2(Time),stop_d2(Time),temp_d2(Temp)]), 'auto_wed' ([temp_n(Temp),start_d1(Time),stop_d1(Time),temp_d1(Temp),start_d2(Time),stop_d2(Time),temp_d2(Temp)]), 'name' (String[16]), 'output0' (Byte), 'output1' (Byte), 'pid_d' (Byte), 'pid_i' (Byte), 'pid_int' (Byte), 'pid_p' (Byte), 'sensor' (Byte), 'setp0' (Temp), 'setp1' (Temp), 'setp2' (Temp), 'setp3' (Temp), 'setp4' (Temp), 'setp5' (Temp)
        """
        return self.exec_action("get_thermostat_configuration", post_data = { "id" : id })

    def get_thermostat_configurations(self):
        """
        Get all thermostat_configurations.

        :returns: list of thermostat_configuration dict: contains 'id' (Id), 'auto_fri' ([temp_n(Temp),start_d1(Time),stop_d1(Time),temp_d1(Temp),start_d2(Time),stop_d2(Time),temp_d2(Temp)]), 'auto_mon' ([temp_n(Temp),start_d1(Time),stop_d1(Time),temp_d1(Temp),start_d2(Time),stop_d2(Time),temp_d2(Temp)]), 'auto_sat' ([temp_n(Temp),start_d1(Time),stop_d1(Time),temp_d1(Temp),start_d2(Time),stop_d2(Time),temp_d2(Temp)]), 'auto_sun' ([temp_n(Temp),start_d1(Time),stop_d1(Time),temp_d1(Temp),start_d2(Time),stop_d2(Time),temp_d2(Temp)]), 'auto_thu' ([temp_n(Temp),start_d1(Time),stop_d1(Time),temp_d1(Temp),start_d2(Time),stop_d2(Time),temp_d2(Temp)]), 'auto_tue' ([temp_n(Temp),start_d1(Time),stop_d1(Time),temp_d1(Temp),start_d2(Time),stop_d2(Time),temp_d2(Temp)]), 'auto_wed' ([temp_n(Temp),start_d1(Time),stop_d1(Time),temp_d1(Temp),start_d2(Time),stop_d2(Time),temp_d2(Temp)]), 'name' (String[16]), 'output0' (Byte), 'output1' (Byte), 'pid_d' (Byte), 'pid_i' (Byte), 'pid_int' (Byte), 'pid_p' (Byte), 'sensor' (Byte), 'setp0' (Temp), 'setp1' (Temp), 'setp2' (Temp), 'setp3' (Temp), 'setp4' (Temp), 'setp5' (Temp)
        """
        return self.exec_action("get_thermostat_configurations")

    def set_thermostat_configuration(self, config):
        """
        Set one thermostat_configuration.

        :param config: The thermostat_configuration to set
        :type config: thermostat_configuration dict: contains 'id' (Id), 'auto_fri' ([temp_n(Temp),start_d1(Time),stop_d1(Time),temp_d1(Temp),start_d2(Time),stop_d2(Time),temp_d2(Temp)]), 'auto_mon' ([temp_n(Temp),start_d1(Time),stop_d1(Time),temp_d1(Temp),start_d2(Time),stop_d2(Time),temp_d2(Temp)]), 'auto_sat' ([temp_n(Temp),start_d1(Time),stop_d1(Time),temp_d1(Temp),start_d2(Time),stop_d2(Time),temp_d2(Temp)]), 'auto_sun' ([temp_n(Temp),start_d1(Time),stop_d1(Time),temp_d1(Temp),start_d2(Time),stop_d2(Time),temp_d2(Temp)]), 'auto_thu' ([temp_n(Temp),start_d1(Time),stop_d1(Time),temp_d1(Temp),start_d2(Time),stop_d2(Time),temp_d2(Temp)]), 'auto_tue' ([temp_n(Temp),start_d1(Time),stop_d1(Time),temp_d1(Temp),start_d2(Time),stop_d2(Time),temp_d2(Temp)]), 'auto_wed' ([temp_n(Temp),start_d1(Time),stop_d1(Time),temp_d1(Temp),start_d2(Time),stop_d2(Time),temp_d2(Temp)]), 'name' (String[16]), 'output0' (Byte), 'output1' (Byte), 'pid_d' (Byte), 'pid_i' (Byte), 'pid_int' (Byte), 'pid_p' (Byte), 'sensor' (Byte), 'setp0' (Temp), 'setp1' (Temp), 'setp2' (Temp), 'setp3' (Temp), 'setp4' (Temp), 'setp5' (Temp)
        """
        return self.exec_action("set_thermostat_configuration", post_data = { "config" : json.dumps(config) })

    def set_thermostat_configurations(self, config):
        """
        Set multiple thermostat_configurations.

        :param config: The list of thermostat_configurations to set
        :type config: list of thermostat_configuration dict: contains 'id' (Id), 'auto_fri' ([temp_n(Temp),start_d1(Time),stop_d1(Time),temp_d1(Temp),start_d2(Time),stop_d2(Time),temp_d2(Temp)]), 'auto_mon' ([temp_n(Temp),start_d1(Time),stop_d1(Time),temp_d1(Temp),start_d2(Time),stop_d2(Time),temp_d2(Temp)]), 'auto_sat' ([temp_n(Temp),start_d1(Time),stop_d1(Time),temp_d1(Temp),start_d2(Time),stop_d2(Time),temp_d2(Temp)]), 'auto_sun' ([temp_n(Temp),start_d1(Time),stop_d1(Time),temp_d1(Temp),start_d2(Time),stop_d2(Time),temp_d2(Temp)]), 'auto_thu' ([temp_n(Temp),start_d1(Time),stop_d1(Time),temp_d1(Temp),start_d2(Time),stop_d2(Time),temp_d2(Temp)]), 'auto_tue' ([temp_n(Temp),start_d1(Time),stop_d1(Time),temp_d1(Temp),start_d2(Time),stop_d2(Time),temp_d2(Temp)]), 'auto_wed' ([temp_n(Temp),start_d1(Time),stop_d1(Time),temp_d1(Temp),start_d2(Time),stop_d2(Time),temp_d2(Temp)]), 'name' (String[16]), 'output0' (Byte), 'output1' (Byte), 'pid_d' (Byte), 'pid_i' (Byte), 'pid_int' (Byte), 'pid_p' (Byte), 'sensor' (Byte), 'setp0' (Temp), 'setp1' (Temp), 'setp2' (Temp), 'setp3' (Temp), 'setp4' (Temp), 'setp5' (Temp)
        """
        return self.exec_action("set_thermostat_configurations", post_data = { "config" : json.dumps(config) })

    def get_sensor_configuration(self, id):
        """
        Get a specific sensor_configuration defined by its id.

        :param id: The id of the sensor_configuration
        :type id: Id
        :returns: sensor_configuration dict: contains 'id' (Id), 'name' (String[16]), 'offset' (SignedTemp(-7.5 to 7.5 degrees))
        """
        return self.exec_action("get_sensor_configuration", post_data = { "id" : id })

    def get_sensor_configurations(self):
        """
        Get all sensor_configurations.

        :returns: list of sensor_configuration dict: contains 'id' (Id), 'name' (String[16]), 'offset' (SignedTemp(-7.5 to 7.5 degrees))
        """
        return self.exec_action("get_sensor_configurations")

    def set_sensor_configuration(self, config):
        """
        Set one sensor_configuration.

        :param config: The sensor_configuration to set
        :type config: sensor_configuration dict: contains 'id' (Id), 'name' (String[16]), 'offset' (SignedTemp(-7.5 to 7.5 degrees))
        """
        return self.exec_action("set_sensor_configuration", post_data = { "config" : json.dumps(config) })

    def set_sensor_configurations(self, config):
        """
        Set multiple sensor_configurations.

        :param config: The list of sensor_configurations to set
        :type config: list of sensor_configuration dict: contains 'id' (Id), 'name' (String[16]), 'offset' (SignedTemp(-7.5 to 7.5 degrees))
        """
        return self.exec_action("set_sensor_configurations", post_data = { "config" : json.dumps(config) })

    def get_pump_group_configuration(self, id):
        """
        Get a specific pump_group_configuration defined by its id.

        :param id: The id of the pump_group_configuration
        :type id: Id
        :returns: pump_group_configuration dict: contains 'id' (Id), 'outputs' (CSV[32])
        """
        return self.exec_action("get_pump_group_configuration", post_data = { "id" : id })

    def get_pump_group_configurations(self):
        """
        Get all pump_group_configurations.

        :returns: list of pump_group_configuration dict: contains 'id' (Id), 'outputs' (CSV[32])
        """
        return self.exec_action("get_pump_group_configurations")

    def set_pump_group_configuration(self, config):
        """
        Set one pump_group_configuration.

        :param config: The pump_group_configuration to set
        :type config: pump_group_configuration dict: contains 'id' (Id), 'outputs' (CSV[32])
        """
        return self.exec_action("set_pump_group_configuration", post_data = { "config" : json.dumps(config) })

    def set_pump_group_configurations(self, config):
        """
        Set multiple pump_group_configurations.

        :param config: The list of pump_group_configurations to set
        :type config: list of pump_group_configuration dict: contains 'id' (Id), 'outputs' (CSV[32])
        """
        return self.exec_action("set_pump_group_configurations", post_data = { "config" : json.dumps(config) })

    def get_group_action_configuration(self, id):
        """
        Get a specific group_action_configuration defined by its id.

        :param id: The id of the group_action_configuration
        :type id: Id
        :returns: group_action_configuration dict: contains 'id' (Id), 'actions' (Actions[16]), 'name' (String[16])
        """
        return self.exec_action("get_group_action_configuration", post_data = { "id" : id })

    def get_group_action_configurations(self):
        """
        Get all group_action_configurations.

        :returns: list of group_action_configuration dict: contains 'id' (Id), 'actions' (Actions[16]), 'name' (String[16])
        """
        return self.exec_action("get_group_action_configurations")

    def set_group_action_configuration(self, config):
        """
        Set one group_action_configuration.

        :param config: The group_action_configuration to set
        :type config: group_action_configuration dict: contains 'id' (Id), 'actions' (Actions[16]), 'name' (String[16])
        """
        return self.exec_action("set_group_action_configuration", post_data = { "config" : json.dumps(config) })

    def set_group_action_configurations(self, config):
        """
        Set multiple group_action_configurations.

        :param config: The list of group_action_configurations to set
        :type config: list of group_action_configuration dict: contains 'id' (Id), 'actions' (Actions[16]), 'name' (String[16])
        """
        return self.exec_action("set_group_action_configurations", post_data = { "config" : json.dumps(config) })

    def get_scheduled_action_configuration(self, id):
        """
        Get a specific scheduled_action_configuration defined by its id.

        :param id: The id of the scheduled_action_configuration
        :type id: Id
        :returns: scheduled_action_configuration dict: contains 'id' (Id), 'action' (Actions[1]), 'day' (Byte), 'hour' (Byte), 'minute' (Byte)
        """
        return self.exec_action("get_scheduled_action_configuration", post_data = { "id" : id })

    def get_scheduled_action_configurations(self):
        """
        Get all scheduled_action_configurations.

        :returns: list of scheduled_action_configuration dict: contains 'id' (Id), 'action' (Actions[1]), 'day' (Byte), 'hour' (Byte), 'minute' (Byte)
        """
        return self.exec_action("get_scheduled_action_configurations")

    def set_scheduled_action_configuration(self, config):
        """
        Set one scheduled_action_configuration.

        :param config: The scheduled_action_configuration to set
        :type config: scheduled_action_configuration dict: contains 'id' (Id), 'action' (Actions[1]), 'day' (Byte), 'hour' (Byte), 'minute' (Byte)
        """
        return self.exec_action("set_scheduled_action_configuration", post_data = { "config" : json.dumps(config) })

    def set_scheduled_action_configurations(self, config):
        """
        Set multiple scheduled_action_configurations.

        :param config: The list of scheduled_action_configurations to set
        :type config: list of scheduled_action_configuration dict: contains 'id' (Id), 'action' (Actions[1]), 'day' (Byte), 'hour' (Byte), 'minute' (Byte)
        """
        return self.exec_action("set_scheduled_action_configurations", post_data = { "config" : json.dumps(config) })

    def get_pulse_counter_configuration(self, id):
        """
        Get a specific pulse_counter_configuration defined by its id.

        :param id: The id of the pulse_counter_configuration
        :type id: Id
        :returns: pulse_counter_configuration dict: contains 'id' (Id), 'input' (Byte), 'name' (String[16])
        """
        return self.exec_action("get_pulse_counter_configuration", post_data = { "id" : id })

    def get_pulse_counter_configurations(self):
        """
        Get all pulse_counter_configurations.

        :returns: list of pulse_counter_configuration dict: contains 'id' (Id), 'input' (Byte), 'name' (String[16])
        """
        return self.exec_action("get_pulse_counter_configurations")

    def set_pulse_counter_configuration(self, config):
        """
        Set one pulse_counter_configuration.

        :param config: The pulse_counter_configuration to set
        :type config: pulse_counter_configuration dict: contains 'id' (Id), 'input' (Byte), 'name' (String[16])
        """
        return self.exec_action("set_pulse_counter_configuration", post_data = { "config" : json.dumps(config) })

    def set_pulse_counter_configurations(self, config):
        """
        Set multiple pulse_counter_configurations.

        :param config: The list of pulse_counter_configurations to set
        :type config: list of pulse_counter_configuration dict: contains 'id' (Id), 'input' (Byte), 'name' (String[16])
        """
        return self.exec_action("set_pulse_counter_configurations", post_data = { "config" : json.dumps(config) })

    def get_startup_action_configuration(self):
        """
        Get the startup_action_configuration.

        :returns: startup_action_configuration dict: contains 'actions' (Actions[100])
        """
        return self.exec_action("get_startup_action_configuration")

    def set_startup_action_configuration(self, config):
        """
        Set the startup_action_configuration.

        :param config: The startup_action_configuration to set
        :type config: startup_action_configuration dict: contains 'actions' (Actions[100])
        """
        return self.exec_action("set_startup_action_configuration", post_data = { "config" : json.dumps(config) })

    def get_dimmer_configuration(self):
        """
        Get the dimmer_configuration.

        :returns: dimmer_configuration dict: contains 'dim_memory' (Byte), 'dim_step' (Byte), 'dim_wait_cycle' (Byte), 'min_dim_level' (Byte)
        """
        return self.exec_action("get_dimmer_configuration")

    def set_dimmer_configuration(self, config):
        """
        Set the dimmer_configuration.

        :param config: The dimmer_configuration to set
        :type config: dimmer_configuration dict: contains 'dim_memory' (Byte), 'dim_step' (Byte), 'dim_wait_cycle' (Byte), 'min_dim_level' (Byte)
        """
        return self.exec_action("set_dimmer_configuration", post_data = { "config" : json.dumps(config) })

    def get_global_thermostat_configuration(self):
        """
        Get the global_thermostat_configuration.

        :returns: global_thermostat_configuration dict: contains 'outside_sensor' (Byte), 'pump_delay' (Byte), 'threshold_temp' (Temp)
        """
        return self.exec_action("get_global_thermostat_configuration")

    def set_global_thermostat_configuration(self, config):
        """
        Set the global_thermostat_configuration.

        :param config: The global_thermostat_configuration to set
        :type config: global_thermostat_configuration dict: contains 'outside_sensor' (Byte), 'pump_delay' (Byte), 'threshold_temp' (Temp)
        """
        return self.exec_action("set_global_thermostat_configuration", post_data = { "config" : json.dumps(config) })


    def get_room_configurations(self):
        """
        Get all room_configurations.
        :param fields: The field of the room_configuration to get. (None gets all fields)
        :type fields: List of strings
        :returns: list of room_configuration dict: contains 'id' (Id), 'floor' (Byte), 'name' (String)
        """
        return self.exec_action("get_room_configurations")

class OpenMoticsCloudApi(OpenMoticsApi):
    """ Connector for the OpenMotics Cloud API. """

    MSG_OUTPUT_CHANGE       = "TYPE_OUTPUT_CHANGE"
    MSG_THERMOSTAT_CHANGE   = "TYPE_THERMOSTAT_CHANGE"
    MSG_RT_POWER_RAW        = "TYPE_RT_POWER_RAW"
    MSG_RT_POWER_TAGS       = "TYPE_RT_POWER_TAGS"
    MSG_RT_PULSE_COUNTERS   = "TYPE_RT_PULSE_COUNTERS"
    MSG_RT_ENERGY_SUPPLIERS = "TYPE_RT_ENERGY_SUPPLIERS"
    MSG_RT_ENERGY_MODULES   = "TYPE_RT_ENERGY_MODULES"
    MSG_RT_ENERGY_TAGS      = "TYPE_RT_ENERGY_TAGS"

    def __init__(self, username, password):
        """ Create a new cloud connector using the cloud username and password. """
        OpenMoticsApi.__init__(self, username, password, "cloud.openmotics.com", True)
        self.installations = None
        self.installation_id = None

    def get_url(self, action):
        """ Get the url for an action. """
        return "https://%s/api/%s" % (self.hostname, action)

    def get_post_data(self, post_data):
        """ Get the full post data dict. This method adds the token and installation id to the dict. """
        d = OpenMoticsApi.get_post_data(self, post_data)
        if self.installation_id != None:
            d["installation_id"] = self.installation_id
        return d

    def login(self):
        """
        Login to the gateway: sets the token in the connector. The installations for the user
        are also fetched and the installation_id is set when only one installation is available.
        """
        result = self.fetch_url("login", self.auth)
        if not result["success"]:
            raise AuthenticationException()
        else:
            self.token = result["token"]
            self.installations = self.get_installations()
            if len(self.installations) >= 1:
                self.installation_id = self.installations[0]["id"]

    def get_installations(self):
        """ Get all installations for the current user. """
        if self.installations == None:
            self.installations = self.exec_action("get_installations")
        return self.installations

    def set_installation_id(self, installation_id):
        """
        Set the current installation.
        Only required when the user has access to multiple installations.
        """
        self.installation_id = installationd_id

    def _update_msg_subscription(self, subscriber_id, message_types):
        """ Update a subscriber with a list of message types. """
        url = "update_message_subscription"
        params = { 'id' : self.installation_id, 'subscriber' : subscriber_id,
                   'timestamp' : int(time.time()) }
        post_data = { 'types' : json.dumps(message_types) }

        return self.exec_action(url, post_data, params)

    def _get_last_msg_id(self, subscriber_id):
        """ Get the id of the last message. """
        url = "get_last_message_id"
        params = { 'id' : self.installation_id, 'subscriber' : subscriber_id,
                   'timestamp' : int(time.time()) }

        return self.exec_action(url, {}, params, False)

    def _get_msg(self, subscriber_id, message_id):
        """ Get one message from the messaging system. """
        url = "get_messages_wait"
        params = { 'id' : self.installation_id, 'subscriber' : subscriber_id,
                   'messageid' : message_id, 'timestamp' : int(time.time()) }

        return self.exec_action(url, {}, params)


    def msg_loop(self, message_types, callback):
        """
        Start a message loop. message_types should contain a list of message types
        that the callback should receive. The callback is a function that returns
        a boolean, if the callback returns False, the message loop is terminated.
        """
        self.login()

        subscriber_id = random.randint(0, 1000000)
        msg_id = 0

        self._update_msg_subscription(subscriber_id, message_types)
        msg_id = self._get_last_msg_id(subscriber_id)

        while True:
            msg = self._get_msg(subscriber_id, msg_id)
            msg_id = msg["last_message_id"]
            messages = msg["messages"]

            for msg in messages:
                if callback(msg) is False:
                    return
