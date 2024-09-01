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
        return self.convert_state_to_observation(self.state), {}

    def step(self, action):
        server_id, quantity = action

        # Ensure the server ID is within the range of available servers.
        if server_id >= len(self.givens.servers_df):
            reward = -100
            done = True
            return self.state, reward, done, {"error": "Server ID out of range"}

        server_info = self.givens.servers_df.iloc[server_id]
        print(server_info.columns)
        server_type = server_info['type']
        print(server_type.columns)
        dc_id = server_info['dc_id']

        # Check if the action is feasible with the current inventory and time constraints
        if self.current_time_step < server_info['release_start'] or self.current_time_step > server_info['release_end']:
            reward = -50
            done = False
            return self.state, reward, done, {"error": "Server not available for purchase due to release time constraints"}

        # Process buying servers
        success = self.inventory.add_server(server_type, quantity, dc_id)
        reward = 100 if success else -10

        self.current_time_step += 1
        done = self.current_time_step >= self.max_time_steps

        self.state = self.update_state()
        observation = self.convert_state_to_observation(self.state)
        return observation, reward, False, done, {}


    # def step(self, action):
    #     server_id, quantity = action
    #     server_info = self.givens.servers_df.iloc[server_id]
    #     print(server_info)
    #     server_type = server_info['type']
    #     dc_id = server_info['dc_id']

    #     reward = 0
    #     done = False

    #     # Check if server can be bought at this timestep
    #     if self.current_time_step in range(server_info['available_from'], server_info['available_until'] + 1):
    #         # Proceed with buying servers
    #         success = self.inventory.buy_server(server_type, dc_id, quantity)
    #         reward = 100 if success else -10  # Example reward logic
    #     else:
    #         reward = -50  # Penalty for attempting to buy out of allowed time

    #     self.current_time_step += 1
    #     if self.current_time_step > self.max_time_steps:
    #         done = True

    #     self.current_demand_rows = self.demand_data.demand_data_df[self.demand_data.demand_data_df['time_step'] == self.current_time_step]
    #     self.state = self.update_state()

    #     return self.convert_state_to_observation(self.state), reward, done, {}

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
        # Convert the state dictionary into a structured numpy array
        observation = np.zeros(self.observation_shape)
        for i, key in enumerate(sorted(state.keys())):
            observation[i] = state[key]
        return observation

# Additional classes and methods such as Inventory, DataCenter should handle specifics of managing servers and data centers
