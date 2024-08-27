import utils as utl
import application as app
import seeds as sds
import pandas as pd

class Server:
    def __init__(self, data_center, generation, servers_df, selling_prices_df):
        server_data = servers_df[servers_df['server_generation'] == generation].iloc[0]
        selling_price_data = selling_prices_df[selling_prices_df['server_generation'] == generation]
        
        self.identifier = f"{generation}_{data_center.identifier}"  # Example to create a unique identifier
        self.generation = generation
        self.server_type = server_data['server_type']
        self.capacity = server_data['capacity']
        self.slots_size = server_data['slots_size']
        self.energy_consumption = server_data['energy_consumption']
        self.purchase_price = server_data['purchase_price']
        self.life_expectancy = server_data['life_expectancy']
        self.remaining_life = self.life_expectancy  # Assuming starts at full life expectancy
        self.cost_of_moving = server_data['cost_of_moving']
        self.maintenance_fee = server_data['average_maintenance_fee']
        self.operational_time = 0
        self.deployed = False
        self.data_center = data_center
        self.release_time_bounds = eval(server_data['release_time'])
        
        self.sell_price_low = selling_price_data[selling_price_data['latency_sensitivity'] == 'low']['selling_price'].iloc[0]
        self.sell_price_medium = selling_price_data[selling_price_data['latency_sensitivity'] == 'medium']['selling_price'].iloc[0]
        self.sell_price_high = selling_price_data[selling_price_data['latency_sensitivity'] == 'high']['selling_price'].iloc[0]

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


# # THIS IS CALLED DDSS
# demand, datacenters, servers, selling_prices = utl.load_problem_data()
# # THIS IS CALLED DDSS

# class Server:
#     def __init__(self, data_center, generation):
#         '''
#         server_generation,server_type,release_time,purchase_price,slots_size,energy_consumption,capacity,life_expectancy,cost_of_moving,average_maintenance_fee
#         CPU.S1,CPU,"[1,60]",15000,2,400,60,96,1000,288
#         CPU.S2,CPU,"[37,96]",16000,2,460,75,96,1000,308
#         CPU.S3,CPU,"[73,132]",19500,2,800,120,96,1000,375
#         CPU.S4,CPU,"[109,168]",22000,2,920,160,96,1000,423
#         GPU.S1,GPU,"[1,72]",120000,4,3000,8,96,1000,2310
#         GPU.S2,GPU,"[49,120]",140000,4,3000,8,96,1000,2695
#         GPU.S3,GPU,"[97,168]",160000,4,4200,8,96,1000,3080
#         '''
#         self.identifier = identifier # We need to identify servers, we need a function to generate unique identifiers
#         self.generation = generation # should be gathered from DDSS
#         self.server_type = server_type # should be gathered from DDSS <- dependent on the server type or generation
#         self.capacity = capacity # should be gathered from DDSS <- dependent on the server type or generation
#         self.slots_size = slots_size # should be gathered from DDSS <- dependent on the server type or generation
#         self.energy_consumption = energy_consumption # should be gathered from DDSS <- dependent on the server type or generation
#         self.purchase_price = purchase_price # should be gathered from DDSS <- dependent on the server type or generation
#         self.life_expectancy = 96
#         self.remaining_life = 96
#         self.cost_of_moving = 1000
#         self.average_maintenance_fee = maintenance_fee # should be gathered from DDSS <- dependent on the server type or generation
#         self.operational_time = 0  # Time since deployment <- Unsure what holding action means and whether there can be time where server is not deployed but installed
#         self.deployed = False
#         self.release_time_left_bound, self.release_time_right_bound = var, var # should be computed from identifier of server because for each server, the time when it can be purchased is different - use DDSS
#         self.data_center = data_center
#         self.sell_price_low = forlow # should be computed from identifier of server because for each server, the selling price for three levels is different - use DDSS
#         self.sell_price_medium = formedium # should be computed from identifier of server because for each server, the selling price for three levels is different - use DDSS
#         self.sell_price_high = forhigh # should be computed from identifier of server because for each server, the selling price for three levels is different - use DDSS

#     def age_server(self):
#         if self.deployed:
#             self.operational_time += 1
#             if self.operational_time >= self.life_expectancy:
#                 self.decommission()

#     def deploy(self, data_center):
#         self.deployed = True
#         self.data_center = data_center

#     def decommission(self):
#         self.deployed = False
#         # Additional cleanup logic here


# class DataCenter:
#     def __init__(self, identifier):
#         '''
#         datacenter_id,cost_of_energy,latency_sensitivity,slots_capacity
#         DC1,0.25,low,25245
#         DC2,0.35,medium,15300
#         DC3,0.65,high,7020
#         DC4,0.75,high,8280
#         '''
#         self.identifier = identifier # We need to specify whether it is DC1, DC2, DC3, or DC4
#         self.slots_capacity = slots_capacity # should be gathered from DDSS <- dependent on the datacenter identifier
#         self.filled_slots = 0
#         self.empty_slots = self.slots_capacity # should be gathered from DDSS <- dependent on the datacenter identifier
#         self.cost_of_energy = cost_of_energy # should be gathered from DDSS <- dependent on the datacenter identifier
#         self.latency_sensitivity = latency_sensitivity # should be gathered from DDSS <- dependent on the datacenter identifier
#         self.servers = []  # List of Servers Installed

#     def add_server(self, server):
#         if self.can_add_server(server):
#             self.servers.append(server)
#             server.deploy(self)
#             print(f"Server {server.generation} added to {self.identifier}")
#         else:
#             print("Not enough slots to add this server")

#     def remove_server(self, server):
#         if server in self.servers:
#             self.servers.remove(server)
#             server.decommission()
#             print(f"Server {server.generation} removed from {self.identifier}")

#     def can_add_server(self, server):
#         total_slots_used = sum(s.slots_size for s in self.servers if s.deployed)
#         return total_slots_used + server.slots_size <= self.slots_capacity

#     def simulate_time_step(self):
#         for server in self.servers:
#             server.age_server()

class DataCenter:
    def __init__(self, identifier, datacenters_df):
        datacenter_data = datacenters_df[datacenters_df['datacenter_id'] == identifier].iloc[0]
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
            self.filled_slots += server.slots_size
            self.empty_slots = self.slots_capacity - self.filled_slots
            print(f"Server {server.generation} added to {self.identifier}")
        else:
            print("Not enough slots to add this server")

    def remove_server(self, server):
        if server in self.servers:
            self.servers.remove(server)
            server.decommission()
            self.filled_slots -= server.slots_size
            self.empty_slots = self.slots_capacity - self.filled_slots
            print(f"Server {server.generation} removed from {self.identifier}")

    def can_add_server(self, server):
        total_slots_used = sum(s.slots_size for s in self.servers if s.deployed)
        return total_slots_used + server.slots_size <= self.slots_capacity

    def simulate_time_step(self):
        for server in self.servers:
            server.age_server()

class Inventory:
    def __init__(self, datacenters_df, servers_df, selling_prices_df):
        # Loading the data might typically happen outside of this class, but we include it here for completeness
        self.datacenters_df = datacenters_df
        self.servers_df = servers_df
        self.selling_prices_df = selling_prices_df
        self.datacenters = [DataCenter(dc_id, datacenters_df) for dc_id in datacenters_df['datacenter_id']]
        self.servers = []  # List of all servers in all datacenters

    def update_servers(self):
        # This method would be used to sync servers across datacenters if needed
        for dc in self.datacenters:
            for server in dc.servers:
                if server not in self.servers:
                    self.servers.append(server)

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

    def simulate_time_step(self):
        # Simulate a time step across all datacenters
        for dc in self.datacenters:
            dc.simulate_time_step()

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

    def get_total_revenue(self, demand_data):
        # Calculate total revenue based on demand and selling prices
        total_revenue = 0
        for dc in self.datacenters:
            for server in dc.servers:
                if server.deployed:
                    demand = demand_data.get((server.generation, dc.latency_sensitivity), 0)
                    met_demand = min(server.capacity, demand)
                    selling_price = self.selling_prices_df.loc[(self.selling_prices_df['server_generation'] == server.generation) & 
                                                               (self.selling_prices_df['latency_sensitivity'] == dc.latency_sensitivity), 'selling_price'].iloc[0]
                    total_revenue += met_demand * selling_price
        return total_revenue

    def get_utilization(self, demand_data):
        # Calculate total utilization for all servers across all datacenters
        total_utilization = 0
        count = 0
        for dc in self.datacenters:
            for server in dc.servers:
                if server.deployed:
                    demand = demand_data.get((server.generation, dc.latency_sensitivity), 0)
                    met_demand = min(server.capacity, demand)
                    total_utilization += met_demand / server.capacity if server.capacity > 0 else 0
                    count += 1
        return total_utilization / count if count > 0 else 0