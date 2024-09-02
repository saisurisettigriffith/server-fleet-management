import numpy as np
import pandas as pd
from Classes import *
from scipy.stats import truncweibull_min

class Simulation:
    def __init__(self, givens, input_actual, seed, time_steps, debugging):
        # CONSTANTS or PROPERTIES!!!
        self.magic_number_future = 30
        self.givens = givens
        self.demand = input_actual
        self.end_time_step = time_steps
        self.debugging = debugging
        self.inventory = Inventory(givens)
        self.capacities = []
        # Variables
        self.current_demand = None
        self.seed = seed
        self.current_time_step = 0
        self.transactions = []

    def start_simulation(self):
        self.capacities = self.inventory.get_aggregated_server_capacities()
        self.current_demand = self.demand.get_demand_for_time_step(self.current_time_step)
        print(self.demand.demand_data_df)
        while self.current_time_step < self.end_time_step:
            # Step 1: Age the servers
            self.inventory.update()
            # Because Aging them can reveal more slots so we can buy servers without unavailable slots BIASING OUR DECISION
            self.current_time_step += 1
            # Action
            self.buy()
            # Update Inventory according to: 1. Inreased Time Step and 2. Actions
            self.inventory.update()
        with open(f'{self.seed}.json', 'a') as f:
            f.write('\n')
            json.dump(self.transactions, f, indent=4)

    def buy(self):
        # Access current demand for the timestep
        current_demand = self.demand.get_demand_for_time_step(self.current_time_step)
        current_demand.columns.name = None
        if current_demand.empty:
            return  # No demand to satisfy

        print(f"Current Demand: {current_demand}")
        print("---------")

        # Evaluate each demand row for potential purchase
        for index, demand_row in current_demand.iterrows():
            print(f"Processing Demand Row: {demand_row}")
            server_type = demand_row['server_generation']
            release_time = self.inventory._givens.servers_df[self.inventory._givens.servers_df['server_generation'] == server_type]['release_time'].iloc[0]
            release_time = release_time[1:-1]  # Remove the leading '[' and trailing ']'
            release_start, release_end = release_time.split(',')
            release_start = int(release_start.strip())
            release_end = int(release_end.strip())
            if self.current_time_step < release_start or self.current_time_step > release_end:
                continue
            # Maximum of demand_row['high'], demand_row['low'] and demand_row['medium']
            latency_sensitivity = demand_row[['high', 'low', 'medium']].idxmax()
            print(f"Server Type: {server_type}, Latency Sensitivity: {latency_sensitivity}")
            # Determine future demand and profitability
            future_demand = self.demand.get_future_demand(server_type, latency_sensitivity, self.magic_number_future, self.current_time_step)
            if not future_demand:
                continue  # Skip if no future demand is predicted

            if latency_sensitivity == 'high':
                if self.inventory.DC3.empty_slots > 0:
                    pick_dc = 'DC3'
                else:
                    if self.inventory.DC4.empty_slots > 0:
                        pick_dc = 'DC4'
            elif latency_sensitivity == 'low':
                if self.inventory.DC1.empty_slots > 0:
                    pick_dc = 'DC1'
            else:
                if self.inventory.DC2.empty_slots > 0:
                    pick_dc = 'DC2'
            # self.capacities = self.inventory.get_aggregated_server_capacities()
            # print("---------")
            # print(f"Capacities: {self.capacities}")
            # print("---------")
            capacity_value = self.inventory._givens.servers_df[self.inventory._givens.servers_df['server_generation'] == server_type]['capacity'].iloc[0]
            quanity_needed = demand_row[f'{latency_sensitivity}'] // capacity_value
            # Something like - quanity_present = self.inventory.'f{pick_dc}'.servers.query(f"server_generation == '{server_type}'")['quantity'].iloc[0]
            # like if ...servers[i].generation == server_type: quanity_present+=1
            server_list = getattr(self.inventory, f'{pick_dc}').servers

            # Initialize the counter
            quantity_present = 0

            # Loop through each server in the list
            for server in server_list:
                if server.generation == server_type:
                    quantity_present += 1
            
            quanity_to_buy = quanity_needed - quantity_present
            if quanity_to_buy <= 0:
                quanity_to_buy = 0
            print(f"Quantity Needed: {quanity_needed}")
            print(f"Quantity Present: {quantity_present}")
            print(f"Quantity to Buy: {quanity_to_buy}")
            if quanity_to_buy <= 0:
                continue
            added = self.inventory.add_server(server_type, quanity_to_buy, pick_dc, self.current_time_step, self.transactions)
            print(f"Added: {added}")

    def calculate_profit_margin(self, server_type, latency_sensitivity, demand):
        # Placeholder to calculate expected profit margin
        sell_price = self.inventory.selling_price_df.query(
            f"server_generation == '{server_type}' and latency_sensitivity == '{latency_sensitivity}'"
        )['selling_price'].iloc[0]
        buy_cost = self.givens.servers_df.query(
            f"server_generation == '{server_type}'"
        )['purchase_price'].iloc[0]
        return sell_price - buy_cost

def solution_function(givens, input_actual, seed = 8501, time_steps=168, debugging=False):
    simulation = Simulation(givens, input_actual, seed, time_steps, debugging)
    simulation.start_simulation()
    return [{'message': 'Simulation Completed Successfully'}]