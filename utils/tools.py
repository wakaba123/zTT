import configparser
import subprocess

check_flag = False
check_result = []

def execute(cmd):
    cmds = [ 'su',cmd, 'exit']
    # cmds = [cmd, 'exit']
    obj = subprocess.Popen("adb shell", shell= True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    info = obj.communicate(("\n".join(cmds) + "\n").encode('utf-8'))
    return info[0].decode('utf-8')

# check soc architecture
def check_soc():
    if check_flag:
        return check_result

    position = '/sys/devices/system/cpu/cpufreq'
    cmd = f'ls {position}'
    result = execute(cmd)
    check_result = result.split()
    return check_result
    

# set cpu governor
def set_cpu_governor(governor):
    cpu_type = check_soc()
    for policy in cpu_type:
        execute(f'echo {governor} > /sys/devices/system/cpu/cpufreq/{policy}/scaling_governor')

# set cpu frequency
def set_cpu_freq(freq):
    cpu_type = check_soc()
    policy = cpu_type
    for i in range(len(cpu_type)):
        execute(f'echo {freq[i]} > /sys/devices/system/cpu/cpufreq/{policy[i]}/scaling_min_freq')
        execute(f'echo {freq[i]} > /sys/devices/system/cpu/cpufreq/{policy[i]}/scaling_max_freq')

# set cpu frequency by type
def set_cpu_freq_by_type(type, freq): # 0 means little, 1 means big , 2 means super big
    cpu_type = check_soc()
    execute(f'echo {freq} > /sys/devices/system/cpu/cpufreq/{cpu_type[type]}/scaling_min_freq')
    execute(f'echo {freq} > /sys/devices/system/cpu/cpufreq/{cpu_type[type]}/scaling_max_freq')

# get cpu frequency
def get_cpu_freq():
    cpu_type = check_soc()
    # print(cpu_type)
    result = []
    for policy in cpu_type:
        result.append(execute(f'cat /sys/devices/system/cpu/cpufreq/{policy}/scaling_cur_freq').replace('\n',''))
    return result

# set gpu governor
def set_gpu_governor(governor):
    execute(f'echo {governor} > /sys/class/kgsl/kgsl-3d0/devfreq/governor')

# set gpu frequency
def set_gpu_freq(freq, index):
    execute(f'echo {freq} > /sys/class/kgsl/kgsl-3d0/devfreq/min_freq')
    execute(f'echo {freq} > /sys/class/kgsl/kgsl-3d0/devfreq/max_freq')
    execute(f'echo {index} > /sys/class/kgsl/kgsl-3d0/min_pwrlevel')
    execute(f'echo {index} > /sys/class/kgsl/kgsl-3d0/max_pwrlevel')
    execute(f'echo {freq[:-6]} > /sys/class/kgsl/kgsl-3d0/max_clock_mhz')
    execute(f'echo {freq[:-6]} > /sys/class/kgsl/kgsl-3d0/min_clock_mhz')
    execute(f'echo {index} > /sys/class/kgsl/kgsl-3d0/thermal_pwrlevel')
    execute(f'echo {index} > /sys/class/kgsl/kgsl-3d0/default_pwrlevel')
    
# get gpu frequency
def get_gpu_freq():
    return execute(f'cat /sys/class/kgsl/kgsl-3d0/devfreq/cur_freq').replace('\n','')

def turn_off_on_core(type, on): # type should be 0,1,2   on should be 0 , 1
    cpu_type = check_soc()
    cpu_type[0]='1'
    for i in range(int(cpu_type[type][-1]), 8 if int(type) == 1 else  int(cpu_type[type + 1][-1])):
        execute(f'echo {on} > /sys/devices/system/cpu/cpu{i}/online') 

def get_freq_list(device_name):
    config = configparser.ConfigParser()
    config.read('/home/wakaba/Desktop/zTT/utils/config.ini')

    cpu_type = check_soc()
    cpu_type = len(cpu_type)

    freq_lists = {
        2: ['little_freq_list','big_freq_list'],
        3: ['little_freq_list', 'big_freq_list', 'super_freq_list']
    }
    if cpu_type in freq_lists:
        cpu_freq_list = [config.get(device_name, freq).split() for freq in freq_lists[cpu_type]]
    else:
        print("Unsupported CPU type")
        raise ValueError

    gpu_freq_list = config.get(device_name,'gpu_freq_list').split()
    return cpu_freq_list, gpu_freq_list

def uniformly_select_elements(n, array):
    """
    从给定的数组中均匀选择 n 个元素。
    
    参数:
    n (int): 要选择的元素个数。
    array (list): 输入的数组。

    返回:
    list: 包含 n 个均匀分布的元素的新数组。
    """
    if n <= 0 or not array:
        return []

    step = len(array) / n
    selected_elements = [array[int(i * step)] for i in range(n)]
    return selected_elements