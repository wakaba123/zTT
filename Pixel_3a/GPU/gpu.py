'''
Author: wakaba blues243134@gmail.com
Date: 2024-04-11 17:22:59
LastEditors: wakaba blues243134@gmail.com
LastEditTime: 2024-04-12 10:30:18
FilePath: /zTT/Pixel_3a/GPU/gpu.py
Description: 

Copyright (c) 2024 by wakaba All Rights Reserved. 
'''
import subprocess

# gpu_clock_list=[180000000, 267000000, 355000000, 430000000]
gpu_clock_list='257000000 414000000 596000000 710000000'.split()
dir_thermal='/sys/devices/virtual/thermal'

class GPU:
    def __init__(self,ip):
        self.clk=3
        self.clock_data=[]
        self.temp_data=[]
        self.ip = ip
        
        fname='/sys/class/kgsl/kgsl-3d0/devfreq/max_freq'
        subprocess.check_output(['adb', '-s', self.ip, 'shell', 'su -c', '\"echo', str(gpu_clock_list[3])+" >", fname+"\""])
        fname='/sys/class/kgsl/kgsl-3d0/devfreq/min_freq'
        subprocess.check_output(['adb', '-s', self.ip, 'shell', 'su -c', '\"echo', str(gpu_clock_list[0])+" >", fname+"\""])
		
    def setGPUclock(self,i):
        self.clk=i
        fname='/sys/class/kgsl/kgsl-3d0/devfreq/userspace/set_freq'
        subprocess.check_output(['adb', '-s', self.ip, 'shell', 'su -c', '\"echo', str(gpu_clock_list[i])+" >", fname+"\""])
		
    def getGPUtemp(self):
        fname='{}/thermal_zone10/temp'.format(dir_thermal)
        output = subprocess.check_output(['adb', '-s', self.ip, 'shell',  'su -c', '\"cat', fname+"\""])
        output = output.decode('utf-8')
        output = output.strip()
        return int(output)/1000

    def getGPUclock(self):
        fname='/sys/class/kgsl/kgsl-3d0/devfreq/cur_freq'
        output = subprocess.check_output(['adb', '-s', self.ip, 'shell',  'su -c', '\"cat', fname+"\""])
        output = output.decode('utf-8')
        output = output.strip()
        return int(output)/1000000

    def collectdata(self):
        self.clock_data.append(self.getGPUclock())
        self.temp_data.append(self.getGPUtemp())

    def setUserspace(self):
        fname='/sys/class/kgsl/kgsl-3d0/devfreq/governor'
        subprocess.check_output(['adb', '-s', self.ip, 'shell',  'su -c', '\"echo userspace >', fname+"\""])
        print('[gpu]Set userspace')
    
    def setdefault(self):
        fname='/sys/class/kgsl/kgsl-3d0/devfreq/governor'
        subprocess.check_output(['adb', '-s', self.ip, 'shell',  'su -c', '\"echo msm-adreno-tz >', fname+"\""])
        print('[gpu]Set msm-adreno-tz')
    
    def getCurrentClock(self):
        fname='/sys/class/kgsl/kgsl-3d0/devfreq/cur_freq'
        output = subprocess.check_output(['adb', '-s', self.ip, 'shell',  'su -c', '\"cat', fname+"\""])
        output = output.decode('utf-8')
        output = output.strip()
        print('[gpu]{}Hz'.format(output))
