from stable_baselines3 import PPO
from envs.server_management_env import ServerManagementEnv
from Classes import *

def train_model():
    givens = ProblemData()
    actual_demand = InputDemandDataActual(seed=42)
    print(actual_demand.demand_data_df.head())
    env = ServerManagementEnv(givens, actual_demand)
    model = PPO('MlpPolicy', env, verbose=1)
    model.learn(total_timesteps=100)
    model.save("server_management_rl_model")

if __name__ == "__main__":
    print("Training the model...")
    train_model()
