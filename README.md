
## Description

This is a quick listener for the WeatherFlow UDP broadcasts that can:

 * print received broadcasts
 * print decoded broadcasts to stdout
 * publish to MQTT
 * optionally mapped to match WeeWX schema

##  Usage

```

Usage: listen.py [-h] [--debug] [--stdout] [--indent] [--mqtt] [--no_pub]
                 [--weewx] [--limit LIMIT]

optional arguments:
  -h, --help            show this help message and exit
  --debug, -d           print debug data to stdout
  --stdout, -s          print decoded data to stdout
  --indent, -i          indent debug UDP to stdout (requires -d)
  --mqtt, -m            publish to MQTT
  --no_pub, -n          report but do not publish to MQTT
  --weewx, -w           convert to weewx schema mapping
  --limit LIMIT, -l LIMIT
                        limit to one obs type

for --limit, possibilities are:
   rapid_wind, obs_sky, obs_air,
   status_hub, device_status, evt_precip, evt_strike

```

## Typical Usage

### Generating MQTT topics for other systems to subscribe to

Typically it is expected that this script would be used to generate MQTT publish messages via running as daemon ala:

```

nohup python listen.py --mqtt [--weewx] &

```

## Examples

### Debugging your WeatherFlow hub, sky, and air

The --debug option prints out decoded UDP broadcasts in JSON format to stdout...

```

pi@zero:~ $ python listen.py --debug
setting up socket - done
listening for broadcasts..
{"hub_sn": "HB-00010412", "ob": [1535684062, 0.63, 272], "serial_number": "SK-00013695", "type": "rapid_wind"}

```

Adding the '--limit type' option limits the output to just one type of event/status/observation.

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


### Publishing to MQTT

The --mqtt option publishes JSON to MQTT.

```
pi@zero:~ $ /usr/bin/python listen.py --mqtt
setting up socket - done
listening for broadcasts..
    publishing to mqtt://mqtt/wf/status/sky
    publishing to mqtt://mqtt/wf/obs/sky
    publishing to mqtt://mqtt/wf/rapid_wind
    publishing to mqtt://mqtt/wf/rapid_wind
    publishing to mqtt://mqtt/wf/status/hub
```

Adding the --no_pub option will show the same output as above but not actually publish anything. This could also be used to quickly see if the Hub is broadcasting periodically.

Adding the --stdout option will report the decoded data it would report.

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


### Decoding WeatherFlow data into WeeWX terminology

The --weewx option maps WeatherFlow variable names to WeeWX-compatible parameter names, matching the WeeWX schema. Only some observations from the Air and Sky have mappings to WeeWX fields, so many of the available WeatherFlow measurements are skipped.

In this example we add the --stdout option to get more info of what it's decoding for illustrative purposes below... 

```

pi@zero:~ $ python listen.py --weewx --stdout
setting up socket - done
listening for broadcasts..
obs_sky        =>  time_epoch  = 1535684549 uv  = 0.02 rain_accumulated  = 0.0 wind_lull = 0.72 wind_avg = 1.37 wind_gust = 2.01 wind_direction = 226
{"UV": 0.02, "dateTime": 1535684549, "radiation": 1, "rain": 0.0, "windBatteryStatus": 3.44, "windGust": 2.01, "windSpeed": 1.37, "wind_direction": 226}
```

Similar to the examples above, adding the --mqtt option 'also' publishes to MQTT.  In this example we add --no_pub which will show which topic would be published to.

```

pi@zero:~ $ python listen.py --weewx --mqtt --no_pub
setting up socket - done
listening for broadcasts..
    publishing to mqtt://mqtt/wf/weewx
    publishing to mqtt://mqtt/wf/weewx
    publishing to mqtt://mqtt/wf/weewx

```

Adding the --stdout option will show the JSON that is (or would be) published.

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


