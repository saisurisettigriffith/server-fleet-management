import gym
from gym import spaces
import numpy as np
from Classes import *

class ServerManagementEnv(gym.Env):
    '''
    Columns and Head of Sample demand data: 
    Index(['time_step', 'server_generation', 'high', 'low', 'medium'], dtype='object', name='latency_sensitivity')
    latency_sensitivity  time_step server_generation   high    low  medium
    0                            1            CPU.S1   6230  19865    7220
    1                            1            GPU.S1     35     19       1
    2                            2            CPU.S1  12584  37035   14514
    3                            2            GPU.S1     69     38       4
    4                            3            CPU.S1  17781  54178   16664
    Columns and Head of Hackathon Input Format demand data: 
    Index(['time_step', 'server_generation', 'high', 'low', 'medium'], dtype='object', name='latency_sensitivity')
    latency_sensitivity  time_step server_generation   high    low  medium
    0                            1            CPU.S1   6230  19865    7220
    1                            1            GPU.S1     35     19       1
    2                            2            CPU.S1  12584  37035   14514
    3                            2            GPU.S1     69     38       4
    4                            3            CPU.S1  17781  54178   16664
    '''
    def __init__(self, givens, demand_data):
        super(ServerManagementEnv, self).__init__()
        self.givens = givens
        self.demand_data = demand_data.demand_data_df
        self.inventory = Inventory(givens)

        # Define the action and observation spaces
        # Assuming actions are defined as tuples (data_center_id, server_type, action_type, quantity)
        '''
        To ChatGPT: Are they defined as tuples?
        '''
        self.action_space = spaces.MultiDiscrete([len(self.inventory.datacenters), len(self.givens.servers_df), 3, 10])
        self.observation_space = spaces.Box(low=0, high=np.inf, shape=(self._determine_obs_space_size(),), dtype=np.float32)
        self.state = self.reset()

    def _determine_obs_space_size(self):
        # Placeholder function to calculate the size of the observation space
        return len(self.inventory.datacenters) * 10  # Example complexity
    
    def reset(self):
        # Directly compute required_capacity from the known columns
        demand_columns = ['high', 'low', 'medium']  # Adjust these as necessary
        if all(col in self.demand_data.columns for col in demand_columns):
            self.demand_data['required_capacity'] = self.demand_data[demand_columns].sum(axis=1)
        else:
            print("Warning: Demand columns necessary to calculate 'required_capacity' are missing.")

        self.state = {
            "data_centers": [dc.summary() for dc in self.inventory.datacenters],
            "demand": [
                {
                    "type": gen,
                    "required_capacity": sum(row['required_capacity'] for _, row in self.demand_data[self.demand_data['server_generation'] == gen].iterrows()),
                    "latency_sensitivity": row['latency_sensitivity']
                }
                for gen, row in self.demand_data.groupby('server_generation')
            ]
        }
        return self.state

    def reset(self):
        print("Columns in demand_data:", self.demand_data.columns)
        self.state = {
            "data_centers": [dc.summary() for dc in self.inventory.datacenters],
            "demand": [{
                "type": gen,
                "required_capacity": sum(row['some_other_capacity_field'] for _, row in self.demand_data[self.demand_data['server_generation'] == gen].iterrows()),
                "latency_sensitivity": row['latency_sensitivity']
            } for gen, row in self.demand_data.groupby('server_generation')]
        }
        return self.state


    def step(self, action):
        self.state = self._apply_action(action)
        reward = self._calculate_reward()
        done = self._check_done()
        return self.state, reward, done, {}

    def _initialize_state(self):
        # Logic to initialize the environment state
        pass
    
    def _apply_action(self, action):
        # Logic to apply action and update state
        # Decode the action
        dc_id, server_type, action_type, quantity = action
        if action_type == 0:  # Deploy servers
            self.inventory.datacenters[dc_id].deploy_server(server_type, quantity)
        elif action_type == 1:  # Power down servers
            self.inventory.datacenters[dc_id].power_down_server(server_type, quantity)
        # Update state after action
        self.update_state()
    def _calculate_reward(self):
        #Placeholder function to calculate the reward
        required_capacities = [demand['required_capacity'] for demand in self.state['demand']]
        available_capacities = [dc['available_capacity'] for dc in self.state['data_centers']]
        costs = self.calculate_costs()
        unmet_demand_penalty = sum(max(0, req - avail) for req, avail in zip(required_capacities, available_capacities))
        reward = -costs - unmet_demand_penalty
        return reward

    def _check_done(self):
        # Logic to check if the episode is done
        pass
    def reset(self):
    # Reset the environment to an initial state
        self.state = {
            "data_centers": [
                {
                    "identifier": dc.identifier,
                    "total_capacity": sum(server.capacity for server in dc.servers),
                    "available_capacity": sum(server.capacity for server in dc.servers if server.deployed),
                    "energy_cost": dc.cost_of_energy,
                    "servers": [
                        {
                            "type": server.generation,
                            "capacity_used": server.capacity if server.deployed else 0,
                            "uptime": server.operational_time,
                            "latency_sensitivity": server.latency_sensitivity
                        }
                        for server in dc.servers
                    ]
                }
                for dc in self.inventory.datacenters
            ],
            "demand": [
                {
                    "type": gen,
                    "required_capacity": sum(self.demand_data.loc[self.demand_data['server_generation'] == gen, 'required_capacity']),
                    "latency_sensitivity": row['latency_sensitivity']
                }
                for gen, row in self.demand_data.groupby('server_generation')
            ]
        }
        return self.state
    
    def deploy_server(self, server_type, quantity):
        for _ in range(quantity):
            server = Server(self.givens, server_type, "high", self, f"{self.identifier}_new")
            if self.can_add_server(server):
                self.add_server(server)
            else:
                break  # No more space to add servers

    def power_down_server(self, server_type, quantity):
        powered_down = 0
        for server in self.servers:
            if server.type == server_type and server.deployed and powered_down < quantity:
                server.decommission()  # Assuming decommission will power down the server
                powered_down += 1
            if powered_down >= quantity:
                break

    def calculate_costs(self):
        return sum(dc.calculate_operating_cost() for dc in self.inventory.datacenters)
    
    def _check_done(self):
        # Example completion condition
        return self.current_time_step >= self.max_time_steps
    
    def update_state(self):
        self.state['data_centers'] = [dc.summary() for dc in self.inventory.datacenters]
        # Include any other state properties that need updating