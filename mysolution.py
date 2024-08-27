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
    input_actual = InputDemandDataActual(seed=seed)
    solution_json = app.solution_function(givens, input_actual, time_steps=4, debugging=True)
    # SAVE YOUR SOLUTION
    save_solution(solution_json, f'{outputdirectory}/{seed}.json')
    x -= 1