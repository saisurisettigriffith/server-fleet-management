'''
(.venv) saisurisetti@SAIS-MBP server-fleet-management % /Users/saisurisetti/Projects/server-fleet-management/.venv/bin/python /Users/saisurisetti/Projects/server-fleet-management/application_training.py
Training the model...
IMPORTANT: The ProblemData Class should not be changed. It is used to load the data for the problem.
Columns and Head of ProblemData: datacenters_df: 
Index(['datacenter_id', 'cost_of_energy', 'latency_sensitivity',
       'slots_capacity'],
      dtype='object')
  datacenter_id  cost_of_energy latency_sensitivity  slots_capacity
0           DC1            0.25                 low           25245
1           DC2            0.35              medium           15300
2           DC3            0.65                high            7020
3           DC4            0.75                high            8280
Columns and Head of ProblemData: servers_df: 
Index(['server_generation', 'server_type', 'release_time', 'purchase_price',
       'slots_size', 'energy_consumption', 'capacity', 'life_expectancy',
       'cost_of_moving', 'average_maintenance_fee'],
      dtype='object')
  server_generation server_type release_time  purchase_price  slots_size  energy_consumption  capacity  life_expectancy  cost_of_moving  average_maintenance_fee
0            CPU.S1         CPU       [1,60]           15000           2                 400        60               96            1000                      288
1            CPU.S2         CPU      [37,96]           16000           2                 460        75               96            1000                      308
2            CPU.S3         CPU     [73,132]           19500           2                 800       120               96            1000                      375
3            CPU.S4         CPU    [109,168]           22000           2                 920       160               96            1000                      423
4            GPU.S1         GPU       [1,72]          120000           4                3000         8               96            1000                     2310
Columns and Head of ProblemData: selling_prices_df: 
Index(['server_generation', 'latency_sensitivity', 'selling_price'], dtype='object')
  server_generation latency_sensitivity  selling_price
0            CPU.S1                 low           10.0
1            CPU.S2                 low           10.0
2            CPU.S3                 low           11.0
3            CPU.S4                 low           12.0
4            GPU.S1                 low         1500.0
IMPORTANT: The ProblemData Class should not be changed. It is used to load the data for the problem.
IMPORTANT: The InputDemandDataActual AND YOUR ORIGINAL COPIES should not be changed BECAUSE THE AGENT NEEDS TO BE TRAINED ON THE ORIGINAL INPUT FORMAT HOW THEY APPEAR.
Columns and Head of Hackathon Input Format demand data: 
Index(['time_step', 'server_generation', 'high', 'low', 'medium'], dtype='object', name='latency_sensitivity')
latency_sensitivity  time_step server_generation   high    low  medium
0                            1            CPU.S1   6230  19865    7220
1                            1            GPU.S1     35     19       1
2                            2            CPU.S1  12584  37035   14514
3                            2            GPU.S1     69     38       4
4                            3            CPU.S1  17781  54178   16664
IMPORTANT: The InputDemandDataActual AND YOUR ORIGINAL COPIES should not be changed BECAUSE THE AGENT NEEDS TO BE TRAINED ON THE ORIGINAL INPUT FORMAT HOW THEY APPEAR.
'''

# import gymnasium as gym
# from gymnasium import spaces
# import numpy as np
# from Classes import *

# class ServerManagementEnv(gym.Env):
#     def __init__(self, givens, demand_data):
#         super().__init__()
#         self.givens = givens
#         self.demand_data = demand_data.demand_data_df
#         self.inventory = Inventory(givens)

#         num_data_centers = len(self.inventory.datacenters)
#         num_server_types = len(self.givens.servers_df['server_type'].unique())
#         num_action_types = 3  # e.g., add, remove, move
#         max_quantity = 10  # Max units per action

#         self.action_space = spaces.MultiDiscrete([num_data_centers, num_server_types, num_action_types, max_quantity])
#         self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(10,), dtype=np.float32)
#         self.state = self.reset()

#     def reset(self, **kwargs):
#         self.state = self.initialize_environment_state()
#         return self.convert_state_to_observation(self.state)

#     def convert_state_to_observation(self, state):
#         return np.array([
#             state['feature1'],
#             state['feature2'],
#             # Ensure all dummy features are included to match the expected shape
#             np.random.random(), np.random.random(), np.random.random(),
#             np.random.random(), np.random.random(), np.random.random(),
#             np.random.random(), np.random.random()
#         ])

#     def step(self, action):
#         self._apply_action(action)
#         self.state = self.update_state()
#         observation = self.convert_state_to_observation(self.state)
#         reward = self.calculate_reward()
#         done = self._check_done()
#         info = {}
#         return observation, reward, done, info


#     def _apply_action(self, action):
#         dc_id, server_type, action_type, quantity = action
#         if action_type == 0:
#             self.inventory.datacenters[dc_id].deploy_server(server_type, quantity)
#         elif action_type == 1:
#             self.inventory.datacenters[dc_id].power_down_server(server_type, quantity)

#     def update_state(self):
#         return {"feature1": np.random.rand(), "feature2": np.random.rand()}

#     def calculate_reward(self):
#         return -np.random.rand()

#     def _check_done(self):
#         return np.random.rand() > 0.95

import gymnasium as gym
from gymnasium import spaces
import numpy as np
from Classes import *

class ServerManagementEnv(gym.Env):
    def __init__(self, givens, demand_data):
        super().__init__()
        self.givens = givens
        self.demand_data = demand_data.demand_data_df
        self.inventory = Inventory(givens)

        num_data_centers = len(self.inventory.datacenters)
        num_server_types = len(self.givens.servers_df['server_type'].unique())
        num_action_types = 3  # e.g., add, remove, move
        max_quantity = 10  # Max units per action

        self.action_space = spaces.MultiDiscrete([num_data_centers, num_server_types, num_action_types, max_quantity])
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(10,), dtype=np.float32)
        self.state = self.reset()

    def reset(self):
        # Initialize the environment state at the start of each episode
        self.state = self.initialize_environment_state()
        return self.convert_state_to_observation(self.state)

    def initialize_environment_state(self):
        # Setup initial state of the environment
        state = {
            "feature1": 0,
            "feature2": 0,
            # Initialize other features as needed
            "feature3": 0,
            "feature4": 0,
            "feature5": 0,
            "feature6": 0,
            "feature7": 0,
            "feature8": 0,
            "feature9": 0,
            "feature10": 0,
        }
        return state

    def convert_state_to_observation(self, state):
        # Convert the state dictionary to a numpy array for the observation
        return np.array([
            state['feature1'],
            state['feature2'],
            state['feature3'],
            state['feature4'],
            state['feature5'],
            state['feature6'],
            state['feature7'],
            state['feature8'],
            state['feature9'],
            state['feature10']
        ])

    def step(self, action):
        # Apply the action and update the environment
        self._apply_action(action)
        self.state = self.update_state()
        observation = self.convert_state_to_observation(self.state)
        reward = self.calculate_reward()
        done = self._check_done()
        info = {}
        return observation, reward, done, info

    def _apply_action(self, action):
        # Detailed logic to apply an action to modify the environment
        dc_id, server_type, action_type, quantity = action
        if action_type == 0:
            self.inventory.datacenters[dc_id].deploy_server(server_type, quantity)
        elif action_type == 1:
            self.inventory.datacenters[dc_id].power_down_server(server_type, quantity)

    def update_state(self):
        # Simulate the passing of one time unit in the environment
        for datacenter in self.inventory.datacenters:
            datacenter.simulate_time_step()

        # Assume the state features include total capacity, energy costs, and other operational metrics
        total_capacity_used = sum(dc.summary()['available_capacity'] for dc in self.inventory.datacenters)
        total_energy_cost = sum(dc.summary()['energy_cost'] for dc in self.inventory.datacenters)
        total_servers_deployed = sum(len(dc.servers) for dc in self.inventory.datacenters)

        # Example of more complex features that might be tracked
        average_latency = np.random.random()  # Placeholder for actual calculation
        operational_efficiency = np.random.random()  # Placeholder for actual calculation

        # Update state dictionary
        self.state = {
            "feature1": total_capacity_used,
            "feature2": total_energy_cost,
            "feature3": total_servers_deployed,
            "feature4": average_latency,
            "feature5": operational_efficiency,
            # Add more features based on other dynamics you might be simulating
            "feature6": np.random.rand(),  # Example of additional random feature for variation
            "feature7": np.random.rand(),
            "feature8": np.random.rand(),
            "feature9": np.random.rand(),
            "feature10": np.random.rand()
        }

        return self.state


    def calculate_reward(self):
        # Calculate and return the reward
        return -np.random.rand()

    def _check_done(self):
        # Determine whether the episode should end
        return np.random.rand() > 0.95
