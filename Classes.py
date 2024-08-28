import pandas as pd
from utils import *
from evaluation import *

class Server:
    def __init__(self, givens, generation, latency, data_center, identifier):
        self.generation = generation
        self.latency_sensitivity = latency
        self.data_center = data_center
        self.moved_this_step = False
        self.identifier = identifier
        # Using properties to dynamically fetch data when needed
        self._givens = givens

    @property
    def server_data(self):
        # Dynamically fetches server data
        return self._givens.servers_df[self._givens.servers_df['server_generation'] == self.generation].iloc[0]

    @property
    def selling_price_data(self):
        # Dynamically fetches selling price data
        return self._givens.selling_prices_df[self._givens.selling_prices_df['server_generation'] == self.generation]

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
        # Dynamic fetching based on latency sensitivity
        price_row = self.selling_price_data[self.selling_price_data['latency_sensitivity'] == self.latency_sensitivity]
        return price_row['selling_price'].iloc[0] if not price_row.empty else None

    def age_server(self):
        if self.deployed:
            self.operational_time += 1
            if self.operational_time >= self.life_expectancy:
                self.decommission()

    def deploy(self):
        self.deployed = True
        self.remaining_life = self.life_expectancy
        self.operational_time = 0

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
        self._givens = givens
        self.identifier = identifier
        self.datacenter_data = self._givens.datacenters_df[self._givens.datacenters_df['datacenter_id'] == identifier].iloc[0]
        self.servers = []  # List of Server objects

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
        if self.can_add_server(server):
            self.servers.append(server)
            server.deploy()
            print(f"Server {server.generation} added to {self.identifier}")
        else:
            print("Not enough slots to add this server")

    def dismiss_servers(self):
        """ Method to remove servers that are no longer operational due to end of life. """
        for server in list(self.servers):
            if server.remaining_life <= 0:
                self.remove_server(server)

    def remove_server(self, server):
        if server in self.servers:
            self.servers.remove(server)
            server.decommission()
            print(f"Server {server.generation} removed from {self.identifier}")

    def can_add_server(self, server):
        return self.empty_slots >= server.slots_needed

    def has_capacity_for_servers(self, required_slots):
        """
        Check if the data center has enough empty slots to accommodate a given number of slots.
        
        Args:
            required_slots (int): Number of slots required for new servers.

        Returns:
            bool: True if there is enough capacity, False otherwise.
        """
        return self.empty_slots >= required_slots

    def simulate_time_step(self):
        for server in self.servers:
            server.age_server()

    def __str__(self):
        return f"DataCenter {self.identifier}: Capacity {self.slots_capacity}, Empty Slots {self.empty_slots}"


# class DataCenter:
#     def __init__(self, givens, identifier):
#         self._givens = givens
#         self.identifier = identifier
#         self.datacenter_data = self._givens.datacenters_df[self._givens.datacenters_df['datacenter_id'] == identifier].iloc[0]
#         self.servers = []  # List of Server objects

#     @property
#     def slots_capacity(self):
#         return self.datacenter_data['slots_capacity']

#     @property
#     def cost_of_energy(self):
#         return self.datacenter_data['cost_of_energy']

#     @property
#     def latency_sensitivity(self):
#         return self.datacenter_data['latency_sensitivity']

#     @property
#     def filled_slots(self):
#         return sum(server.slots_needed for server in self.servers if server.deployed)

#     @property
#     def empty_slots(self):
#         return self.slots_capacity - self.filled_slots

#     def add_server(self, server):
#         if self.can_add_server(server):
#             self.servers.append(server)
#             server.deploy()
#             print(f"Server {server.generation} added to {self.identifier}")
#         else:
#             print("Not enough slots to add this server")

#     def dismiss_servers(self):
#         """ Method to remove servers that are no longer operational due to end of life. """
#         for server in list(self.servers):
#             if server.remaining_life <= 0:
#                 self.remove_server(server)

#     def remove_server(self, server):
#         if server in self.servers:
#             self.servers.remove(server)
#             server.decommission()
#             print(f"Server {server.generation} removed from {self.identifier}")

#     def can_add_server(self, server):
#         return self.empty_slots >= server.slots_needed

#     def simulate_time_step(self):
#         for server in self.servers:
#             server.age_server()

#     def __str__(self):
#         return f"DataCenter {self.identifier}: Capacity {self.slots_capacity}, Empty Slots {self.empty_slots}"


class Inventory:
    def __init__(self, givens):
        self._givens = givens
        self.datacenters = [DataCenter(givens, dc_id) for dc_id in self._givens.datacenters_df['datacenter_id']]

    def update_servers(self):
        """ Synchronizes the state of all servers across datacenters, checking end-of-life and updating capacities. """
        for datacenter in self.datacenters:
            for server in datacenter.servers[:]:  # Copy to avoid modification during iteration
                if server.remaining_life <= 0:
                    datacenter.remove_server(server)
                else:
                    server.update()

    def simulate_time_step_servers(self):
        """ Advances the simulation by one time step for each server. """
        for datacenter in self.datacenters:
            datacenter.simulate_time_step()

    def get_datacenter_by_id(self, identifier):
        """ Returns the datacenter object by its identifier. """
        return next((dc for dc in self.datacenters if dc.identifier == identifier), None)
    
    def get_total_energy_cost(self):
        total_cost = 0
        for server in self.servers:
            if server.deployed:
                total_cost += server.energy_consumption * self.cost_of_energy
        return total_cost
    
    def get_total_costs(self):
        energy_cost = self.get_total_energy_cost()
        maintenance_cost = sum(dc.get_total_maintenance_cost() for dc in self.datacenters)
        purchase_cost = sum(dc.get_total_purchase_cost() for dc in self.datacenters)
        moving_cost = sum(dc.get_total_moving_cost() for dc in self.datacenters)
        return {
            'energy_cost': energy_cost,
            'maintenance_cost': maintenance_cost,
            'purchase_cost': purchase_cost,
            'moving_cost': moving_cost
        }

    # def predictive_scaling(self):
    #     predicted_load = self.predict_load()
    #     self.adjust_server_operations(predicted_load)
    
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
            aggregated = df.groupby('server_generation')['capacity'].sum()
            return aggregated.to_frame('capacity')  # Convert to DataFrame explicitly
        else:
            return pd.DataFrame(columns=['capacity'])  # Ensure it's always a DataFrame



    def __str__(self):
        """ Provides a string representation of the inventory for debugging purposes. """
        return f"Inventory with Datacenters: {[dc.identifier for dc in self.datacenters]}"

class ProblemData:
    def __init__(self):
        self.datacenters_df, self.servers_df, self.selling_prices_df = load_problem_data_without_demand()

    def __str__(self):
        return f"ProblemData: {len(self.datacenters_df)} datacenters, {len(self.servers_df)} servers, {len(self.selling_prices_df)} selling prices"

class InputDemandDataSample:
    def __init__(self):
        self.demand_data_df = load_demand()

    def __str__(self):
        return f"InputDemandDataSample: {len(self.demand_data_df)} rows of demand data"

class InputDemandDataActual:
    def __init__(self, sample_data=InputDemandDataSample(), seed=None):
        np.random.seed(seed)
        self.demand_data_df = self.adjust_demand_with_hackathon_method(sample_data.demand_data_df)

    def adjust_demand_with_hackathon_method(self, demand_df):
        return get_actual_demand(demand_df)

    def __str__(self):
        return f"InputDemandDataActual: {len(self.demand_data_df)} rows of adjusted demand data"
    
# Assuming you have historical demand data loaded and a method to predict future demand
# class DemandForecaster:
#     def __init__(self, historical_data):
#         self.historical_data = historical_data

#     def predict_demand(self, future_periods):
#         # Implement your forecasting model here
#         # This could be a simple time series model or a more complex machine learning model
#         pass
#     def plan_capacity(self, demand_forecasts):
#         # Calculate required capacity for each server type and data center
#         # Make decisions on server purchases or re-allocations
#         pass
#     def automate_deployment(self, capacity_plan):
#         # Automatically deploy or re-allocate servers according to the planned capacity
#         # Could interface with virtualization management platforms or use API calls to manage physical servers
#         pass