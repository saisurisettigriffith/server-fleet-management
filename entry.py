from seeds import known_seeds
from utils import save_solution
import application as app
from Classes import *

outputdirectory = "output_actual/"
seeds = known_seeds('training')

selected_seed = 8501

x = 1
for s in seeds:
    if (x == 0):
        break
    givens = ProblemData()
    actual_demand = InputDemandDataActual(seed = selected_seed)
    inventory = Inventory(givens)
    time_steps_send = 168
    print(givens)
    print(actual_demand)
    print(inventory)
    solution_json = app.solution_function(givens, actual_demand, seed = selected_seed, time_steps=time_steps_send, debugging=True)
    # SAVE YOUR SOLUTION
    save_solution(solution_json, f'{outputdirectory}/{s}.json')
    x -= 1