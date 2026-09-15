---
sidebar_position: 4
sidebar_label: 入门案例：CartPole + REINFORCE（含代码逐行解读）
---

## 一、本案例的目标

我们要用[**策略梯度法公式推导**](策略梯度法公式推导.md)里最后得到的 **朴素 REINFORCE 算法**，把倒立摆（CartPole-v1）训练到"玩满 500 步不倒下"。

- 代码文件：[强化学习入门案例_REINFORCE_CartPole.py](强化学习入门案例_REINFORCE_CartPole.py)
- 对应推导章节：策略梯度法公式推导 §2.5 的 (4) 式（"Σ log π × 整局回报"的朴素版本）

### 1.1 CartPole 环境速记（先把 $\mathcal{S}$ 和 $\mathcal{A}$ 搞清楚）

| 项目 | 含义 | 代码里的形状/取值 |
|---|---|---|
| 状态 $\mathcal{S}$ | 4 个浮点数：小车位置、小车速度、杆角度、杆角速度 | `np.array.shape = (4,)` |
| 动作 $\mathcal{A}$ | 2 个离散动作：0=向左推，1=向右推 | `int ∈ {0, 1}` |
| 奖励 | 每存活一步 +1，死了也不扣分，满分一局 = 500 | 每步 `reward = 1.0` |
| 结束条件 | 杆歪了/车冲出 → `terminated=True`；玩满 500 步 → `truncated=True` | `done = terminated or truncated` |

---

## 二、代码每个模块在干嘛 + 数据形状逐行跟踪

下面的章节结构**完全对应代码文件里的顺序**。

---

### 2.1 导入 + Episode 数据结构

```python
import matplotlib.pyplot as plt
import gymnasium as gym
import torch.nn as nn
import torch
import torch.nn.functional as F
from dataclasses import dataclass

@dataclass
class Episode:
    states: torch.Tensor   # 一条轨迹里见过的所有状态
    actions: torch.Tensor  # 每个时刻采取的动作
    _return: float         # 这条轨迹的总奖励 G(τ) = Σ R
```

> `Episode` 的用途：函数 `rollout()` 把"一整局玩下来"产生的所有 $S_{t},\ A_{t},\ G(\tau)$ 打包成一个对象方便传参。
>
> 以一局 120 步倒下为例：
> - `states.shape  = (120, 4)`
> - `actions.shape = (120, 1)`（这里故意做成列向量，后续 `gather` 更方便）
> - `_return       = 120.0`（每步 +1，没折扣）

---

### 2.2 PolicyNet（策略网络）—— 把 $s$ 映射成 $P(a \mid s)$

```python
class PolicyNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.l1 = nn.Linear(4, 128)
        self.l2 = nn.Linear(128, 2)

    def forward(self, x):          # x: (B, 4)
        x = self.l1(x);  x = F.relu(x)   # -> (B, 128)
        logits = self.l2(x)               # -> (B, 2)
        probs = F.softmax(logits, dim=-1) # -> (B, 2)，且每行和 = 1
        return probs
```

这里实现的就是公式里的 $\pi_{\theta}(a \mid s)$：输入状态 $s$（长度 4），输出长度为 2 的概率向量 $\big[\pi_{\theta}(\text{左} \mid s),\ \pi_{\theta}(\text{右} \mid s)\big]$。

#### 举个具体例子（B=1 时，单步输入）

假设 $s = [+0.03,\ -0.02,\ +0.01,\ +0.05]$（杆有点偏右），通过网络输出可能是：

| 位置 | 数值 | 含义 |
|---|---|---|
| `probs[0]` | 0.37 | 向左推的概率 37% |
| `probs[1]` | 0.63 | 向右推的概率 63%（杆偏右 → 网络倾向于往右推来对杆） |

---

### 2.3 Agent.get_action —— 给定单个状态，采样一个动作

```python
def get_action(self, state):
    # state 是 numpy，形状 = (4,)  例: [ 0.03, -0.02,  0.01,  0.05]
    state = torch.tensor(state).unsqueeze(0)   # -> (1, 4) （加一个 batch 维）
    probs = self.pi(state).squeeze(0)          # -> (2,)    去掉 batch 维
    action = torch.multinomial(probs, num_samples=1).item()  # 按概率抽 0 或 1
    return action, probs
```

**为什么必须 `unsqueeze(0)`？**
因为 `nn.Linear(in, out)` 只接受形如 `(B, in)` 的二维输入。单个状态是一维的 `(4,)`，Linear 不知道它代表"batch=1 的 4 维特征"还是"batch=4 的 1 维特征"，所以要手动加一个 batch 维变成 `(1, 4)`。

**形状流动表**

| 变量 | 形状 | 例 |
|---|---|---|
| `state` (numpy 入参) | `(4,)` | `[ 0.03, -0.02,  0.01,  0.05]` |
| `state` (tensor) | `(1, 4)` | `[[0.03, -0.02, 0.01, 0.05]]` |
| `probs = pi(state)` | `(1, 2)` | `[[0.37, 0.63]]` |
| `probs` (squeeze 后) | `(2,)` | `[0.37, 0.63]` |
| `action`（int） | 标量 | `1` （表示这次采样到"向右推"） |

> `torch.multinomial(probs, 1)` 就是"按 probs 的权重从 {0,1} 抽 1 个样本"——这是策略是随机策略的体现：同一个 state 多跑两次，action 可能不一样。

---

### 2.4 Agent.rollout —— 用当前策略玩一整局，拿到一条完整轨迹 $\tau$

```python
def rollout(self, env) -> Episode:
    state, _ = env.reset()   # S0

    states, actions, rewards = [], [], []
    done = False

    while not done:
        action, _ = self.get_action(state)                # ① 选动作 A_t
        next_state, reward, terminated, truncated, _ = \
            env.step(action)                               # ② 执行，拿 R_{t+1}, S_{t+1}
        done = terminated or truncated
        states.append(state);  actions.append(action);  rewards.append(reward)
        state = next_state                                 # ③ 状态转移

    states  = torch.tensor(states)              # (T, 4)
    actions = torch.tensor(actions).view(-1, 1) # (T, 1)
    _return = sum(rewards)                      # 标量 = G(τ)
    return Episode(states, actions, _return)
```

#### 循环内每一步 append 的数据形状

假设一局在 $T=120$ 步时倒下。循环跑 120 次，每次往 list 里追加：

| 变量 | 每次追加的元素 | 第 120 次结束后 list 长度 | 最终 tensor 形状 |
|---|---|---|---|
| `states` | `np.array.shape=(4,)` 的 $S_{t}$ | 120 | `states.shape = (120, 4)` |
| `actions` | `int ∈ {0,1}` 的 $A_{t}$ | 120 | `actions.view(-1,1).shape = (120, 1)` |
| `rewards` | `1.0` 的 $R_{t+1}$ | 120 | `sum(rewards) = 120.0 = G(\tau)` |

> 为什么要把 `actions` 从 `(120,)` reshape 成 `(120, 1)`？是为了下一步 `gather` 能当索引用——gather 要求 `index` 和 `input` 维数相同。

---

### 2.5 Agent.update —— 用 8 条轨迹估算策略梯度、更新一次 $\theta$

这是整个文件**最重要的一段**，它直接对应 [策略梯度法公式推导](策略梯度法公式推导.md) §2.5 的 (4) 式：

$$
\nabla_{\theta} J(\theta) \approx \frac{1}{|\mathcal{B}|}\sum_{\tau\in\mathcal{B}}\Big[\sum_{t=0}^{T-1}\nabla_{\theta} \log\pi_{\theta}(A_{t} \mid S_{t})\Big]\cdot G(\tau)
$$

由于 PyTorch 的 `optimizer.step()` 默认是**梯度下降**（让 loss 变小），而我们想做的是**梯度上升**（让 $J(\theta)$ 变大），所以代码里会取一个负号：$loss = -\dfrac{1}{|\mathcal{B}|}\sum obj$，loss.backward 得到的梯度方向就正好是 $\nabla_{\theta} J$。

```python
def update(self, episodes):   # episodes 是一个长度 = 8 的 list，每个元素是 Episode
    objs = []
    for episode in episodes:
        # (1) 把一条轨迹所有状态一次性丢进策略网络
        #     episode.states : (T, 4)  ->  pi_output : (T, 2)
        pi_output = self.pi(episode.states)

        # (2) 挑出"当时真的采样出来的那个动作"对应的概率
        #     episode.actions : (T, 1)  ->  action_probs : (T, 1)
        action_probs = torch.gather(pi_output, dim=-1, index=episode.actions)

        # (3) 取对数 -> log π_θ(A_t | S_t)
        log_action_probs = torch.log(action_probs)    # (T, 1)

        # (4) Σ_t log π * G(τ)      —— 这里就是 (4) 式里一条 τ 的部分
        obj = torch.sum(log_action_probs) * episode._return   # 标量
        objs.append(obj)

    # (5) 跨 batch 平均 + 加负号 → loss（这样对 loss 做梯度下降 = 对 J 做梯度上升）
    loss = - sum(objs) / len(objs)

    # (6) 标准三件套：清零梯度 -> 反向传播 -> 参数走一步
    self.optimizer.zero_grad()
    loss.backward()
    self.optimizer.step()
```

#### `torch.gather` 在做什么？（最容易看不懂的一行，举个数例）

假设某条轨迹 $T=3$ 步，网络输出如下表：

| 时刻 $t$ | `pi_output[t]` = $[P(\text{左} \mid s),\ P(\text{右} \mid s)]$ | `episode.actions[t,0]`（当时实际选的动作） | `gather 挑出来的 action_probs[t,0]` |
|---|---|---|---|
| 0 | `[0.2, 0.8]` | `1`（向右推） | `0.8` |
| 1 | `[0.6, 0.4]` | `0`（向左推） | `0.6` |
| 2 | `[0.3, 0.7]` | `1`（向右推） | `0.7` |

- `pi_output.shape = (3, 2)`，`actions.shape = (3, 1)`
- `gather(dim=-1, index=actions)` 语义："在每一行里（dim=-1 就是最后一维），按 index 指定的列号把元素取出来"
- 结果 `action_probs.shape = (3, 1)`，数值为 `[[0.8], [0.6], [0.7]]`

#### 形状流动表（一条 $T=120$ 的轨迹）

| 变量 | 形状 | 含义 |
|---|---|---|
| `episode.states` | `(120, 4)` | 120 步的状态 |
| `pi_output` | `(120, 2)` | 120 步的 $[\pi(\text{左}),\ \pi(\text{右})]$ |
| `action_probs` | `(120, 1)` | 120 步的 $\pi(A_{t} \mid S_{t})$ |
| `log_action_probs` | `(120, 1)` | 120 步的 $\log \pi(A_{t} \mid S_{t})$ |
| `torch.sum(log_action_probs)` | 标量 | $\sum_{t} \log \pi_{t}$ |
| `obj = sum_log_prob × _return` | 标量 | $G(\tau) \cdot \sum_{t} \log \pi_{t}$，这就是策略梯度估计里"一条轨迹对 θ 的推动方向"的反向传播锚点 |
| `loss` | 标量 | $-\frac{1}{8}\sum obj$ |

#### 直觉（非常关键）
- 如果这条轨迹的 $G(\tau)$ 很大（玩了 500 步赢了），那么 `obj` 里的"$\sum_{t} \log \pi_{t}$"会被乘上一个大正数，等价于告诉网络："刚才这一整局你做过的所有动作（的对数概率）都给我增加一点，下次这些动作出现的概率更大。"
- 如果这条轨迹的 $G(\tau)$ 很小（10 步就死了），`obj` 里乘的权重很小甚至为正但很小（我们当前用的是无折扣无基线版），那么这一局动作就几乎得不到提升——下次出现概率不会显著变大。
- 这正是策略梯度方法的核心直觉：**用"奖励大小"当权重，加权调节"动作出现概率的 log-likelihood"，让高回报轨迹在未来更多被采样。**

---

### 2.6 主训练循环（1000 次更新）

```python
env = gym.make("CartPole-v1")
agent = Agent()

returns = []

for step in range(1000):
    # ① 采样 batch_size = 8 条轨迹
    episodes = []
    for _ in range(8):
        episodes.append(agent.rollout(env))

    # ② 用这 8 条更新一次策略网络 θ
    agent.update(episodes)

    avg_return = sum(ep._return for ep in episodes) / 8
    print(f"Step: {step + 1:4d}   Avg Return: {avg_return:7.2f}")
    returns.append(avg_return)
```

每次循环就是一次完整的"**采样 → 估梯度 → 走一步优化器**"，一共做 1000 次。对 CartPole 这种小任务，通常 100~300 次更新就能把平均回报打到接近 500。

---

### 2.7 画图

```python
f = plt.figure()
plt.plot(returns)
plt.xlabel("Update Step")
plt.ylabel("Average Episode Return")
plt.title("CartPole-v1  (REINFORCE, batch=8, lr=1e-3)")
f.savefig("pgm.pdf")
plt.show()
```

典型曲线：前几十步在 20~50 左右抖，随后突然陡峭地爬上 400+，并在 475~500 附近收敛。

---

## 三、代码 ↔ 公式 的位置对照表

| 代码位置 | 对应的公式（在[策略梯度法公式推导](策略梯度法公式推导.md)里） |
|---|---|
| `Episode._return = sum(rewards)` | §1.2 的 $R(\tau)=\sum R$（这里代码没乘折扣，$\gamma=1$） |
| `PolicyNet.forward` 输出 `softmax(logits)` | §1.2 的策略 $\pi_{\theta}(a \mid s)$ |
| `get_action()` 里 `torch.multinomial` | 从 $\pi_{\theta}(\cdot \mid s)$ 采样 $A_{t} \sim \pi_{\theta}$ |
| `rollout()` 的 while 循环 | 生成 $\tau=(S_{0},A_{0},R_{1},\dots)$，概率分布是 §2.4 的 $P_{\theta}(\tau)$ |
| `update()` 的 `log_action_probs` | §2.4 (3) 式里的 $\nabla$ 后面那串的被求导变量：$\log \pi_{\theta}(A_{t} \mid S_{t})$ |
| `update()` 的 `obj = sum(log_action_probs) * _return` | §2.5 (4) 式的"方括号 × G(τ)"，因为 `loss.backward` 对 $\theta$ 求导，正好等于 $\nabla \log \pi_{t}$ 的累加乘以 $G(\tau)$ |
| `loss = -sum(objs)/8` | §2.5 末尾：把"梯度上升"转换成 PyTorch 的"最小化 loss"约定 |

---

## 四、朴素版的小缺陷（改进方向 = 下一步学什么）

1. **没有因果修正**：当前版本里 $t=0$ 的动作也被乘了"整局的总奖励"，等价于文档 §2.6 提到的朴素 REINFORCE。下一版应该把 `episode._return` 换成"每个时刻 $t$ 单独的 $G_{t} = R_{t+1} + \gamma R_{t+2} + \cdots$"权重。
2. **（已在基线版实现 → 见§五）** ~~没有减基线：奖励都在 0 以上，会导致"所有动作的 `log_prob` 都想被放大，只是大小有差"，学起来比较慢、方差大。~~

> 完整的下一步改进是同时做到：**因果的 $G_t$ 权重 + 用状态价值网络 $V_{\phi}(s)$ 算优势函数** $A_{t} = G_{t} - V_{\phi}(S_{t})$，即 Actor-Critic 框架。

即便如此，这版朴素代码已经把**策略梯度法从"公式"变成"能跑的程序"**的所有核心骨架跑通了，值得反复对照推导看几遍。

---

## 五、带基线（Baseline）版本——代码逐行对照 & 公式锚点

基线版本代码文件：[强化学习入门案例_REINFORCE_CartPole_baseline.py](强化学习入门案例_REINFORCE_CartPole_baseline.py)

它和朴素版的差别**只在 `update()` 函数里加了两行**，其余 `Episode / PolicyNet / get_action / rollout` 完全一致。下面只讲"变了什么、为什么变"。

### 5.1 变在哪里？—— `update()` 两行核心改动

```python
def update(self, episodes):
    objs = []
    # ✨ 改动①：计算当前 batch 的平均回报当作基线 b
    avg_reward = sum([ep._return for ep in episodes]) / len(episodes)   # (B-1)
    for episode in episodes:
        log_action_probs = torch.log(torch.gather(
            self.pi(episode.states), -1, episode.actions))
        # ✨ 改动②：用 (G(τ) − b) 代替原来的 G(τ) 做权重
        obj = torch.sum(log_action_probs) * (episode._return - avg_reward)  # (B-2)
        objs.append(obj)
    loss = - sum(objs) / len(objs)
    ...
```

### 5.2 它对应公式推导里的哪一式？

对应 [基线原理与优势函数公式推导](基线原理与优势函数公式推导.md) §2 的 (基线-梯度估计) 式：

$$
\nabla_{\theta} J(\theta) \approx \frac{1}{|\mathcal{B}|}\sum_{\tau\in\mathcal{B}}\Big[\sum_{t=0}^{T-1}\nabla_{\theta} \log\pi_{\theta}(A_{t} \mid S_{t})\Big]\cdot \big(G(\tau) - b\big)
\tag{基线-梯度估计}
$$

其中基线取的是**当前这批 8 条轨迹的回报均值**：

$$
b = \frac{1}{|\mathcal{B}|}\sum_{\tau\in\mathcal{B}} G(\tau) \tag{B-line: 批均值基线}
$$

### 5.3 为什么 `avg_reward` 可以当基线？—— 无偏性直觉

在 [基线原理与优势函数公式推导](基线原理与优势函数公式推导.md) §2 中证明了**任何只和 $\tau$ 无关（或仅与同一批轨迹统计量有关）的量 $b$ 都不会引入偏差**，本质是利用了 Softmax 梯度的零均值恒等式：

$$
\mathbb{E}_{\tau \sim P_{\theta}}\left[\Big(\sum_{t}\nabla \log\pi_{t}\Big)\cdot b\right] = b \cdot \nabla_{\theta}\sum_{a}\pi_{\theta}(a\mid s)\bigg|_{归一化=1} = 0
$$

所以把权重从 $G(\tau)$ 换成 $G(\tau)-b$，**期望不变**（依然指向真实的 $\nabla J(\theta)$），但**方差会被砍掉 $(G-b)^2 < G^2$ 的部分**——尤其是 CartPole 里所有 $G(\tau)$ 都 $\ge 0$，原始 $G^2$ 很大，减基线后一半轨迹权重正、一半负，平方和显著下降。

### 5.4 `(B-1)(B-2)` 在代码里的形状/数值流动（举个 batch=8 的数例）

假设某次 8 条轨迹的回报是：

| τ₁ | τ₂ | τ₃ | τ₄ | τ₅ | τ₆ | τ₇ | τ₈ |
|---|---|---|---|---|---|---|---|
| 30 | 45 | 50 | 22 | 60 | 38 | 41 | 54 |

那么：

$$
b = \text{avg\_reward} = \frac{30+45+50+22+60+38+41+54}{8} = \frac{340}{8} = 42.5
$$

每条轨迹的"优势权重"（这里是 $G(\tau)-b$，还不是严格 $A_t$，但直觉类似）：

| τ | $G(\tau)$ | $G(\tau) - b$ | 对 `obj` 的贡献方向 |
|---|---|---|---|
| 1 | 30 | **−12.5** | 这一局动作 `log_prob` 整体↓（相当于惩罚） |
| 2 | 45 | **+2.5**  | 轻微↑ |
| 3 | 50 | **+7.5**  | 明显↑ |
| 4 | 22 | **−20.5** | 强力惩罚（这 22 步就死的局最该被压低概率） |
| 5 | 60 | **+17.5** | 强力奖励 |
| 6 | 38 | **−4.5**  | 轻微惩罚 |
| 7 | 41 | **−1.5**  | 几乎不变 |
| 8 | 54 | **+11.5** | 明显奖励 |

**关键对比——朴素版 vs 基线版：**

| 版本 | τ₄ (G=22，最差局) 的权重 | 对差局的惩罚力度 |
|---|---|---|
| 朴素 REINFORCE | `obj = Σlogπ × 22` （**还是正数**！只是比别人"加得少"） | 间接：相对抑制 |
| 带基线 REINFORCE | `obj = Σlogπ × (−20.5)` （**直接负数**！） | 直接：显式压低差轨迹的动作概率 |

这就是为什么基线版通常**收敛更快、曲线抖动更小**——它不再是"大家一起涨，好的涨得多"，而是"好的涨、差的跌"，梯度信号更干净。

### 5.5 代码-公式位置对照表（基线版新增的两行）

| 代码位置 | 对应公式 |
|---|---|
| `avg_reward = sum(ep._return)/len(episodes)` | (B-line) 批均值基线 $b = \frac{1}{\|\mathcal{B}\|}\sum G(\tau)$ |
| `obj = sum(log_action_probs) * (ep._return − avg_reward)` | (基线-梯度估计) 里的"方括号 $\times (G(\tau)-b)$"，经 `loss.backward` 对 $\theta$ 求导后给出 $\nabla \log\pi_t \cdot (G(\tau)-b)$ |

### 5.6 这版基线的局限（为下一版 Actor-Critic 铺垫）

当前实现用的是"同一批 8 条轨迹的均值"当基线，优点是简单、不用额外网络，但仍有两个限制：

1. **不是状态依赖的基线**：对于 CartPole，所有 $s$ 共用同一个 $b$；而真正的最优基线应该是 $V_{\phi}(S_t)$（Critic 网络），每个状态有自己的基线值，方差缩减更彻底。
2. **还不是因果的**：仍然是整局 $G(\tau)$ 乘整条轨迹的 $\sum\log\pi_t$，还没拆成每个时刻独立的 $G_t$ 权重。

> 下一步就是把"批均值基线"升级为"状态价值 Critic + 因果 $G_t$"，即 **REINFORCE with baseline (Critic)**，它是通向 Actor-Critic / PPO 的最后一块拼图。
