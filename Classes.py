import os
import numpy
import pandas as pd
from utils import *
from evaluation import *
import random
import uuid

class Server:
    def __init__(self, givens, generation, data_center, data_center_object, identifier=None):
        self.generation = generation
        self.data_center = data_center
        self.data_center_object = data_center_object
        self.identifier = identifier
        self._givens = givens
        self.deployed = False
        self.operational_time = 0
        self.release_time = self._givens.servers_df[self._givens.servers_df['server_generation'] == self.generation].iloc[0]['release_time']
        s = self.release_time.strip("[]")
        self.identifier = identifier if identifier else uuid.uuid4().hex
        numbers = [int(num) for num in s.split(",")]
        self.release_time_start = numbers[0]
        self.release_time_end = numbers[1]
        self.capacity = self._givens.servers_df[self._givens.servers_df['server_generation'] == self.generation].iloc[0]['capacity']

        # Fetch server data once to avoid repeated calls
        self.server_data = self._givens.servers_df[self._givens.servers_df['server_generation'] == self.generation].iloc[0]
        self.selling_price_data = self._givens.selling_prices_df[self._givens.selling_prices_df['server_generation'] == self.generation]

    @property
    def status(self):
        return {
            "type": self.generation,
            "capacity_used": self.server_data['capacity'] if self.deployed else 0,
            "uptime": self.operational_time,
            "latency_sensitivity": self.data_center_object.latency_sensitivity,
        }

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
        if not self.deployed:
            return None
        # Ensure there is a price row available
        #print("<<<<<<HERE>>>>>>>", self.data_center_object.latency_sensitivity);
        price_row = self.selling_price_data[self.selling_price_data['latency_sensitivity'] == self.data_center_object.latency_sensitivity]
        return price_row['selling_price'].iloc[0] if not price_row.empty else None

    def deploy(self):
        self.deployed = True
        self.operational_time = 0

    def decommission(self):
        self.deployed = False
        #print(f"Server {self.identifier} decommissioned.")

    def automate_remove_dead_cells(self):
        if self.operational_time >= self.life_expectancy:
            self.decommission()

    def update_time_step(self, time):
        self.operational_time += time

    def update(self):
        self.update_time_step(1)
        self.automate_remove_dead_cells()

class DataCenter:
    def __init__(self, givens, identifier):
        self._givens = givens
        self.identifier = identifier
        self.datacenter_data = self._givens.datacenters_df[self._givens.datacenters_df['datacenter_id'] == identifier].iloc[0]
        self.servers = []
        self.empty_slots = self.datacenter_data['slots_capacity']
        self.occupied_slots = 0
        self.total_slots = self.datacenter_data['slots_capacity']
        self.current_time_step = 0
        self.cost_of_energy = self.datacenter_data['cost_of_energy']
        self.latency_sensitivity = self.datacenter_data['latency_sensitivity']

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
    
    def calculate_utilization(self):
        total_capacity = sum(server.capacity for server in self.servers)
        used_capacity = sum(server.capacity for server in self.servers if server.deployed)
        utilization = (used_capacity / total_capacity) * 100 if total_capacity > 0 else 0
        return utilization

    def utilization_summary(self):
        return {
            "data_center_id": self.identifier,
            "total_capacity": sum(server.capacity for server in self.servers),
            "used_capacity": sum(server.capacity for server in self.servers if server.deployed),
            "utilization": self.calculate_utilization(),
            "servers": [server.status for server in self.servers]
        }
    
    def update_time_step(self):
        for server in self.servers:
            server.update()

    def update_slots(self):
        self.update_empty_slots()

    def update_empty_slots(self):
        self.empty_slots = self.total_slots - sum(server.slots_needed for server in self.servers if server.deployed)
    
    def update_occupied_slots(self):
        self.occupied_slots = self.total_slots - self.empty_slots
    
    def update(self):
        self.update_time_step()
        self.update_slots()
        self.update_occupied_slots()

class Inventory:
    def __init__(self, givens):
        self._givens = givens
        self.datacenters = [DataCenter(givens, dc_id) for dc_id in givens.datacenters_df['datacenter_id']]
        self.current_time_step = 0
        self.expenses = ExpensesReturns()
        self.utilization_log = []

    def log_utilization(self):
        for dc in self.datacenters:
            utilization_summary = dc.utilization_summary()
            self.utilization_log.append((self.current_time_step, utilization_summary))
            #print(f"Logged utilization at time step {self.current_time_step} for data center {dc.identifier}: {utilization_summary['utilization']}%")

    def get_all_datacenters_identifiers(self):
        return [dc.identifier for dc in self.datacenters]

    def get_datacenter_by_id(self, identifier):
        """ Returns the datacenter object by its identifier. """
        return next((dc for dc in self.datacenters if dc.identifier == identifier), None)

    def get_total_costs(self):
        # Sum up all the costs tracked in the expenses
        energy_cost = sum(dc.get_total_energy_cost() for dc in self.datacenters)
        maintenance_cost = sum(dc.get_total_maintenance_cost() for dc in self.datacenters)
        return energy_cost + maintenance_cost + self.expenses.get_total_expenses()

    def get_time_step(self):
        return self.current_time_step

    def get_utilization_log(self):
        return self.utilization_log

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

    # def move_server(self, server_type, quantity, source_dc_id, target_dc_id):
    #     source_dc = self.get_datacenter_by_id(source_dc_id)
    #     target_dc = self.get_datacenter_by_id(target_dc_id)
    #     print(f"Attempting to move {quantity} servers of type {server_type} from {source_dc_id} to {target_dc_id}.")
        
    #     if source_dc and target_dc:
    #         servers_to_move = [s for s in source_dc.servers if s.generation == server_type and s.deployed][:quantity]
    #         print(f"Found {len(servers_to_move)} servers to move.")

    #         if len(servers_to_move) == quantity and all(target_dc.empty_slots >= s.slots_needed for s in servers_to_move):
    #             for server in servers_to_move:
    #                 source_dc.servers.remove(server)
    #                 target_dc.servers.append(server)
    #                 server.data_center = target_dc
    #                 print(f"Successfully moved server {server.identifier} to {target_dc_id}.")
    #                 self.expenses.add_moving_cost(server.cost_of_moving)
    #             return True
    #         else:
    #             print(f"Not enough servers or slots. Available slots: {target_dc.empty_slots}")
    #             return False
    #     else:
    #         print(f"Invalid data center IDs: {source_dc_id}, {target_dc_id}")
    #         return False

    def add_server(self, server_generation, quantity, datacenter_id):
        datacenter = self.get_datacenter_by_id(datacenter_id)
        if not datacenter:
            #print(f"Data center DC{datacenter_id} not found.")
            return False

        # Check if the server type exists in the DataFrame
        server_type = f"{server_generation}".removesuffix(f".S{server_generation[-1]}")
        #print(f"<<<BUY>>>Server type: {server_type}")
        filtered_df = self._givens.servers_df[self._givens.servers_df['server_type'] == server_type]
        #print(self._givens.servers_df)
        if filtered_df.empty:
            #print(f"Server type {server_type} not found in the database.")
            return []

        server_info = filtered_df.iloc[0]
        slots_needed = server_info['slots_size']
        #print(f"<<<BUY>>>Slots needed: {slots_needed}")
        
        if datacenter.empty_slots < slots_needed * quantity:
            #print(f"Not enough slots to deploy {quantity} servers of type {server_type} in data center DC{datacenter_id}. Needed: {slots_needed * quantity}, Available: {datacenter.empty_slots}")
            return []
        
        final = []
        for _ in range(quantity):
            details = []
            # Create a new server with a unique UUID and datacenter identifier
            new_server = Server(self._givens, server_generation, f"DC{datacenter_id}", datacenter, uuid.uuid4().hex)
            #print(f"<<<BUY>>><<<<CAPACITY>>>> {new_server.capacity}")
            datacenter.servers.append(new_server)
            datacenter.update_slots()
            new_server.deploy()
            details.append(new_server.identifier)
            details.append(new_server.generation)
            details.append(new_server.data_center)
            details.append(new_server.data_center_object.latency_sensitivity)
            #print(f"Server {new_server.identifier} of type {server_type} deployed in data center DC{datacenter_id}.")
            final.append(details)

        # Update Empty Slots
        #print(f"Empty slots before: {datacenter.empty_slots}")
        datacenter.update_empty_slots()
        #print(f"Empty slots after: {datacenter.empty_slots}")

        return final

    # def remove_server(self, server_type, quantity, datacenter_id):
    #     datacenter = self.get_datacenter_by_id(datacenter_id)
    #     if datacenter:
    #         matching_servers = [server for server in datacenter.servers if server.generation == server_type]
    #         if len(matching_servers) >= quantity:
    #             servers_to_remove = random.sample(matching_servers, quantity)
    #             for server in servers_to_remove:
    #                 datacenter.servers.remove(server)
    #                 server.decommission()
    #             return True  # Indicating success
    #         else:
    #             print(f"Not enough servers of type {server_type} to remove {quantity} units from data center {datacenter_id}.")
    #             return False  # Indicating failure
    #     else:
    #         print(f"Data center not found: {datacenter_id}")
    #         return False  # Indicating failure

    def update(self):
        """ Advance all data centers and their servers one time step forward. """
        self.current_time_step += 1
        for dc in self.datacenters:
            dc.update()
        # Log utilization at this time step
        self.log_utilization()

    def perform_action(self, action_type, *args):
        """ Perform an action and log both expenses and utilization """
        if action_type == 'add_server':
            success = self.add_server(*args)
        elif action_type == 'move_server':
            success = self.move_server(*args)
        else:
            success = False
        # Log expenses
        snapshot = self.expenses.get_snapshot()
        #print(f"Snapshot of expenses at time step {self.current_time_step} after {action_type}: {snapshot}")
        # Log utilization after the action
        self.log_utilization()
        return success  # Return whether the action was successful

class ExpensesReturns:
    def __init__(self):
        self.total_costs = {
            'energy_cost': 0,
            'maintenance_cost': 0,
            'purchase_cost': 0,
            'moving_cost': 0,
            'returns': 0
        }
        self.expense_log = []  # Log of expenses over time

    def add_energy_cost(self, amount):
        self.total_costs['energy_cost'] += amount
        self._log_expense('energy_cost', amount)
        #print(f"Added energy cost: {amount}, Total energy cost: {self.total_costs['energy_cost']}")

    def add_maintenance_cost(self, amount):
        self.total_costs['maintenance_cost'] += amount
        self._log_expense('maintenance_cost', amount)
        #print(f"Added maintenance cost: {amount}, Total maintenance cost: {self.total_costs['maintenance_cost']}")

    def add_purchase_cost(self, amount):
        self.total_costs['purchase_cost'] += amount
        self._log_expense('purchase_cost', amount)
        #print(f"Added purchase cost: {amount}, Total purchase cost: {self.total_costs['purchase_cost']}")

    def add_returns(self, amount):
        self.total_costs['returns'] += amount
        self._log_expense('returns', amount)
        #print(f"Added demand met cost: {amount}, Total demand met cost: {self.total_costs['returns']}")

    def add_moving_cost(self, amount):
        self.total_costs['moving_cost'] += amount
        self._log_expense('moving_cost', amount)
        #print(f"Added moving cost: {amount}, Total moving cost: {self.total_costs['moving_cost']}")

    def _log_expense(self, expense_type, amount):
        """Log the expense with a timestamp or action marker."""
        self.expense_log.append({
            'type': expense_type,
            'amount': amount,
            'total_after_action': self.total_costs[expense_type],
            'timestamp': len(self.expense_log)  # Assuming this represents the time step or action count
        })

    def get_total_expenses(self):
        return sum(self.total_costs.values())

    def summary(self):
        return self.total_costs

    def get_expense_log(self):
        """Returns the entire expense log."""
        return self.expense_log

    def get_snapshot(self):
        """Takes a snapshot of the current total costs."""
        return {key: value for key, value in self.total_costs.items()}

class ProblemData:
    def __init__(self):
        self.datacenters_df, self.servers_df, self.selling_prices_df = load_problem_data_without_demand()
        # print("IMPORTANT: The ProblemData Class should not be changed. It is used to load the data for the problem.")
        # print("Columns and Head of ProblemData: datacenters_df: ")
        # print(self.datacenters_df.columns)
        # print(self.datacenters_df)
        # print("Columns and Head of ProblemData: servers_df: ")
        # print(self.servers_df.columns)
        # print(self.servers_df)
        # print("Columns and Head of ProblemData: selling_prices_df: ")
        # print(self.selling_prices_df.columns)
        # print(self.selling_prices_df)
        # print("IMPORTANT: The ProblemData Class should not be changed. It is used to load the data for the problem.")

class InputDemandDataActual:
    def __init__(self, seed=None):
        np.random.seed(seed)
        self.sample_demand_data_df = load_demand()
        self.demand_data_df = self.adjust_demand_with_hackathon_method(self.sample_demand_data_df)
        # print("IMPORTANT: The InputDemandDataActual AND YOUR ORIGINAL COPIES should not be changed BECAUSE THE AGENT NEEDS TO BE TRAINED ON THE ORIGINAL INPUT FORMAT HOW THEY APPEAR.")
        # print("Columns and Head of Hackathon Input Format demand data: ")
        # print(self.demand_data_df.columns)
        print(self.demand_data_df.head())
        # print("IMPORTANT: The InputDemandDataActual AND YOUR ORIGINAL COPIES should not be changed BECAUSE THE AGENT NEEDS TO BE TRAINED ON THE ORIGINAL INPUT FORMAT HOW THEY APPEAR.")
        '''
        Logic on the other parts of the project need to be adjusted to understand the format of the Hackathon Input Format demand data.
        This Class or the input data should not be changed.
        Change how you handle the data in the other parts of the project with regards to required_capacity.
        '''

    def adjust_demand_with_hackathon_method(self, demand_df):
        return get_actual_demand(demand_df)
    
    def get_demand_for_time_step(self, time_step):
        filtered_df = self.demand_data_df[self.demand_data_df['time_step'] == time_step]
        return filtered_df