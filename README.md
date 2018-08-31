
## Description

This is a quick listener for the WeatherFlow UDP broadcasts that can:

 * print received broadcasts
 * print decoded broadcasts to stdout
    * and/or publish to MQTT
    * optionally reformatted to match weewx schema

##  Usage

```

pi@zero:~ $ python listen.py --help
usage: listen.py [-h] [--debug] [--stdout] [--indent] [--mqtt] [--no_pub]
                 [--weewx]

optional arguments:
  -h, --help    show this help message and exit
  --debug, -d   print debug data to stdout
  --stdout, -s  print decoded data to stdout
  --indent, -i  indent debug UDP to stdout (requires -d)
  --mqtt, -m    publish to MQTT
  --no_pub, -n  report but do not publish to MQTT
  --weewx, -w   convert to weewx schema mapping

```

## Typical Usage

Typically it is expected that this script would be used to generate MQTT publish messages via running as daemon ala:

```

nohup python listen.py --mqtt [--weewx] &


```


## Examples

### --debug option

The --debug option prints out decoded UDP broadcasts in JSON format to stdout...

```

pi@zero:~ $ python listen.py --debug
setting up socket - done
listening for broadcasts..
{"hub_sn": "HB-00010412", "ob": [1535684062, 0.63, 272], "serial_number": "SK-00013695", "type": "rapid_wind"}

```

### --debug --indent

Adding the --indent option reformats the output to be a little more readable...

```

pi@zero:~ $ python listen.py --debug --indent
setting up socket - done
listening for broadcasts..
###################################
{
  "hub_sn": "HB-00010412",
  "ob": [
    1535684197,
    2.01,
    211
  ],
  "serial_number": "SK-00013695",
  "type": "rapid_wind"
}
###################################
{
  "hub_sn": "HB-00010412",
  "ob": [
    1535684200,
    1.65,
    219
  ],
  "serial_number": "SK-00013695",
  "type": "rapid_wind"
}

```


### --mqtt --stdout option

The --mqtt option publishes to MQTT. In this example we also add the --stdout option to get more info of what it's decoding and publishing...

```

pi@zero:~ $ python listen.py --mqtt --stdout
setting up socket - done
listening for broadcasts..
rapid_wind     =>  ts  = 1535684269 mps = 1.52 dir = 215
    publishing to mqtt://mqtt/wf/rapid_wind
rapid_wind     =>  ts  = 1535684272 mps = 0.72 dir = 285
    publishing to mqtt://mqtt/wf/rapid_wind
hub_status     =>  ts  = 1535684275 firmware_revision  = 91 uptime  = 198261 rssi  = -37
    publishing to mqtt://mqtt/wf/status/hub
rapid_wind     =>  ts  = 1535684275 mps = 0.72 dir = 254
    publishing to mqtt://mqtt/wf/rapid_wind

```

### --weewx option

The --weewx option maps WeatherFlow variable names to WeeWX-compatible parameter names, matching the WeeWX schema.  In this example we add --stdout to get more info os what it's decoding and what JSON content was generated.

```

pi@zero:~ $ python listen.py --weewx --stdout
setting up socket - done
listening for broadcasts..
obs_sky        =>  time_epoch  = 1535684549 uv  = 0.02 rain_accumulated  = 0.0 wind_lull = 0.72 wind_avg = 1.37 wind_gust = 2.01 wind_direction = 226
{"UV": 0.02, "dateTime": 1535684549, "radiation": 1, "rain": 0.0, "windBatteryStatus": 3.44, "windGust": 2.01, "windSpeed": 1.37, "wind_direction": 226}
```

### --weewx --mqtt --stdout

Similar to the examples above, adding the --mqtt option publishes to MQTT.  Again, in this example we add --stdout to show what is being published and to which MQTT topic.

```
pi@zero:~ $ python listen.py --weewx --mqtt --stdout
setting up socket - done
listening for broadcasts..
obs_air        =>  ts  = 1535684899 station_pressure = 1006.8 temperature = 18.8 relative_humidity = 74 lightning_strikes = 0 lightning_avg_km  = 0
    publishing to mqtt://mqtt/wf/weewx
{"dateTime": 1535684899, "outHumidity": 74, "outTemp": 18.8, "outTempBatteryStatus": 3.51, "pressure": 1006.8}
```

## Subscribing to MQTT published topics

### WeatherFlow MQTT topics (non-weewx format)
```

pi@zero$ mosquitto_sub -t "wf/obs/#" -h mqtt

{"firmware_revision": 20, "hub_sn": "HB-00010412", "obs": [[1535685379, 1006.8, 18.51, 76, 0, 0, 3.51, 1]], "serial_number": "AR-00013349", "type": "obs_air"}

{"firmware_revision": 43, "hub_sn": "HB-00010412", "obs": [[1535685389, 18, 0.0, 0.0, 0.0, 1.08, 2.06, 258, 3.45, 1, 0, null, 0, 3]], "serial_number": "SK-00013695", "type": "obs_sky"}

```

### WeatherFlow MQTT topics (weewx format)
```

pi@zero$ mosquitto_sub -t "wf/weewx" -h mqtt

{"dateTime": 1535685559, "outHumidity": 77, "outTemp": 18.41, "outTempBatteryStatus": 3.51, "pressure": 1006.8}

{"UV": 0.0, "dateTime": 1535685568, "radiation": 0, "rain": 0.0, "windBatteryStatus": 3.44, "windGust": 1.79, "windSpeed": 0.97, "wind_direction": 216}

```


