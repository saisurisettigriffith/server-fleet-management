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
        self.failure_rates = self.sample_failure_rates()  # Sample once and use throughout the simulation
        self.hello = self.print_available_keys()

    def print_available_keys(self):
        print("Available keys in failure_rates:", self.failure_rates.keys())
        
        return True

    def sample_failure_rates(self):
        # Sampling failure rates for each server type and generation
        rates = {}
        for generation in self.givens.servers_df['server_generation'].unique():
            rates[generation] = truncweibull_min.rvs(0.3, 0.05, 0.1, size=1).item()
        return rates

    def adjust_capacity_by_failure_rate(self, capacity, generation):
        # Use the pre-sampled failure rate
        failure_rate = self.failure_rates[generation]
        adjusted_capacity = int(capacity * (1 - failure_rate))
        if self.debugging:
            print(f"Adjusting capacity for {generation}: original={capacity}, adjusted={adjusted_capacity}, failure_rate={failure_rate}")
        return adjusted_capacity

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
        if not current_capacities.empty:
            # If the DataFrame is not empty, adjust capacities
            self.adjusted_capacities = current_capacities.apply(
                lambda x: self.adjust_capacity_by_failure_rate(x['capacity'], x.name),
                axis=1
            )
            print(f"Adjusted Capacities at time step {current_time_step}:")
            print(self.adjusted_capacities)
        else:
            print("No capacities to adjust.")

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
                total_available_capacity = sum(server.capacity for server in available_servers)

                if needed_capacity > total_available_capacity:
                    self.buy_servers(demand['server_generation'], latency_sensitivity, needed_capacity - total_available_capacity)

    def buy_servers(self, generation, latency_sensitivity, additional_capacity_needed):
        print(f"Trying to meet additional demand of {additional_capacity_needed} with new servers.")
        server_data = self.givens.servers_df[self.givens.servers_df['server_generation'] == generation].iloc[0]
        slots_needed = server_data['slots_size']
        purchase_limit = 10  # This could be adjusted based on strategic needs

        for datacenter in self.inventory.datacenters:
            purchase_count = 0
            while additional_capacity_needed > 0 and datacenter.empty_slots >= slots_needed and purchase_count < purchase_limit:
                new_server = Server(self.givens, generation, latency_sensitivity, datacenter)
                if datacenter.can_add_server(new_server):
                    datacenter.add_server(new_server)
                    additional_capacity_needed -= new_server.capacity
                    purchase_count += 1
                    print(f"Added one {generation} server to {datacenter.identifier}; remaining demand: {additional_capacity_needed}.")
                if additional_capacity_needed <= 0:
                    break

            if additional_capacity_needed <= 0 or purchase_count == purchase_limit:
                break

        if additional_capacity_needed > 0:
            print(f"Warning: Not enough capacity to meet the demand for {generation} servers with {latency_sensitivity} sensitivity after {purchase_limit} purchases. Missing capacity: {additional_capacity_needed}")

    def dismiss_servers(self):
        for datacenter in self.inventory.datacenters:
            datacenter.dismiss_servers()

    def calculate_utilization(self, current_time_step):
        total_capacity = 0
        total_demand_met = 0
        for datacenter in self.inventory.datacenters:
            for server in datacenter.servers:
                if server.deployed:
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