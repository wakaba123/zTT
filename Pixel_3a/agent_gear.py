#!/usr/bin/env python3

import warnings
import os
from threading import Thread
import time
import random
import socket
import struct
import math
from collections import namedtuple
import numpy as np
import torch
from torch import nn
import torch.nn.functional as F
import torch.utils.data
import train_utils as train_utils
import matplotlib.pyplot as plt


PORT = 8702
experiment_time=1000#14100
clock_change_time=30
cpu_power_limit=1000
gpu_power_limit=1600
action_space=9
target_fps=60
target_temp=65
beta=2 #4

Transition = namedtuple('Transition',
                        ('state', 'action', 'next_state', 'reward'))

class ReplayMemory(torch.utils.data.Dataset):
    """
    Basic ReplayMemory class. 
    Note: Memory should be filled before load.
    """
    def __init__(self, capacity):
        self.capacity = capacity
        self.memory = []
        self.position = 0

    def __getitem__(self, idx):        
        return self.memory[idx] 

    def __len__(self):
        return len(self.memory)

    def push(self, *args):
        """Saves a transition."""
        if len(self.memory) < self.capacity:
            # to avoid index out of range
            self.memory.append(None)
        transition = Transition(*args)
        self.memory[self.position] = transition
        self.position = (self.position + 1) % self.capacity


# RL Controller with action branching
class DQN_AB(nn.Module):
    def __init__(self, s_dim=10, h_dim=25, branches=[1,2,3]):
        super(DQN_AB, self).__init__()
        self.s_dim, self.h_dim = s_dim, h_dim
        self.branches = branches
        self.shared = nn.Sequential(nn.Linear(self.s_dim, self.h_dim), nn.ReLU())
        self.shared_state = nn.Sequential(nn.Linear(self.h_dim, self.h_dim), nn.ReLU())
        self.domains, self.outputs = [], []
        for i in range(len(branches)):
            layer = nn.Sequential(nn.Linear(self.h_dim, self.h_dim), nn.ReLU())
            self.domains.append(layer)
            layer_out = nn.Sequential(nn.Linear(self.h_dim*2, branches[i]))
            self.outputs.append(layer_out)

    def forward(self, x):
        # return list of tensors, each element is Q-Values of a domain
        f = self.shared(x)
        s = self.shared_state(f)
        outputs = []
        for i in range(len(self.branches)):
            branch = self.domains[i](f)
            branch = torch.cat([branch,s],dim=1)
            outputs.append(self.outputs[i](branch))

        return outputs

# Agent with action branching without time context
class DQN_AGENT_AB():
    def __init__(self, s_dim, h_dim, branches, buffer_size, params):
        self.eps = 0.8
        # 2D action space
        self.actions = [np.arange(i) for i in branches]
        # Experience Replay(requires belief state and observations)
        self.mem = ReplayMemory(buffer_size)
        # Initi networks
        self.policy_net = DQN_AB(s_dim, h_dim, branches)
        self.target_net = DQN_AB(s_dim, h_dim, branches)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()

        self.optimizer = torch.optim.RMSprop(self.policy_net.parameters())
        self.criterion = nn.SmoothL1Loss() # Huber loss
        
    def max_action(self, state):
        # actions for multidomains
        max_actions = []
        with torch.no_grad():
            # Inference using policy_net given (domain, batch, dim)
            q_values = self.policy_net(state)
            for i in range(len(q_values)):
                domain = q_values[i].max(dim=1).indices
                max_actions.append(self.actions[i][domain])
        return max_actions

    def e_gready_action(self, actions, eps):
        # Epsilon-Gready for exploration
        final_actions = []
        for i in range(len(actions)):
            p = np.random.random()
            if isinstance(actions[i],np.ndarray):
                if p < 1- eps:
                    final_actions.append(actions[i])
                else:
                    # randint in (0, domain_num), for batchsize
                    final_actions.append(np.random.randint(len(self.actions[i]),size=len(actions[i])))
            else:
                if p < 1- eps:
                    final_actions.append(actions[i])
                else:
                    final_actions.append(np.random.choice(self.actions[i]))

        return final_actions

    def select_action(self, state):
        return self.e_gready_action(self.max_action(state),self.eps)

    def train(self, n_round, n_update, n_batch):
        # Train on policy_net
        losses = []
        self.target_net.train()
        train_loader = torch.utils.data.DataLoader(
            self.mem, shuffle=True, batch_size=n_batch, drop_last=True)

        length = len(train_loader.dataset)
        GAMMA = 1.0

        # Calcuate loss for each branch and then simply sum up
        for i, trans in enumerate(train_loader):
            loss = 0.0 # initialize loss at the beginning of each batch
            states, actions, next_states, rewards = trans
            with torch.no_grad():
                target_result = self.target_net(next_states)
            policy_result = self.policy_net(states)
            # Loop through each action domain
            for j in range(len(self.actions)):
                next_state_values = target_result[j].max(dim=1)[0].detach()
                expected_state_action_values = (next_state_values*GAMMA) + rewards.float()
                # Gather action-values that have been taken
                branch_actions = actions[:,j].long()
                state_action_values = policy_result[j].gather(1, branch_actions.unsqueeze(1))
                loss += self.criterion(state_action_values, expected_state_action_values.unsqueeze(1))
            losses.append(loss.item())
            self.optimizer.zero_grad()
            loss.backward()
            if i>n_update:
                break
            # Gradient clipping to prevent exploding gradients
            # for param in self.policy_net.parameters()
            #     param.grad.data.clamp_(-1, 1)
            self.optimizer.step()
        return losses

    def save_model(self, n_round, savepath):
        train_utils.save_checkpoint({'epoch': n_round, 'model_state_dict':self.target_net.state_dict(),
            'optimizer_state_dict':self.optimizer.state_dict()}, savepath)

    def load_model(self, loadpath):
        if not os.path.isdir(loadpath): os.makedirs(loadpath)
        checkpoint = train_utils.load_checkpoint(loadpath)
        self.policy_net.load_state_dict(checkpoint['model_state_dict'])
        self.target_net.load_state_dict(checkpoint['model_state_dict'])
        self.target_net.eval()

    def sync_model(self):
        self.target_net.load_state_dict(self.policy_net.state_dict())

def get_reward(fps, power, target_fps, c_t, g_t, c_t_prev, g_t_prev, beta):
    v1=0
    v2=0
    print('power={}'.format(power))
    u=max(1,fps/target_fps)

    if g_t<= target_temp:
        v2=0
    else:
        v2=2*(target_temp-g_t)
    if c_t_prev < target_temp:
        if c_t >= target_temp:
            v1=-2

    if fps>=target_fps:
        u=1
    else :
        u=math.exp(0.1*(fps-target_fps))
    return u+v1+v2+beta/power

    
if __name__=="__main__":

    # s_dim: 状态维度，即输入的状态向量的维度。
    # h_dim: 隐藏层的维度，即神经网络中间层的神经元数量。
    # branches : 每个分支的action的数量
    agent = DQN_AGENT_AB(7, 15, [3,3,3], 200, None) 
    scores, episodes = [], []

    t=1
    learn=1
    ts=[]
    fps_data=[]
    power_data=[]
    avg_q_max_data=[]
    loss_data = []
    avg_reward=[]
    reward_tmp=[]

    cnt=0
    c_c=3
    g_c=3
    c_t=37
    g_t=37
    c_t_prev=37
    g_t_prev=37
    print("TCPServr Waiting on port 8702")
    state=(3,3,20,27,40,40,30)
    score=0
    action=[0,0,0]
    losses = 0

    clk=11
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("", PORT))
    server_socket.listen(5)
    f = open("output.csv", "w")

    try:
        client_socket, address = server_socket.accept()

        while t < experiment_time:
            msg = client_socket.recv(512).decode()  # 获取从客户端发来的数据
            state_tmp = msg.split(',')
            
            if not msg:
                print('No receiveddata')
                break

            # 解析数据
            c_t_prev=c_t
            g_t_prev=g_t
            c_c, g_c, c_p, g_p, c_t, g_t, fps = int(state_tmp[0]), int(state_tmp[1]), float(state_tmp[2]), float(state_tmp[3]), float(state_tmp[4]), float(state_tmp[5]), float(state_tmp[6])

            next_state=(c_c, g_c, c_p, g_p, c_t, g_t,fps)
            
            # reward  TBD 第一次如何考虑
            reward = get_reward(fps, c_p+g_p, target_fps, c_t, g_t, c_t_prev, g_t_prev, beta)

            # replay memory
            agent.mem.push(torch.tensor(state).float(), torch.tensor(action).float(), torch.tensor(next_state).float(), torch.tensor(reward).float())
            f.write(str(t)+','+str(c_c)+','+str(g_c)+','+str(c_p)+','+str(g_p)+','+str(c_t)+','+str(g_t)+','+str(fps)+','+str(reward)+',' + str(losses) + '\n')
            f.flush() 
            print('[{}] state:{} action:{} next_state:{} reward:{} fps:{}'.format(t, state,action,next_state,reward,fps))

            # 获得action
            with torch.no_grad():
                action = agent.select_action(agent.mem[-1].state.unsqueeze(0))

            # 发送action
            c_c, c2_c, g_c = action
            send_msg=str(c_c)+','+str(c2_c)+','+str(g_c)
            client_socket.send(send_msg.encode())

            if (t > 5):
                losses = agent.train(1,2,2)
            
            # get action
            state=next_state
            t += 1
           
    finally:
        f.close()
        server_socket.close()