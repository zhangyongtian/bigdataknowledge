import os
import random
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from collections import deque, namedtuple
import gymnasium as gym
import matplotlib.pyplot as plt

Transition = namedtuple('Transition', ('state', 'action', 'reward', 'next_state', 'done'))


class ReplayBuffer:
    def __init__(self, capacity: int):
        self.buffer = deque(maxlen=capacity)

    def push(self, *args):
        self.buffer.append(Transition(*args))

    def sample(self, batch_size: int):
        batch = random.sample(self.buffer, batch_size)
        return Transition(*zip(*batch))

    def __len__(self) -> int:
        return len(self.buffer)


class QNetwork(nn.Module):
    def __init__(self, state_dim: int, action_dim: int, hidden_dim: int = 128):
        super(QNetwork, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, action_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class DQNAgent:
    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        hidden_dim: int = 128,
        lr: float = 1e-3,
        gamma: float = 0.99,
        epsilon_start: float = 1.0,
        epsilon_end: float = 0.01,
        epsilon_decay: float = 500,
        target_update: int = 100,
        buffer_capacity: int = 10000,
        batch_size: int = 64,
        device: str = 'auto',
    ):
        if device == 'auto':
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = torch.device(device)

        self.state_dim = state_dim
        self.action_dim = action_dim
        self.gamma = gamma
        self.epsilon_start = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.target_update = target_update
        self.batch_size = batch_size

        self.policy_net = QNetwork(state_dim, action_dim, hidden_dim).to(self.device)
        self.target_net = QNetwork(state_dim, action_dim, hidden_dim).to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()

        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=lr)
        self.buffer = ReplayBuffer(buffer_capacity)
        self.criterion = nn.SmoothL1Loss()
        self.total_steps = 0

    def epsilon(self) -> float:
        return self.epsilon_end + (self.epsilon_start - self.epsilon_end) * \
            np.exp(-1.0 * self.total_steps / self.epsilon_decay)

    def select_action(self, state: np.ndarray, train: bool = True) -> int:
        if train and random.random() < self.epsilon():
            return random.randint(0, self.action_dim - 1)
        with torch.no_grad():
            s = torch.tensor(state, dtype=torch.float32, device=self.device).unsqueeze(0)
            q_values = self.policy_net(s)
            return int(q_values.argmax(dim=1).item())

    def store_transition(self, state, action, reward, next_state, done):
        self.buffer.push(
            torch.tensor(state, dtype=torch.float32),
            torch.tensor(action, dtype=torch.long),
            torch.tensor(reward, dtype=torch.float32),
            torch.tensor(next_state, dtype=torch.float32),
            torch.tensor(done, dtype=torch.float32),
        )

    def optimize_model(self) -> float:
        if len(self.buffer) < self.batch_size:
            return 0.0

        batch = self.buffer.sample(self.batch_size)

        state_batch = torch.stack(batch.state).to(self.device)
        action_batch = torch.stack(batch.action).to(self.device).unsqueeze(1)
        reward_batch = torch.stack(batch.reward).to(self.device)
        next_state_batch = torch.stack(batch.next_state).to(self.device)
        done_batch = torch.stack(batch.done).to(self.device)

        current_q = self.policy_net(state_batch).gather(1, action_batch).squeeze(1)

        with torch.no_grad():
            next_q_max = self.target_net(next_state_batch).max(dim=1)[0]
            target_q = reward_batch + self.gamma * next_q_max * (1.0 - done_batch)

        loss = self.criterion(current_q, target_q)

        self.optimizer.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(self.policy_net.parameters(), max_norm=1.0)
        self.optimizer.step()

        self.total_steps += 1
        if self.total_steps % self.target_update == 0:
            self.target_net.load_state_dict(self.policy_net.state_dict())

        return float(loss.item())

    def save(self, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        torch.save({
            'policy_net': self.policy_net.state_dict(),
            'target_net': self.target_net.state_dict(),
            'optimizer': self.optimizer.state_dict(),
            'total_steps': self.total_steps,
        }, path)

    def load(self, path: str):
        checkpoint = torch.load(path, map_location=self.device)
        self.policy_net.load_state_dict(checkpoint['policy_net'])
        self.target_net.load_state_dict(checkpoint['target_net'])
        self.optimizer.load_state_dict(checkpoint['optimizer'])
        self.total_steps = checkpoint['total_steps']


def train_cartpole(
    env_name: str = 'CartPole-v1',
    max_episodes: int = 500,
    max_steps: int = 500,
    seed: int = 42,
    solve_threshold: float = 475.0,
    solve_window: int = 100,
    save_path: str = 'checkpoints/cartpole_dqn.pth',
    render_during_train: bool = False,
):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    render_mode = 'human' if render_during_train else None
    env = gym.make(env_name, render_mode=render_mode)
    state_dim = env.observation_space.shape[0]
    action_dim = env.action_space.n

    agent = DQNAgent(
        state_dim=state_dim,
        action_dim=action_dim,
        hidden_dim=128,
        lr=1e-3,
        gamma=0.99,
        epsilon_start=1.0,
        epsilon_end=0.01,
        epsilon_decay=1000,
        target_update=100,
        buffer_capacity=10000,
        batch_size=64,
    )

    episode_rewards = []
    avg_rewards = []
    losses = []
    solved = False

    print(f'Start training on {env_name} | device={agent.device}')
    print(f'State dim: {state_dim}, Action dim: {action_dim}')
    print('=' * 60)

    for episode in range(1, max_episodes + 1):
        state, _ = env.reset(seed=seed + episode)
        episode_reward = 0.0
        episode_loss = 0.0

        for step in range(max_steps):
            action = agent.select_action(state, train=True)
            next_state, reward, terminated, truncated, _ = env.step(action)
            done = terminated or truncated
            agent.store_transition(state, action, reward, next_state, done)
            loss = agent.optimize_model()
            episode_loss += loss
            episode_reward += reward
            state = next_state
            if done:
                break

        episode_rewards.append(episode_reward)
        losses.append(episode_loss / max(step + 1, 1))
        window = min(solve_window, len(episode_rewards))
        avg_reward = np.mean(episode_rewards[-window:])
        avg_rewards.append(avg_reward)

        if episode % 10 == 0:
            print(
                f'Episode {episode:4d} | Reward: {episode_reward:6.1f} | '
                f'Avg{window}: {avg_reward:6.1f} | Epsilon: {agent.epsilon():.3f} | '
                f'Loss: {episode_loss:.4f}'
            )

        if avg_reward >= solve_threshold and len(episode_rewards) >= solve_window:
            print(f'\nEnvironment solved in {episode} episodes! Avg reward over last {solve_window}: {avg_reward:.2f}')
            solved = True
            agent.save(save_path)
            print(f'Model saved to {save_path}')
            break

    if not solved:
        agent.save(save_path)
        print(f'\nTraining finished after {max_episodes} episodes. Model saved to {save_path}')

    env.close()

    plt.figure(figsize=(10, 5))
    plt.subplot(1, 2, 1)
    plt.plot(episode_rewards, label='Episode Reward', alpha=0.6)
    plt.plot(avg_rewards, label=f'Avg Reward (window={solve_window})', linewidth=2)
    plt.axhline(solve_threshold, color='r', linestyle='--', label=f'Threshold ({solve_threshold})')
    plt.xlabel('Episode')
    plt.ylabel('Reward')
    plt.title('Training Reward')
    plt.legend()
    plt.grid(True, alpha=0.3)

    plt.subplot(1, 2, 2)
    plt.plot(losses, label='Loss', alpha=0.6)
    plt.xlabel('Episode')
    plt.ylabel('Loss')
    plt.title('Training Loss')
    plt.legend()
    plt.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('cartpole_training_curve.png', dpi=150)
    print('Training curve saved to cartpole_training_curve.png')
    plt.close()

    return agent, episode_rewards, avg_rewards


def evaluate_agent(
    env_name: str = 'CartPole-v1',
    model_path: str = 'checkpoints/cartpole_dqn.pth',
    episodes: int = 10,
    max_steps: int = 500,
    seed: int = 0,
    render: bool = True,
):
    render_mode = 'human' if render else None
    env = gym.make(env_name, render_mode=render_mode)
    state_dim = env.observation_space.shape[0]
    action_dim = env.action_space.n

    agent = DQNAgent(state_dim=state_dim, action_dim=action_dim)
    agent.load(model_path)

    rewards = []
    for ep in range(episodes):
        state, _ = env.reset(seed=seed + ep)
        total_reward = 0.0
        for step in range(max_steps):
            action = agent.select_action(state, train=False)
            next_state, reward, terminated, truncated, _ = env.step(action)
            total_reward += reward
            state = next_state
            if terminated or truncated:
                break
        rewards.append(total_reward)
        print(f'Evaluate Episode {ep+1:2d} | Reward: {total_reward:.1f}')

    env.close()
    avg = np.mean(rewards)
    std = np.std(rewards)
    print(f'\nEvaluation over {episodes} episodes: Mean={avg:.2f}, Std={std:.2f}')
    return rewards


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='DQN for CartPole')
    parser.add_argument('--mode', type=str, default='train', choices=['train', 'eval', 'both'])
    parser.add_argument('--episodes', type=int, default=500, help='Max training episodes')
    parser.add_argument('--eval-episodes', type=int, default=10, help='Evaluation episodes')
    parser.add_argument('--model', type=str, default='checkpoints/cartpole_dqn.pth', help='Model path')
    parser.add_argument('--render', action='store_true', help='Render during eval')
    parser.add_argument('--no-render-train', action='store_true', help='Do not render during training')
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()

    if args.mode in ('train', 'both'):
        train_cartpole(
            max_episodes=args.episodes,
            save_path=args.model,
            seed=args.seed,
            render_during_train=not args.no_render_train,
        )

    if args.mode in ('eval', 'both'):
        evaluate_agent(
            model_path=args.model,
            episodes=args.eval_episodes,
            seed=args.seed,
            render=args.render,
        )
