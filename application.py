import numpy as np
import pandas as pd
from Classes import *
from scipy.stats import truncweibull_min

class Simulation:
    def __init__(self, givens, input_actual, time_steps, debugging):
        # CONSTANTS or PROPERTIES!!!
        self.givens = givens
        self.demand = input_actual
        self.end_time_step = time_steps
        self.debugging = debugging
        self.inventory = Inventory(givens)
        # Variables
        self.current_demand = None
        self.current_time_step = 0

    def start_simulation(self):
        while self.current_time_step < self.end_time_step:
            self.current_time_step += 1
            # Action
            self.buy()
            # Update Inventory according to: 1. Inreased Time Step and 2. Actions
            self.inventory.update()

    def buy(self):
        current_demand_data = self.demand.get_demand_for_time_step(self.current_time_step)
        self.current_demand = current_demand_data
        print(self.current_demand)


def solution_function(givens, input_actual, time_steps=168, debugging=False):
    simulation = Simulation(givens, input_actual, time_steps, debugging)
    simulation.start_simulation()
    return [{'message': 'Simulation Completed Successfully'}]