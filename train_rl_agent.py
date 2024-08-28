import gymnasium as gym
from stable_baselines3 import PPO
from envs.server_management_env import ServerManagementEnv

# Assuming you have already defined or loaded `givens` and `demand_data`
from Classes import *
from application import *
from mysolution import *

# Create the custom environment
env = ServerManagementEnv(givens, actual_demand)

# Create the RL model
model = PPO('MlpPolicy', env, verbose=1)

# Train the model
model.learn(total_timesteps=10000)  # Adjust timesteps as needed

# Save the model
model.save("server_management_rl_model")

# Load the trained model
model = PPO.load("server_management_rl_model")

# Evaluate the model
obs = env.reset()
for _ in range(1000):  # Run for a number of steps to evaluate performance
    action, _states = model.predict(obs, deterministic=True)
    obs, rewards, done, info = env.step(action)
    if done:
        obs = env.reset()