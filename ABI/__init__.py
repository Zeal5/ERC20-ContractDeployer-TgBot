import json 
import os
current_dir = os.path.dirname(__file__)

with open(f"{current_dir}/BasuFactory.json", 'r') as f:
    factory = json.load(f)
    factory_abi = factory['abi']

