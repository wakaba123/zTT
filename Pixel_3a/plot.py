import csv
import matplotlib.pyplot as plt

# 初始化空列表以存储每个字段的数据
t, c_c, g_c, c_p, g_p, c_t, g_t, fps, reward, losses = [], [], [], [], [], [], [], [], [], []

# 从 output.csv 文件中读取数据
with open('output.csv', newline='') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        t.append(int(row[0]))
        c_c.append(int(row[1]))
        g_c.append(int(row[2]))
        c_p.append(float(row[3]))
        g_p.append(float(row[4]))
        c_t.append(float(row[5]))
        g_t.append(float(row[6]))
        fps.append(float(row[7]))
        reward.append(float(row[8]))
        # losses.append(float(row[9]))

# 定义字段名称和对应的数据
fields = {
    't': t,
    'c_c': c_c,
    'g_c': g_c,
    'c_p': c_p,
    'g_p': g_p,
    'c_t': c_t,
    'g_t': g_t,
    'fps': fps,
    'reward': reward,
    # 'losses': losses
}

# 为每个字段生成并保存图表
for field_name, field_data in fields.items():
    plt.figure()
    plt.plot(field_data)
    plt.title(f'{field_name} vs. Index')
    plt.xlabel('Index')
    plt.ylabel(field_name)
    plt.grid(True)
    plt.savefig(f'{field_name}.png')
    plt.close()

print("所有图表均已保存。")
