<?php

//require php5-curl

require_once("src/Netatmo/autoload.php");

$config = array();
$config['client_id'] = "client-id-from-dev.netatmo.com";
$config['client_secret'] = "client-secret-from-dev.netatmo.com";
$config['scope'] = 'read_station read_thermostat write_thermostat';
$client = new Netatmo\Clients\NAWSApiClient($config);



#token
$username = "your-netatmo-login";
$pwd = "your-netatmo-password";
$client->setVariable('username', $username);
$client->setVariable('password', $pwd);
try
{
    $tokens = $client->getAccessToken();
    $refresh_token = $tokens["refresh_token"];
    $access_token = $tokens["access_token"];
}
catch(Netatmo\Exceptions\NAClientException $ex)
{
    echo "An error occcured while trying to retrieve your tokens \n";
}

$data = $client->getData(NULL, TRUE);

foreach($data['devices'] as $device)
{
//    print_r($device['dashboard_data']);
//    echo "Device name: " . $device['station_name'] . "\n";
    if ($argv[1] == "discovery") {
        echo "Device name: " . $device['station_name'] . "\n";
    }
    elseif ($argv[1] == "data") {
       echo "- netatmo." . $device['station_name'] . ".main.pressure " . $device['dashboard_data']['Pressure'] . "\n";
       echo "- netatmo." . $device['station_name'] . ".main.noise " . $device['dashboard_data']['Noise'] . "\n";
       echo "- netatmo." . $device['station_name'] . ".main.temp " . $device['dashboard_data']['Temperature'] . "\n";
       echo "- netatmo." . $device['station_name'] . ".main.humidity " . $device['dashboard_data']['Humidity'] . "\n";
       echo "- netatmo." . $device['station_name'] . ".main.co2 " . $device['dashboard_data']['CO2'] . "\n";
    }

       foreach($device['modules'] as $module)
       {
        //print_r($module['dashboard_data']);
           if ($argv[1] == "discovery") {
              echo "Module name: " . $module['module_name'] . "\n";
           }
           elseif ($argv[1] == "data") {
              echo "- netatmo." . $device['station_name'] . "." . $module['module_name'] . ".temp " . $module['dashboard_data']['Temperature'] . "\n";
              echo "- netatmo." . $device['station_name'] . "." . $module['module_name'] . ".humdity " . $module['dashboard_data']['Humidity'] . "\n";
              if(isset($module['dashboard_data']['CO2'])){
                 echo "- netatmo." . $device['station_name'] . "." . $module['module_name'] . ".co2 " . $module['dashboard_data']['CO2'] . "\n";
              }
           }
       }
}


?>
