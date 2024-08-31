from stable_baselines3 import PPO
from envs.server_management_env import ServerManagementEnv
from stable_baselines3.common.vec_env import DummyVecEnv
from Classes import *
import os 

def train_model(seed = 144):
    givens = ProblemData()
    actual_demand = InputDemandDataActual(seed)
    env = DummyVecEnv([lambda: ServerManagementEnv(givens, actual_demand)])

    model_path = "server_management_rl_model.zip"
    if os.path.exists(model_path):
        model = PPO.load(model_path, env=env)
        print("Model loaded from saved state.")
    else:
        model = PPO('MlpPolicy', env, verbose=1)
        print("Training new model.")

    obs = env.reset()
    step_count = 0
    for _ in range(30):  # Define the number of steps or use a more complex termination condition
        action = model.predict(obs, deterministic=False)[0]
        print(f"Action: {action}")
        obs, reward, dones, info = env.step(action)
        step_count += 1
        #print(f"Step {step_count}: Reward={reward}, Done={dones}")
        if dones[0]:
            obs = env.reset()  # Reset the environment when a terminal state is reached

    model.save("server_management_rl_model")
    print("Training completed and model saved.")

if __name__ == "__main__":
    print("Training the model...")
    i = 0
    while (i < 10):
        train_model(18)
        i += 1