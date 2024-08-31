import gymnasium as gym
from gymnasium import spaces
import numpy as np
from Classes import *

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
        # Hardcoded release times based on the provided CSV

        # Define your action and observation spaces based on these attributes
        max_quantity = 10
        self.action_space = spaces.MultiDiscrete([
            4,  # action type: buy, dismiss, move, hold
            self.num_server_types * self.num_data_centers,  # "magic code" for each server type at each DC - BUY
            max_quantity, # How Many to buy
            self.num_server_types * self.num_data_centers,  # "magic code" for each server type at each DC - DISMISS
            max_quantity, # How Many to dismiss
            self.num_data_centers * self.num_server_types,  # "magic code" for each server type at each DC - MOVE.Source
            4,  # "magic code" for each server type at each DC - MOVE.Target
            max_quantity, # How Many to move
        ])
        self.observation_shape = 55  # Set this to the expected max size
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(self.observation_shape,), dtype=np.float64)
        self.state = self.reset()

    def get_observation_space_size(self):
        # Modify this method to reflect the size of your observation space
        num_state_variables = 5 * self.num_data_centers + 2  # Adjust for the number of state variables you are using
        return num_state_variables + 2 + 8

    def reset(self):
        self.state = self.initialize_environment_state()
        return self.convert_state_to_observation(self.state)

    def initialize_environment_state(self):
        state = {}
        total_profit = 0
        total_utilization = 0

        server_generation_map = {
            "CPU.S1": 1,
            "CPU.S2": 2,
            "CPU.S3": 3,
            "CPU.S4": 4,
            "GPU.S1": 5,
            "GPU.S2": 6,
            "GPU.S3": 7,
            "GPU.S4": 8
        }

        server_dataceneter_map = {
            1: {"Type": "CPU", "Generation": "1", "DC": 1}, 2: {"Type": "CPU", "Generation": "2", "DC": 1}, 3: {"Type": "CPU", "Generation": "3", "DC": 1}, 4: {"Type": "CPU", "Generation": "4", "DC": 1}, 5: {"Type": "GPU", "Generation": "1", "DC": 1}, 6: {"Type": "GPU", "Generation": "2", "DC": 1}, 7: {"Type": "GPU", "Generation": "3", "DC": 1},
            8: {"Type": "CPU", "Generation": "1", "DC": 2}, 9: {"Type": "CPU", "Generation": "2", "DC": 2}, 10: {"Type": "CPU", "Generation": "3", "DC": 2}, 11: {"Type": "CPU", "Generation": "4", "DC": 2}, 12: {"Type": "GPU", "Generation": "1", "DC": 2}, 13: {"Type": "GPU", "Generation": "2", "DC": 2}, 14: {"Type": "GPU", "Generation": "3", "DC": 2},
            15: {"Type": "CPU", "Generation": "1", "DC": 3}, 16: {"Type": "CPU", "Generation": "2", "DC": 3}, 17: {"Type": "CPU", "Generation": "3", "DC": 3}, 18: {"Type": "CPU", "Generation": "4", "DC": 3}, 19: {"Type": "GPU", "Generation": "1", "DC": 3}, 20: {"Type": "GPU", "Generation": "2", "DC": 3}, 21: {"Type": "GPU", "Generation": "3", "DC": 3},
            22: {"Type": "CPU", "Generation": "1", "DC": 4}, 23: {"Type": "CPU", "Generation": "2", "DC": 4}, 24: {"Type": "CPU", "Generation": "3", "DC": 4}, 25: {"Type": "CPU", "Generation": "4", "DC": 4}, 26: {"Type": "GPU", "Generation": "1", "DC": 4}, 27: {"Type": "GPU", "Generation": "2", "DC": 4}, 28: {"Type": "GPU", "Generation": "3", "DC": 4}
        }

        for i, dc in enumerate(self.inventory.datacenters):
            dc_id = dc.identifier
            state[f"{dc_id}_TOTAL_SERVERS"] = len(dc.servers)
            state[f"{dc_id}_OPERATIONAL_SERVERS"] = sum(1 for s in dc.servers if s.deployed)
            state[f"{dc_id}_ENERGY_CONSUMPTION"] = dc.get_total_energy_cost()
            state[f"{dc_id}_AVAILABLE_SLOTS"] = dc.empty_slots
            state[f"{dc_id}_UTILIZATION"] = dc.calculate_utilization()
            total_utilization += dc.calculate_utilization()

        # Add demand data to the state with numerical encoding for server generation
        for idx, row in self.current_demand_rows.iterrows():
            server_generation = row['server_generation']
            state[f"INPUT_DEMAND_high_{server_generation}"] = row['high']
            state[f"INPUT_DEMAND_low_{server_generation}"] = row['low']
            state[f"INPUT_DEMAND_medium_{server_generation}"] = row['medium']
            # Convert server generation to its mapped numerical value
            state[f"INPUT_DEMAND_CHIP_{server_generation}"] = server_generation_map[server_generation]

        #total_costs = self.inventory.expenses.get_total_expenses()
        #total_revenue = sum(s.selling_price for dc in self.inventory.datacenters for s in dc.servers if s.deployed)
        #total_profit = total_revenue - total_costs
        #state["TOTAL_REVENUE"] = total_revenue
        #state["TOTAL_COSTS"] = total_costs
        state["/\ TOTAL_PROFIT"] = self.calculate_profit()
        state["/\ TOTAL_UTILIZATION"] = total_utilization / self.num_data_centers if self.num_data_centers > 0 else 0

        return state

    def convert_state_to_observation(self, state):
        observation = np.zeros(self.observation_shape)  # Start with an array of zeros of fixed size
        state_keys = sorted(state.keys())
        state_values = np.array([state[key] for key in state_keys])
        
        observation[:len(state_values)] = state_values  # Fill in the observation with the state values
        
        # Print observation keys and values
        print("Observation Keys and Values:")
        for key, value in zip(state_keys, observation):
            print(f"{key}: {value}")
        
        return observation
    
    def step(self, action):
        total_action_array_elements = 23

        # Define mappings
        server_generation_map = {
            "CPU.S1": 1,
            "CPU.S2": 2,
            "CPU.S3": 3,
            "CPU.S4": 4,
            "GPU.S1": 5,
            "GPU.S2": 6,
            "GPU.S3": 7,
            "GPU.S4": 8
        }

        server_datacenter_map = {
            1: {"Type": "CPU", "Generation": "1", "DC": 1}, 2: {"Type": "CPU", "Generation": "2", "DC": 1}, 3: {"Type": "CPU", "Generation": "3", "DC": 1}, 4: {"Type": "CPU", "Generation": "4", "DC": 1}, 5: {"Type": "GPU", "Generation": "1", "DC": 1}, 6: {"Type": "GPU", "Generation": "2", "DC": 1}, 7: {"Type": "GPU", "Generation": "3", "DC": 1},
            8: {"Type": "CPU", "Generation": "1", "DC": 2}, 9: {"Type": "CPU", "Generation": "2", "DC": 2}, 10: {"Type": "CPU", "Generation": "3", "DC": 2}, 11: {"Type": "CPU", "Generation": "4", "DC": 2}, 12: {"Type": "GPU", "Generation": "1", "DC": 2}, 13: {"Type": "GPU", "Generation": "2", "DC": 2}, 14: {"Type": "GPU", "Generation": "3", "DC": 2},
            15: {"Type": "CPU", "Generation": "1", "DC": 3}, 16: {"Type": "CPU", "Generation": "2", "DC": 3}, 17: {"Type": "CPU", "Generation": "3", "DC": 3}, 18: {"Type": "CPU", "Generation": "4", "DC": 3}, 19: {"Type": "GPU", "Generation": "1", "DC": 3}, 20: {"Type": "GPU", "Generation": "2", "DC": 3}, 21: {"Type": "GPU", "Generation": "3", "DC": 3},
            22: {"Type": "CPU", "Generation": "1", "DC": 4}, 23: {"Type": "CPU", "Generation": "2", "DC": 4}, 24: {"Type": "CPU", "Generation": "3", "DC": 4}, 25: {"Type": "CPU", "Generation": "4", "DC": 4}, 26: {"Type": "GPU", "Generation": "1", "DC": 4}, 27: {"Type": "GPU", "Generation": "2", "DC": 4}, 28: {"Type": "GPU", "Generation": "3", "DC": 4}
        }

        action_map = {
            0: "BUY",
            1: "DISMISS",
            2: "MOVE",
            3: "HOLD"
        }

        release_times_start = {
            'CPU.S1': 1,
            'CPU.S2': 37,
            'CPU.S3': 73,
            'CPU.S4': 109,
            'GPU.S1': 1,
            'GPU.S2': 49,
            'GPU.S3': 97
        }

        release_times_end = {
            'CPU.S1': 60,
            'CPU.S2': 96,
            'CPU.S3': 132,
            'CPU.S4': 168,
            'GPU.S1': 72,
            'GPU.S2': 120,
            'GPU.S3': 168
        }

        # Start processing the action
        print("Step function in ServerManagementEnv called")
        action_type = action_map[action[0]]
        print("Action type:", action_type)
        reward = 0

        # Parse the action array based on the structure defined in the action space
        buy_action_code = action[1]
        buy_action_code += 1
        buy_quantity = action[2]
        dismiss_action_code = action[3]
        dismiss_action_code += 1
        dismiss_quantity = action[4]
        move_source_code = action[5]
        move_source_code += 1
        move_target_code = action[6]
        move_target_code += 1
        move_quantity = action[7]

        # Get details from the server_dataceneter_map
        buy_action_details = server_datacenter_map[buy_action_code]
        dismiss_action_details = server_datacenter_map[dismiss_action_code]
        move_source_details = server_datacenter_map[move_source_code]
        move_target_details = move_target_code + 1

        # Print action keys and values
        print("Action Keys and Values:")
        print(f"Action Type: {action_type}")
        print(f"Buy Action Code: {buy_action_code} == (Server Type: {buy_action_details['Type']}, Generation: {buy_action_details['Generation']}, DC: {buy_action_details['DC']})")
        print(f"Buy Quantity: {buy_quantity}")
        print(f"Dismiss Action Code: {dismiss_action_code} == (Server Type: {dismiss_action_details['Type']}, Generation: {dismiss_action_details['Generation']}, DC: {dismiss_action_details['DC']})")
        print(f"Dismiss Quantity: {dismiss_quantity}")
        print(f"Move Source Code: {move_source_code} == (Server Type: {move_source_details['Type']}, Generation: {move_source_details['Generation']}, DC: {move_source_details['DC']})")
        print(f"Move Target Code: {move_target_code} == (Data Center: {move_target_details})")
        print(f"Move Quantity: {move_quantity}")

        print("DONEEE")

        # Logic for each action type
        if action_type == "BUY":
            server_type = f"{buy_action_details['Type']}.S{buy_action_details['Generation']}"
            dc_identifier = f"DC{buy_action_details['DC']}"

            # Check release time constraints
            release_start = release_times_start[server_type]
            release_end = release_times_end[server_type]
            if release_start <= self.current_time_step <= release_end:
                success = self.inventory.add_server(server_type, buy_quantity, dc_identifier)
                if success:
                    reward += self.calculate_profit()  # Assuming this method calculates the profit
                else:
                    reward -= 1
            else:
                print(f"Server type {server_type} is not available for purchase at time step {self.current_time_step}.")
                reward -= 1

        elif action_type == "DISMISS":
            reward -= 99999
            server_type = f"{dismiss_action_details['Type']}.S{dismiss_action_details['Generation']}"
            dc_identifier = f"DC{dismiss_action_details['DC']}"

            success = self.inventory.remove_server(server_type, dismiss_quantity, dc_identifier)
            if success:
                reward += self.calculate_reward()  # Assuming this method calculates the reward for successful action
            else:
                reward -= 1

        elif action_type == "MOVE":
            reward -= 99999
            source_server_type = f"{move_source_details['Type']}.S{move_source_details['Generation']}"
            source_dc_identifier = f"DC{move_source_details['DC']}"
            target_dc_identifier = f"DC{move_target_details}"

            success = self.inventory.move_server(source_server_type, move_quantity, source_dc_identifier, target_dc_identifier)
            if success:
                reward += self.calculate_reward()  # Assuming this method calculates the reward for successful action
            else:
                reward -= 1

        elif action_type == "HOLD":
            reward -= 99999
            # No operation, but potentially calculate passive rewards or penalties
            reward += self.calculate_reward()  # Assuming there's a reward calculation for holding

        # Update the state and calculate reward as needed
        self.state = self.update_state()
        observation = self.convert_state_to_observation(self.state)
        done = self.check_done()

        self.current_time_step += 1
        if self.current_time_step <= len(self.demand_data.demand_data_df['time_step'].unique()):
            self.current_demand_rows = self.demand_data.demand_data_df[self.demand_data.demand_data_df['time_step'] == self.current_time_step]
        else:
            done = True

        return observation, reward, done, {}

    def update_state(self):
        print(f"Updating state after move. : {self.current_time_step}")
        for datacenter in self.inventory.datacenters:
            datacenter.update()
        new_state = self.initialize_environment_state()
        print("New state:", new_state)
        return new_state


    def calculate_profit(self):
        # Calculate the current total costs
        current_total_costs = self.inventory.get_total_costs()
        
        # Calculate the revenue generated in this step
        current_total_revenue = sum(s.selling_price for dc in self.inventory.datacenters for s in dc.servers if s.deployed and s.operational_time == 1)
        
        # Step-specific profit calculation
        step_profit = current_total_revenue - current_total_costs
        print(f"Step Revenue: {current_total_revenue}, Step Costs: {current_total_costs}, Step Profit: {step_profit}")
        return step_profit

    def calculate_utilization(self):
        total_utilization = 0
        for dc in self.inventory.datacenters:
            total_utilization += dc.calculate_utilization()
        return total_utilization / self.num_data_centers if self.num_data_centers > 0 else 0

    def calculate_reward(self):
        step_profit = self.calculate_profit()
        utilization_contribution = self.calculate_utilization() * 0.5  # Weight utilization equally
        
        reward = step_profit * 0.5 + utilization_contribution
        print(f"Reward: {reward}")
        return reward

    def check_done(self):
        return self.current_time_step > 100