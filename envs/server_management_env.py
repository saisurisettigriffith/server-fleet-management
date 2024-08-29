# import gymnasium as gym
# from gymnasium import spaces
# import numpy as np
# from Classes import *

# class ServerManagementEnv(gym.Env):
#     def __init__(self, givens, demand_data):
#         super().__init__()
#         self.givens = givens
#         self.current_time_step = 1
#         self.current_demand_rows = demand_data.demand_data_df[demand_data.demand_data_df['time_step'] == self.current_time_step]
#         self.inventory = Inventory(givens)
#         num_data_centers = len(self.inventory.datacenters) # e.g., DC1, DC2, DC3, DC4
#         num_server_types = len(self.givens.servers_df['server_type'].unique()) # e.g., CPU.S1, CPU.S2, CPU.S3, CPU.S4, GPU.S1, GPU.S2, GPU.S3
#         num_action_types = 3  # e.g., add, remove, move
#         max_quantity = 10  # Max units per action

#         self.action_space = spaces.MultiDiscrete([num_data_centers, num_server_types, num_action_types, max_quantity])
#         self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(10,), dtype=np.float32)
#         self.state = self.reset()

#     def map_numbers_to_action(self, action):
#         if action == 0:
#             return 'buy'
#         elif action == 1:
#             return 'hold'
#         elif action == 2:
#             return 'move'

#     def reset(self):
#         # Initialize the environment state at the start of each episode
#         self.state = self.initialize_environment_state()
#         return self.convert_state_to_observation(self.state)

#     def initialize_environment_state(self):
#         state = {}

#         # Initialization for each data center according to specified metrics
#         for i, dc in enumerate(self.inventory.datacenters):
#             dc_id = dc.identifier  # Identifiers like 'DC1', 'DC2', etc.
#             state[f"{dc_id}_TOTAL_SERVERS"] = 0
#             state[f"{dc_id}_OPERATIONAL_SERVERS"] = 0
#             state[f"{dc_id}_ENERGY_CONSUMPTION"] = 0.0
#             state[f"{dc_id}_AVAILABLE_SLOTS"] = dc.slots_capacity
#             state[f"{dc_id}_ENERGY_COST"] = dc.cost_of_energy
#             state[f"{dc_id}_UTILIZATION_RATE"] = 0.0

#             # Server type counts within this data center
#             for server_type in self.givens.servers_df['server_type'].unique():
#                 state[f"{dc_id}_COUNT_{server_type}"] = 0  # Initialize count for each server type

#         # System-wide aggregate metrics
#         state["SYSTEM_TOTAL_OPERATING_COST"] = 0.0
#         state["TOTAL_DEMAND_MET"] = 0
#         state["TOTAL_SERVERS_DEPLOYED"] = 0
#         state["TOTAL_CAPACITY_USED"] = 0

#         # Server lifecycle metrics focusing on the aging and utilization of servers
#         state["SERVERS_NEAR_EOL"] = 0  # Servers nearing end-of-life
#         state["SERVERS_MID_LIFE"] = 0  # Servers at mid-life stage
#         state["SERVERS_NEW"] = 0       # Recently deployed servers

#         # Detailed tracking of energy usage and server demand
#         state["TOTAL_ENERGY_COST"] = 0.0
#         state["TOTAL_ENERGY_CONSUMPTION"] = 0.0
#         state["TOTAL_FAILURES"] = 0
#         state["AVERAGE_LATENCY"] = 0.0
#         state["AVERAGE_OPERATIONAL_EFFICIENCY"] = 0.0

#         # Initialize demand-related metrics for each server type, adjusted by the demand data
#         for server_type in self.givens.servers_df['server_type'].unique():
#             state[f"DEMAND_{server_type}"] = 0  # Placeholder, to be updated dynamically with demand data

#         # Economic factors such as profitability calculations
#         state["REVENUE_FROM_DEPLOYMENT"] = 0.0
#         state["COST_OF_DEPLOYMENTS"] = 0.0
#         state["NET_PROFIT"] = 0.0

#         # Optional: Tracking specific server attributes could be useful for advanced metrics
#         for server_type in self.givens.servers_df['server_type'].unique():
#             for attr in ['capacity', 'life_expectancy', 'energy_consumption']:
#                 state[f"TOTAL_{attr.upper()}_{server_type}"] = 0

#         return state

#     def convert_state_to_observation(self, state):
#         # Convert the state dictionary to a numpy array for the observation
#         # This list should include all keys from the state dictionary that you consider relevant for the agent's decision-making process.
#         observation_keys = [
#             key for key in state.keys()  # This captures all keys dynamically
#         ]
#         return np.array([state[key] for key in observation_keys])


#     def step(self, action):
#         dc_id, server_type, action_type, quantity = action
#         data_center = self.inventory.datacenters[dc_id]
#         if action_type == 0:  # Buy
#             server_info = self.givens.servers_df[self.givens.servers_df['server_type'] == server_type].iloc[0]
#             slots_needed = server_info['slots_size'] * quantity
#             if data_center.empty_slots >= slots_needed:
#                 data_center.deploy_server(server_type, quantity)
#             else:
#                 print(f"Not enough slots to deploy {quantity} servers of type {server_type}.")
#                 reward = -1  # Penalize the attempt to buy without enough slots
#         elif action_type == 1:  # Move
#             self.inventory.move_server(dc_id, server_type, quantity)
#         elif action_type == 2:  # Remove
#             self.inventory.remove_server(dc_id, server_type, quantity)

#         self.state = self.update_state()
#         observation = self.convert_state_to_observation(self.state)
#         reward = self.calculate_reward()  # Update reward based on the action's success or failure
#         done = self._check_done()
#         info = {}

#         self.current_time_step += 1
#         self.current_demand_rows = self.demand_data.demand_data_df[self.demand_data.demand_data_df['time_step'] == self.current_time_step]

#         return observation, reward, done, info

#     def update_state(self):
#         # Simulate the passing of one time unit in the environment
#         for datacenter in self.inventory.datacenters:
#             datacenter.simulate_time_step()

#         # Reset or update the system-wide metrics
#         system_total_operating_cost = 0.0
#         total_demand_met = 0
#         total_servers_deployed = 0
#         total_capacity_used = 0
#         total_energy_cost = 0.0

#         # Iterate over each data center to update their respective metrics
#         for i, dc in enumerate(self.inventory.datacenters):
#             dc_id = dc.identifier
#             summary = dc.summary()

#             # Update data center specific metrics
#             self.state[f"{dc_id}_TOTAL_SERVERS"] = len(dc.servers)
#             self.state[f"{dc_id}_OPERATIONAL_SERVERS"] = sum(1 for s in dc.servers if s.deployed)
#             self.state[f"{dc_id}_ENERGY_CONSUMPTION"] = summary['energy_cost']
#             self.state[f"{dc_id}_AVAILABLE_SLOTS"] = dc.empty_slots
#             self.state[f"{dc_id}_UTILIZATION_RATE"] = summary['utilization_rate']

#             # Aggregate the system-wide metrics
#             system_total_operating_cost += summary['operational_cost']
#             total_capacity_used += summary['used_capacity']
#             total_energy_cost += summary['energy_cost']
#             total_servers_deployed += self.state[f"{dc_id}_OPERATIONAL_SERVERS"]
#             total_demand_met += summary['demand_met']  # Assuming you calculate this somewhere

#         # Update the system-wide state variables
#         self.state["SYSTEM_TOTAL_OPERATING_COST"] = system_total_operating_cost
#         self.state["TOTAL_DEMAND_MET"] = total_demand_met
#         self.state["TOTAL_SERVERS_DEPLOYED"] = total_servers_deployed
#         self.state["TOTAL_CAPACITY_USED"] = total_capacity_used
#         self.state["TOTAL_ENERGY_COST"] = total_energy_cost

#         # Calculate averages or other derived metrics
#         self.state["AVERAGE_LATENCY"] = np.random.random()  # Update with actual computation if available
#         self.state["AVERAGE_OPERATIONAL_EFFICIENCY"] = np.random.random()  # Update with actual computation if available

#         return self.state

#     def calculate_reward(self, state):
#         # Example reward calculations based on state variables
#         demand_met = state['demand_met']
#         capacity_used = state['capacity_used']
#         total_capacity = state['total_capacity']
        
#         reward = 0
#         reward += demand_met * 1  # Reward for each unit of demand met
#         reward -= (total_capacity - capacity_used) * 0.5  # Penalty for unused capacity
        
#         # Additional penalties or rewards can be added based on other factors
#         return reward


#     def _check_done(self):
#         # Determine whether the episode should end
#         return np.random.rand() > 0.95

import gymnasium as gym
from gymnasium import spaces
import numpy as np
from Classes import *

class ServerManagementEnv(gym.Env):
    def __init__(self, givens, demand_data):
        super().__init__()
        self.givens = givens
        self.current_time_step = 1
        self.current_demand_rows = demand_data.demand_data_df[demand_data.demand_data_df['time_step'] == self.current_time_step]
        self.inventory = Inventory(givens)
        num_data_centers = len(self.inventory.datacenters)
        num_server_types = len(givens.servers_df['server_type'].unique())
        num_action_types = 3  # Actions: add, remove, move
        max_quantity = 10  # Maximum units per action

        self.action_space = spaces.MultiDiscrete([num_data_centers, num_server_types, num_action_types, max_quantity])
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(24,), dtype=np.float32)
        self.state = self.reset()

    def map_numbers_to_action(self, action):
        if action == 0:
            return 'buy'
        elif action == 1:
            return 'hold'
        elif action == 2:
            return 'move'

    def reset(self):
        self.state = self.initialize_environment_state()
        return self.convert_state_to_observation(self.state)

    def initialize_environment_state(self):
        state = {}
        for i, dc in enumerate(self.inventory.datacenters):
            dc_id = dc.identifier
            state[f"{dc_id}_TOTAL_SERVERS"] = len(dc.servers)
            state[f"{dc_id}_OPERATIONAL_SERVERS"] = sum(1 for s in dc.servers if s.deployed)
            state[f"{dc_id}_ENERGY_CONSUMPTION"] = dc.get_total_energy_cost()
            state[f"{dc_id}_AVAILABLE_SLOTS"] = dc.empty_slots
            state[f"{dc_id}_ENERGY_COST"] = dc.cost_of_energy
            #state[f"{dc_id}_UTILIZATION_RATE"] = dc.utilization_rate()

        #state["SYSTEM_TOTAL_OPERATING_COST"] = sum(dc.get_total_operational_cost() for dc in self.inventory.datacenters)
        state["TOTAL_DEMAND_MET"] = 0  # Placeholder
        state["TOTAL_SERVERS_DEPLOYED"] = sum(state[f"{dc.identifier}_OPERATIONAL_SERVERS"] for dc in self.inventory.datacenters)
        #state["TOTAL_CAPACITY_USED"] = sum(dc.used_capacity() for dc in self.inventory.datacenters)
        state["TOTAL_ENERGY_COST"] = sum(dc.get_total_energy_cost() for dc in self.inventory.datacenters)

        # state["SERVERS_NEAR_EOL"] = sum(dc.servers_near_EOL() for dc in self.inventory.datacenters)
        # state["SERVERS_MID_LIFE"] = sum(dc.servers_mid_life() for dc in self.inventory.datacenters)
        # state["SERVERS_NEW"] = sum(dc.servers_new() for dc in self.inventory.datacenters)

            # state["TOTAL_ENERGY_CONSUMPTION"] = sum(dc.total_energy_consumption() for dc in self.inventory.datacenters)
            # state["TOTAL_FAILURES"] = sum(dc.total_failures() for dc in self.inventory.datacenters)
        state["TOTAL_COST_TILL_NOW"] = self.inventory.delta_purchase_cost + self.inventory.delta_moving_cost
        # state["AVERAGE_LATENCY"] = np.mean([dc.average_latency() for dc in self.inventory.datacenters if dc.servers])
        #state["AVERAGE_OPERATIONAL_EFFICIENCY"] = np.mean([dc.operational_efficiency() for dc in self.inventory.datacenters if dc.servers])

        # for server_type in self.givens.servers_df['server_type'].unique():
        #     state[f"DEMAND_{server_type}"] = self.current_demand_rows.get(server_type, 0)
        #     state[f"TOTAL_CAPACITY_{server_type}"] = sum(dc.capacity_for_type(server_type) for dc in self.inventory.datacenters)

        # state["REVENUE_FROM_DEPLOYMENT"] = sum(dc.revenue_from_deployment() for dc in self.inventory.datacenters)
        # state["COST_OF_DEPLOYMENTS"] = sum(dc.cost_of_deployments() for dc in self.inventory.datacenters)
        # state["NET_PROFIT"] = state["REVENUE_FROM_DEPLOYMENT"] - state["COST_OF_DEPLOYMENTS"]

        return state

    def convert_state_to_observation(self, state):
        return np.array([state[key] for key in sorted(state.keys())])

    def step(self, action):
        dc_id, server_type, action_type, quantity = action
        data_center = self.inventory.get_datacenter_by_id(dc_id)
        reward = 0
        '''
        def add_server(self, server, datacenter_id, moving=False):
        '''
        if action_type == 0:  # Buy
            if self.inventory.add_server(server_type, quantity, dc_id):
                print(f"Deployed {quantity} servers of type {server_type} in data center {dc_id}.")
            else:
                print(f"Not enough slots to deploy {quantity} servers of type {server_type}.")
                reward = -1
        elif action_type == 1:  # Move
            # Example: Moving from one data center to another is not handled here due to missing context
            print("Moving logic is not implemented.")
        elif action_type == 2:  # Remove
            '''
            def remove_server(self, server_id, datacenter_id):
            '''
            if self.inventory.remove_server(server_type, quantity, dc_id):
                print(f"Removed {quantity} servers of type {server_type} from data center {dc_id}.")
            else:
                print(f"Not enough servers of type {server_type} to remove {quantity} units.")
                reward = -1

        self.state = self.update_state()
        observation = self.convert_state_to_observation(self.state)
        reward += self.calculate_reward()  # Update reward based on the action's outcome
        done = self.check_done()

        self.current_time_step += 1
        self.current_demand_rows = self.demand_data.demand_data_df[self.demand_data.demand_data_df['time_step'] == self.current_time_step]

        return observation, reward, done, {}

    def update_state(self):
        for datacenter in self.inventory.datacenters:
            datacenter.update()
        return self.initialize_environment_state()

    def calculate_reward(self):
        # Example reward logic based on efficiency
        return np.random.random()

    def check_done(self):
        # Example termination condition
        return self.current_time_step > 100