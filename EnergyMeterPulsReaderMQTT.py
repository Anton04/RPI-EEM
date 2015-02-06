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
import mosquitto



#Functions
#Time
def CurrentTime():
	return strftime("%Y-%m-%d %H:%M:%S", localtime())


#Class
class EnergyLogger(mosquitto.Mosquitto):

	def __init__(self,pin=23,user = "driver", password="1234",server = "localhost", prefix = "MainMeter",client = "EnergyLogger"):

		self.Factor = 0.01 # kWh per pulse
		self.Threshhold = 10.0
		self.SentThreshhold = None
	
		self.LastTime = 0.0
		self.Counter = 0.0
		self.LastPeriod = 0.0
		self.Falling = 0.0
		self.LastPower = 0.0

		self.error_threshhold = 70000

		self.pulse_lenght = 0.080 
		self.pulse_lenght_max_dev = 0.0005

		self.pin = pin

	
		self.prefix = prefix

		#Init and connect to MQTT server
		mosquitto.Mosquitto.__init__(self,client)
		self.will_set( topic = "system/" + self.prefix, payload="Offline", qos=1, retain=True)

		if user != None:
    			self.username_pw_set(user,password)
    			
    		self.on_connect = self.mqtt_on_connect
    		self.on_message = self.mqtt_on_message

		self.connect(server,keepalive=10)
		self.publish(topic = "system/"+ self.prefix, payload="Online", qos=1, retain=True)

		GPIO.setmode(GPIO.BCM)

		# GPIO self.pin set up as inputs, pulled up to avoid false detection.
		GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

		# when a falling or rising edge is detected on port self.pin, call callback2
		GPIO.add_event_detect(self.pin, GPIO.BOTH, callback=self.my_callback2, bouncetime=0)

		self.loop_start()

		return

	#Posting data to couchDB  
	def Update(self,sub_topic,value,timestamp = time()):

		topic = self.prefix+"/"+sub_topic

        	msg = json.dumps({"time":timestamp,"value":value})

		#print "New event: " + topic
        	self.publish(topic,msg,1)
		
		return

	def SendMeterEvent(self,timestamp,power,counter,period,pulselenght,threshhold):
		#self.Update("power",power,timestamp)
		#self.Update("counter",counter,timestamp)
		
		topic = self.prefix+"/meterevent"
		
		msg = json.dumps({"time":timestamp,"power":power})

		self.publish(topic,msg,1)
		#if self.SentThreshhold != self.Threshhold:
		#	self.Update("threshhold",threshhold,timestamp)
		#	self.SentThreshhold = self.Threshhold

		return

	def SendIOEvent(self,Period,Counter,PulseLenght):
		topic = self.prefix+"/ioevent"
		msg = json.dumps({"time":timestamp,"power":power,"counter":counter,"period":period,"pulselenght":pulselenght})
		self.publish(topic,msg,1)
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

		print "Pulse lengt on port %i was %.2fms\na deviation of %.3fms from expected %.2fms" %(self.pin,PulseLenght*1000,PulseDeviation *1000,self.pulse_lenght *1000)



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
		
		print "Period is: %.2f s \nPower is: %.2f W\nEnergy: %.2f kWh\nChange: %.2f " % (Period,Power,Energy,Delta)
		print " "

		if Delta > self.error_threshhold:
			print "Interference detected"
			print " "
			return


		#Store for future reference
		self.LastPower = Power
		self.LastEnergy = Energy
		self.LastDelta = Delta


		print "Period is: %.2f s \nPower is: %.2f W\nEnergy: %.2f kWh\nChange: %.2f " % (Period,Power,Energy,Delta)

		if Delta > self.Threshhold: 
			print "Updating..."
			counter,period,pulselenght
			self.SendMeterEvent(str(TimeStamp),str(Power),str(Energy),str(self.Threshhold))
			self.SendIOEvent(str(Period),str(Counter),str(PulseLenght))
		return
	
	def mqtt_on_connect(self, selfX,mosq, result):
    		print "MQTT connected!"
    		self.subscribe(self.prefix + "/#", 0)
    
  	def mqtt_on_message(self, selfX,mosq, msg):
    		print("RECIEVED MQTT MESSAGE: "+msg.topic + " " + str(msg.payload))
    	
    		return


if __name__ == "__main__":

	
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

