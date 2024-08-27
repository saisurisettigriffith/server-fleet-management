import utils as utl
import application as app
import seeds as sds
import pandas as pd
from utils import *
from evaluation import *

class Server:
    def __init__(self, givens, generation, latency, data_center):
        server_data = givens.servers_df[givens.servers_df['server_generation'] == generation].iloc[0]
        selling_price_data = givens.selling_prices_df[givens.selling_prices_df['server_generation'] == generation]
        self.identifier = f"{generation}_{data_center.identifier}_{np.random.randint}"  # Example to create a unique identifier
        self.generation = generation
        self.server_type = server_data['server_type']
        self.capacity = server_data['capacity']
        self.slots_needed = server_data['slots_size']
        self.energy_consumption = server_data['energy_consumption']
        self.purchase_price = server_data['purchase_price']
        self.life_expectancy = server_data['life_expectancy']
        self.cost_of_moving = server_data['cost_of_moving']
        self.maintenance_fee = server_data['average_maintenance_fee']
        self.release_time_bounds = eval(server_data['release_time'])
        self.latency_sensitivity = latency

        self.sell_price_low = selling_price_data[selling_price_data['latency_sensitivity'] == 'low']['selling_price'].iloc[0]
        self.sell_price_medium = selling_price_data[selling_price_data['latency_sensitivity'] == 'medium']['selling_price'].iloc[0]
        self.sell_price_high = selling_price_data[selling_price_data['latency_sensitivity'] == 'high']['selling_price'].iloc[0]

        self.remaining_life = self.life_expectancy
        self.deployed = self.remaining_life > 0
        self.operational_time = 0
        self.data_center = data_center
        self.selling_price = self.sell_price_low if self.latency_sensitivity == 'low' else self.sell_price_medium if self.latency_sensitivity == 'medium' else self.sell_price_high

    def age_server(self):
        if self.deployed:
            self.operational_time += 1
            if self.operational_time >= self.life_expectancy:
                self.decommission()

    def deploy(self):
        self.deployed = True

    def decommission(self):
        self.deployed = False
        print(f"Server {self.identifier} decommissioned.")

    def update_life(self, time):
        self.remaining_life -= time
        self.operational_time += 1
        if self.remaining_life <= 0 or self.operational_time >= self.life_expectancy:
            self.decommission()

    def update(self):
        self.update_life(1)


class DataCenter:
    def __init__(self, givens, identifier):
        self.datacenters_df = givens.datacenters_df
        datacenter_data = self.datacenters_df[self.datacenters_df['datacenter_id'] == identifier].iloc[0]
        self.identifier = identifier
        self.slots_capacity = datacenter_data['slots_capacity']
        self.filled_slots = 0
        self.empty_slots = self.slots_capacity
        self.cost_of_energy = datacenter_data['cost_of_energy']
        self.latency_sensitivity = datacenter_data['latency_sensitivity']
        self.servers = []  # List of Server objects

    def add_server(self, server):
        if self.can_add_server(server):
            self.servers.append(server)
            server.deploy()
            self.filled_slots += server.slots_needed
            self.empty_slots = self.slots_capacity - self.filled_slots
            print(f"Server {server.generation} added to {self.identifier}")
        else:
            print("Not enough slots to add this server")

    def remove_server(self, server):
        if server in self.servers:
            self.servers.remove(server)
            server.decommission()
            self.filled_slots -= server.slots_needed
            self.empty_slots = self.slots_capacity - self.filled_slots
            print(f"Server {server.generation} removed from {self.identifier}")

    def can_add_server(self, server):
        total_slots_used = sum(s.slots_needed for s in self.servers if s.deployed)
        return total_slots_used + server.slots_needed <= self.slots_capacity

    def simulate_time_step(self):
        for server in self.servers:
            server.age_server()

class Inventory:
    def __init__(self, givens):
        # Loading the data might typically happen outside of this class, but we include it here for completeness
        self.datacenters_df = givens.datacenters_df
        self.servers_df = givens.servers_df
        self.selling_prices_df = givens.selling_prices_df
        self.datacenters = [DataCenter(givens, dc) for dc in self.datacenters_df['datacenter_id']]
        self.filled_slots = 0
        self.empty_slots = sum(dc.slots_capacity for dc in self.datacenters)
        self.servers = []  # List of all servers in all datacenters

    def update_servers(self):
        # This method would be used to sync servers across datacenters if needed
        self.update_end_of_life_servers()
        for dc in self.datacenters:
            for server in dc.servers:
                if server not in self.servers:
                    self.servers.append(server)
    
    def update_end_of_life_servers(self):
        # Decommission servers that have reached the end of their life expectancy
        for server in self.servers:
            if server.remaining_life <= 0:
                server.decommission()
    
    def simulate_time_step_servers(self):
        for server in self.servers:
            server.update()

    def get_datacenter_by_id(self, identifier):
        # Retrieve a datacenter by its ID
        for dc in self.datacenters:
            if dc.identifier == identifier:
                return dc
        return None

    def get_server_by_generation(self, generation):
        # Retrieve a server by its generation
        for server in self.servers:
            if server.generation == generation:
                return server
        return None

    def get_total_energy_cost(self):
        # Calculate total energy cost across all datacenters
        total_cost = 0
        for dc in self.datacenters:
            for server in dc.servers:
                if server.deployed:
                    total_cost += dc.cost_of_energy * server.energy_consumption
        return total_cost

    def get_total_maintenance_cost(self):
        # Calculate total maintenance cost for all deployed servers
        total_cost = 0
        for server in self.servers:
            if server.deployed:
                total_cost += server.maintenance_fee
        return total_cost

    def get_total_purchase_cost(self):
        # Calculate total purchase cost for all deployed servers
        total_cost = 0
        for server in self.servers:
            if server.deployed:
                total_cost += server.purchase_price
        return total_cost

    def get_total_moving_cost(self):
        # Calculate total moving cost for all moved servers
        total_cost = 0
        for server in self.servers:
            if server.deployed and server.moved_this_step:
                total_cost += server.cost_of_moving
        return total_cost
    def get_aggregated_server_capacities(self):
        # Aggregate server capacities by generation and latency sensitivity
        capacity_data = []
        for dc in self.datacenters:
            for server in dc.servers:
                if server.deployed:
                    capacity_data.append({
                        'server_generation': server.generation,
                        'latency_sensitivity': server.latency_sensitivity,
                        'capacity': server.capacity
                    })

        df = pd.DataFrame(capacity_data)
        if not df.empty:
            return df.groupby(['server_generation', 'latency_sensitivity'])['capacity'].sum().unstack(fill_value=0)
        else:
            return pd.DataFrame()

class ProblemData:
    # Constructor that uses load_problem_data to load the data from the csv files
    def __init__(self):
        self.datacenters_df, self.servers_df, self.selling_prices_df = load_problem_data_without_demand()

class InputDemandDataSample:
    def __init__(self):
        self.demand_data_df = load_demand()
        
class InputDemandDataActual:
    def __init__(self, sample_data=InputDemandDataSample(), seed=None):
        np.random.seed(seed)
        self.demand_data_df = get_actual_demand(sample_data.demand_data_df)