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
        self.failure_rates = self.sample_failure_rates()
        
        if self.debugging:
            self.debug_initial_data()

    def debug_initial_data(self):
        # Print DataFrame heads to check initial rows
        print("Servers DataFrame:\n", self.givens.servers_df.head())
        print("Datacenters DataFrame:\n", self.givens.datacenters_df.head())
        print("Selling Prices DataFrame:\n", self.givens.selling_prices_df.head())
        print("Demand Data DataFrame:\n", self.input_actual.head())

        # Check for null values
        print("Null values in servers_df:\n", self.givens.servers_df.isnull().sum())
        print("Null values in datacenters_df:\n", self.givens.datacenters_df.isnull().sum())
        print("Null values in selling_prices_df:\n", self.givens.selling_prices_df.isnull().sum())
        print("Null values in input_actual:\n", self.input_actual.isnull().sum())

        # Check data types
        print("Data types in servers_df:\n", self.givens.servers_df.dtypes)
        print("Data types in datacenters_df:\n", self.givens.datacenters_df.dtypes)
        print("Data types in selling_prices_df:\n", self.givens.selling_prices_df.dtypes)
        print("Data types in input_actual:\n", self.input_actual.dtypes)

    # Existing methods...  

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
        
        self.current_normalized_lifespan = self.calculate_normalized_lifespan()
        print(f"Normalized Lifespan at time step {current_time_step}: {self.current_normalized_lifespan}")
        self.current_profit = self.calculate_profit()
        print(f"Profit at time step {current_time_step}: {self.current_profit}")
        self.current_utilization = self.calculate_utilization(current_time_step)
        print(f"Utilization at time step {current_time_step}: {self.current_utilization}")
        self.make_a_choice(current_time_step)
        self.dismiss_servers()

    def make_a_choice(self, current_time_step):
        self.handle_demand(current_time_step)
        print("Making a choice...")

    # This is just an example and should be replaced with non-brute force logic
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
                    # Buy servers if there is a deficiency in capacity
                    self.buy_servers(demand['server_generation'], latency_sensitivity, needed_capacity - total_available_capacity)
                elif needed_capacity < total_available_capacity:
                    # Calculate excess capacity
                    excess_capacity = total_available_capacity - needed_capacity
                    # Efficiently manage excess servers if the excess is significant
                    self.manage_excess_servers(demand['server_generation'], latency_sensitivity, excess_capacity)

    def manage_excess_servers(self, generation, latency_sensitivity, excess_capacity):
        if excess_capacity <= 0:
            return  # No excess capacity to manage

        # Iterate through datacenters to find and move excess servers if needed
        for dc in self.inventory.datacenters:
            excess_servers = [
                server for server in dc.servers
                if server.generation == generation and server.latency_sensitivity == latency_sensitivity and server.deployed
            ]
            excess_capacity_dc = sum(server.capacity for server in excess_servers)
            
            if excess_capacity_dc > 0:
                target_dc = self.find_target_datacenter(dc, generation, latency_sensitivity, excess_capacity_dc)
                if target_dc:
                    moved_capacity = self.move_servers(dc, target_dc, generation, latency_sensitivity, excess_capacity_dc)
                    print(f"Moved {moved_capacity} units of capacity from {dc.identifier} to {target_dc.identifier}")
                    excess_capacity -= moved_capacity
                if excess_capacity <= 0:
                    break  # Stop if no more excess capacity needs to be managed

    def find_target_datacenter(self, source_dc, generation, latency_sensitivity, required_capacity):
        # Placeholder logic to find a target datacenter that needs more capacity
        # This could be based on current load, proximity, energy cost, etc.
        for dc in self.inventory.datacenters:
            if dc != source_dc and dc.has_capacity_for_servers(required_capacity):
                potential_addition = sum(
                    server.capacity for server in dc.servers
                    if server.generation == generation and server.latency_sensitivity == latency_sensitivity and not server.deployed
                )
                # Check if after adding potential new servers the dc can handle the load
                if dc.empty_slots + potential_addition >= required_capacity:
                    return dc
        return None

    def move_servers(self, from_dc, to_dc, generation, latency_sensitivity, capacity_to_move):
        """
        Moves servers from one data center to another to handle increased demand or excess capacity.
        
        Args:
            from_dc (DataCenter): The data center from which servers are moved.
            to_dc (DataCenter): The data center to which servers are moved.
            generation (str): The generation of servers to be moved.
            latency_sensitivity (str): The latency sensitivity category of the servers.
            capacity_to_move (int): The additional capacity needed at the destination data center.
        """
        # Identify servers that can be moved
        movable_servers = [
            server for server in from_dc.servers
            if server.generation == generation and server.latency_sensitivity == latency_sensitivity and server.deployed
        ]
        
        moved_capacity = 0
        servers_moved = []

        # Move servers until the needed capacity is met or no more movable servers
        for server in movable_servers:
            if moved_capacity >= capacity_to_move:
                break
            
            # Move server from from_dc to to_dc
            from_dc.remove_server(server)
            to_dc.add_server(server)
            servers_moved.append(server)
            moved_capacity += server.capacity

            print(f"Moved server {server.identifier} from {from_dc.identifier} to {to_dc.identifier}. Added capacity: {server.capacity}")
            
        # Check if the movement met the demand
        if moved_capacity < capacity_to_move:
            print(f"Warning: Not enough servers moved to meet the demand. Moved {moved_capacity}, needed {capacity_to_move}.")
            # Optionally, move servers back if operation needs to be atomic and fully satisfying
            for server in servers_moved:
                to_dc.remove_server(server)
                from_dc.add_server(server)
            print("Reverted server movements due to insufficient capacity.")
        else:
            print(f"Successfully moved {moved_capacity} capacity to {to_dc.identifier}.")

        return moved_capacity

    def get_demand(self, generation, latency_sensitivity):
        # Accessing demand data based on server generation and a specific latency sensitivity
        try:
            current_demand = self.input_actual.loc[
                self.input_actual['server_generation'] == generation, latency_sensitivity
            ].sum()
            return current_demand
        except KeyError as e:
            print(f"Column not found: {latency_sensitivity}, available columns: {self.input_actual.columns}")
            return 0

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

    ### b. The servers' normalized lifespan \( L \)

    # This is defined in Eq. 3, for all the servers of the fleet \( S \), as the ratio of the operating time \( x_s \), that is the number of time-steps since the server \( s \) has been deployed, to \( \hat{x}_s \), that is the server life expectancy. It should be noted that after \( \hat{x}_s \) time-steps, the server must be dismissed.

    # \[
    # L = \frac{1}{|S|} \times \sum_{s \in S} \frac{x_s}{\hat{x}_s} \tag{3}
    # \]

    def calculate_normalized_lifespan(self):
        total_lifespan_ratio = 0
        deployed_servers_count = 0

        for datacenter in self.inventory.datacenters:
            for server in datacenter.servers:
                if server.deployed:
                    lifespan_ratio = server.operational_time / server.life_expectancy
                    total_lifespan_ratio += lifespan_ratio
                    deployed_servers_count += 1

        normalized_lifespan = (total_lifespan_ratio / deployed_servers_count) if deployed_servers_count > 0 else 0
        return normalized_lifespan

    ### c. The profit \( P \)

    # This is defined in Eq. 4 as the difference between the revenue \( R \) and the cost \( C \).

    # \[
    # P = R - C \tag{4}
    # \]

        # The revenue \( R \) is defined in Eq. 4.1 as the sum of the revenue generated by the capacity \( Z_{i,g}^f \) deployed to satisfy the demand \( D_{i,g} \) for a certain latency sensitivity \( i \) and server generation \( g \). The revenue equals the met demand \( \text{min}(Z_{i,g}^f, D_{i,g}) \) times the price \( p_{i,g} \). As in Eq. 2, \( f \) represents the failure rate. Selling prices are stored in the file `./data/selling_prices.csv`.

        # \[
        # R = \sum_{i \in I} \sum_{g \in G} \text{min}(Z_{i,g}^f, D_{i,g}) \times p_{i,g} \tag{4.1}
        # \]

        # The cost \( C \) is defined in Eq. 4.2 as the sum of the cost of all servers \( S_k \) deployed across all data-centers \( K \). The cost of a server is equal to the sum of the server purchase price \( r_s \), the cost of the server energy consumption \( e_s \), and the server maintenance cost \( \alpha(\cdot) \). If the server is moved from one data-center to another it is necessary to account for the moving cost \( m \). The server energy consumption, as defined in Eq. 4.2.1, is equal to the product of the server energy consumption \( \hat{e}_s \) times the cost of energy \( h_k \) that is the cost of energy at the data-center \( k \) where the server \( s \) is deployed. Finally, the maintenance cost is calculated according to a function \( \alpha(\cdot) \) defined in Eq. 4.2.2. This function takes as input: the server operating time \( x_s \), the server life expectancy \( \hat{x}_s \), and average maintenance fee \( b_s \).

        # \[
        # C = \sum_{k \in K} \sum_{s \in S_k} \begin{cases} 
        # r_s + e_s + \alpha(x_s) & \text{if } x_s = 1 \\
        # e_s + \alpha(x_s) + m & \text{if action = move} \\
        # e_s + \alpha(x_s) & \text{otherwise}
        # \end{cases} \tag{4.2}
        # \]

        # \[
        # e_s = \hat{e}_s \times h_k \tag{4.2.1}
        # \]        

        # \[
        # \alpha(x_s) = b_s \times \left[ 1 + \frac{1.5 x_s}{\hat{x}_s} \times \log_2\left(\frac{1.5 x_s}{\hat{x}_s}\right) \right] \tag{4.2.2}
        # \]

    def calculate_profit(self):
        total_revenue = 0
        total_cost = 0

        for datacenter in self.inventory.datacenters:
            for server in datacenter.servers:
                if server.deployed:
                    # Ensure server.capacity and demand are compatible types
                    demand = min(float(server.capacity), float(self.get_demand(server.generation, server.latency_sensitivity)))
                    revenue = demand * float(server.selling_price)  # Ensure selling_price is a float
                    total_revenue += revenue

                    # Continue with further calculations ensuring all are numeric types
                    energy_cost = float(server.energy_consumption) * float(datacenter.cost_of_energy)
                    if server.operational_time == 1:
                        total_cost += server.purchase_price + energy_cost + server.maintenance_fee
                    else:
                        total_cost += energy_cost + server.maintenance_fee
                    if server.moved_this_step:
                        total_cost += server.cost_of_moving

        profit = total_revenue - total_cost
        return profit

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

    def buy_servers(self, generation, latency_sensitivity, additional_capacity_needed):
        print(f"Trying to meet additional demand of {additional_capacity_needed} with new servers.")
        # Using a simplified approach to get the first server of the requested generation
        server_data = self.givens.servers_df[self.givens.servers_df['server_generation'] == generation].iloc[0]
        slots_needed = server_data['slots_size']
        purchase_limit = 10  # This could be adjusted based on strategic needs

        for datacenter in self.inventory.datacenters:
            purchase_count = 0
            while additional_capacity_needed > 0 and datacenter.empty_slots >= slots_needed and purchase_count < purchase_limit:
                new_server = Server(self.givens, generation, datacenter.identifier, datacenter)
                if datacenter.can_add_server(new_server):
                    datacenter.add_server(new_server)
                    additional_capacity_needed -= new_server.capacity
                    additional_capacity_needed = max(0, additional_capacity_needed)
                    purchase_count += 1
                    print(f"Added one {generation} server to {datacenter.identifier}; remaining demand: {additional_capacity_needed}.")
                if additional_capacity_needed <= 0:
                    break

            if additional_capacity_needed <= 0 or purchase_count == purchase_limit:
                break

        if additional_capacity_needed > 0:
            print(f"Warning: Not enough capacity to meet the demand for {generation} servers with {latency_sensitivity} sensitivity after {purchase_limit} purchases. Missing capacity: {additional_capacity_needed}")

    def move_servers(self, from_dc, to_dc, generation, latency_sensitivity, additional_capacity_needed):
        """
        Moves servers from one data center to another to handle increased demand.
        
        Args:
            from_dc (DataCenter): The data center from which servers are moved.
            to_dc (DataCenter): The data center to which servers are moved.
            generation (str): The generation of servers to be moved.
            latency_sensitivity (str): The latency sensitivity category of the servers.
            additional_capacity_needed (int): The additional capacity needed at the destination data center.
        """
        # Identify servers that can be moved
        movable_servers = [
            server for server in from_dc.servers
            if server.generation == generation and server.latency_sensitivity == latency_sensitivity and server.deployed
        ]
        
        moved_capacity = 0
        servers_moved = []

        # Move servers until the needed capacity is met or no more movable servers
        for server in movable_servers:
            if moved_capacity >= additional_capacity_needed:
                break
            
            # Move server from from_dc to to_dc
            from_dc.remove_server(server)
            to_dc.add_server(server)
            servers_moved.append(server)
            moved_capacity += server.capacity

            print(f"Moved server {server.identifier} from {from_dc.identifier} to {to_dc.identifier}. Added capacity: {server.capacity}")
            
        # Check if the movement met the demand
        if moved_capacity < additional_capacity_needed:
            print(f"Warning: Not enough servers moved to meet the demand. Moved {moved_capacity}, needed {additional_capacity_needed}.")
            # Optionally, move servers back if operation needs to be atomic and fully satisfying
            for server in servers_moved:
                to_dc.remove_server(server)
                from_dc.add_server(server)
            print("Reverted server movements due to insufficient capacity.")
        else:
            print(f"Successfully moved {moved_capacity} capacity to {to_dc.identifier}.")

        return moved_capacity

    def age_servers(self):
        for datacenter in self.inventory.datacenters:
            datacenter.age_servers()

    ### a. The servers' utilization \( U \)

    # This is defined in Eq. 2 as the ratio of the demand \( D_{i,g} \) for a certain latency sensitivity \( i \) and server generation \( g \) to the capacity \( Z_{i,g}^f \) deployed to satisfy such demand. As the demand could be higher than the capacity (and vice versa), in the numerator, we use the met demand \( \text{min}(Z_{i,g}^f, D_{i,g}) \). Here, \( f \) represents the failure rate that is sampled from a truncated Weibull distribution with \( f \in [0.05, 0.1] \). Specifically, the capacity \( Z_{i,g}^f \) is equal to the sum of the capacities of all servers of generation \( g \) deployed across all data-centers with latency sensitivity \( i \) adjusted by the failure rate \( f \) as follows: \( Z_{i,g}^f = (1 - f) \times Z_{i,g} \). Also, servers' utilization is averaged across the total number of latency sensitivity and server generation pairs \( |I \times G| \). Finally, it should be noted that, at each time-step \( t \), the demand is stochastic as outlined in Eq. 2.1.

    # \[
    # U = \frac{1}{|I \times G|} \times \sum_{i \in I} \sum_{g \in G} \frac{\text{min}(Z_{i,g}^f, D_{i,g})}{Z_{i,g}} \tag{2}
    # \]

    # \[
    # D_{i,g,t} = D_{i,g,t-1} + \mathcal{N} \tag{2.1}
    # \]

def solution_function(givens, input_actual, time_steps=168, debugging=False):
    simulation = Simulation(givens, input_actual, time_steps, debugging)
    simulation.start_simulation()
    return [{'message': 'Simulation Completed Successfully'}]