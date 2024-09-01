import gymnasium as gym
from gymnasium import spaces
import numpy as np
from Classes import Inventory

class ServerManagementEnv(gym.Env):
    def __init__(self, givens, demand_data):
        super().__init__()
        self.givens = givens
        self.demand_data = demand_data
        self.current_time_step = 1
        self.current_demand_rows = demand_data.demand_data_df[demand_data.demand_data_df['time_step'] == self.current_time_step]
        self.inventory = Inventory(givens)
        self.num_data_centers = len(self.inventory.datacenters)
        self.num_server_types = len(givens.servers_df['server_type'].unique())
        self.max_time_steps = 100
        
        self.action_space = spaces.MultiDiscrete([
            28,  # number of server types * data centers
            2    # maximum number of servers to buy
        ])
        self.observation_shape = 500  # example size, adjust as needed
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(self.observation_shape,), dtype=np.float64)

    def reset(self, **kwargs):
        self.current_time_step = 1
        self.current_demand_rows = self.demand_data.demand_data_df[self.demand_data.demand_data_df['time_step'] == self.current_time_step]
        self.state = self.initialize_environment_state()
        observation, info = self.convert_state_to_observation(self.state), {}
        #print(f"Reset observation (first 4 values): {observation[:4]}")
        return self.convert_state_to_observation(self.state), {}

    def step(self, action):
        print(f"Action received: {action}")
        # Ensure that the action is a valid index
        server_id, quantity = action
        if server_id >= len(self.givens.servers_df):
            print("Server ID out of range.. action:", action, " is greater than Length of servers_df:", len(self.givens.servers_df), "Reward: -100")
            reward = -100
            done = True
            truncated = False  # Adding the truncated return value here
            return np.full(self.observation_shape, -1.0, dtype=np.float32), reward, done, truncated, {"error": "Server ID out of range"}

        server_info = self.givens.servers_df.iloc[server_id]
        server_type = server_info['server_type']
        dc_id = np.random.choice(self.num_data_centers)

        release_times = server_info['release_time'].strip("[]").split(',')
        release_start, release_end = int(release_times[0]), int(release_times[1])

        # Check time constraints
        if not (release_start <= self.current_time_step <= release_end):
            print("Bad Timing.. action: ", action, "Current: ", self.current_time_step, "Release_start: ", release_start, "Release_end", release_end, "Reward: -50")
            reward = -50
            done = False
            truncated = False  # No early truncation of the episode
            return self.convert_state_to_observation(self.state), reward, done, truncated, {"error": "Server not available due to timing"}

        # Execute the purchase
        success = self.inventory.add_server(server_type, quantity, dc_id)
        reward = 100 if success else -10
        print("Success:", success, "Reward:", reward)
        self.current_time_step += 1
        done = self.current_time_step >= self.max_time_steps
        truncated = False  # No early truncation of the episode

        # Update the environment state
        self.state = self.update_state()
        observation = self.convert_state_to_observation(self.state)

        return observation, reward, done, truncated, {}  # Include truncated status and empty info dict if no additional info


    def initialize_environment_state(self):
        # Initialize or reset your environment's state
        state = {}
        for i, dc in enumerate(self.inventory.datacenters):
            state[f"DC{dc.identifier}_capacity"] = dc.empty_slots
        return state

    def update_state(self):
        # Update the state of the environment based on current conditions
        state = {}
        for i, dc in enumerate(self.inventory.datacenters):
            state[f"DC{dc.identifier}_capacity"] = dc.empty_slots
        return state

    def convert_state_to_observation(self, state):
        # Create an array of the proper shape with default values
        observation = np.full(self.observation_shape, -1.0, dtype=np.float32)

        # Populate the start of the array with state values
        state_values = np.array(list(state.values()), dtype=np.float32)
        observation[:len(state_values)] = state_values
        #observation shape:", observation.shape)  # Ensure it matches expected shape
        #print("Data type of observation:", observation.dtype)  # Should be float32
        return observation