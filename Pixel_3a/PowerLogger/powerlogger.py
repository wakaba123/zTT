'''
Author: wakaba blues243134@gmail.com
Date: 2024-04-11 17:22:59
LastEditors: wakaba blues243134@gmail.com
LastEditTime: 2024-04-12 11:14:47
FilePath: /zTT/Pixel_3a/PowerLogger/powerlogger.py
Description: 

Copyright (c) 2024 by wakaba All Rights Reserved. 
'''
import time
import Monsoon.HVPM as HVPM
import Monsoon.sampleEngine as sampleEngine
import Monsoon.Operations as op
import subprocess

def execute(cmd):
    cmds = [ 'su',cmd, 'exit']
    obj = subprocess.Popen("adb shell", shell= True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    info = obj.communicate(("\n".join(cmds) + "\n").encode('utf-8'))
    return info[0].decode('utf-8')

class PowerLogger:
	def __init__(self):
		self.power=0
		self.voltage=0
		self.current=0
		self.power_data = []
		self.Mon = HVPM.Monsoon()
		self.Mon.setup_usb()
		self.engine = sampleEngine.SampleEngine(self.Mon)
		self.engine.disableCSVOutput()
		self.engine.ConsoleOutput(False)

	def _getTime(self):
		return time.clock_gettime(time.CLOCK_REALTIME)

	def getPower(self):
		self.getCurrent()
		self.getVoltage()
		self.power = self.voltage * self.current
		self.power_data.append(self.power)
		return self.power

		self.engine.enableChannel(sampleEngine.channels.MainCurrent)
		self.engine.enableChannel(sampleEngine.channels.MainVoltage)
		self.engine.startSampling(1)
		sample = self.engine.getSamples()
		current = sample[sampleEngine.channels.MainCurrent][0]
		voltage = sample[sampleEngine.channels.MainVoltage][0]
		self.Mon.stopSampling()
		self.engine.disableChannel(sampleEngine.channels.MainCurrent)
		self.engine.disableChannel(sampleEngine.channels.MainVoltage)
		self.power = current * voltage
		self.power_data.append(self.power)
		#print(self.power)
		return current * voltage

	def getVoltage(self):
		self.voltage = int(execute('cat /sys/class/power_supply/battery/voltage_now')) / 1000000
		print(self.voltage)
		return self.voltage

		self.engine.startSampling(1)
		sample = self.engine.getSamples()
		voltage = sample[sampleEngine.channels.MainVoltage][0]
		self.Mon.stopSampling()
		self.voltage = voltage
		return voltage

	def getCurrent(self):
		self.current = int(execute('cat /sys/class/power_supply/battery/current_now')) / 1000000
		print(self.current)
		return self.current

		self.engine.startSampling(1)
		sample = self.engine.getSamples()
		current = sample[sampleEngine.channels.MainCurrent][0]
		self.Mon.stopSampling()
		self.current = current
		return current
