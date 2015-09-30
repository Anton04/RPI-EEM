RPI-EEM
=======

Raspberry PI Energi Meter Monitor (RPI-EEM). This solution enables you to connect you Raspberry pi to the S0 port of a power meter or an light sensor on the blinking LED to monitor the power use at some site. 

Usage:

Install mosquitto mqtt broaker. 
> sudo apt-get install mosquitto

and 

> sudo apt-get install mosquitto-clients

If you want to be able to view messages on it with (>mosquitto_sub -t "#" -v)

Download the 

EnergyMeterPulsReaderMQTT.py and 
install-startup-script

to your RPI

do a 

> sudo bash install-startup-script

then change the path in /ect/init.d/eem to wherever you put the EnergyMeterPulsReaderMQTT.py with

> sudo pico /ect/init.d/eem  

do a 

> sudo service eem start

and view the pulses with 

> mosquitto_sub -t "#" -v

To use the data you can now install tools like nodered, influxdb and grafana see: op-en.se for more info. 

I might do a better installation script for this in the future. 

The script will two kinds of events one with the pulses and their lenght and one with a filtered value (i.e. ignoring pulselenghts that are odd). You can change the filer value in the script. 


