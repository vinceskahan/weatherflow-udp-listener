#
# This is a quick Dockerfile to build and run the
# WeatherFlow UDP listener via a Docker container.
#

FROM python:3.8-alpine
LABEL maintainer="Vince Skahan vinceskahan@gmail.com"

ADD https://raw.githubusercontent.com/vinceskahan/weatherflow-udp-listener/master/listen.py /
# Conversely, you can add a modified copy from this directory:
# ADD listen.py /

# Install the required Python packages for InfluxDB and MQTT support
RUN pip3 install influxdb paho-mqtt

# Uncomment an ENTRYPOINT below, or modify to suit your needs:

# Show the help screen and exit
# ENTRYPOINT ["python", "/listen.py", "--help"]

# Publish to InfluxDB (Edit the INFLUX_ placeholders as needed to match your environment)
# ENTRYPOINT ["python", "/listen.py", "--influxdb", "--influxdb_host=INFLUX_HOST", "--influxdb_db=INFLUX_DB", "--influxdb_pass=INFLUX_PASS", "--influxdb_port=8086", "--influxdb_user=INFLUX_USER"]

# Publish but exclude rapid_wind observations
# ENTRYPOINT ["python", "/listen.py", "--mqtt", "--exclude", "rapid_wind"]

# Publish known observations only
ENTRYPOINT ["python", "/listen.py", "--mqtt", "--syslog"]

#
# To run bash interactively in the container for troubleshooting purposes,
# you can run this container and override the ENTRYPOINT to instead execute
# a shell via:
#
#  docker run -it -p 50222:50222/udp --entrypoint sh --rm -pdocker_wfudp
#
# Once in the container, you can run the listenener interactively to ensure you
# can see it listening and writing JSON to the console via:
#
#  python /listen.py --raw
#

# Expose 50222/udp for inbound UDP multicast from WeatherFlow hub
EXPOSE 50222/udp