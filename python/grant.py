# https://dev.netatmo.com/en-US/resources/technical/guides/authentication/clientcredentials
import requests
import six

try:
    import configparser
except:
    from six.moves import configparser

Config = configparser.ConfigParser()
Config.read('config.ini')

payload = {'grant_type': 'password',
           'username': Config.get('main', 'username'),
           'password': Config.get('main', 'password'),
           'client_id': Config.get('main', 'client_id'),
           'client_secret': Config.get('main', 'client_secret'),
           'scope': 'read_station'}

try:
    response = requests.post('https://api.netatmo.com/oauth2/token', data=payload)
    response.raise_for_status()
    access_token=response.json()['access_token']
    refresh_token=response.json()['refresh_token']
    expires_in=response.json()['expires_in']
    scope=response.json()['scope']
    print("Your access token is:", access_token)
    print("Your refresh token is:", refresh_token)
    print("Token expires in (s):", expires_in)

    Config.set('token', 'access_token', access_token)
    Config.set('token', 'refresh_token', refresh_token)
    Config.set('token', 'token_expires', expires_in)
    with open('config.ini', 'w') as configfile:
        Config.write(configfile)
        configfile.close()

except requests.exceptions.HTTPError as error:
    print(error.response.status_code, error.response.text)
except requests.exceptions.RequestException as error:
    print(error)
