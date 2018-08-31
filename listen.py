#!/usr/bin/python
#
# WeatherFlow listener
#
#  - this listens for WeatherFlow UDP broadcasts
#    and prints the decoded info to standard out (optionally)
#    or publishes the decoded data to MQTT (also optionally)
#
#----------------
#
# usage: listen.py [-h] [--mqtt] [--stdout] [--no_pub] [--weewx] [--debug]
#
# optional arguments:
#   -h, --help    show this help message and exit
#   --stdout, -s  print decoded data to stdout
#   --debug, -d   print debug UDP data to stdout
#   --indent, -i  indent debug UDP to stdout (requires -d)
#   --mqtt, -m    publish to MQTT
#   --no_pub, -n  report but do not publish to MQTT
#   --weewx, -w   convert to weewx schema mapping
#
#----------------

from __future__ import print_function
import paho.mqtt.client  as mqtt
import paho.mqtt.publish as publish

import sys, time
from socket import *
import json

# weatherflow broadcasts on this port
MYPORT = 50222

# FQDN of the host to publish mqtt messages to
MQTT_HOST = "mqtt"
MQTT_PORT = 1883
MQTT_CLIENT_ID = "weatherflow"

def process_rapid_wind(data):
    rapid_wind_air_serial_number = data["serial_number"]   # of the device reporting the data
    rapid_wind_time_epoch        = data["ob"][0]
    rapid_wind_speed             = data["ob"][1]           # meters/second
    rapid_wind_direction         = data["ob"][2]           # degrees

    # no need to map to weewx, as the obs_sky wind data already
    # reports the max rapid_wind_speed between obs_sky intervals
    # as the wind gust speed

    if args.stdout:
        print ("rapid_wind     => ", end='')
        print (" ts  = " + str(rapid_wind_time_epoch), end='')
        print (" mps = " + str(rapid_wind_speed), end='')
        print (" dir = " + str(rapid_wind_direction), end='')
        print ('')

    # we don't bother reporting rapid_wind if --weewx was specified
    # since obs_sky has that info already when that period comes around again
    if args.mqtt:
        if args.weewx:
            pass
        else:
            mqtt_publish(MQTT_HOST,"wf/rapid_wind",data)

    return data

def process_obs_air(data):
    obs_air_serial_number                 = data["serial_number"]   # of the device reporting the data
    obs_air_hub_sn                        = data["hub_sn"]
    obs_air_time_epoch                    = data["obs"][0][0]
    obs_air_station_pressure              = data["obs"][0][1]        # MB
    obs_air_temperature                   = data["obs"][0][2]        # deg-C
    obs_air_relative_humidity             = data["obs"][0][3]        # %
    obs_air_lightning_strike_count        = data["obs"][0][4]
    obs_air_lightning_strike_avg_distance = data["obs"][0][5]        # km
    obs_air_battery                       = data["obs"][0][6]        # volts
    obs_air_report_interval               = data["obs"][0][7]        # minutes
    obs_air_firmware_revision             = data["firmware_revision"]

    if args.weewx:
        data["weewx"]["dateTime"]             = obs_air_time_epoch
        data["weewx"]["pressure"]             = obs_air_station_pressure
        data["weewx"]["outTemp"]              = obs_air_temperature
        data["weewx"]["outHumidity"]          = obs_air_relative_humidity
        data["weewx"]["outTempBatteryStatus"] = obs_air_battery

    if args.stdout:
        print ("obs_air        => ", end='')
        print (" ts  = " + str(obs_air_time_epoch), end='')
        print (" station_pressure = " + str(obs_air_station_pressure), end='')
        print (" temperature = " + str(obs_air_temperature), end='')
        print (" relative_humidity = " + str(obs_air_relative_humidity), end='')
        print (" lightning_strikes = " + str(obs_air_lightning_strike_count), end='')
        print (" lightning_avg_km  = " + str(obs_air_lightning_strike_avg_distance), end='')
        print ('')

    if args.mqtt:
        if args.weewx:
            mqtt_publish(MQTT_HOST,"wf/weewx",data["weewx"])
        else:
            mqtt_publish(MQTT_HOST,"wf/obs/air",data)

    return data

def process_obs_sky(data):
    obs_sky_serial_number                 = data["serial_number"]   # of the device reporting the data
    obs_sky_hub_sn                        = data["hub_sn"]
    obs_sky_time_epoch                    = data["obs"][0][0]
    obs_sky_illuminance                   = data["obs"][0][1]       # lux
    obs_sky_uv                            = data["obs"][0][2]       # index
    obs_sky_rain_accumulated              = data["obs"][0][3]       # mm (in this reporting interval)
    obs_sky_wind_lull                     = data["obs"][0][4]       # meters/second min 3 sec sample
    obs_sky_wind_avg                      = data["obs"][0][5]       # meters/second avg over report interval
    obs_sky_wind_gust                     = data["obs"][0][6]       # meters_second max 3 sec sample
    obs_sky_wind_direction                = data["obs"][0][7]       # degrees
    obs_sky_battery                       = data["obs"][0][8]       # volts
    obs_sky_report_interval               = data["obs"][0][9]       # minutes
    obs_sky_solar_radiation               = data["obs"][0][10]      # W/m^2
    obs_sky_local_day_rain_accumulation   = data["obs"][0][11]      # mm (does not work in v91 of their firmware)
    obs_sky_precipitation_type            = data["obs"][0][12]      # 0=none, 1=rain, 2=hail
    obs_sky_wind_sample_interval          = data["obs"][0][13]      # seconds
    obs_sky_firmware_revision             = data["firmware_revision"]

    if args.weewx:
        data["weewx"]["dateTime"]          = obs_sky_time_epoch
        data["weewx"]["UV"]                = obs_sky_uv
        data["weewx"]["windBatteryStatus"] = obs_sky_battery
        data["weewx"]["radiation"]         = obs_sky_solar_radiation
        data["weewx"]["windGust"]          = obs_sky_wind_gust
        data["weewx"]["windSpeed"]         = obs_sky_wind_avg
        data["weewx"]["wind_direction"]    = obs_sky_wind_direction
        data["weewx"]["rain"]              = obs_sky_rain_accumulated

    if args.stdout:
        print ("obs_sky        => ", end='')
        print (" time_epoch  = " + str(obs_sky_time_epoch) ,  end='')
        print (" uv  = " + str(obs_sky_uv) , end='')
        print (" rain_accumulated  = " + str(obs_sky_rain_accumulated) , end='')
        print (" wind_lull = " + str(obs_sky_wind_lull) , end='')
        print (" wind_avg = " + str(obs_sky_wind_avg) , end='')
        print (" wind_gust = " + str(obs_sky_wind_gust) , end='')
        print (" wind_direction = " + str(obs_sky_wind_direction) , end='')
        print ('')

    if args.mqtt:
        if args.weewx:
            mqtt_publish(MQTT_HOST,"wf/weewx",data["weewx"])
        else:
            mqtt_publish(MQTT_HOST,"wf/obs/sky",data)

    return data

def process_device_status(data):   
    device_status_serial_number       = data["serial_number"]       # of the device reporting the data
    device_status_hub_sn              = data["hub_sn"]
    device_status_timestamp           = data["timestamp"]
    device_status_uptime              = data["uptime"]              # seconds
    device_status_voltage             = data["voltage"]             # volts
    device_status_firmware_revision   = data["firmware_revision"]
    device_status_rssi                = data["rssi"]
    device_status_hub_rssi            = data["hub_rssi"]
    device_status_sensor_status       = data["sensor_status"]
    device_status_debug               = data["debug"]                # 0=disabled, 1=enabled

    # sensor_status is an encoded enumeration
    #    0x00000000    all = sensors ok
    #    0x00000001    air = lightning failed
    #    0x00000002    air = lightning noise
    #    0x00000004    air = lightning disturber
    #    0x00000008    air = pressure failed
    #    0x00000010    air = temperature failed
    #    0x00000020    air = rh failed
    #    0x00000040    sky = wind failed
    #    0x00000080    sky = precip failed
    #    0x00000100    sky = light/uv failed

    if args.stdout:
        print ("device_status  => ", end='')
        print (" serial_number  = " + str(device_status_serial_number), end='')
        print (" ts  = " + str(device_status_timestamp), end='')
        print (" uptime  = " + str(device_status_uptime), end='')
        print (" voltage  = " + str(device_status_voltage), end='')
        print (" firmware_revision  = " + str(device_status_firmware_revision), end='')
        print (" rssi  = " + str(device_status_rssi), end='')
        print (" hub_rssi  = " + str(device_status_hub_rssi), end='')
        print ('')

    # both outside devices use the same reporting
    if "AR-" in device_status_serial_number:
            device_type = "air"
    elif "SK-" in device_status_serial_number:
            device_type = "sky"
    else:
            device_type = "unknown_type"
    topic = "wf/status/" + device_type
    if args.mqtt:
        if args.weewx:
            pass
        else:
            mqtt_publish(MQTT_HOST,topic,data)

    return data

def process_hub_status(data):
    hub_status_serial_number       = data["serial_number"]      # of the device reporting the data
    hub_status_firmware_revision   = data["firmware_revision"]
    hub_status_uptime              = data["uptime"]             # seconds
    hub_status_rssi                = data["rssi"]
    hub_status_timestamp           = data["timestamp"]
    hub_status_reset_flags         = data["reset_flags"]
    hub_status_seq                 = data["seq"]
    hub_status_fs                  = data["fs"]                 # internal use only
    hub_status_radio_stats_version = data["radio_stats"][0]
    hub_status_reboot_count        = data["radio_stats"][1]
    hub_status_mqtt_stats          = data["mqtt_stats"]         # internal use only

    # reset flags are a comma-delimited string with values:
    #   BOR = brownout reset
    #   PIN = PIN reset
    #   POR = power reset
    #   SFT = software reset
    #   WDG = watchdog reset
    #   WWD = window watchdog reset
    #   LPW = low-power reset

    if args.stdout:
        print ("hub_status     => ", end='')
        print (" ts  = " + str(hub_status_timestamp), end='')
        print (" firmware_revision  = " + str(hub_status_firmware_revision), end='')
        print (" uptime  = " + str(hub_status_uptime), end='')
        print (" rssi  = " + str(hub_status_rssi), end='')
        print ('')

    if args.mqtt:
        if args.weewx:
            pass
        else:
            mqtt_publish(MQTT_HOST,"wf/status/hub",data)

    return data

def process_evt_strike(data):
    evt_strike_serial_number = data["serial_number"]   # of the device reporting the data
    evt_strike_hub_sn        = data["hub_sn"]
    evt_strike_time_epoch    = data["evt"][0]
    evt_strike_distance      = data["evt"][1]          # km
    evt_strike_energy        = data["evt"][2]          # no units documented

    if args.stdout:
        print ("evt_strike     => ", end='')
        print (" ts  = " + str(evt_strike_time_epoch), end='')
        print (" distance  = " + str(evt_strike_distance), end='')
        print (" energy  = " + str(evt_strike_energy), end='')
        print ('')

    if args.mqtt:
        if args.weewx:
            pass
        else:
            mqtt_publish(MQTT_HOST,"wf/evt/strike",data)

    return data

def process_evt_precip(data):
    evt_precip_serial_number = data["serial_number"]   # of the device reporting the data
    evt_precip_hub_sn        = data["hub_sn"]
    evt_precip_time_epoch    = data["evt"][0]

    if args.stdout:
        print ("evt_precip     => ", end='')
        print (" ts  = " + str(evt_precip_time_epoch), end='')
        print ('')

    if args.mqtt:
        if args.weewx:
            pass
        else:
            mqtt_publish(MQTT_HOST,"wf/evt/precip",data)

    return data

def mqtt_publish(mqtt_host,mqtt_topic,data):
    if args.stdout or args.no_pub:
        print ("    publishing to mqtt://%s/%s" % (mqtt_host, mqtt_topic))

    if not args.no_pub:
        broker_address=mqtt_host
        client_id=MQTT_CLIENT_ID
        topic=mqtt_topic
        payload=json.dumps(data,sort_keys=True)
        port=MQTT_PORT

        # ref: https://www.eclipse.org/paho/clients/python/docs/#single
        publish.single(
            topic,
            payload=payload,
            hostname=broker_address,
            client_id=client_id,
            port=port,
            protocol=mqtt.MQTTv311)

    return


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--debug",  "-d", dest="debug",  action="store_true", help="print debug data to stdout")
    parser.add_argument("--stdout", "-s", dest="stdout", action="store_true", help="print decoded data to stdout")
    parser.add_argument("--indent", "-i", dest="indent", action="store_true", help="indent debug UDP to stdout (requires -d)")
    parser.add_argument("--mqtt",   "-m", dest="mqtt",   action="store_true", help="publish to MQTT")
    parser.add_argument("--no_pub", "-n", dest="no_pub", action="store_true", help="report but do not publish to MQTT")
    parser.add_argument("--weewx",  "-w", dest="weewx",  action="store_true", help="convert to weewx schema mapping")

    args = parser.parse_args()

    if (args.indent) and (not args.debug):
        print ("\n# exiting - must also specify --debug")
        parser.print_usage()
        print ()
        sys.exit(1)

    if (not args.mqtt) and (not args.stdout) and (not args.weewx) and (not args.debug):
        print ("\n# exiting - must specify at least one option")
        parser.print_usage()
        print ()
        sys.exit(1)

    print ("setting up socket - ", end='')
    s = socket(AF_INET, SOCK_DGRAM)
    s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
    s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    s.bind(('', MYPORT))
    print ("done")

    print ("listening for broadcasts..")
    while 1:
        msg=s.recvfrom(1024)
        data=json.loads(msg[0])      # this is the JSON payload

        if args.debug:
            if args.indent:
                print ("###################################")
                print (json.dumps(data,sort_keys=True,indent=2));
            else:
                print (json.dumps(data,sort_keys=True));
            next

        # initialize weewx keys in data
        if args.weewx:
            data['weewx'] = {}
        #
        # this matches https://weatherflow.github.io/SmartWeather/api/udp/v91/
        # in the order shown on that page....
        #
        # yes tearing apart the pieces could be done 'cooler' via enumerating
        # a sensor map ala the WeatherflowUDP weewx driver, but lets go for
        # readability for the time being.....
        #

        if   data["type"] == "evt_strike":    process_evt_strike(data)
        elif data["type"] == "evt_precip":    process_evt_precip(data)
        elif data["type"] == "rapid_wind":    process_rapid_wind(data)
        elif data["type"] == "obs_air":       process_obs_air(data)
        elif data["type"] == "obs_sky":       process_obs_sky(data)
        elif data["type"] == "device_status": process_device_status(data)
        elif data["type"] == "hub_status":    process_hub_status(data)
        else:
           print ("ERROR: unknown data['type'] in", data)

        # we have our data updated with weewx-mapped content by now
        # so print it out if there was anything mapped to weewx fields
        if args.weewx:
            if len(data["weewx"]) and args.stdout:
                print (json.dumps(data["weewx"],sort_keys=True))


#
# that's all folks
#
