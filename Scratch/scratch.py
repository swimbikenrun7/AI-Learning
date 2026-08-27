import json

roast = {
    "date": "10/28/1987",
    "bean": "Misty Valley",
    "green_weight": "205",
    "finished_weight": "180",
    "roast_time": "495",
    "first_crack": "405"
}

json_string = json.dump(roast)

parsed_data = json.load(json_string)
