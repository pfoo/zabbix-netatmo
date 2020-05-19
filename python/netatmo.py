#!/usr/bin/python
# -*- coding: UTF-8 -*-
# API : https://dev.netatmo.com/en-US/resources/technical/reference/weatherstation/getstationsdata
import requests
import sys
import six
import os
import datetime
import pprint

#import configparser for both python2 and 3
try:
    import configparser
except:
    from six.moves import configparser

def unitwrapper(type):
    unit = ''
    if type.lower() == 'temperature':
      if data['user']['administrative']['unit'] == 0: unit = 'C'
      if data['user']['administrative']['unit'] == 1: unit = 'F'
    if type.lower() == 'rain':
      if data['user']['administrative']['unit'] == 0: unit = 'mm'
      if data['user']['administrative']['unit'] == 1: unit = 'inches'
    if type.lower() == 'pressure':
      if data['user']['administrative']['pressureunit'] == 0: unit = 'Bar'
      if data['user']['administrative']['pressureunit'] == 1: unit = 'inHg'
      if data['user']['administrative']['pressureunit'] == 2: unit = 'mmHg'
    if type.lower() == 'wind': 
      if data['user']['administrative']['windunit'] == 0: unit = 'kph'
      if data['user']['administrative']['windunit'] == 1: unit = 'mph'
      if data['user']['administrative']['windunit'] == 2: unit = 'm/s'
      if data['user']['administrative']['windunit'] == 3: unit = 'beaufort'
      if data['user']['administrative']['windunit'] == 4: unit = 'knot'
    return unit

#load config
Config = configparser.ConfigParser()
Config.read(os.path.join(sys.path[0], 'config.ini'))

try:

  #Renew access_token if necessary
  elapsed = datetime.datetime.now() - datetime.datetime.strptime(Config.get('token', 'last_renewed'), '%Y-%m-%d %H:%M:%S.%f')
  #compare time of previous token renew and current time with token expires duration
  # substracting 30s to real token expiration in case we run just before expiration (remote server might receive the request after expiration and deny it otherwise)
  if elapsed > datetime.timedelta(seconds=int(Config.get('token', 'token_expires'))-30):
    payload = {'grant_type': 'refresh_token',
           'refresh_token': Config.get('token', 'refresh_token'),
           'client_id': Config.get('main', 'client_id'),
           'client_secret': Config.get('main', 'client_secret')}
    response = requests.post('https://api.netatmo.com/oauth2/token', data=payload)
    response.raise_for_status()
    #update in memory config and write it to config file
    Config.set('token', 'access_token', response.json()['access_token'])
    Config.set('token', 'refresh_token', response.json()['refresh_token'])
    Config.set('token', 'token_expires', str(response.json()['expires_in']))
    Config.set('token', 'last_renewed', str(datetime.datetime.now()))
    with open(os.path.join(sys.path[0], 'config.ini'), 'w') as configfile:
        Config.write(configfile)
        configfile.close()
  
  #POST request and get json in response
  device_id = Config.get('main', 'device_id')
  if device_id:
    payload = {
      'access_token': Config.get('token', 'access_token'),
      'device_id': device_id
    }
  else:
    payload = {
      'access_token': Config.get('token', 'access_token')
    }
  response = requests.post('https://api.netatmo.com/api/getstationsdata', data=payload)
  response.raise_for_status()
  data = response.json()['body']
  #Remove config from memory
  del Config
  
  #Parse json for trappers metrics recovery and format them for zabbix-sender
  if not sys.argv[1:]:
    for station in data['devices']:
      #Stations gather data every 10mn or so. If the data provided by the API for a station is older than 15mn, it is old data from from a broken or disconnected station so we are not providing them.
      station['connected'] = 0
      elapsed = datetime.datetime.now() - datetime.datetime.fromtimestamp(int(station['dashboard_data']['time_utc']))
      if elapsed < datetime.timedelta(minutes=15):
        station['connected'] = 1
        for type in station['data_type']:
          #zabbix expects value in main unit (bar) but netatmo api provide a mbar value. Others units (inHg, mmHg) should work as is.
          if type == 'Pressure' and data['user']['administrative']['pressureunit'] == 0: station['dashboard_data'][type] = station['dashboard_data'][type]/1000
          print("- netatmo.weather.{}.{}[{},{}] {}".format(station['type'].lower(), type.lower(), station['station_name'].lower(), station['module_name'].lower(), station['dashboard_data'][type]))
      #print the connected status and the wifi status as it might provides informations on why the station is not connected
      print("- netatmo.weather.namain.connected[{},{}] {}".format(station['station_name'].lower(), station['module_name'].lower(), station['connected']))
      print("- netatmo.weather.namain.wifi_status[{},{}] {}".format(station['station_name'].lower(), station['module_name'].lower(), station['wifi_status']))

      for module in station['modules']:
        #Modules gather data every 10mn or so. If the data provided by the API for a module is older than 15mn, it is old data from a broken or unpowered module so we are not providing them.
        module['connected'] = 0
        elapsed = datetime.datetime.now() - datetime.datetime.fromtimestamp(int(module['dashboard_data']['time_utc']))
        if elapsed < datetime.timedelta(minutes=15):
          module['connected'] = 1
          # anemometer
          if module['type'].lower() == 'namodule2':
              print("- netatmo.weather.{}.{}[{},{}] {}".format(module['type'].lower(), 'windstrength', station['station_name'].lower(), module['module_name'].lower(), module['dashboard_data']['WindStrength']))
              print("- netatmo.weather.{}.{}[{},{}] {}".format(module['type'].lower(), 'windangle', station['station_name'].lower(), module['module_name'].lower(), module['dashboard_data']['WindAngle']))
              print("- netatmo.weather.{}.{}[{},{}] {}".format(module['type'].lower(), 'guststrength', station['station_name'].lower(), module['module_name'].lower(), module['dashboard_data']['GustStrength']))
              print("- netatmo.weather.{}.{}[{},{}] {}".format(module['type'].lower(), 'gustangle', station['station_name'].lower(), module['module_name'].lower(), module['dashboard_data']['GustAngle']))
              print("- netatmo.weather.{}.{}[{},{}] {}".format(module['type'].lower(), 'max_wind_angle', station['station_name'].lower(), module['module_name'].lower(), module['dashboard_data']['max_wind_angle']))
              print("- netatmo.weather.{}.{}[{},{}] {}".format(module['type'].lower(), 'max_wind_str', station['station_name'].lower(), module['module_name'].lower(), module['dashboard_data']['max_wind_str']))
              print("- netatmo.weather.{}.{}[{},{}] {}".format(module['type'].lower(), 'date_max_wind_str', station['station_name'].lower(), module['module_name'].lower(), module['dashboard_data']['date_max_wind_str']))
          # rain gauge
          elif module['type'].lower() == 'namodule3':
             print("- netatmo.weather.{}.{}[{},{}] {}".format(module['type'].lower(), 'rain', station['station_name'].lower(), module['module_name'].lower(), module['dashboard_data']['Rain']))
             print("- netatmo.weather.{}.{}[{},{}] {}".format(module['type'].lower(), 'sum_rain_1', station['station_name'].lower(), module['module_name'].lower(), module['dashboard_data']['sum_rain_1']))
             print("- netatmo.weather.{}.{}[{},{}] {}".format(module['type'].lower(), 'sum_rain_24', station['station_name'].lower(), module['module_name'].lower(), module['dashboard_data']['sum_rain_24']))
          # everything else
          else:
              for type in module['data_type']:
                  print("- netatmo.weather.{}.{}[{},{}] {}".format(module['type'].lower(), type.lower(), station['station_name'].lower(), module['module_name'].lower(), module['dashboard_data'][type]))
        #print the connected and others status as they might provide informations on why the module is not connected
        print("- netatmo.weather.{}.connected[{},{}] {}".format(module['type'].lower(), station['station_name'].lower(),  module['module_name'].lower(), module['connected']))
        print("- netatmo.weather.{}.rf_status[{},{}] {}".format(module['type'].lower(), station['station_name'].lower(),  module['module_name'].lower(), module['rf_status']))
        print("- netatmo.weather.{}.battery_status[{},{}] {}".format(module['type'].lower(), station['station_name'].lower(),  module['module_name'].lower(), module['battery_vp']))
        print("- netatmo.weather.{}.battery_percent[{},{}] {}".format(module['type'].lower(), station['station_name'].lower(),  module['module_name'].lower(), module['battery_percent']))
  
  #Parse json for discovery and format them for zabbix-sender
  if sys.argv[1:]:
    if sys.argv[1] == 'discovery':
      import json
      #variables for json output
      output_station = {}
      output_module1 = {}
      output_module2 = {}
      output_module3 = {}
      output_module4 = {}
      #variables for station/module list
      datalist_station = []
      datalist_module1 = []
      datalist_module2 = []
      datalist_module3 = []
      datalist_module4 = []
      for station in data['devices']:
        curdata = {}
        curdata['{#STATION_NAME}'] = station['station_name'].lower()
        curdata['{#MODULE_NAME}'] = station['module_name'].lower()
        curdata['{#TEMPERATURE_UNIT}'] = unitwrapper('temperature')
        curdata['{#PRESSURE_UNIT}'] = unitwrapper('pressure')
        datalist_station.append(curdata)
        for module in station['modules']:
          curdata = {}
          curdata['{#STATION_NAME}'] = station['station_name'].lower()
          curdata['{#MODULE_NAME}'] = module['module_name'].lower()
          if module['type'].lower() == 'namodule1': 
            curdata['{#TEMPERATURE_UNIT}'] = unitwrapper('temperature')
            datalist_module1.append(curdata)
          if module['type'].lower() == 'namodule2':
            curdata['{#WIND_UNIT}'] = unitwrapper('wind')
            datalist_module2.append(curdata)
          if module['type'].lower() == 'namodule3':
            curdata['{#RAIN_UNIT}'] = unitwrapper('rain')
            datalist_module3.append(curdata)
          if module['type'].lower() == 'namodule4':
            curdata['{#TEMPERATURE_UNIT}'] = unitwrapper('temperature')
            datalist_module4.append(curdata)
      #push station/modules list into output json
      output_station['data'] = datalist_station
      output_module1['data'] = datalist_module1
      output_module2['data'] = datalist_module2
      output_module3['data'] = datalist_module3
      output_module4['data'] = datalist_module4
      print('- netatmo.weather.station.discovery {}'.format(json.dumps(output_station)))
      print('- netatmo.weather.module.namodule1.discovery {}'.format(json.dumps(output_module1)))
      print('- netatmo.weather.module.namodule2.discovery {}'.format(json.dumps(output_module2)))
      print('- netatmo.weather.module.namodule3.discovery {}'.format(json.dumps(output_module3)))
      print('- netatmo.weather.module.namodule4.discovery {}'.format(json.dumps(output_module4)))

except requests.exceptions.HTTPError as error:
     print(error.response.status_code, error.response.text)
     sys.exit(1)
except requests.exceptions.RequestException as error:
     print(error)
     sys.exit(1)
