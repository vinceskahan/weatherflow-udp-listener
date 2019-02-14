#
# This is a quick Dockerfile to build and run the
# WeatherFlow UDP listener via a Docker container.
#
# tested on a MacbookAir running macOS Mojave 10.14.1
#
# cleanup of apt remnants courtesy of:
#  https://gist.github.com/marvell/7c812736565928e602c4

#-------
# use python slim to stay lean and mean
# this is 175MB or so in size

FROM python:2.7.15-slim
MAINTAINER Vince Skahan "vinceskahan@gmail.com"
RUN apt-get update \
    && apt-get install -y wget \
    && pip install paho-mqtt \
    && apt-get clean autoclean \
    && apt-get autoremove --yes \
    && rm -rf /var/lib/{apt,dpkg,cache,log}/

#--- to download a verbatim copy of the latest on github
RUN cd /root && wget https://raw.githubusercontent.com/vinceskahan/weatherflow-udp-listener/master/listen.py

#--- or to copy in an edited one from this directory
# ADD listen.py /root/listen.py

# uncertain if this is needed
EXPOSE 50222/udp

# ENTRYPOINT ["python", "/root/listen.py", "--help"]

# run it for real, publishing known observations only
ENTRYPOINT ["python", "/root/listen.py", "--mqtt", "--syslog"]

# to run bash interactively comment out the ENTRYPOINT above
# and rebuild the image using 'debian' as your base box,
# being sure to add the apt-get line for python-pip too,
# then run the container ala:
#    docker run -p 50222:50222/udp --add-host mqtt:192.168.1.169  -it docker_wfudp sh
# which will start a shell in the container.  Then run the listener interactively ala:
#    python /root/listen.py --raw
# and verify that you see it listening and writing the JSON it heard to the console
#

# another example of how to run it, excluding rapid_wind observations
# ENTRYPOINT ["python", "/root/listen.py", "--mqtt", "--exclude", "rapid_wind"]
