from seeds import known_seeds
from utils import save_solution
import application as app
from Classes import *

outputdirectory = "output_actual/"
seeds = known_seeds('training')

x = 1
for seed in seeds:
    if (x == 0):
        break
    givens = ProblemData()
    sample_demand = InputDemandDataSample()
    actual_demand = InputDemandDataActual(sample_data=sample_demand, seed=42)
    inventory = Inventory(givens)
    print(givens)
    print(sample_demand)
    print(actual_demand)
    print(inventory)
    solution_json = app.solution_function(givens, actual_demand, time_steps=3, debugging=True)
    # SAVE YOUR SOLUTION
    save_solution(solution_json, f'{outputdirectory}/{seed}.json')
    x -= 1