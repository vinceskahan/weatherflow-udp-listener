#!/usr/bin/python3
#
# WeatherFlow listener
#
#  - this listens for WeatherFlow UDP broadcasts
#    and prints the decoded info to standard out (optionally)
#    or publishes the decoded data to MQTT (also optionally)
#
# IMPORTANT - this is tested versus v91 of the hub firmware
#             and coded versus the matching API docs at
#             https://weatherflow.github.io/SmartWeather/api/udp
#
#             While it 'might' work for different firmware,
#             your mileage might vary....
#
# this is updated to v114 of the firmware as documented in
#   https://weatherflow.github.io/SmartWeather/api/udp/v114/
#
#----------------

"""
usage: listen.py [-h] [-r] [-d] [-s] [-l LIMIT] [-x EXCLUDE] [-i] [-m] [-n]
                 [-w] [-b MQTT_BROKER] [-t MQTT_TOPIC]

optional arguments:
  -h, --help            show this help message and exit
  -r, --raw             print raw data to stddout
  -d, --decoded         print decoded data to stdout
  -s, --syslog          syslog unexpected data received
  -l LIMIT, --limit LIMIT
                        limit obs type(s) processed
  -x EXCLUDE, --exclude EXCLUDE
                        exclude obs type(s) from being processed
  -i, --indent          indent raw data to stdout (requires -d)
  -m, --mqtt            publish to MQTT (one air/sky)
  -M, --multi-mqtt      specify there are multiple air/sky present
  -n, --no_pub          report but do not publish to MQTT
  -b MQTT_BROKER, --mqtt_broker MQTT_BROKER
                        MQTT broker hostname
  -t MQTT_TOPIC, --mqtt_topic MQTT_TOPIC
                        MQTT topic to post to
  -a ADDRESS, --address ADDRESS
                        address to listen on
  --influxdb            publish to influxdb
  --influxdb_host INFLUXDB_HOST
                        hostname or ip of InfluxDb HTTP API
  --influxdb_port INFLUXDB_PORT
                        port of InfluxDb HTTP API
  --influxdb_user INFLUXDB_USER
                        InfluxDb username
  --influxdb_pass INFLUXDB_PASS
                        InfluxDb password
  --influxdb_db INFLUXDB_DB
                        InfluxDb database name
  -v, --verbose         verbose output to watch the threads

for --limit, possibilities are:
   rapid_wind, obs_sky, obs_air,
   hub_status, device_status, evt_precip, evt_strike
"""

#----------------
#
# compatibility notes:
#   - The v91 API uses 'timestamp' in one place and 'time_epoch' in all others
#     For consistency, this program uses 'timestamp' everywhere in decoded output

# uncomment for python2
from __future__ import print_function

import argparse
import datetime
import json
import paho.mqtt.client  as mqtt
import paho.mqtt.publish as publish
import sys
import syslog
import time
import threading
import os
from socket import *
from influxdb import InfluxDBClient

# python3 renamed it to 'queue'
try:
  from queue import Queue
except:
  from Queue import Queue

# weatherflow broadcasts on this port
MYPORT = 50222

# by default listen on all interfaces and addresses
ADDRESS = ''                       # supersede this with --address

# FQDN of the host to publish mqtt messages to
MQTT_HOST = "mqtt"                 # supersede this with --mqtt-broker
MQTT_TOPLEVEL_TOPIC = "wf"         # supersede this with --mqtt-topic
MQTT_CLIENT_ID = "weatherflow"
MQTT_PORT = 1883

# syslog routines (reused with thanks from weewx examples)
#   severity low->high:
#          DEBUG INFO WARNING ERROR CRITICAL
#

def logmsg(level, msg):
    syslog.syslog(level, '[wf-udp-listener]: %s' % msg)

def logdbg(msg):
    logmsg(syslog.LOG_DEBUG, msg)

def loginf(msg):
    logmsg(syslog.LOG_INFO, msg)

def logerr(msg):
    logmsg(syslog.LOG_ERR, msg)

#----------------
#
# process the various types of events or observations
#
# these routines are in the order shown in __main__ which
# should match up with the order in the WeatherFlow UDP API docs online
#

def process_evt_precip(data):
    if args.exclude and ("evt_precip" in args.exclude): return
    if args.limit and ("evt_precip" not in args.limit): return
    if args.raw: print_raw(data)

    evt_precip = {}
    serial_number = data["serial_number"]
                                                      # skip hub_sn
    evt_precip["timestamp"] = data["evt"][0]

    if args.decoded:
        print ("evt_precip     => ", end='')
        print (" ts  = " + str(evt_precip["timestamp"]), end='')
        print ('')

    if args.mqtt:
        topic = MQTT_TOPLEVEL_TOPIC + "/evt/precip"
        if args.mqtt_multisensor:
            topic = "sensors/" + serial_number + "/" + topic
        mqtt_publish(MQTT_HOST,topic,evt_precip)

    if args.influxdb:
        influxdb_publish('precip', evt_precip)

    return data

#----------------

def process_evt_strike(data):
    if args.exclude and ("evt_strike" in args.exclude): return
    if args.limit and ("evt_strike" not in args.limit): return
    if args.raw: print_raw(data)

    evt_strike = {}
    serial_number = data["serial_number"]
                                                      # skip hub_sn
    evt_strike["timestamp"] = data["evt"][0]
    evt_strike["distance"]  = data["evt"][1]          # km
    evt_strike["energy"]    = data["evt"][2]          # no units documented

    if args.decoded:
        print ("evt_strike     => ", end='')
        print (" ts  = "       + str(evt_strike["timestamp"]), end='')
        print (" distance  = " + str(evt_strike["distance"]), end='')
        print (" energy  = "   + str(evt_strike["energy"]), end='')
        print ('')

    if args.mqtt:
        topic = MQTT_TOPLEVEL_TOPIC + "/evt/strike"
        if args.mqtt_multisensor:
            topic = "sensors/" + serial_number + "/" + topic
        mqtt_publish(MQTT_HOST,topic,evt_strike)

    if args.influxdb:
        influxdb_publish('strike', evt_strike)

    return data

#----------------

def process_rapid_wind(data):
    if args.exclude and ("rapid_wind" in args.exclude): return
    if args.limit and ("rapid_wind" not in args.limit): return
    if args.raw: print_raw(data)

    rapid_wind = {}
    serial_number = data["serial_number"]
                                                      # skip hub_sn
    rapid_wind['timestamp']  = data["ob"][0]
    rapid_wind['speed']      = data["ob"][1]          # meters/second
    rapid_wind['direction']  = data["ob"][2]          # degrees

    if args.decoded:
        print ("rapid_wind     => ", end='')
        print (" ts  = " + str(rapid_wind['timestamp']), end='')
        print (" mps = " + str(rapid_wind['speed']), end='')
        print (" dir = " + str(rapid_wind['direction']), end='')
        print ('')

    if args.mqtt:
        topic = MQTT_TOPLEVEL_TOPIC + "/rapid_wind"
        if args.mqtt_multisensor:
            topic = "sensors/" + serial_number + "/" + topic
        mqtt_publish(MQTT_HOST,topic,rapid_wind)

    if args.influxdb:
        influxdb_publish('rapid_wind', rapid_wind)

    return data

#----------------

def process_obs_air(data):
    if args.exclude and ("obs_air" in args.exclude): return
    if args.limit and ("obs_air" not in args.limit): return
    if args.raw: print_raw(data)

    obs_air = {}
    serial_number = data["serial_number"]
                                                                        # skip hub_sn
    obs_air["timestamp"]                     = data["obs"][0][0]
    obs_air["station_pressure"]              = data["obs"][0][1]        # MB
    obs_air["temperature"]                   = data["obs"][0][2]        # deg-C
    obs_air["relative_humidity"]             = data["obs"][0][3]        # %
    obs_air["lightning_strike_count"]        = data["obs"][0][4]
    obs_air["lightning_strike_avg_distance"] = data["obs"][0][5]        # km
    obs_air["battery"]                       = data["obs"][0][6]        # volts
    obs_air["report_interval"]               = data["obs"][0][7]        # minutes
    obs_air["firmware_revision"]             = data["firmware_revision"]

    if args.decoded:
        print ("obs_air        => ", end='')
        print (" ts  = "               + str(obs_air["timestamp"]), end='')
        print (" station_pressure = "  + str(obs_air["station_pressure"]), end='')
        print (" temperature = "       + str(obs_air["temperature"]), end='')
        print (" relative_humidity = " + str(obs_air["relative_humidity"]), end='')
        print (" lightning_strikes = " + str(obs_air["lightning_strike_count"]), end='')
        print (" lightning_avg_km  = " + str(obs_air["lightning_strike_avg_distance"]), end='')
        print ('')

    if args.mqtt:
        topic = MQTT_TOPLEVEL_TOPIC + "/obs_air"
        if args.mqtt_multisensor:
            topic = "sensors/" + serial_number + "/" + topic
        mqtt_publish(MQTT_HOST,topic,obs_air)

    if args.influxdb:
        influxdb_publish('obs_air', obs_air)

    return data

#----------------

def process_obs_sky(data):
    if args.exclude and ("obs_sky" in args.exclude): return
    if args.limit and ("obs_sky" not in args.limit): return
    if args.raw: print_raw(data)

    obs_sky = {}
    serial_number = data["serial_number"]
                                                                     # skip hub_sn
    obs_sky["timestamp"]                   = data["obs"][0][0]
    obs_sky["illuminance"]                 = data["obs"][0][1]       # lux
    obs_sky["uv"]                          = data["obs"][0][2]       # index
    obs_sky["rain_accumulated"]            = data["obs"][0][3]       # mm (in this reporting interval)
    obs_sky["wind_lull"]                   = data["obs"][0][4]       # meters/second min 3 sec sample
    obs_sky["wind_avg"]                    = data["obs"][0][5]       # meters/second avg over report interval
    obs_sky["wind_gust"]                   = data["obs"][0][6]       # meters_second max 3 sec sample
    obs_sky["wind_direction"]              = data["obs"][0][7]       # degrees
    obs_sky["battery"]                     = data["obs"][0][8]       # volts
    obs_sky["report_interval"]             = data["obs"][0][9]       # minutes
    obs_sky["solar_radiation"]             = data["obs"][0][10]      # W/m^2
                                                                     # local_rain_day_accumulation does not work in v91 of their firmware
    obs_sky["precipitation_type"]          = data["obs"][0][12]      # 0=none, 1=rain, 2=hail
    obs_sky["wind_sample_interval"]        = data["obs"][0][13]      # seconds
    obs_sky["firmware_revision"]           = data["firmware_revision"]

    if args.decoded:
        print ("obs_sky        => ", end='')
        print (" timestamp  = "        + str(obs_sky["timestamp"]) ,  end='')
        print (" uv  = "               + str(obs_sky["uv"]) , end='')
        print (" rain_accumulated  = " + str(obs_sky["rain_accumulated"]) , end='')
        print (" wind_lull = "         + str(obs_sky["wind_lull"]) , end='')
        print (" wind_avg = "          + str(obs_sky["wind_avg"]) , end='')
        print (" wind_gust = "         + str(obs_sky["wind_gust"]) , end='')
        print (" wind_direction = "    + str(obs_sky["wind_direction"]) , end='')
        print ('')

    if args.mqtt:
        topic = MQTT_TOPLEVEL_TOPIC + "/obs_sky"
        if args.mqtt_multisensor:
            topic = "sensors/" + serial_number + "/" + topic
        mqtt_publish(MQTT_HOST,topic,obs_sky)

    if args.influxdb:
        influxdb_publish('obs_sky', obs_sky)

    return data

#----------------

def process_device_status(data):
    if args.exclude and ("device_status" in args.exclude): return
    if args.limit and ("device_status" not in args.limit): return
    if args.raw: print_raw(data)

    # both outside devices use the same status schema
    if "AR-" in data["serial_number"]:
            device_type = "air"
    elif "SK-" in data["serial_number"]:
            device_type = "sky"
    else:
            device_type = "unknown_type"

    device_status = {}
    serial_number = data["serial_number"]
                                                                   # skip hub_sn
    device_status["device"]            = device_type
    device_status["timestamp"]         = data["timestamp"]
    device_status["uptime"]            = data["uptime"]            # seconds
    device_status["voltage"]           = data["voltage"]           # volts
    device_status["firmware_revision"] = data["firmware_revision"]
    device_status["rssi"]              = data["rssi"]
    device_status["hub_rssi"]          = data["hub_rssi"]
    device_status["sensor_status"]     = data["sensor_status"]     # enumerated - see API for details
    device_status["debug"]             = data["debug"]             # 0=disabled, 1=enabled

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

    if args.decoded:
        print ("device_status  => ", end='')
        print (" device_type = "        + str(device_type), end='')
        print (" ts  = "                + str(device_status["timestamp"]), end='')
        print (" uptime  = "            + str(device_status["uptime"]), end='')
        print (" voltage  = "           + str(device_status["voltage"]), end='')
        print (" firmware_revision  = " + str(device_status["firmware_revision"]), end='')
        print (" rssi  = "              + str(device_status["rssi"]), end='')
        print (" hub_rssi  = "          + str(device_status["hub_rssi"]), end='')
        print ('')

    # construct the status topic to publish to
    if args.mqtt:
        topic = MQTT_TOPLEVEL_TOPIC + "/status/" + device_type
        if args.mqtt_multisensor:
            topic = "sensors/" + serial_number + "/" + topic
        mqtt_publish(MQTT_HOST,topic,device_status)

    if args.influxdb:
        influxdb_publish('device_status', device_status)

    return data

#----------------

def process_hub_status(data):
    if args.exclude and ("hub_status" in args.exclude): return
    if args.limit and ("hub_status" not in args.limit): return
    if args.raw: print_raw(data)

    hub_status = {}
    serial_number = data["serial_number"]
    hub_status["device"]              = "hub"                      # (future use for this program)
    hub_status["firmware_revision"]   = int(data["firmware_revision"])
    hub_status["uptime"]              = data["uptime"]             # seconds
    hub_status["rssi"]                = data["rssi"]
    hub_status["timestamp"]           = data["timestamp"]
    hub_status["reset_flags"]         = data["reset_flags"]
    hub_status["seq"]                 = data["seq"]
    hub_status["fs"]                  = data["fs"]                 # internal use only
    hub_status["radio_stats_version"] = data["radio_stats"][0]
    hub_status["reboot_count"]        = data["radio_stats"][1]
    hub_status["i2c_bus_error_count"] = data["radio_stats"][2]
    hub_status["radio_status"]        = data["radio_stats"][3]     # 0=off, 1=on, 3=active
    hub_status["mqtt_stats"]          = data["mqtt_stats"]         # internal use only

    # reset flags are a comma-delimited string with values:
    #   BOR = brownout reset
    #   PIN = PIN reset
    #   POR = power reset
    #   SFT = software reset
    #   WDG = watchdog reset
    #   WWD = window watchdog reset
    #   LPW = low-power reset

    if args.decoded:
        print ("hub_status     => ", end='')
        print (" ts  = "                + str(hub_status["timestamp"]), end='')
        print (" firmware_revision  = " + str(hub_status["firmware_revision"]), end='')
        print (" uptime  = "            + str(hub_status["uptime"]), end='')
        print (" rssi  = "              + str(hub_status["rssi"]), end='')
        print ('')

    if args.mqtt:
        topic = MQTT_TOPLEVEL_TOPIC + "/status/hub"
        if args.mqtt_multisensor:
            topic = "sensors/" + serial_number + "/" + topic
        mqtt_publish(MQTT_HOST,topic,hub_status)

    if args.influxdb:
        influxdb_publish('hub_status', hub_status)     # careful here, might need to hub_status.pop("foo", None) for arrays

    return data

#----------------

def influxdb_publish(event, data):

    try:
        client = InfluxDBClient(host=args.influxdb_host,
                                port=args.influxdb_port,
                                username=args.influxdb_user,
                                password=args.influxdb_pass,
                                database=args.influxdb_db)
        payload = {}
        payload['measurement'] = event

        payload['time']   = data['timestamp']
        payload['fields'] = data

        if args.verbose:
            print ("publishing to influxdb [%s:%s]: %s" % (args.influxdb_host, args.influxdb_port, payload))

        # write_points() allows us to pass in a precision with the timestamp
        client.write_points([payload], time_precision='s')

    except Exception as e:
        print("Failed to connect to InfluxDB: %s" % e)
        print("  Payload was: %s" % payload)

#----------------

def mqtt_publish(mqtt_host,mqtt_topic,data):
    print ("publishing to mqtt://%s/%s" % (mqtt_host, mqtt_topic))
    if args.no_pub:
        print ("    ", json.dumps(data,sort_keys=True));

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

#----------------

def print_raw(data):
        if args.raw:
            if args.indent:
                print ("")
                print (json.dumps(data,sort_keys=True,indent=2));
            else:
                print ("    raw data: ", json.dumps(data,sort_keys=True));
            next


#---------

def listener_task(q):
    thread_name = threading.current_thread().name
    thread_pid  = format(os.getpid())
    if args.verbose:
      print("starting thread: " + thread_name + " pid = " + thread_pid)

    # this is lame, but it's the listener
    while 1:
      try:
        msg=s.recvfrom(1024)
        data=json.loads(msg[0])      # this is the JSON payload
        q.put(data)                  # save in the queue  (do this 5 times to prove the queue queues)
        if args.verbose:
            print("-------------")
            print(thread_name + ": " + str(datetime.datetime.now()) + " " + json.dumps(data,sort_keys=True))
      except:
        pass
      time.sleep(0.01)

    print("listener_task done")

#---------

def reporter_task(q):
    thread_name = threading.current_thread().name
    thread_pid  = format(os.getpid())
    if args.verbose:
      print("starting thread: " + thread_name + " pid = " + thread_pid)

    while 1:
      try:
        while not q.empty():
          data = q.get()
          if args.verbose:
            print(thread_name + ": " + str(datetime.datetime.now()) + " " + json.dumps(data,sort_keys=True))
          report_it(data)
      except:
        pass
      time.sleep(0.01)
      ####time.sleep(30)        # uncomment to see the queue queueing

def report_it(data):

    #
    # this matches https://weatherflow.github.io/SmartWeather/api/udp/v91/
    # in the order shown on that page....
    #
    # yes tearing apart the pieces could be done 'cooler' via enumerating
    # a sensor map ala the WeatherflowUDP weewx driver, but lets go for
    # readability for the time being.....
    #

    if   data["type"] == "evt_precip":    process_evt_precip(data)
    elif data["type"] == "evt_strike":    process_evt_strike(data)
    elif data["type"] == "rapid_wind":    process_rapid_wind(data)
    elif data["type"] == "obs_air":       process_obs_air(data)
    elif data["type"] == "obs_sky":       process_obs_sky(data)
    elif data["type"] == "device_status": process_device_status(data)
    elif data["type"] == "hub_status":    process_hub_status(data)

    # --- uncomment to skip undocumented debug types ---
    # elif data["type"] == "wind_debug":    pass
    # elif data["type"] == "light_debug":   pass
    # elif data["type"] == "rain_debug":    pass

    else:
       # this catches 'lack of' a data["type"] in the data as well
       print ("ERROR: unknown data type in", data)
       if args.syslog:
         message = "unknown data type in " + json.dumps(data,sort_keys=True)
         loginf(message);

#---------

if __name__ == "__main__":

    # argument parsing is u.g.l.y it ain't got no alibi, it's ugly !
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
for --limit, possibilities are:
   rapid_wind, obs_sky, obs_air,
   hub_status, device_status, evt_precip, evt_strike
       """,
    )

    parser.add_argument("-r", "--raw",     dest="raw",     action="store_true", help="print raw data to stddout")
    parser.add_argument("-d", "--decoded", dest="decoded", action="store_true", help="print decoded data to stdout")
    parser.add_argument("-s", "--syslog",  dest="syslog",  action="store_true", help="syslog unexpected data received")
    parser.add_argument("-l", "--limit",   dest="limit",   action="store",      help="limit obs type(s) processed")
    parser.add_argument("-x", "--exclude", dest="exclude", action="store",      help="exclude obs type(s) from being processed")

    parser.add_argument("-i", "--indent",  dest="indent",  action="store_true", help="indent raw data to stdout (requires -d)")

    parser.add_argument("-m", "--mqtt",       dest="mqtt",             action="store_true", help="publish to MQTT")
    parser.add_argument("-M", "--multi-mqtt", dest="mqtt_multisensor", action="store_true", help="specify there are multiple air/sky present")

    parser.add_argument("-n", "--no_pub",  dest="no_pub",  action="store_true", help="report but do not publish to MQTT")

    parser.add_argument("-b", "--mqtt_broker", dest="mqtt_broker", action="store", help="MQTT broker hostname")
    parser.add_argument("-t", "--mqtt_topic",  dest="mqtt_topic",  action="store", help="MQTT topic to post to")
    parser.add_argument("-a", "--address",     dest="address",     action="store", help="address to listen on")

    parser.add_argument("--influxdb",      dest="influxdb",      action="store_true",                                 help="publish to influxdb")
    parser.add_argument("--influxdb_host", dest="influxdb_host", action="store",      default="localhost",            help="hostname of InfluxDB HTTP API")
    parser.add_argument("--influxdb_port", dest="influxdb_port", action="store",      default=8086,         type=int, help="hostname of InfluxDB HTTP API")
    parser.add_argument("--influxdb_user", dest="influxdb_user", action="store",                                      help="InfluxDB username")
    parser.add_argument("--influxdb_pass", dest="influxdb_pass", action="store",                                      help="InfluxDB password")
    parser.add_argument("--influxdb_db",   dest="influxdb_db",   action="store",      default="smartweather",         help="InfluxDB database name")

 
    parser.add_argument("-v", "--verbose", dest="verbose", action="store_true", help="verbose mode - show threads")

    args = parser.parse_args()

    if (args.indent) and (not args.raw):
        print ("\n# exiting - must also specify --raw")
        parser.print_usage()
        print ()
        sys.exit(1)

    if (not args.mqtt) and (not args.decoded) and (not args.raw) and (not args.influxdb):
        print ("\n#")
        print ("# exiting - must specify at least one option")
        print ("#           --raw, --decoded, --mqtt, --influxdb")
        print ("#\n")
        parser.print_usage()
        print ()
        sys.exit(1)

    if args.mqtt_broker:
        MQTT_HOST = args.mqtt_broker

    if args.mqtt_topic:
        MQTT_TOPLEVEL_TOPIC = args.mqtt_topic

    if args.address:
        ADDRESS = args.address

    # the socket
    if args.verbose:
      print("setting up socket - ", end='')
    s = socket(AF_INET, SOCK_DGRAM)
    s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
    s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    s.setblocking(False)
    s.bind((ADDRESS, MYPORT))
    if args.verbose:
      print("socket set up")

    # the main thread
    if (sys.version_info > (3,0)):
      thread_name = threading.main_thread().name
    else:
      thread_name = threading.current_thread().name
    thread_pid  = format(os.getpid())
    if args.verbose:
      print("starting main thread: " + thread_name + " pid = " + thread_pid)

    # define the queue
    q = Queue(maxsize=0)
    q.join()

    # define the threads
    threads = [
        threading.Thread(target=listener_task, name='listener', args=(q,)),
        threading.Thread(target=reporter_task, name='reporter', args=(q,)),
    ]

    # start them up
    for t in threads:
        t.start()

    # wait for them to finish
    for t in threads:
        t.join()

    if args.verbose:
      print()
      print("done")


#############

sys.exit(0)


#
# that's all folks
#
