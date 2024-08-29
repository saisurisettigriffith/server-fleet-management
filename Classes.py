import os
import numpy
import pandas as pd
from utils import *
from evaluation import *

class Server:
    def __init__(self, givens, generation, latency, data_center, identifier):
        self.generation = generation
        self.latency_sensitivity = latency
        self.data_center = data_center
        self.identifier = identifier
        self._givens = givens
        self.deployed = False
        self.operational_time = 0

        # Fetch server data once to avoid repeated calls
        self.server_data = self._givens.servers_df[self._givens.servers_df['server_generation'] == self.generation].iloc[0]
        self.selling_price_data = self._givens.selling_prices_df[self._givens.selling_prices_df['server_generation'] == self.generation]

    @property
    def status(self):
        return {
            "type": self.generation,
            "capacity_used": self.server_data['capacity'] if self.deployed else 0,
            "uptime": self.operational_time,
            "latency_sensitivity": self.latency_sensitivity
        }

    @property
    def capacity(self):
        return self.server_data['capacity']

    @property
    def slots_needed(self):
        return self.server_data['slots_size']

    @property
    def energy_consumption(self):
        return self.server_data['energy_consumption']

    @property
    def purchase_price(self):
        return self.server_data['purchase_price']

    @property
    def life_expectancy(self):
        return self.server_data['life_expectancy']

    @property
    def cost_of_moving(self):
        return self.server_data['cost_of_moving']

    @property
    def maintenance_fee(self):
        return self.server_data['average_maintenance_fee']

    @property
    def selling_price(self):
        # Ensure there is a price row available
        price_row = self.selling_price_data[self.selling_price_data['latency_sensitivity'] == self.latency_sensitivity]
        return price_row['selling_price'].iloc[0] if not price_row.empty else None

    def age_server(self):
        if self.deployed:
            self.operational_time += 1
            if self.operational_time >= self.life_expectancy:
                self.decommission()

    def deploy(self):
        self.deployed = True
        self.operational_time = 0

    def decommission(self):
        self.deployed = False
        print(f"Server {self.identifier} decommissioned.")

    def update_life(self, time):
        self.operational_time += time
        if self.operational_time >= self.life_expectancy:
            self.decommission()

    def update(self):
        self.update_life(1)

class DataCenter:
    def __init__(self, givens, identifier):
        self._givens = givens
        self.identifier = identifier
        self.datacenter_data = self._givens.datacenters_df[self._givens.datacenters_df['datacenter_id'] == identifier].iloc[0]
        self.servers = []

    def deploy_server(self, server_type, quantity):
        slots_needed = sum(self._givens.servers_df.loc[self._givens.servers_df['server_type'] == server_type, 'slots_size']) * quantity
        available_slots = self.datacenter_data['slots_capacity'] - sum(s.slots_needed for s in self.servers if s.deployed)
        if slots_needed <= available_slots:
            for _ in range(quantity):
                new_server = Server(self._givens, server_type, self.datacenter_data['latency_sensitivity'], self, f"{self.identifier}_new_{server_type}")
                self.servers.append(new_server)
                new_server.deploy()
                print(f"Deployed server {server_type} in data center {self.identifier}")
        else:
            print(f"Not enough slots to deploy {quantity} servers of type {server_type}. Available slots: {available_slots}, needed: {slots_needed}")

    def get_total_maintenance_cost(self):
        return sum(server.maintenance_fee for server in self.servers if server.deployed)

    def get_total_energy_cost(self):
        return sum(server.energy_consumption for server in self.servers if server.deployed) * self.datacenter_data['cost_of_energy']

    def summary(self):
        return {
            "total_capacity": sum(server.capacity for server in self.servers),
            "available_capacity": sum(server.capacity for server in self.servers if not server.deployed),
            "energy_cost": self.get_total_energy_cost(),
            "servers": [server.status for server in self.servers]
        }

    @property
    def slots_capacity(self):
        return self.datacenter_data['slots_capacity']

    @property
    def cost_of_energy(self):
        return self.datacenter_data['cost_of_energy']

    @property
    def latency_sensitivity(self):
        return self.datacenter_data['latency_sensitivity']

    @property
    def filled_slots(self):
        return sum(server.slots_needed for server in self.servers if server.deployed)

    @property
    def empty_slots(self):
        return self.slots_capacity - self.filled_slots

    def add_server(self, server):
        if self.empty_slots >= server.slots_needed:
            self.servers.append(server)
            server.deploy()
            print(f"Server {server.generation} added to {self.identifier}")
        else:
            print("Error: Not enough slots to add this server")

    def remove_server(self, server):
        if server in self.servers:
            server.decommission()
            self.servers.remove(server)
            print(f"Server {server.generation} removed from {self.identifier}")
        else:
            print("Error: Server not found in data center")

    def update(self):
        for server in self.servers:
            server.update()

class Inventory:
    def __init__(self, givens):
        self._givens = givens
        self.datacenters = [DataCenter(givens, dc_id) for dc_id in givens.datacenters_df['datacenter_id']]
        self.delta_moving_cost = 0
        self.delta_purchase_cost = 0
        self.current_moving_cost = 0
        self.current_purchase_cost = 0

    def get_datacenter_by_id(self, identifier):
        """ Returns the datacenter object by its identifier. """
        return next((dc for dc in self.datacenters if dc.identifier == identifier), None)

    def get_total_costs(self):
        energy_cost = sum(dc.get_total_energy_cost() for dc in self.datacenters)
        maintenance_cost = sum(dc.get_total_maintenance_cost() for dc in self.datacenters)
        return {
            'energy_cost': energy_cost,
            'maintenance_cost': maintenance_cost,
            'purchase_cost': self.current_purchase_cost,
            'moving_cost': self.current_moving_cost
        }

    def get_aggregated_server_capacities(self):
        """ Aggregates server capacities by server generation across all datacenters. """
        capacity_data = []
        for dc in self.datacenters:
            for server in dc.servers:
                if server.deployed:
                    capacity_data.append({
                        'server_generation': server.generation,
                        'capacity': server.capacity
                    })
        df = pd.DataFrame(capacity_data)
        if not df.empty:
            return df.groupby('server_generation')['capacity'].sum().to_frame('capacity')
        return pd.DataFrame(columns=['capacity'])

    def move_server(self, server_id, source_dc_id, target_dc_id):
        source_dc = self.get_datacenter_by_id(source_dc_id)
        target_dc = self.get_datacenter_by_id(target_dc_id)
        if source_dc and target_dc:
            server = next((s for s in source_dc.servers if s.identifier == server_id), None)
            if server and target_dc.empty_slots >= server.slots_needed:
                source_dc.servers.remove(server)
                target_dc.servers.append(server)
                server.data_center = target_dc
                self.delta_moving_cost += server.cost_of_moving
                self.current_moving_cost += server.cost_of_moving
                print(f"Server {server_id} moved from {source_dc_id} to {target_dc_id}.")
            else:
                print(f"Not enough slots or server not found.")
        else:
            print("Invalid data center ID provided.")

    def add_server(self, server, datacenter_id, moving=False):
        datacenter = self.get_datacenter_by_id(datacenter_id)
        if (server < 4):
            gen = "CPU"+"."+"S"+server+1
        else:
            gen = "GPU"+"."+"S"+server-3
        if datacenter and datacenter.empty_slots >= server.slots_needed:
            server_new = Server(self._givens, gen, datacenter.latency_sensitivity, datacenter, f"{server}_{numpy.random.randint(1000)}")
            datacenter.servers.append(server_new)
            server_new.deploy()
            if not moving:
                self.delta_purchase_cost += server_new.purchase_price
                self.current_purchase_cost += server_new.purchase_price
            print(f"Server Type {gen} added to {datacenter_id}")
        else:
            print(f"Not enough slots or data center not found for adding server {gen}.")

    def remove_server(self, server_id, datacenter_id):
        datacenter = self.get_datacenter_by_id(datacenter_id)
        if datacenter:
            server = next((s for s in datacenter.servers if s.identifier == server_id), None)
            if server:
                datacenter.servers.remove(server)
                server.decommission()
                print(f"Server {server_id} removed from {datacenter_id}.")
            else:
                print("Server not found in specified data center.")
        else:
            print("Data center not found.")

    def update(self):
        """ Advances all data centers and their servers one time step forward. """
        for dc in self.datacenters:
            dc.update()

    def __str__(self):
        return f"Inventory with Datacenters: {[dc.identifier for dc in self.datacenters]}"

class ProblemData:
    def __init__(self):
        self.datacenters_df, self.servers_df, self.selling_prices_df = load_problem_data_without_demand()
        print("IMPORTANT: The ProblemData Class should not be changed. It is used to load the data for the problem.")
        print("Columns and Head of ProblemData: datacenters_df: ")
        print(self.datacenters_df.columns)
        print(self.datacenters_df)
        print("Columns and Head of ProblemData: servers_df: ")
        print(self.servers_df.columns)
        print(self.servers_df)
        print("Columns and Head of ProblemData: selling_prices_df: ")
        print(self.selling_prices_df.columns)
        print(self.selling_prices_df)
        print("IMPORTANT: The ProblemData Class should not be changed. It is used to load the data for the problem.")

class InputDemandDataActual:
    def __init__(self, seed=None):
        np.random.seed(seed)
        self.sample_demand_data_df = load_demand()
        self.demand_data_df = self.adjust_demand_with_hackathon_method(self.sample_demand_data_df)
        print("IMPORTANT: The InputDemandDataActual AND YOUR ORIGINAL COPIES should not be changed BECAUSE THE AGENT NEEDS TO BE TRAINED ON THE ORIGINAL INPUT FORMAT HOW THEY APPEAR.")
        print("Columns and Head of Hackathon Input Format demand data: ")
        print(self.demand_data_df.columns)
        print(self.demand_data_df.head())
        print("IMPORTANT: The InputDemandDataActual AND YOUR ORIGINAL COPIES should not be changed BECAUSE THE AGENT NEEDS TO BE TRAINED ON THE ORIGINAL INPUT FORMAT HOW THEY APPEAR.")
        '''
        Logic on the other parts of the project need to be adjusted to understand the format of the Hackathon Input Format demand data.
        This Class or the input data should not be changed.
        Change how you handle the data in the other parts of the project with regards to required_capacity.
        '''

    def adjust_demand_with_hackathon_method(self, demand_df):
        return get_actual_demand(demand_df)