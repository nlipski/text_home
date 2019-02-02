import requests
import json




def check_location(location):

    r = requests.get(
        "https://maps.googleapis.com/maps/api/place/findplacefromtext/json?key=" + api_key + "&input=" + location + "&inputtype=textquery");
    testing = json.loads(r.text)
    candidates = testing["candidates"]

    if(len(candidates) < 1):
        autoAddress = autocomplete_location(location)
        print("Did you mean to type " + autoAddress + "?")
        questionAddress = autoAddress
    else:
        for place in candidates:
            r = requests.get(
                "https://maps.googleapis.com/maps/api/place/details/json?key=" + api_key + "&placeid=" + place["place_id"])
            ploop = json.loads(r.text)
            questionAddress = ploop["result"]["formatted_address"]
            print("Did you mean " + questionAddress + "?")

    return questionAddress

def autocomplete_location(location):
    r = requests.get(
        "https://maps.googleapis.com/maps/api/place/autocomplete/json?key=" + api_key + "&input=" + location);
    testing = json.loads(r.text)

    descr = testing["predictions"][0]["description"]
    return descr

incoming_text = "I am in Kingston, ON and want to walk to Disneyland, FL."

api_key = "AIzaSyBUlQyHBJsv-GBooA_64cyA_9q-abYSehE"
dataa = {"document": {
    "type": "PLAIN_TEXT",
    "content": incoming_text},
    "encodingType":"UTF16"}
r=requests.post("https://language.googleapis.com/v1beta2/documents:analyzeEntities?key=" + api_key, json=dataa)
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
            print(toLoc)
        elif fromLoc == "":
            print("FROM B" + entities["name"])
            fromLoc = entities["name"]
            fromLoc = check_location(fromLoc)
            print(fromLoc)
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


r=requests.get("https://maps.googleapis.com/maps/api/directions/json?origin=" + fromLoc + "&destination=" + toLoc + "&mode=" + mode + "&key=" + api_key)
testing = json.loads(r.text)
something = testing["routes"]
some = something[0]
steps = some["legs"][0]["steps"]


for step in steps:
   print("For " + step["distance"]["text"] + " " + step["html_instructions"])
