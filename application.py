import numpy as np
import pandas as pd
from Classes import *

class Simulation:
    def __init__(self, givens, input_actual, time_steps, debugging):
        self.givens = givens
        self.input_actual = input_actual.demand_data_df
        self.inventory = Inventory(givens)
        self.time_steps = time_steps
        self.debugging = debugging

    def print_data(self):
        print("\'input_actual\' Data:")
        print(self.input_actual)
        print(self.givens)

    def start_simulation(self):
        self.print_data()
        print("Simulation Started")
        for t in range(1, self.time_steps + 1):
            print(f"Simulating time step {t}")
            self.process_time_step(t)

    def process_time_step(self, current_time_step):
        self.handle_demand(current_time_step)
        self.dismiss_servers()
        print(f"Utilization at time step {current_time_step}: {self.calculate_utilization(current_time_step)}")


    def handle_demand(self, current_time_step):
        # Fetching demand data for the current time step
        demand_data = self.input_actual[self.input_actual['time_step'] == current_time_step]
        print(f"Handling demand for time step {current_time_step}")
        print(demand_data)
        for index, demand in demand_data.iterrows():
            # Process each latency sensitivity level separately
            for latency_sensitivity in ['high', 'low', 'medium']:
                needed_capacity = demand[latency_sensitivity]
                available_servers = [
                    server for dc in self.inventory.datacenters for server in dc.servers
                    if server.generation == demand['server_generation'] and server.latency_sensitivity == latency_sensitivity
                ]
                total_available_capacity = sum(server.capacity for server in available_servers)

                # Check if additional servers are needed to meet the demand
                if needed_capacity > total_available_capacity:
                    self.buy_servers(demand['server_generation'], latency_sensitivity, needed_capacity - total_available_capacity)


    def buy_servers(self, generation, latency_sensitivity, additional_capacity_needed):
        # Fetch server data based on the generation
        server_data = self.givens.servers_df[self.givens.servers_df['server_generation'] == generation].iloc[0]
        slots_needed = server_data['slots_size']

        # Iterate through each data center to find space for new servers
        for datacenter in self.inventory.datacenters:
            while additional_capacity_needed > 0 and datacenter.empty_slots >= slots_needed:
                new_server = Server(self.givens, generation, latency_sensitivity, datacenter)
                # Check again if there is enough space after server object creation
                if datacenter.can_add_server(new_server):
                    datacenter.add_server(new_server)
                    additional_capacity_needed -= new_server.capacity
                # Break the inner loop if the current data center can no longer accommodate more servers
                if datacenter.empty_slots < slots_needed:
                    break

        # Optionally handle the scenario where additional capacity could not be met by existing data centers
        if additional_capacity_needed > 0:
            print(f"Not enough capacity to meet the demand for {generation} servers with {latency_sensitivity} sensitivity. Missing capacity: {additional_capacity_needed}")


    def dismiss_servers(self):
        # Dismiss servers based on life expectancy
        for datacenter in self.inventory.datacenters:
            for server in datacenter.servers[:]:
                if server.remaining_life <= 0:
                    datacenter.remove_server(server)

    def calculate_utilization(self, current_time_step):
        total_capacity = 0
        total_demand_met = 0
        for datacenter in self.inventory.datacenters:
            for server in datacenter.servers:
                if server.deployed:
                    # Aggregate demand based on latency sensitivity handled by the server
                    latency_column = server.latency_sensitivity
                    demand = self.input_actual.loc[
                        (self.input_actual['time_step'] == current_time_step) &
                        (self.input_actual['server_generation'] == server.generation), latency_column].sum()
                    met_demand = min(demand, server.capacity)
                    total_demand_met += met_demand
                    total_capacity += server.capacity
        if total_capacity > 0:
            return total_demand_met / total_capacity
        else:
            return 0

def solution_function(givens, input_actual, time_steps=168, debugging=False):
    simulation = Simulation(givens, input_actual, time_steps, debugging)
    simulation.start_simulation()
    return [{'message': 'Simulation Completed Successfully'}]