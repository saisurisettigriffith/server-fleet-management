from seeds import known_seeds
from utils import save_solution
import application as app
from Classes import *

outputdirectory = "output_actual/"
seeds = known_seeds('training')

x = 1
for s in seeds:
    if (x == 0):
        break
    givens = ProblemData()
    actual_demand = InputDemandDataActual(seed = s)
    inventory = Inventory(givens)
    print(givens)
    print(actual_demand)
    print(inventory)
    solution_json = app.solution_function(givens, actual_demand, time_steps=5, debugging=True)
    # SAVE YOUR SOLUTION
    save_solution(solution_json, f'{outputdirectory}/{s}.json')
    x -= 1