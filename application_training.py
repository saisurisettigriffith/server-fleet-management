from stable_baselines3 import PPO
from envs.server_management_env import ServerManagementEnv
from Classes import *

def train_model():
    givens = ProblemData()
    actual_demand = InputDemandDataActual(seed=42)
    env = ServerManagementEnv(givens, actual_demand)
    print(env)

    # Using a model to train
    model = PPO('MlpPolicy', env, verbose=1)

    obs = env.reset()
    print("Initial Observation:", obs)
    
    # Perform multiple steps
    for _ in range(100):  # Define the number of steps or use a more complex termination condition
        action = model.predict(obs, deterministic=True)[0]
        print(f"Predicted Action: {action}")
        obs, reward, done, info = env.step(action)
        print(f"Action: {action}, Observation: {obs}, Reward: {reward}, Done: {done}")

        if done:
            obs = env.reset()  # Reset the environment when a terminal state is reached

    model.save("server_management_rl_model")
    print("Training completed and model saved.")

if __name__ == "__main__":
    print("Training the model...")
    train_model()
