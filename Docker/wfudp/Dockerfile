#
# This is a quick Dockerfile to build and run the
# WeatherFlow UDP listener via a Docker container.
#
# tested on a MacbookAir running HighSierra 10.13.6
#
# cleanup of apt remnants courtesy of:
#  https://gist.github.com/marvell/7c812736565928e602c4


#FROM debian
FROM python:2.7.15-slim
MAINTAINER Vince Skahan "vinceskahan@gmail.com"
RUN apt-get update \
    && apt-get install -y wget \
    && pip install paho-mqtt \
    && apt-get clean autoclean \
    && apt-get autoremove --yes \
    && rm -rf /var/lib/{apt,dpkg,cache,log}/

##### uncomment only 'one' of the 'RUN' or 'ADD' lines here
##### to select whether you want to build the default listener
##### or one you have saved in this directory as 'listen.py'
#####

#--- to download a verbatim copy of the latest on github
RUN cd /root && wget https://raw.githubusercontent.com/vinceskahan/weatherflow-udp-listener/master/listen.py

#--- or to copy in an edited one from this directory
# ADD listen.py /root/listen.py

# uncertain if this is needed
EXPOSE 50222/udp

# verify it works
# ENTRYPOINT ["python", "/root/listen.py", "--help"]

# run it for real, publishing known observations only
ENTRYPOINT ["python", "/root/listen.py", "--mqtt"]

# another example of how to run it, excluding rapid_wind observations
# ENTRYPOINT ["python", "/root/listen.py", "--mqtt", "--exclude", "rapid_wind"]
