import subprocess
import random
import sys
sys.path.append('/home/wakaba/Desktop/zTT/')
import utils.tools as tools


cpu_freq_list, gpu_freq_list = tools.get_freq_list('k20p')
little_cpu_clock_list = tools.uniformly_select_elements(6, cpu_freq_list[0])
big_cpu_clock_list = tools.uniformly_select_elements(6, cpu_freq_list[1])
dir_thermal='/sys/devices/virtual/thermal'

flag = 0

class CPU:
	def __init__(self,idx,cpu_type,ip):
		self.idx=idx
		self.cpu_type = cpu_type
		self.ip = ip
		self.clock_data=[]
		self.temp_data=[]

		if self.cpu_type == 'b':
			self.cpu_type = 1
			self.max_freq = len(big_cpu_clock_list) - 1
			self.clk = len(big_cpu_clock_list) - 1
			self.cpu_clock_list = big_cpu_clock_list
		elif self.cpu_type == 'l':
			self.cpu_type = 0
			self.max_freq =  len(little_cpu_clock_list) - 1 
			self.clk = len(little_cpu_clock_list) - 1 
			self.cpu_clock_list = little_cpu_clock_list
		
		if flag:
			return None
		fname='/sys/devices/system/cpu/cpu%s/cpufreq/scaling_max_freq' %(self.idx)
		subprocess.check_output(['adb', '-s', self.ip, 'shell', 'su -c', '\"echo', str(self.cpu_clock_list[self.max_freq])+" >", fname+"\""])
		fname='/sys/devices/system/cpu/cpu%s/cpufreq/scaling_min_freq' %(self.idx)
		subprocess.check_output(['adb', '-s', self.ip, 'shell', 'su -c', '\"echo', str(self.cpu_clock_list[0])+" >", fname+"\""])		

	def setCPUclock(self,i):
		if flag:
			return 0
		i = min(i , len(self.cpu_clock_list) - 1)
		self.clk=i
		# fname='/sys/devices/system/cpu/cpu%s/cpufreq/scaling_setspeed' %(self.idx)
		# subprocess.check_output(['adb', '-s', self.ip, 'shell', 'su -c', '\"echo', str(self.cpu_clock_list[i])+" >", fname+"\""])
		tools.set_cpu_freq_by_type(self.cpu_type, self.cpu_clock_list[i])
		
	def getCPUtemp(self):
		if flag:
			return random.randint(50,70)
		fname='{}/thermal_zone10/temp'.format(dir_thermal)
		output = subprocess.check_output(['adb', '-s', self.ip, 'shell', 'su -c', '\"cat', fname+"\""])
		output = output.decode('utf-8')
		output = output.strip()
		return int(output)/1000

	def getCPUclock(self, idx):
		if flag:
			return random.randint(800000,2500000)
		fname='/sys/devices/system/cpu/cpu%s/cpufreq/cpuinfo_cur_freq' %idx
		output = subprocess.check_output(['adb', '-s', self.ip, 'shell', 'su -c', '\"cat', fname+"\""])
		output = output.decode('utf-8')
		output = output.strip()
		return int(output)/1000

	# def getAvailableClock(self):
	# 	for i in range(0,8):
	# 				fname='/sys/devices/system/cpu/cpu%s/cpufreq/scaling_available_frequencies' %(i)
	# 				output = subprocess.check_output(['adb', '-s', self.ip, 'shell', 'su -c', '\"cat', fname+"\""])
	# 				output = output.decode('utf-8')
	# 				output = output.strip()

	def collectdata(self):
		self.clock_data.append(self.getCPUclock(self.idx))
		self.temp_data.append(self.getCPUtemp())

	def currentCPUstatus(self):
		fname='/sys/devices/system/cpu/online'
		with open(fname,'r') as f:
			line=f.readline()
			print(line)
			f.close()

	def getCurrentClock(self):
		if self.cpu_type == 'l':
			for i in range(0,6):
				fname='/sys/devices/system/cpu/cpu%s/cpufreq/cpuinfo_cur_freq' %(i)
				output = subprocess.check_output(['adb', '-s', self.ip, 'shell', 'su -c', '\"cat', fname+"\""])
				output = output.decode('utf-8')
				output = output.strip()
				print('[cpu{}]{}KHz '.format(i,output),end=""),

		if self.cpu_type == 'b':
			for i in range(6,8):
				fname='/sys/devices/system/cpu/cpu%s/cpufreq/cpuinfo_cur_freq' %(i)
				output = subprocess.check_output(['adb', '-s', self.ip, 'shell', 'su -c', '\"cat', fname+"\""])
				output = output.decode('utf-8')
				output = output.strip()
				print('[cpu{}]{}KHz '.format(i,output),end=""),

	def setUserspace(self):
		return 0
		if flag:
			return 0
		if self.cpu_type == 'l':
			for i in range(0,6):
				fname='/sys/devices/system/cpu/cpu%s/cpufreq/scaling_governor' %(i)
				subprocess.check_output(['adb', '-s', self.ip, 'shell', 'su -c', '\"echo userspace >', fname+"\""])
				print('[cpu{}]Set userspace '.format(i),end="")

		if self.cpu_type == 'b':
			for i in range(6,8):
				fname='/sys/devices/system/cpu/cpu%s/cpufreq/scaling_governor' %(i)
				subprocess.check_output(['adb', '-s', self.ip, 'shell', 'su -c', '\"echo userspace >', fname+"\""])
				print('[cpu{}]Set userspace '.format(i),end="")

	def setdefault(self, mode):
		if flag:
			return 0
		if self.cpu_type == 'l':
			for i in range(0,6):
				fname='/sys/devices/system/cpu/cpu%s/cpufreq/scaling_governor' %(i)
				subprocess.check_output(['adb', '-s', self.ip, 'shell', 'su -c', '\"echo '+mode+' >', fname+"\""])
				print('[cpu{}]Set {}'.format(i,mode),end="")

		if self.cpu_type == 'b':
			for i in range(6,8):
				fname='/sys/devices/system/cpu/cpu%s/cpufreq/scaling_governor' %(i)
				subprocess.check_output(['adb', '-s', self.ip, 'shell', 'su -c', '\"echo '+mode+' >', fname+"\""])
				print('[cpu{}]Set {}'.format(i,mode),end="")
