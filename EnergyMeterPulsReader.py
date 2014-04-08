#!/usr/bin/python
# Energymeter puls reader to MQTT for Raspberry PI
# by Anton Gustafsson
# 2013-09-20

import RPi.GPIO as GPIO
from time import gmtime, strftime, time, localtime, mktime, strptime
import json
import urllib2
import base64
from math import fabs

config = {
      'user': 'spsensors',
      'password': 'BuCSlvWpl8reZP3R',
      'server': 'livinglab.powerprojects.se:6984'
      }


#Functions
#Time
def CurrentTime():
	return strftime("%Y-%m-%d %H:%M:%S", localtime())


#Class
class EnergyLogger():

	def __init__(self):

		self.Factor = 1 # kWh per pulse
		self.Threshhold = 10.0
	
		self.LastTime = 0.0
		self.Counter = 0.0
		self.LastPeriod = 0.0
		self.Falling = 0.0
		self.LastPower = 0.0

		self.error_threshhold = 50000

		self.pulse_lenght = 0.080 
		self.pulse_lenght_max_dev = 0.0005

		self.pin = 23

		#Config
		self.config = {
		      'user': 'spsensors',
		      'password': 'BuCSlvWpl8reZP3R',
		      'server': 'livinglab.powerprojects.se:6984',
		      'database': 'ii'
		}


		GPIO.setmode(GPIO.BCM)

		# GPIO 23 set up as inputs, pulled up to avoid false detection.
		GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

		# when a falling or rising edge is detected on port 23, call callback2
		GPIO.add_event_detect(self.pin, GPIO.BOTH, callback=self.my_callback2, bouncetime=0)

		return

	#Posting data to couchDB  
	def post(self, doc):


		url = 'https://%(server)s/%(database)s/_design/energy_data/_update/measurement' % self.config
		request = urllib2.Request(url, data=json.dumps(doc))
		auth = base64.encodestring('%(user)s:%(password)s' % self.config).replace('\n', '')
		request.add_header('Authorization', 'Basic ' + auth)
		request.add_header('Content-Type', 'application/json')
		request.get_method = lambda: 'POST'
		urllib2.urlopen(request, timeout=1)
		
		return


	# now we'll define two threaded callback functions
	# these will run in another thread when our events are detected
	def my_callback(self,channel):
    		print "%s falling edge detected on 17" % CurrentTime()
		return

	def my_callback3(self,channel):
		self.falling = time()

		print "%s falling edge detected on 23" % CurrentTime()
		return

	def my_callback2(self,channel):

    		TimeStamp = time()    
		#print CurrentTime()		

		#Detect high or low
		if not GPIO.input(channel):
			self.Falling = TimeStamp		
			print CurrentTime()	
			print "Falling edge on " + str(channel)
			return
		else:
			print "Rising edge on " + str(channel)

		#Check pulse lenght.
		PulseLenght = TimeStamp - self.Falling
		PulseDeviation = fabs(PulseLenght - self.pulse_lenght)		

		print "Pulse lengt on port 23 was %.2fms\na deviation of %.3fms from expected %.2fms" %(PulseLenght*1000,PulseDeviation *1000,self.pulse_lenght *1000)



		if PulseDeviation >  self.pulse_lenght_max_dev:
			print "Pulselenght error"
			return 


		if self.LastTime == 0:
			self.LastTime = TimeStamp
			return

		Period = TimeStamp - self.LastTime

		#Debounce function
		#if Period < 1.0:
		#	return 

		self.Counter += 1

		self.LastTime = TimeStamp
		self.LastPeriod = Period

    		#Calculate values. 
    		Energy = self.Counter * self.Factor
    		Power = self.Factor / (Period / 3600000.0) # The energy divided on the time in hours.
    		Delta = fabs(Power - self.LastPower)

		if Delta > self.error_threshhold:
			print "Interference detected"
			return


		#Store for future reference
		self.LastPower = Power
		self.LastEnergy = Energy
		self.LastDelta = Delta


		print "Period is: %.2f s \nPower is: %.2f W\nEnergy: %.2f kWh\nChange: %.2f " % (Period,Power,Energy,Delta)

		if Delta > self.Threshhold: 
			print "Updating..."
			self.post({
                        	"source": "Munktell",
	                        "timestamp": str(TimeStamp),
	                        "ElectricPower": str(Power),
	                        "ElectricEnergy": str(Energy),
	                        "PowerThreshold": str(self.Threshhold)
                        })
		return


if __name__ == "__main__":

	print "Make sure you have a button connected so that when pressed"
	print "it will connect GPIO port 23 (pin 16) to GND (pin 6)\n"
	print "You will also need a second button connected so that when pressed"
	print "it will connect GPIO port 24 (pin 18) to 3V3 (pin 1)\n"
	print "You will also need a third button connected so that when pressed"
	print "it will connect GPIO port 17 (pin 11) to GND (pin 14)"
	#raw_input("Press Enter when ready\n>")

	Logger = EnergyLogger()

	try:
		while(1):
			raw_input("Press Enter to simulate pulse\n>")
			Logger.my_callback(1)

    		print "Waiting for rising edge on port 24"
    		GPIO.wait_for_edge(24, GPIO.RISING)
    		print "Rising edge detected on port 24. Here endeth the third lesson."

	except KeyboardInterrupt:
    		GPIO.cleanup()       # clean up GPIO on CTRL+C exit
	GPIO.cleanup()           # clean up GPIO on normal exit

