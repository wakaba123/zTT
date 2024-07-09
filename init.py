import subprocess

def execute(cmd):
    cmds = [ 'su',cmd, 'exit']
    obj = subprocess.Popen("adb -s shell", shell= True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    info = obj.communicate(("\n".join(cmds) + "\n").encode('utf-8'))
    return info[0].decode('utf-8')

execute('echo schedutil > /sys/devices/system/cpu/cpufreq/policy0/scaling_governor')
execute('echo schedutil > /sys/devices/system/cpu/cpufreq/policy4/scaling_governor')
execute('echo msm-adreno-tz > /sys/class/kgsl/kgsl-3d0/devfreq/governor')

