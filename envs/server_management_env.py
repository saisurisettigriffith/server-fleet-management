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

        # Define your action and observation spaces based on these attributes
        max_quantity = 10
        self.action_space = spaces.MultiDiscrete([
            4,  # action type: buy, dismiss, move, hold
            *([max_quantity] * self.num_server_types * self.num_data_centers),  # Buy quantities for each type at each DC
            *([max_quantity] * self.num_server_types * self.num_data_centers),  # Dismiss quantities for each type at each DC
            *([self.num_data_centers] * self.num_server_types),  # Source DC for each server type
            *([self.num_data_centers] * self.num_server_types),  # Target DC for each server type
            *([max_quantity] * self.num_server_types)  # Quantity to move for each server type
        ])
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(20,), dtype=np.float32)
        self.state = self.reset()


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
        #     state[f"{dc_id}_UTILIZATION_RATE"] = dc.utilization_rate()

        # state["SYSTEM_TOTAL_OPERATING_COST"] = sum(dc.get_total_operational_cost() for dc in self.inventory.datacenters)
        # state["TOTAL_DEMAND_MET"] = 0  # Placeholder
        # state["TOTAL_SERVERS_DEPLOYED"] = sum(state[f"{dc.identifier}_OPERATIONAL_SERVERS"] for dc in self.inventory.datacenters)
        # state["TOTAL_CAPACITY_USED"] = sum(dc.used_capacity() for dc in self.inventory.datacenters)
        # state["TOTAL_ENERGY_COST"] = sum(dc.get_total_energy_cost() for dc in self.inventory.datacenters)

        # state["SERVERS_NEAR_EOL"] = sum(dc.servers_near_EOL() for dc in self.inventory.datacenters)
        # state["SERVERS_MID_LIFE"] = sum(dc.servers_mid_life() for dc in self.inventory.datacenters)
        # state["SERVERS_NEW"] = sum(dc.servers_new() for dc in self.inventory.datacenters)

        # state["TOTAL_ENERGY_CONSUMPTION"] = sum(dc.total_energy_consumption() for dc in self.inventory.datacenters)
        # state["TOTAL_FAILURES"] = sum(dc.total_failures() for dc in self.inventory.datacenters)
        # state["TOTAL_COST_TILL_NOW"] = self.inventory.delta_purchase_cost + self.inventory.delta_moving_cost
        # state["AVERAGE_LATENCY"] = np.mean([dc.average_latency() for dc in self.inventory.datacenters if dc.servers])
        # state["AVERAGE_OPERATIONAL_EFFICIENCY"] = np.mean([dc.operational_efficiency() for dc in self.inventory.datacenters if dc.servers])

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
        action_type = action[0]
        reward = 0

        # Define action parsing offsets based on the action space configuration
        buy_actions = action[1:self.num_server_types * self.num_data_centers + 1]
        dismiss_actions = action[self.num_server_types * self.num_data_centers + 1:2 * self.num_server_types * self.num_data_centers + 1]
        move_source_dcs = action[2 * self.num_server_types * self.num_data_centers + 1:3 * self.num_server_types * self.num_data_centers + 1]
        move_target_dcs = action[3 * self.num_server_types * self.num_data_centers + 1:4 * self.num_server_types * self.num_data_centers + 1]
        move_quantities = action[4 * self.num_server_types * self.num_data_centers + 1:]

        if action_type == 0:  # Buy
            print("Buy action:")
            for idx, qty in enumerate(buy_actions):
                print(f"Buy quantity: {qty}")
                if qty > 0:
                    print("Something is greater than 0")
                    server_type = idx % self.num_server_types
                    dc_id = idx // self.num_server_types
                    dc_identifier = "DC" + str(dc_id + 1)
                    print("FROM: BUY - Datacenter ID: ", dc_identifier)

                    success = self.inventory.add_server(server_type, qty, dc_identifier)
                    print(f"Attempt to deploy {qty} servers of type {server_type} in data center {dc_identifier}.")
                    if success:
                        print(f"Deployed {qty} servers of type {server_type} in data center {dc_identifier}.")
                    else:
                        print(f"Failed to deploy {qty} servers of type {server_type} in data center {dc_identifier}.")
                        reward -= 1

        elif action_type == 1:  # Move
            print("Move action:")
            for idx, qty in enumerate(move_quantities):
                print(f"Move quantity: {qty}")
                if qty > 0:
                    print("Something is greater than 0")
                    source_dc_id = "DC" + str(move_source_dcs[idx] + 1)
                    target_dc_id = "DC" + str(move_target_dcs[idx] + 1)
                    print("FROM: MOVE - Source Datacenter ID: ", source_dc_id)
                    print("FROM: MOVE - Destination Datacenter ID: ", target_dc_id)
                    server_type = idx % self.num_server_types
                    success = self.inventory.move_server(server_type, qty, source_dc_id, target_dc_id)
                    print(f"Attempt to move {qty} servers of type {server_type} from {source_dc_id} to {target_dc_id}.")
                    if success:
                        print(f"Moved {qty} servers of type {server_type} from {source_dc_id} to {target_dc_id}.")
                    else:
                        print(f"Failed to move {qty} servers from {source_dc_id} to {target_dc_id}.")
                        reward -= 1
                    ''' ********** IMPORTANT - Training Area: Constraint Violation **********
                    
                    1. However, post-testing, no matter how well our model performs, we must still ensure that the during the execution of the model, 
                    the constraints are not violated.

                    2. This means that the number of servers of type server_type that are deployed in the data center dc_identifier should be shown to the RL agent.
                    
                    Because by giving negative reward, the agent will learn that it should not dismiss servers of type server_type from the data center dc_identifier.
                    Especially if the number of servers of type server_type that are deployed in the data center dc_identifier is less than the number of servers of type server_type that are dismissed from the data center dc_identifier.
                    We must check this in the code.
                    ********** IMPORTANT - Training Area: Constraint Violation **********
                    '''

        elif action_type == 2:  # Dismiss
            print("Dismiss action:")
            for idx, qty in enumerate(dismiss_actions):
                print(f"Dismiss quantity: {qty}")
                if qty > 0:
                    print("Something is greater than 0")
                    server_type = idx % self.num_server_types
                    dc_id = idx // self.num_server_types
                    dc_identifier = "DC" + str(dc_id + 1)
                    print("FROM: DISMISS - Datacenter ID: ", dc_identifier)
                    success = self.inventory.remove_server(server_type, qty, dc_identifier)
                    print(f"Attempt to remove {qty} servers of type {server_type} from data center {dc_identifier}.")
                    if success:
                        print(f"Removed {qty} servers of type {server_type} from data center {dc_identifier}.")
                    else:
                        print(f"Failed to remove {qty} servers of type {server_type} from data center {dc_identifier}.")
                        reward -= 1

                    ''' ********** IMPORTANT - Training Area: Constraint Violation **********
                    
                    1. However, post-testing, no matter how well our model performs, we must still ensure that the during the execution of the model, 
                    the constraints are not violated.

                    2. This means that the number of servers of type server_type that are deployed in the data center dc_identifier should be shown to the RL agent.
                    
                    Because by giving negative reward, the agent will learn that it should not dismiss servers of type server_type from the data center dc_identifier.
                    
                    **Especially if the number of servers of type server_type that are deployed in the data center dc_identifier is less than the number of servers of type server_type that are dismissed from the data center dc_identifier.
                    We must check this in the code.**
                    ********** IMPORTANT - Training Area: Constraint Violation **********
                    '''

        elif action_type == 3:  # Hold
            print("No action taken.")

        self.state = self.update_state()
        observation = self.convert_state_to_observation(self.state)
        reward += self.calculate_reward()
        done = self.check_done()

        self.current_time_step += 1
        if self.current_time_step <= len(self.demand_data.demand_data_df['time_step'].unique()):
            self.current_demand_rows = self.demand_data.demand_data_df[self.demand_data.demand_data_df['time_step'] == self.current_time_step]
        else:
            done = True

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