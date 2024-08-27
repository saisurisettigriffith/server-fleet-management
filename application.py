import numpy as np
import pandas as pd
import evaluation as ev
from scipy.stats import truncweibull_min, truncnorm
from Classes import DataCenter, Server, Inventory

global inventory
global simulation
global debuggingmode

def calculate_utilization(data_centers, demand_data):
    total_utilization = 0
    count = 0
    
    for dc in data_centers:
        for server in dc.servers:
            if server.deployed:
                demand = demand_data.get((server.generation, dc.latency_sensitivity), 0)
                met_demand = min(server.capacity, demand)
                total_utilization += met_demand / server.capacity if server.capacity > 0 else 0
                count += 1

    average_utilization = total_utilization / count if count > 0 else 0
    return average_utilization

def manage_server_actions(data_centers, demand_data, time_step):
    for dc in data_centers:
        for server in dc.servers:
            if server.deployed:
                # Example heuristic: dismiss server if it's reaching end of life
                if server.operational_time >= server.life_expectancy - 1:
                    dc.remove_server(server)
                else:
                    # Evaluate demand and decide whether to hold or move
                    current_demand = demand_data.get((server.generation, dc.latency_sensitivity), 0)
                    if current_demand < server.capacity * 0.3:  # Arbitrary threshold to consider moving
                        target_dc = find_new_datacenter(data_centers, dc, server)
                        if target_dc:
                            move_server(dc, target_dc, server)
                    # Otherwise, hold (do nothing)
            else:
                # Check if buying a new server is beneficial
                if should_buy_new_server(dc, server, demand_data, time_step):
                    dc.add_server(server)

def find_new_datacenter(data_centers, current_dc, server):
    # Example logic to find a new datacenter with more demand and enough capacity
    for dc in data_centers:
        if dc != current_dc and dc.can_add_server(server):
            return dc
    return None

def move_server(source_dc, target_dc, server):
    source_dc.remove_server(server)
    target_dc.add_server(server)

def should_buy_new_server(dc, server, demand_data, time_step):
    # Example heuristic: buy new server if current demand exceeds a certain threshold
    demand = demand_data.get((server.generation, dc.latency_sensitivity), 0)
    return demand > server.capacity * 0.8  # Another arbitrary threshold

def initialize_variables(demand, datacenters, servers, selling_prices, time_steps, seed=None, debugging=False):

    debuggingmode = debugging
    # SET SEED
    np.random.seed(seed)
    # GET ACTUAL DEMAND
    demand = ev.get_actual_demand(demand)
    print("Demand: \n", demand)
    print("Datacenters: \n", datacenters)
    print("Servers: \n", servers)
    print("Selling Prices: \n", selling_prices)
    print("Time Steps: \n", time_steps)
    selling_prices = selling_prices.pivot(index='server_generation', columns='latency_sensitivity', values='selling_price')
    simulation = demand.merge(selling_prices, on='server_generation', how='left', suffixes=('_demand', '_price'))
    simulation = simulation.rename(columns={
        'high_demand': 'high',
        'low_demand': 'low',
        'medium_demand': 'medium',
        'high_price': 'price_high',
        'low_price': 'price_low',
        'medium_price': 'price_medium'
    })
    simulation = simulation.reset_index(drop=True, inplace=False)
    print("Simulation: \n", simulation)
    return simulation

def start_simulation(demand, datacenters, servers, selling_prices, time_steps, seed=None, debugging=False):
    # Initialize the simulation environment
    global inventory  # Ensure inventory is accessible globally if needed elsewhere
    inventory = Inventory(datacenters, servers, selling_prices)
    
    # Set random seed for reproducibility
    np.random.seed(seed)

    # Main simulation loop
    for t in range(1, time_steps + 1):
        print(f"Time Step {t}/{time_steps}")
        # Simulate time step in inventory
        inventory.simulate_time_step()
        
        # Optionally, calculate and display metrics at each step or based on condition
        if debugging:
            print("Current Utilization:", calculate_utilization(inventory.datacenters, demand))
            print("Total Energy Cost:", inventory.get_total_energy_cost())
    
    # Final output after simulation ends
    print("Simulation Complete")
    return inventory  # Return the inventory for further analysis if needed

def solution_function(demand, datacenters, servers, selling_prices, time_steps=168, seed=None, debugging=False):
    # Start the simulation with the given parameters
    start_simulation(demand, datacenters, servers, selling_prices, time_steps, seed, debugging)
    
    return [{'message': 'Simulation Completed Successfully'}]