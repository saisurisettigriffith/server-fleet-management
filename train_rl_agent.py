import gym
from stable_baselines3 import PPO
from envs.server_management_env import ServerManagementEnv

# Assuming you have already defined or loaded `givens` and `demand_data`
from your_data_module import givens, demand_data  # Adjust import based on your actual data structure

# Create the custom environment
env = ServerManagementEnv(givens, demand_data)

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
for _ in range(1000):  # Run for 1000 steps or as needed
    action, _states = model.predict(obs)
    obs, rewards, done, info = env.step(action)
    if done:
        obs = env.reset()