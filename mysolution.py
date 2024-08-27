from seeds import known_seeds
from utils import load_problem_data, save_solution
import application as app

outputdirectory = "output_actual/"
seeds = known_seeds('training')

x = 1
for seed in seeds:
    if (x == 0):
        break
    demand, datacenters, servers, selling_prices = load_problem_data()
    solution_json = app.solution_function(demand, datacenters, servers, selling_prices, seed, debugging=True)
    # SAVE YOUR SOLUTION
    save_solution(solution_json, f'{outputdirectory}/{seed}.json')
    x -= 1