import requests
import json

incoming_text="I am in Kingston and want to go to Disneyland"

api_key="AIzaSyBUlQyHBJsv-GBooA_64cyA_9q-abYSehE"
dataa={"document":{"type":"PLAIN_TEXT","content":incoming_text},"encodingType":"UTF16"}

r=requests.post("https://language.googleapis.com/v1beta2/documents:analyzeEntities?key=" + api_key, json=dataa)
testing = json.loads(r.text)
testbla = testing["entities"]
loc1 = ""
loc2 = ""
for entities in testbla:
    if entities["type"] == "LOCATION":
        if loc1 == "":
            loc1 = entities["name"]
        elif loc2 == "":
            loc2 = entities["name"]


r=requests.get("https://maps.googleapis.com/maps/api/directions/json?origin=" + loc1 + "&destination=" + loc2 + "&key=" + api_key)
testing = json.loads(r.text)

something = testing["routes"]
some = something[0]
steps = some["legs"][0]["steps"]


for step in steps:
    print("For " + step["distance"]["text"] + " " + step["html_instructions"])
