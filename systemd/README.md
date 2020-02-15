
## systemd startup and config files

The UDP listener is a python3 script that typically is run interactively from a shell, meaning you'd need to background and nohup it to make it run as a daemon.   These files permit you to install the listener as a normal systemd service, optionally enabled at boot, and lets you use normal systemd commands to start/stop/check the service.

### INSTALLATION 

IMPORTANT: before starting the service, edit `/etc/default/weatherflow-udp-listener` to set your desired commandline options.

As distributed, the service will run as the non-privileged user=pi group=pi.  Edit the .service file if you want to use a different user/group.

The commands below should be run as root (or via sudo).

* Install the files into the usual places
```
cp etc/default/weatherflow-udp-listener /etc/default/weatherflow-udp-listener
cp lib/systemd/system/weatherflow-udp-listener.service /lib/systemd/service/weatherflow-udp-listener.service
cp listen.py /usr/local/bin/listen.py
chmod 755 /usr/local/bin/listen.py
```

* Tell systemd about the new service
```
systemctl daemon-reload
```

* Check systemd knows the service exists
```
systemctl status weatherflow-udp-listener
```

* Try it out once
```
systemctl start weatherflow-udp-listener
systemctl status weatherflow-udp-listener
```

* Enable it to start on boot
```
systemctl enable weatherflow-udp-listener
```

* To stop the service
```
systemctl stop weatherflow-udp-listener
```

