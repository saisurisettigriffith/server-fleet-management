import os
from utils import load_problem_data, load_solution
from evaluation import evaluation_function

outputdirectory_if_sample = "output_sample/"
outputdirectory_if_actual = "output_actual/"

'''

USAGE IMPORTANT!!!

1. If you want to test your solution on the sample data, set the outputdirectory to outputdirectory_if_sample...
... and directly run the code because when the evaluators gave us the sample data, they had their own my_solution.py file.
... and they ran the code and gave us the OUTPUT ITSELF "<seed>.json" file.

2. If you want to test your solution on the actual data, set the outputdirectory to outputdirectory_if_actual...
... and ensure that you ran mysolution.py on the actual data and ENSURE YOU GENERATED THE "<seed>.json" files in the output_actual folder FIRST.

'''

outputdirectory = outputdirectory_if_actual

json_files = [f for f in os.listdir(outputdirectory) if f.endswith('.json')]

latest_file = max(json_files, key=lambda f: os.path.getmtime(os.path.join(outputdirectory, f)))

filenumber = int(latest_file.split(".")[0])

solution = load_solution(os.path.join(outputdirectory, f'{filenumber}.json')) # SOLUTION IS PANDAS DATAFRAME CREATED FROM <SEED>.JSON FILE

demand, datacenters, servers, selling_prices = load_problem_data() # ALL THESE VARIABLE ARE PANDAS DATAFRAMES CREATED FROM .CSV FILES IN ./DATA/ FOLDER

score = evaluation_function(solution, demand, datacenters, servers, selling_prices, seed=filenumber) # SCORE IS ANSWER, ENTRY POINT STAGE 1

'''
def evaluation_function(solution, 
                        demand,
                        datacenters,
                        servers,
                        selling_prices,
                        time_steps=get_known('time_steps'), <--- This is not needed, it is already defined in evaluation.py, but you can change it if you want.
                        seed=None,
                        verbose=0): <--- This is not needed, it is already defined in evaluation.py, but you can change it if you want. However, we won't be needing this.

Recap: our solution "123.json", ./data/demand.csv, ./data/datacenters.csv, ./data/servers.csv, ./data/selling_prices.csv are all converted into pandas dataframes...
... and passed in as solution, demand, datacenters, servers, selling_prices RESPECTIVELY to evaluation_function in evaluation.py.
... similarly, from <SEED>.json file, we extracted the seed number and passed it as seed to evaluation_function in evaluation.py.
... Two more parameters time_steps and verbose are not needed, they are already defined in evaluation.py, but you can change them if you want.

Entry Point 1, We are getting "score" as the answer, THIS IS THE FINAL OBJECTIVE, TO MAXIMIZE THIS SCORE.
'''

print(f'Solution score: {score}')