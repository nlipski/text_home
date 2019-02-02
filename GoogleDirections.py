import requests
import json


from inner_functions import get_locations, check_location, google_api_key

incoming_text = "I am in Kingston, ON and want to drive to toronto."

api_key = "AIzaSyBUlQyHBJsv-GBooA_64cyA_9q-abYSehE"
dataa = {"document": {
    "type": "PLAIN_TEXT",
    "content": incoming_text},
    "encodingType":"UTF16",
    }

r=requests.post("https://language.googleapis.com/v1beta2/documents:analyzeEntities?key=" + google_api_key, json=dataa)
testing = json.loads(r.text)
testbla = testing["entities"]
toLoc = ""
fromLoc = ""
mode = "driving"
print(len(r.text))
for entities in testbla:
    if entities["type"] == "LOCATION":
        index = int(entities["mentions"][0]["text"]["beginOffset"])
        reference = incoming_text[index-3:index]
        if reference == "to ":
            print("TO B " + entities["name"])
            toLoc = entities["name"]
            toLoc = check_location(toLoc)
            print("this is the checked location",toLoc)
        elif fromLoc == "":
            print("FROM B" + entities["name"])
            fromLoc = entities["name"]
            fromLoc = check_location(fromLoc)
            print("this is the checked from ",fromLoc)
    elif entities["type"] == "OTHER":
        if entities["name"] == "driving" or entities["name"] == "drive":
            mode = "driving"
        if entities["name"] == "walking" or entities["name"] == "walk":
            mode = "walking"
        if entities["name"] == "bicycling" or entities["name"] == "bike":
            mode = "bicycling"
        if entities["name"] == "transit":
            mode = "transit"



#print(r.text)


r=requests.get("https://maps.googleapis.com/maps/api/directions/json?origin=" + fromLoc + "&destination=" + toLoc + "&mode=" + mode + "&key=" + google_api_key+"&region=ca")
testing = json.loads(r.text)
something = testing["routes"]
some = something[0]
steps = some["legs"][0]["steps"]


for step in steps:
   print("For " + step["distance"]["text"] + " " + step["html_instructions"])
