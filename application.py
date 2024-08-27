import numpy as np
import pandas as pd
from Classes import *
from scipy.stats import truncweibull_min

class Simulation:
    def __init__(self, givens, input_actual, time_steps, debugging):
        self.givens = givens
        self.input_actual = input_actual.demand_data_df
        self.inventory = Inventory(givens)
        self.time_steps = time_steps
        self.debugging = debugging
        self.adjusted_capacities = None  # Store adjusted capacities here

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
        current_capacities = self.inventory.get_aggregated_server_capacities()
        self.adjusted_capacities = current_capacities.applymap(self.adjust_capacity_by_failure_rate)
        print(f"Adjusted Capacities at time step {current_time_step}")
        print(self.adjusted_capacities)
        self.handle_demand(current_time_step)
        print(f"Utilization at time step {current_time_step}: {self.calculate_utilization(current_time_step)}")
        self.dismiss_servers()


    def handle_demand(self, current_time_step):
        demand_data = self.input_actual[self.input_actual['time_step'] == current_time_step]
        for index, demand in demand_data.iterrows():
            for latency_sensitivity in ['high', 'low', 'medium']:
                needed_capacity = demand[latency_sensitivity]
                available_servers = [
                    server for dc in self.inventory.datacenters for server in dc.servers
                    if server.generation == demand['server_generation'] and server.latency_sensitivity == latency_sensitivity
                ]
                #print both normal and adjusted capacities
                print(f"Normal Capacities at time step {current_time_step}")
                print(self.inventory.get_aggregated_server_capacities())
                print(f"Adjusted Capacities at time step {current_time_step}")
                print(self.adjusted_capacities)
                total_available_capacity = sum(self.adjusted_capacities.get((server.generation, server.latency_sensitivity), 0) for server in available_servers)

                if needed_capacity > total_available_capacity:
                    self.buy_servers(demand['server_generation'], latency_sensitivity, needed_capacity - total_available_capacity)

    def buy_servers(self, generation, latency_sensitivity, additional_capacity_needed):
        print(f"Trying to meet additional demand of {additional_capacity_needed} with new servers.")
        server_data = self.givens.servers_df[self.givens.servers_df['server_generation'] == generation].iloc[0]
        slots_needed = server_data['slots_size']
        purchase_limit = 10  # Limit the number of server purchases per timestep

        for datacenter in self.inventory.datacenters:
            purchase_count = 0
            while additional_capacity_needed > 0 and datacenter.empty_slots >= slots_needed and purchase_count < purchase_limit:
                new_server = Server(self.givens, generation, latency_sensitivity, datacenter)
                if datacenter.can_add_server(new_server):
                    datacenter.add_server(new_server)
                    additional_capacity_needed -= new_server.capacity
                    purchase_count += 1
                    print(f"Added one {generation} server to {datacenter.identifier}; remaining demand: {additional_capacity_needed}.")
                else:
                    print("No suitable server found or datacenter capacity reached.")
                    break

            if additional_capacity_needed <= 0 or purchase_count == purchase_limit:
                break

        if additional_capacity_needed > 0:
            print(f"Warning: Not enough capacity to meet the demand for {generation} servers with {latency_sensitivity} sensitivity after {purchase_limit} purchases. Missing capacity: {additional_capacity_needed}")


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
    def get_capacity_by_server_generation_latency_sensitivity(self, fleet):
        # Adjust fleet capacity by failure rate
        capacity = fleet.groupby(by=['server_generation', 'latency_sensitivity'])['capacity'].sum().unstack(fill_value=0)
        return capacity.applymap(self.adjust_capacity_by_failure_rate)

    def adjust_capacity_by_failure_rate(self, capacity):
        failure_rate = truncweibull_min.rvs(0.3, 0.05, 0.1, size=1).item()
        return int(capacity * (1 - failure_rate))

def solution_function(givens, input_actual, time_steps=168, debugging=False):
    simulation = Simulation(givens, input_actual, time_steps, debugging)
    simulation.start_simulation()
    return [{'message': 'Simulation Completed Successfully'}]