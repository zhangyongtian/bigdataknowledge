# pip install gymnasium numpy torch matplotlib

import matplotlib.pyplot as plt
import gymnasium as gym
import torch.nn as nn
import torch
import torch.nn.functional as F
from dataclasses import dataclass


@dataclass
class Episode:
    """保存的是一条轨迹的数据"""
    states: torch.Tensor   # 状态
    actions: torch.Tensor  # 动作
    _return: float         # 总的奖励（回报）


class PolicyNet(nn.Module):
    """策略神经网络 π_θ(A_t | S_t)"""

    def __init__(self):
        super().__init__()
        self.l1 = nn.Linear(4, 128)   # 4 表示状态有 4 个浮点数
        self.l2 = nn.Linear(128, 2)   # 2 表示两个动作（左 / 右）

    def forward(self, x):
        """x 是状态, x 的形状是 (B, 4)"""
        x = self.l1(x)          # (B, 128)
        x = F.relu(x)           # (B, 128)
        logits = self.l2(x)     # (B, 2)
        probs = F.softmax(logits, dim=-1)  # (B, 2)
        return probs


class Agent:
    """智能体"""

    def __init__(self):
        self.pi = PolicyNet()                       # 初始化一个策略神经网络
        self.lr_pi = 0.001                          # 策略神经网络的学习率
        self.optimizer = torch.optim.Adam(          # 优化器
            self.pi.parameters(), lr=self.lr_pi)

    def get_action(self, state):
        # 形状变换：(4,) --> (1, 4)  —— 因为 PyTorch 的 Linear 只吃 "Batch × Feature" 的二维输入
        state = torch.tensor(state).unsqueeze(0)
        # 输出动作的概率分布, 形状：(1, 2) --> (2,)
        probs = self.pi(state).squeeze(0)
        # 从概率分布中采样一个动作出来（0 或 1）
        action = torch.multinomial(probs, num_samples=1).item()
        # 返回：(采取的动作，动作的概率分布)
        return action, probs

    def rollout(self, env) -> Episode:
        """在环境 env 中采样一条完整轨迹 τ = (S0, A0, R1, S1, A1, R2, ...)"""
        state, _ = env.reset()                      # 初始状态 S0

        # 轨迹信息（先拿 Python list 攒，最后再一次性转 tensor，性能好）
        states  = []   # [S0, S1, ..., S_{T-1}]
        actions = []   # [A0, A1, ..., A_{T-1}]
        rewards = []   # [R1, R2, ..., R_T    ]   —— 注意：R1 是执行 A0 之后拿到的奖励

        done = False
        while not done:
            # ① 用当前策略选一个动作
            action, _ = self.get_action(state)
            # ② 在环境里执行动作，返回：(S_{t+1}, R_{t+1}, 失败结束, 满500步截断, 调试)
            next_state, reward, terminated, truncated, _ = env.step(action)

            done = terminated or truncated

            states.append(state)
            actions.append(action)
            rewards.append(reward)

            # ③ 状态转移：当前状态变成"下一步的状态"，循环继续
            state = next_state

        states  = torch.tensor(states)                     # (T, 4)
        actions = torch.tensor(actions).view(-1, 1)        # (T, 1)  —— 列向量，方便 gather
        _return = sum(rewards)                             # G(τ) = 累计奖励（无折扣）

        return Episode(states=states, actions=actions, _return=_return)

    def update(self, episodes):
        """
        用一批轨迹 {τ_i} 估计策略梯度，并更新 θ
        对应公式（文档 §2.5 的"朴素 REINFORCE"）：
          ∇_θ J(θ) ≈ (1/|B|) Σ_{τ∈B} [ Σ_t ∇ log π_θ(A_t|S_t) ] · G(τ)
        由于 PyTorch 只支持"最小化 loss"，我们最小化 loss = - (1/|B|) Σ obj_i
        等价于对 J(θ) 做梯度上升。
        """
        objs = []
        for episode in episodes:
            # 1) 对这条轨迹每一步的状态，跑 π_θ，得到每一步的 P(a|s)
            #    episode.states.shape = (T, 4)
            #    pi_output            = (T, 2)  每一行是 [P(左|s), P(右|s)]
            pi_output = self.pi(episode.states)

            # 2) 用 episode.actions 当索引，把"当时真正采样出来的那个动作的概率"挑出来
            #    episode.actions.shape = (T, 1)，gather 的结果形状也是 (T, 1)
            action_probs = torch.gather(pi_output, dim=-1, index=episode.actions)

            # 3) 取对数，得到 log π_θ(A_t|S_t)，形状 (T, 1)
            log_action_probs = torch.log(action_probs)

            # 4) 按文档 (4) 式：Σ_t log π_θ(A_t|S_t)  然后乘以整条轨迹的 G(τ)
            obj = torch.sum(log_action_probs) * episode._return
            objs.append(obj)

        # 5) 跨 batch 取均值，再加负号 → loss
        loss = - sum(objs) / len(objs)

        # 6) 标准三件套：清零梯度 → 反向传播 → 优化器走一步
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()


# =========================
#         主流程
# =========================
env = gym.make("CartPole-v1")   # 倒立摆环境：500 步不倒就算赢
agent = Agent()

returns = []   # 用来可视化：每一步 batch 的平均回报

# 训练：总共 1000 个 update 步
for step in range(1000):
    # ① 采样 8 条轨迹（batch 大小 = 8）
    episodes = []
    for _ in range(8):
        episode = agent.rollout(env)
        episodes.append(episode)

    # ② 用这 8 条轨迹更新一次策略网络 π_θ
    agent.update(episodes)

    avg_return = sum(ep._return for ep in episodes) / 8
    print(f"Step: {step + 1:4d}   Average Return: {avg_return:7.2f}")
    returns.append(avg_return)


# =========================
#       可视化 + 存图
# =========================
f = plt.figure()
plt.plot(returns)
plt.xlabel("Update Step")
plt.ylabel("Average Episode Return")
plt.title("CartPole-v1  (REINFORCE, batch=8, lr=1e-3)")
f.savefig("pgm.pdf")
plt.show()
