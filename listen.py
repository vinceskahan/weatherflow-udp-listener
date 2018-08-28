#!/usr/bin/python
#

from __future__ import print_function

import sys, time
from socket import *
import json

# weatherflow broadcasts on this port
MYPORT = 50222

# FQDN of the host to publish mqtt messages to
mqtt_host = "mqtt"

s = socket(AF_INET, SOCK_DGRAM)
s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
s.bind(('', MYPORT))
#s.bind(('', 0))

def mqtt_publish(mqtt_host,mqtt_topic):
    return     # skip this for now
    print("    publishing to mqtt://%s/%s" % (mqtt_host, mqtt_topic))

while 1:
 msg=s.recvfrom(1024)
 data=json.loads(msg[0])      # this is the JSON payload

 # these match https://weatherflow.github.io/SmartWeather/api/udp/v91/
 # in the order shown on that page....
 #
 # yes this could be done 'cooler' with enumerating a sensor map
 # ala the WeatherflowUDP weewx driver, but lets go for readability
 # for the time being.....
 #

 if data["type"] == "evt_precip":
    evt_precip_serial_number = data["serial_number"]   # of the device reporting the data
    evt_precip_hub_sn        = data["hub_sn"]
    evt_precip_time_epoch    = data["evt"][0]

    print ("evt_precip", end='')
    print (" ts  = " + str(evt_precip_time_epoch), end='')
    print ('')

    mqtt_publish(mqtt_host,"weatherflow/evt/precip")

 elif data["type"] == "evt_strike":
    evt_strike_serial_number = data["serial_number"]   # of the device reporting the data
    evt_strike_hub_sn        = data["hub_sn"]
    evt_strike_time_epoch    = data["evt"][0]
    evt_strike_distance      = data["evt"][1]          # km
    evt_strike_energy        = data["evt"][2]          # no units documented

    print ("evt_strike", end='')
    print (" ts  = " + str(evt_strike_time_epoch), end='')
    print (" distance  = " + str(evt_strike_distance), end='')
    print (" energy  = " + str(evt_strike_energy), end='')
    print ('')

    mqtt_publish(mqtt_host,"weatherflow/evt/strike")

 elif data["type"] == "rapid_wind":
    rapid_wind_air_serial_number = data["serial_number"]   # of the device reporting the data
    rapid_wind_time_epoch        = data["ob"][0]
    rapid_wind_speed             = data["ob"][1]           # meters/second
    rapid_wind_direction         = data["ob"][2]           # degrees

    print ("rapid_wind", end='')
    print (" ts  = " + str(rapid_wind_time_epoch), end='')
    print (" mps = " + str(rapid_wind_speed), end='')
    print (" dir = " + str(rapid_wind_direction), end='')
    print ('')

    mqtt_publish(mqtt_host,"weatherflow/obs/rapid_wind")

 elif data["type"] == "obs_air":
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

    print ("obs_air", end='')
    print (" ts  = " + str(obs_air_time_epoch), end='')
    print (" station_pressure = " + str(obs_air_station_pressure), end='')
    print (" temperature = " + str(obs_air_temperature), end='')
    print (" relative_humidity = " + str(obs_air_relative_humidity), end='')
    print ('')

    mqtt_publish(mqtt_host,"weatherflow/obs/air")

 elif data["type"] == "obs_sky":
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

    print ("obs_sky", end='')
    print (" time_epoch  = " + str(obs_sky_time_epoch) ,  end='')
    print (" uv  = " + str(obs_sky_uv) , end='')
    print (" rain_accumulated  = " + str(obs_sky_rain_accumulated) , end='')
    print (" wind_lull = " + str(obs_sky_wind_lull) , end='')
    print (" wind_avg = " + str(obs_sky_wind_avg) , end='')
    print (" wind_gust = " + str(obs_sky_wind_gust) , end='')
    print (" wind_direction = " + str(obs_sky_wind_direction) , end='')
    print ('')

    mqtt_publish(mqtt_host,"weatherflow/obs/sky")

 elif data["type"] == "device_status":
    device_status_serial_number       = data["serial_number"]       # of the device reporting the data
    device_status_hub_sn              = data["hub_sn"]
    device_status_timestamp           = data["timestamp"]
    device_status_uptime              = data["uptime"]              # seconds
    device_status_voltage             = data["voltage"]             # volts
    device_status_firmware_revision   = data["firmware_revision"]
    device_status_rssi                = data["rssi"]
    device_status_hub_rssi            = data["hub_rssi"]
    device_status_sensor_status       = data["sensor_status"]
    device_status_debug               = data["debug"]               # 0=disabled, 1=enabled

    # sensor_status is an encored enumeration
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

    print ("device_status", end='')
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
    topic = "weatherflow/status/" + device_type
    mqtt_publish(mqtt_host,topic)

 elif data["type"] == "hub_status":
    print ("hub_status")
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

    print ("hub_status", end='')
    print (" ts  = " + str(hub_status_timestamp), end='')
    print (" firmware_revision  = " + str(hub_status_firmware_revision), end='')
    print (" uptime  = " + str(hub_status_uptime), end='')
    print (" rssi  = " + str(hub_status_rssi), end='')
    print ('')

    mqtt_publish(mqtt_host,"weatherflow/status/hub")

 else:
    print ("=> skipping unknown type " + data["type"])


# rapid wind
#   {"serial_number":"SK-00013695","type":"rapid_wind","hub_sn":"HB-00010412","ob":[1535400638,0.76,250]}

# hub status
#   {"serial_number":"HB-00010412","type":"hub_status","firmware_revision":"91","uptime":274133,"rssi":-48,"timestamp":1535400642,"reset_flags":"PIN,SFT","seq":27408,"fs":"1,0","radio_stats":[5,1],"mqtt_stats":[1]}

# device status - air
#   {"serial_number":"AR-00013349","type":"device_status","hub_sn":"HB-00010412","timestamp":1535400712,"uptime":591162,"voltage":3.49,"firmware_revision":20,"rssi":-47,"hub_rssi":0,"sensor_status":4,"debug":0}

# device status - sky
# {"serial_number":"SK-00013695","type":"device_status","hub_sn":"HB-00010412","timestamp":1535400715,"uptime":591122,"voltage":3.47,"firmware_revision":43,"rssi":-52,"hub_rssi":-50,"sensor_status":0,"debug":0}

# obs air
#   {"serial_number":"AR-00013349","type":"obs_air","hub_sn":"HB-00010412","obs":[[1535400712,1009.60,19.56,69,0,0,3.49,1]],"firmware_revision":20}

# obs sky
# {"serial_number":"SK-00013695","type":"obs_sky","hub_sn":"HB-00010412","obs":[[1535400715,115335,12.79,0.000000,0.00,0.80,1.92,247,3.47,1,961,null,0,3]],"firmware_revision":43}
