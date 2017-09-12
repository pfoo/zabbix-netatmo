# https://dev.netatmo.com/en-US/resources/technical/reference/weatherstation/getstationsdata
import requests
import sys
import six
import os
import datetime

#import configparser for both python2 and 3
try:
  import configparser
except:
  from six.moves import configparser

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
    access_token=response.json()['access_token']
    refresh_token=response.json()['refresh_token']
    expires_in=response.json()['expires_in']
    #print("Your access token is:", access_token)
    #print("Your refresh token is:", refresh_token)
    #print("Token expires in (s):", expires_in)
    #update in memory config and write it to config file
    Config.set('token', 'access_token', access_token)
    Config.set('token', 'refresh_token', refresh_token)
    Config.set('token', 'token_expires', str(expires_in))
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
  if not device_id:
    payload = {
      'access_token': Config.get('token', 'access_token'),
    }
  response = requests.post('https://api.netatmo.com/api/getstationsdata', data=payload)
  response.raise_for_status()
  data = response.json()['body']
  #import json
  #print(json.dumps(data))
  #Remove config from memory
  del Config

  #Parse json for trappers metrics recovery and format them for zabbix-sender
  if not sys.argv[1:]:
    for station in data['devices']:
      print("- netatmo.{}.{}.wifi_status {}".format(station['station_name'].lower(), station['module_name'].lower(), station['wifi_status']))
      if station['type'] == 'NAMain':
        print("- netatmo.{}.{}.noise {}".format(station['station_name'].lower(), station['module_name'].lower(), station['dashboard_data']['Noise']))
        print("- netatmo.{}.{}.temperature {}".format(station['station_name'].lower(), station['module_name'].lower(), station['dashboard_data']['Temperature']))
        print("- netatmo.{}.{}.humidity {}".format(station['station_name'].lower(), station['module_name'].lower(), station['dashboard_data']['Humidity']))
        print("- netatmo.{}.{}.pressure {}".format(station['station_name'].lower(), station['module_name'].lower(), station['dashboard_data']['Pressure']))
        print("- netatmo.{}.{}.co2 {}".format(station['station_name'].lower(), station['module_name'].lower(), station['dashboard_data']['CO2']))
      for module in station['modules']:
        print("- netatmo.{}.{}.rf_status {}".format(station['station_name'].lower(),  module['module_name'].lower(), module['rf_status']))
        print("- netatmo.{}.{}.battery_status {}".format(station['station_name'].lower(),  module['module_name'].lower(), module['battery_vp']))
        print("- netatmo.{}.{}.battery_percent {}".format(station['station_name'].lower(),  module['module_name'].lower(), module['battery_percent']))
        if module['type'] in ['NAModule4', 'NAModule1']:
          print("- netatmo.{}.{}.temperature {}".format(station['station_name'].lower(),  module['module_name'].lower(), module['dashboard_data']['Temperature']))
          print("- netatmo.{}.{}.humidity {}".format(station['station_name'].lower(),  module['module_name'].lower(), module['dashboard_data']['Humidity']))
        if module['type'] == 'NAModule4':
          print("- netatmo.{}.{}.co2 {}".format(station['station_name'].lower(),  module['module_name'].lower(), module['dashboard_data']['CO2']))
        # Placeholder for wind gauge (2) and rain gauge (3)
        #if module['type'] == 'NAModule2':
        #if module['type'] == 'NAModule3':

  #Parse json for discovery and format them for zabbix-sender
  if sys.argv[1:]:
    if sys.argv[1] == 'discovery':
      import json
      print('todo')
      for station in data['devices']:
        print(station['station_name'].lower())
        print(station['module_name'].lower())
        print(json.dumps(station['data_type']))
        for module in station['modules']:
          print(module['module_name'].lower())
          print(json.dumps(module['data_type']))

except requests.exceptions.HTTPError as error:
  print(error.response.status_code, error.response.text)
  sys.exit(1)
except requests.exceptions.RequestException as error:
  print(error)
  sys.exit(1)
