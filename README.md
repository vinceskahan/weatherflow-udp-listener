
## Description

This is a quick listener for the WeatherFlow UDP broadcasts that can:

 * print received broadcasts
 * print decoded broadcasts to decoded
 * publish to MQTT
 * optionally mapped to match WeeWX schema

NOTE - this requires at least v91 of the WeatherFlow hub firmware.

## Installation

This requires installing the paho mqtt python library. On a debian(ish) system that can be done by:
```
sudo apt-get install -y python-pip && sudo pip install paho-mqtt
```

##  Usage

```
usage: listen.py [-h] [-r] [-d] [-l LIMIT] [-i] [-m] [-n] [-w]

optional arguments:
  -h, --help            show this help message and exit
  -r, --raw             print raw data to stddout
  -d, --decoded         print decoded data to stdout
  -l LIMIT, --limit LIMIT
                        limit to one obs type
  -i, --indent          indent raw data to stdout (requires -d)
  -m, --mqtt            publish to MQTT
  -n, --no_pub          report but do not publish to MQTT
  -w, --weewx           convert to weewx schema mapping

for --limit, possibilities are:
   rapid_wind, obs_sky, obs_air,
   hub_status, device_status, evt_precip, evt_strike

```

## Typical Usage

### Publishing WeatherFlow data to MQTT

Typically it is expected that this script would be used to generate MQTT publish messages via running as daemon ala:
```
nohup python /usr/local/bin/listen.py --mqtt  --limit "obs_sky obs_air" >/dev/null 2>&1 &
(limit to only two observations)

nohup python /usr/local/bin/listen.py --mqtt  --exclude "rapid_wind"      >/dev/null 2>&1 &
(exclude an observation type)

nohup python /usr/local/bin/listen.py --mqtt  --syslog --exclude "rapid_wind"      >/dev/null 2>&1 &
(exclude an observation type, syslog unknown data received)

```

### Debugging your WeatherFlow hub, sky, and air

#### Printing out unaltered data received from the station broadcasts
The --raw option prints out decoded UDP broadcasts in JSON format to stdout...
```
pi@zero:~ $ python listen.py --raw
setting up socket - done
listening for broadcasts..
{"hub_sn": "HB-00010412", "ob": [1535684062, 0.63, 272], "serial_number": "SK-00013695", "type": "rapid_wind"}
```

#### Decoding the station data into a more human-friendly format
The --decoded option prints a more human-friendly output of the decoded UDP broadcast...
```
pi@zero:~ $ python listen.py --decoded
setting up socket - done
listening for broadcasts..
hub_status     =>  ts  = 1535819472 firmware_revision  = 91 uptime  = 333458 rssi  = -35
rapid_wind     =>  ts  = 1535819474 mps = 1.34 dir = 190
rapid_wind     =>  ts  = 1535819477 mps = 1.48 dir = 211
```

#### Limiting the output to one observation/status/event type
The '--limit type' option limits the event/status/observation(s) being processed.

```
pi@zero:~ $ python listen.py --raw --limit hub_status
setting up socket - done
listening for broadcasts..
{"firmware_revision": "91", "fs": "1,0", "mqtt_stats": [53], "radio_stats": [5, 3], "reset_flags": "BOR,PIN,POR", "rssi": -35, "seq": 33368, "serial_number": "HB-00010412", "timestamp": 1535819752, "type": "hub_status", "uptime": 333738}
{"firmware_revision": "91", "fs": "1,0", "mqtt_stats": [53], "radio_stats": [5, 3], "reset_flags": "BOR,PIN,POR", "rssi": -35, "seq": 33370, "serial_number": "HB-00010412", "timestamp": 1535819772, "type": "hub_status", "uptime": 333758}
```

Note: you can supply multiple limited observations ala:
```
python listen.py --limit obs_sky,obs_air
python listen.py --limit "obs_sky obs_air"
```

You can also exclude observations, processing everything else, ala:
```
python listen.py --exclude "rapid_wind"
```


#### Reformatting the JSON data for easier interpretation
The --indent option reformats the output to be a little more readable...
```
@zero:~ $ python listen.py --raw --limit rapid_wind --indent
setting up socket - done
listening for broadcasts..

{
  "hub_sn": "HB-00010412",
  "ob": [
    1535819864,
    0.0,
    0
  ],
  "serial_number": "SK-00013695",
  "type": "rapid_wind"
}

{
  "hub_sn": "HB-00010412",
  "ob": [
    1535819867,
    0.0,
    0
  ],
  "serial_number": "SK-00013695",
  "type": "rapid_wind"
}
```

### Syslogging unexpected JSON received

The --syslog option will syslog any received JSON data that has an unknown or missing device["type"].
You almost certainly do 'not' want to use this option and also specify the --indent option, as the
default JSON dumped will be a (long) one-liner suitable for syslog.

### Publishing to MQTT

The --mqtt option publishes JSON to MQTT.

```
pi@zero:~ $ python listen.py --mqtt
setting up socket - done
listening for broadcasts..
publishing to mqtt://mqtt/wf/status/sky
publishing to mqtt://mqtt/wf/obs/sky
publishing to mqtt://mqtt/wf/rapid_wind
publishing to mqtt://mqtt/wf/rapid_wind
```

Adding the --decoded option shows decoded data from the broadcast as well
```
pi@zero:~ $ python listen.py --mqtt --decoded
setting up socket - done
listening for broadcasts..
rapid_wind     =>  ts  = 1535821622 mps = 1.07 dir = 316
publishing to mqtt://mqtt/wf/rapid_wind
hub_status     =>  ts  = 1535821622 firmware_revision  = 91 uptime  = 335608 rssi  = -35
publishing to mqtt://mqtt/wf/status/hub
```

Adding the --raw option shows the data that would be published as well as the raw UDP data
```
pi@zero:~ $ python listen.py --mqtt --raw
setting up socket - done
listening for broadcasts..
    raw data:  {"hub_sn": "HB-00010412", "ob": [1535821559, 0.94, 272], "serial_number": "SK-00013695", "type": "rapid_wind"}
publishing to mqtt://mqtt/wf/rapid_wind
     {"direction": 272, "speed": 0.94, "timestamp": 1535821559}
```

### Decoding WeatherFlow data into WeeWX terminology

The --weewx option maps WeatherFlow variable names to WeeWX-compatible parameter names, matching the WeeWX schema. Only some observations from the Air and Sky have mappings to WeeWX fields, so many of the available WeatherFlow measurements are skipped.

```
pi@zero:~ $ python listen.py --weewx
setting up socket - done
listening for broadcasts..
{"dateTime": 1535821716, "outHumidity": 76, "outTemp": 15.43, "outTempBatteryStatus": 3.48, "pressure": 1010.8}
{"UV": 4.99, "dateTime": 1535821729, "radiation": 380, "rain": 0.0, "windBatteryStatus": 3.43, "windGust": 1.92, "windSpeed": 1.1, "wind_direction": 275}
```

Similar to the examples above, adding the --mqtt option 'also' publishes to MQTT.

```

pi@zero:~ $ python listen.py --weewx --mqtt
setting up socket - done
listening for broadcasts..
    publishing to mqtt://mqtt/wf/weewx
    publishing to mqtt://mqtt/wf/weewx
    publishing to mqtt://mqtt/wf/weewx

```

Adding the --no_pub option will show the JSON that would be published.

```
pi@zero:~ $ python listen.py --weewx --mqtt --no_pub
setting up socket - done
listening for broadcasts..
publishing to mqtt://mqtt/wf/weewx
     {"dateTime": 1535822375, "outHumidity": 76, "outTemp": 15.8, "outTempBatteryStatus": 3.48, "pressure": 1010.7}
publishing to mqtt://mqtt/wf/weewx
     {"UV": 6.19, "dateTime": 1535822388, "radiation": 468, "rain": 0.0, "windBatteryStatus": 3.43, "windGust": 2.5, "windSpeed": 1.44, "wind_direction": 233}
```

## Subscribing to MQTT published topics

### WeatherFlow MQTT topics (non-weewx format)

This gives an example of how to use the mosquitto_sub MQTT client to subscribe to a published topic.   See the mosquito_sub man page for detailed usage of that client.

```

pi@zero$ mosquitto_sub -t "wf/obs/#" -h mqtt

{"firmware_revision": 20, "hub_sn": "HB-00010412", "obs": [[1535685379, 1006.8, 18.51, 76, 0, 0, 3.51, 1]], "serial_number": "AR-00013349", "type": "obs_air"}

{"firmware_revision": 43, "hub_sn": "HB-00010412", "obs": [[1535685389, 18, 0.0, 0.0, 0.0, 1.08, 2.06, 258, 3.45, 1, 0, null, 0, 3]], "serial_number": "SK-00013695", "type": "obs_sky"}

```

### WeatherFlow MQTT topics (weewx format)

If the listener is publishing with the --weewx option specified, all the weewx-compatible topics are on the same MQTT topic for easy subscribing...


```

pi@zero$ mosquitto_sub -t "wf/weewx" -h mqtt

{"dateTime": 1535685559, "outHumidity": 77, "outTemp": 18.41, "outTempBatteryStatus": 3.51, "pressure": 1006.8}

{"UV": 0.0, "dateTime": 1535685568, "radiation": 0, "rain": 0.0, "windBatteryStatus": 3.44, "windGust": 1.79, "windSpeed": 0.97, "wind_direction": 216}

```


