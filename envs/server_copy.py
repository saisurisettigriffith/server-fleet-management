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
        self.baught_servers_time_step = []
        self.total_capacity_demanded = 0
        self.total_capacity_met_due_to_baught = 0
        self.total_capacity_met_actual = 0
        self.max_time_steps = 100
        # Hardcoded release times based on the provided CSV

        # Define your action and observation spaces based on these attributes
        max_quantity = 2
        self.action_space = spaces.MultiDiscrete([
            1,
            28,  # "magic code" for each server type at each DC - BUY
            max_quantity # How Many to buy
            # self.num_server_types * self.num_data_centers,  # "magic code" for each server type at each DC - DISMISS
            # max_quantity, # How Many to dismiss
            # self.num_data_centers * self.num_server_types,  # "magic code" for each server type at each DC - MOVE.Source
            # 4,  # "magic code" for each server type at each DC - MOVE.Target
            # max_quantity, # How Many to move
        ])
        self.observation_shape = 500  # Set this to the expected max size
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(self.observation_shape,), dtype=np.float64)
        self.state = self.reset()

    def reset(self, **kwargs):
        # Handle potential arguments like 'seed' if necessary
        if 'seed' in kwargs:
            np.random.seed(kwargs['seed'])

        self.state = self.initialize_environment_state()
        observation = self.convert_state_to_observation(self.state)
        return observation, {}  # Return an empty dictionary as the second value



    def initialize_environment_state(self):
        state = {}
        total_profit = 0
        total_utilization = 0

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

        # This should show the release times for each server type.. use the "release_times_start" and "release_times_end" dictionaries which are hardcoded within this function
        for server_type, start_time in release_times_start.items():
            state[f"{server_type}_AVAILABLE_FROM"] = start_time
        for server_type, end_time in release_times_end.items():
            state[f"{server_type}_AVAILABLE_UNTIL"] = end_time
        state[f"TIME_STEP"] = self.current_time_step
        state[f"TOTAL_DATA_CENTERS"] = self.num_data_centers
        state[f"TOTAL_SERVER_TYPES"] = self.num_server_types

        for i, dc in enumerate(self.inventory.datacenters):
            dc_id = dc.identifier
            # state[f"{dc_id}_TOTAL_SERVERS"] = len(dc.servers)
            # state[f"{dc_id}_OPERATIONAL_SERVERS"] = sum(1 for s in dc.servers if s.deployed)
            # state[f"{dc_id}_ENERGY_CONSUMPTION"] = dc.get_total_energy_cost()
            state["DC1_AVAILABLE_SLOTS"] = dc.empty_slots if dc_id == "DC1" else 0
            state["DC2_AVAILABLE_SLOTS"] = dc.empty_slots if dc_id == "DC2" else 0
            state["DC3_AVAILABLE_SLOTS"] = dc.empty_slots if dc_id == "DC3" else 0
            state["DC4_AVAILABLE_SLOTS"] = dc.empty_slots if dc_id == "DC4" else 0
            # state[f"{dc_id}_UTILIZATION"] = dc.calculate_utilization()
            # total_utilization += dc.calculate_utilization()

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
        state["TOTAL_DEMAND_MET_ACTUAL"] = self.total_capacity_met_actual
        state["TOTAL_DEMAND_MET_DUE_TO_BOUGHT"] = self.total_capacity_met_due_to_baught
        #state["TOTAL_UTILIZATION"] = total_utilization / self.num_data_centers if self.num_data_centers > 0 else 0

        return state

    def convert_state_to_observation(self, state):
        observation = np.zeros(self.observation_shape)  # Start with an array of zeros of fixed size
        state_keys = sorted(state.keys())
        state_values = np.array([state[key] for key in state_keys])
        
        observation[:len(state_values)] = state_values  # Fill in the observation with the state values        
        # # Print observation keys and values
        # print("Observation Keys and Values:")
        # for key, value in zip(state_keys, observation):
        #     print(f"{key}: {value}")
        
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
        action_type = action_map[action[0]]
        reward = 0

        # Parse the action array based on the structure defined in the action space
        buy_action_code = action[1]
        buy_action_code += 1
        buy_quantity = action[2]
        # dismiss_action_code = action[3]
        # dismiss_action_code += 1
        # dismiss_quantity = action[4]
        # move_source_code = action[5]
        # move_source_code += 1
        # move_target_code = action[6]
        # move_target_code += 1
        # move_quantity = action[7]

        # Get details from the server_dataceneter_map
        buy_action_details = server_datacenter_map[buy_action_code]
        # dismiss_action_details = server_datacenter_map[dismiss_action_code]
        # move_source_details = server_datacenter_map[move_source_code]
        # move_target_details = move_target_code + 1

        server_type = f"{buy_action_details['Type']}.S{buy_action_details['Generation']}"
        dc_identifier = f"DC{buy_action_details['DC']}"

        # Check release time constraints
        release_start = release_times_start[server_type]
        release_end = release_times_end[server_type]
        if release_start <= self.current_time_step <= release_end:
            self.baught_servers_time_step = self.inventory.add_server(server_type, buy_quantity, dc_identifier)
            #print("Asked for servers:")
            for idx, row in self.current_demand_rows.iterrows():
                server_generation = row['server_generation']
                #print(f"Time Step: {self.current_time_step}, Server Generation: {server_generation}, High: {row['high']}, Low: {row['low']}, Medium: {row['medium']}")
            if len(self.baught_servers_time_step) > 0:
                #print("Baught servers:")
                #print(self.baught_servers_time_step)

                capacity_met_ratio = self.calculate_capacity_met_ratio()
                self.calculate_total_capacity_demanded(self.current_time_step)
                self.calculate_total_capacity_met_due_to_baught(self.current_time_step)
                self.calculate_total_capacity_met_actual(self.current_time_step)

                #print(f"Capacity Met Ratio at Time Step {self.current_time_step}: {capacity_met_ratio}%")
                # print(f"Total Capacity Demanded: {self.total_capacity_demanded}")
                # print(f"Total Capacity Met due to Baught: {self.total_capacity_met_due_to_baught}")
                # print(f"Total Capacity Met Actual: {self.total_capacity_met_actual}")
                #reward += ((self.total_capacity_met_actual / self.total_capacity_demanded) * 1000)
                #print("<<<<<<<<<<<<Giving reward>>>>>>>>>>>>: ", reward)
            reward += 1
            print("<<<<<<<<<<<<Giving reward>>>>>>>>>>>>: ", reward)
        else:
            #print(f"Server type {server_type} is not available for purchase at time step {self.current_time_step}.")
            reward -= 1
            print("<<<<<<<<<<<<Giving reward>>>>>>>>>>>>: ", reward)


        self.state = self.update_state()
        observation = self.convert_state_to_observation(self.state)

        self.current_time_step += 1
        print(len(self.current_demand_rows))
        #os._exit(0)
        done = self.check_done()
        truncated = False

        if self.current_time_step <= len(self.demand_data.demand_data_df['time_step'].unique()):
            self.current_demand_rows = self.demand_data.demand_data_df[self.demand_data.demand_data_df['time_step'] == self.current_time_step]
        else:
            done = True
            self.reset()

        info = {}
        if done:
            print("Done")
            truncated = (self.current_time_step > self.max_time_steps)
        
        return observation, reward, done, truncated, info
        #print(f"Action taken: {action}, Reward: {reward}, New State: {self.state}")

    def calculate_total_capacity_demanded(self, time_step):
        self.total_capacity_demanded = 0  # Reset the total capacity demanded

        for idx, row in self.current_demand_rows.iterrows():
            # Add up the demand for high, low, and medium latency sensitivity
            self.total_capacity_demanded += row['high'] + row['low'] + row['medium']
            # print(f"Time Step: {self.current_time_step}, Server Generation: {row['server_generation']}, "
            #     f"High: {row['high']}, Low: {row['low']}, Medium: {row['medium']}")

        # print(f"Total Capacity Demanded at Time Step {self.current_time_step}: {self.total_capacity_demanded}")

    
    def calculate_total_capacity_met_due_to_baught(self, time_step):
        self.total_capacity_met_due_to_baught = 0  # Reset the total capacity met

        for idx, row in self.current_demand_rows.iterrows():
            server_generation = row['server_generation']
            demand_for_high = row['high']
            demand_for_medium = row['medium']
            demand_for_low = row['low']

            # # Print debug statements
            # print(f"Outer loop: Server Generation: {server_generation}, High: {demand_for_high}, "
            #     f"Low: {demand_for_low}, Medium: {demand_for_medium}")
            # print(f"Current demand rows columns: {self.current_demand_rows.columns}")

            for server in self.baught_servers_time_step:
                # Unpack the details for each server bought in this time step
                server_id, server_gen, data_center, latency_sensitivity = server

                # Print debug statements
                # print(f"Inner loop: Server ID: {server_id}, Server Generation: {server_gen}, "
                #     f"Latency Sensitivity: {latency_sensitivity}")

                # Match server generation and latency sensitivity
                if server_gen == server_generation:
                    if latency_sensitivity == 'high' and demand_for_high > 0:
                        self.total_capacity_met_due_to_baught += 1  # Or server capacity if relevant
                        demand_for_high -= 1
                    elif latency_sensitivity == 'medium' and demand_for_medium > 0:
                        self.total_capacity_met_due_to_baught += 1  # Or server capacity if relevant
                        demand_for_medium -= 1
                    elif latency_sensitivity == 'low' and demand_for_low > 0:
                        self.total_capacity_met_due_to_baught += 1  # Or server capacity if relevant
                        demand_for_low -= 1

                    # Stop processing if all demand for this server generation and sensitivity is met
                    if demand_for_high == 0 and demand_for_medium == 0 and demand_for_low == 0:
                        break

            # print(f"Time Step: {self.current_time_step}, Server Generation: {server_generation}, "
            #     f"High: {demand_for_high}, Low: {demand_for_low}, Medium: {demand_for_medium}")
        # print(f"Total Capacity Met at Time Step {self.current_time_step}: {self.total_capacity_met_due_to_baught}")
        # print(f"Total Capacity Demanded at Time Step {self.current_time_step}: {self.total_capacity_demanded}")

    def calculate_total_capacity_met_actual(self, time_step):
        self.total_capacity_met_actual = 0  # Reset the total capacity met

        # Iterate over each demand row for the current time step
        for idx, row in self.current_demand_rows.iterrows():
            server_generation = row['server_generation']
            demand_for_high = row['high']
            demand_for_medium = row['medium']
            demand_for_low = row['low']

            # Debug statements
            # print(f"Outer loop: Server Generation: {server_generation}, High: {demand_for_high}, "
            #     f"Low: {demand_for_low}, Medium: {demand_for_medium}")
            # print(f"Current demand rows columns: {self.current_demand_rows.columns}")

            # Iterate through each data center in the inventory
            for dc in self.inventory.datacenters:
                # Iterate through each server in the data center
                for server in dc.servers:
                    # Ensure the server is deployed and available
                    if not server.deployed:
                        continue  # Skip servers that are not deployed

                    # Unpack server details
                    server_id = server.identifier
                    server_gen = server.generation  # Ensure this attribute exists
                    latency_sensitivity = server.data_center_object.latency_sensitivity  # Ensure this attribute exists

                    # Debug statements
                    # print(f"Inner loop: Server ID: {server_id}, Server Generation: {server_gen}, "
                    #     f"Latency Sensitivity: {latency_sensitivity}")

                    # Match server generation
                    if server_gen != server_generation:
                        continue  # Skip if server generation does not match

                    # Allocate server capacity based on latency sensitivity
                    if latency_sensitivity == 'high' and demand_for_high > 0:
                        self.total_capacity_met_actual += 1  # Adjust if servers have different capacities
                        demand_for_high -= 1
                        #print(f"Allocated to high latency demand. Remaining high demand: {demand_for_high}")
                    elif latency_sensitivity == 'medium' and demand_for_medium > 0:
                        self.total_capacity_met_actual += 1
                        demand_for_medium -= 1
                        #print(f"Allocated to medium latency demand. Remaining medium demand: {demand_for_medium}")
                    elif latency_sensitivity == 'low' and demand_for_low > 0:
                        self.total_capacity_met_actual += 1
                        demand_for_low -= 1
                        #print(f"Allocated to low latency demand. Remaining low demand: {demand_for_low}")

                    # Check if all demands for this server generation are met
                    if demand_for_high == 0 and demand_for_medium == 0 and demand_for_low == 0:
                        #print("All demands for this server generation are met.")
                        break  # Exit the server loop early

                # After iterating through all servers in the data center
                if demand_for_high == 0 and demand_for_medium == 0 and demand_for_low == 0:
                    #print("All demands for this server generation are met across all data centers.")
                    break  # Exit the data center loop early

            # Debug statement after processing all data centers for this demand row
            # print(f"Time Step: {self.current_time_step}, Server Generation: {server_generation}, "
            #     f"High: {demand_for_high}, Low: {demand_for_low}, Medium: {demand_for_medium}")

        # Final debug statements
        # print(f"Total Capacity Met Actual at Time Step {self.current_time_step}: {self.total_capacity_met_actual}")
        # print(f"Total Capacity Demanded at Time Step {self.current_time_step}: {self.total_capacity_demanded}")

    def calculate_capacity_met_ratio(self):
        if self.total_capacity_demanded > 0:
            return (self.total_capacity_met_actual / self.total_capacity_demanded) * 100
        else:
            return 0  # No demand means no capacity could be met, returning 0%

    def update_state(self):
        #print(f"Updating state after the action : {self.current_time_step}")
        self.inventory.update()
        new_state = self.initialize_environment_state()
        #print("New state:", new_state)
        return new_state

    def calculate_utilization(self):
        total_utilization = 0
        for dc in self.inventory.datacenters:
            total_utilization += dc.calculate_utilization()
        return total_utilization / self.num_data_centers if self.num_data_centers > 0 else 0

    def check_done(self):
        return self.current_time_step >= self.max_time_steps