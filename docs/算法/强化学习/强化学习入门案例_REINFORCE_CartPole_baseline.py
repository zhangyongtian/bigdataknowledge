# pip install gymnasium
# pip install numpy

# 使用一组轨迹的回报的均值作为基线
import matplotlib.pyplot as plt
import gymnasium as gym
import torch.nn as nn
import torch
import torch.nn.functional as F
from dataclasses import dataclass


# env = gym.make("CartPole-v1")

# state, _ = env.reset()

# print("S0: ", state)

# action = 0  # 向左推

# next_state, reward, terminated, truncated, _ = env.step(action)  # 在环境中执行动作

# print("S1: ", next_state)
# print("R0: ", reward)
# print("terminated表示以失败终结（没有玩满500步）: ", terminated)
# print("truncated表示成功：", truncated)


@dataclass
class Episode:
    """保存的是一条轨迹的数据"""
    states: torch.Tensor  # 状态
    actions: torch.Tensor  # 动作
    _return: float  # 总的奖励（回报）


class PolicyNet(nn.Module):
    """策略神经网络π_θ(A_t|S_t)"""

    def __init__(self):
        super().__init__()
        self.l1 = nn.Linear(4, 128)  # 4表示状态有4个浮点数
        self.l2 = nn.Linear(128, 2)  # 2表示两个动作

    def forward(self, x):
        """x是状态, x的形状是(B, 4)"""
        x = self.l1(x)  # (B, 128)
        x = F.relu(x)  # (B, 128)
        logits = self.l2(x)  # (B, 2)
        probs = F.softmax(logits, dim=-1)  # (B, 2)

        return probs


class Agent:
    """智能体"""

    def __init__(self):
        self.pi = PolicyNet()  # 初始化一个策略神经网络
        self.lr_pi = 0.001  # 策略神经网络的学习率
        # 优化器
        self.optimizer = torch.optim.Adam(self.pi.parameters(), lr=self.lr_pi)

    def get_action(self, state):
        # 形状变换：(4,) --> (1, 4)
        state = torch.tensor(state).unsqueeze(0)
        # 输出动作的概率分布了, 形状：(1, 2) --> (2,)
        probs = self.pi(state).squeeze(0)
        # 从概率分布中采样一个动作出来
        action = torch.multinomial(probs, num_samples=1).item()
        # 返回：(采取的动作，动作的概率分布)
        return action, probs

    def rollout(self, env) -> Episode:
        """在环境env中采样一条轨迹τ"""
        """τ = (S0, A0, R0, ...., S_T)"""
        state, _ = env.reset()  # 初始状态S0

        # 轨迹信息
        states = []  # [S0, S1, ..., S_{T-1}]
        actions = []  # [A0, A1, ..., A_{T-1}]
        rewards = []  # [R0, R1, ..., R_{T-1}]

        # 是否结束
        done = False

        while not done:
            # 选择一个动作出来
            action, _ = self.get_action(state)
            # 执行动作，返回：(S_{t+1}, R_t, 是否终结，是否截断，调试信息)
            next_state, reward, terminated, truncated, _ = env.step(action)

            # 是否结束
            done = terminated or truncated

            states.append(state)
            actions.append(action)
            rewards.append(reward)

            # 状态转移
            state = next_state

        states = torch.tensor(states)  # 转换成torch张量类型，形状：(B, 4)
        # 转换成torch张量类型，`.view(-1, 1)`的作用：(B,) --> (B, 1)
        actions = torch.tensor(actions).view(-1, 1)
        _return = sum(rewards)  # 累加所有的奖励就是回报

        episode = Episode(
            states=states,
            actions=actions,
            _return=_return
        )

        return episode

    def update(self, episodes):
        """使用n条轨迹计算策略梯度期望值的近似值，然后更新策略模型"""
        objs = []
        # 计算一组轨迹的回报的均值
        avg_reward = sum([episode._return for episode in episodes]) / len(episodes)
        for episode in episodes:
            # [logπ_θ(A_0|S_0), ..., logπ_θ(A_T|S_T)]
            log_action_probs = torch.log(torch.gather(
                self.pi(episode.states), -1, episode.actions))
            # Σ(G(τ) - 基线)logπ_θ(A_t|S_t)
            obj = torch.sum(log_action_probs) * (episode._return - avg_reward)
            objs.append(obj)

        loss = - sum(objs) / len(objs)

        self.optimizer.zero_grad()  # 将参数的梯度设置为0
        loss.backward()  # 对参数θ求梯度
        self.optimizer.step()


env = gym.make("CartPole-v1")

agent = Agent()

# state, _ = env.reset()

# print(agent.get_action(state))

episode = agent.rollout(env)

print(f"states: {episode.states}")
print(f"actions: {episode.actions}")
print(f"return: {episode._return}")

# 用来可视化
returns = []

# 训练
for step in range(300):
    # ① 采样8条轨迹
    episodes = []
    for _ in range(8):
        episode = agent.rollout(env)
        episodes.append(episode)
    # ② 更新策略模型
    agent.update(episodes)

    avg_return = sum([episode._return for episode in episodes]) / 8
    returns.append(avg_return)
    print(f"Step: {step + 1}, Return: {avg_return}")
    # if (step + 1) % 100 == 0:
    #     print(f"Step: {step + 1}, Return: {avg_return}")


f = plt.figure()
plt.plot(returns)
plt.xlabel("Step")
plt.ylabel("Return")
plt.title("CartPole-v1")
f.savefig("baseline-pgm.pdf")
plt.show()
