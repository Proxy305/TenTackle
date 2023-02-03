import os, sys, json

config = {}

if os.path.isfile("config.json"):

    '''
    Use external config first
    '''
    with open("config.json") as config_file:
        config = json.load(config_file)
else:

    '''
    If external config not found, fallback to embedded config
    '''

    config = {
        "axis":{
            "y_unit": "MPa",
            "y_scaling": 1,
            "x_unit": "",
            "x_scaling": 1
        },
        "font":{
            "family" : "Monospace",
            "weight" : "bold",
            "size"   : 12
        },
        "regression":{
            "start": 0.001,
            "end": 0.01           
        },
        "integration":{
            "method": "simps"
        }
    }