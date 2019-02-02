import requests
import json

google_api_key = "AIzaSyBUlQyHBJsv-GBooA_64cyA_9q-abYSehE"

def get_locations(incoming_text):
    data={"document":{"type":"PLAIN_TEXT","content":incoming_text},"encodingType":"UTF16"}

    r=requests.post("https://language.googleapis.com/v1beta2/documents:analyzeEntities?key=" + google_api_key, json=data)
    testing = json.loads(r.text)
    testbla = testing["entities"]

    toLoc = ""
    fromLoc = ""
    mode = "driving"
    for entities in testbla:
        if entities["type"] == "LOCATION":
            index = int(entities["mentions"][0]["text"]["beginOffset"])
            reference = incoming_text[index - 3:index]
            if reference == "to ":
                toLoc = entities["name"]
            else:
                fromLoc = entities["name"]
        elif entities["type"] == "OTHER":
            print(entities["name"])
            if entities["name"] == "driving" or entities["name"] == "drive":
                mode = "driving"
            if entities["name"] == "walking" or entities["name"] == "walk":
                mode = "walking"
            if entities["name"] == "bicycling" or entities["name"] == "bike":
                mode = "bicycling"
            if entities["name"] == "transit" or entities["name"] == "train" or entities["name"] == "bus":
                mode = "transit"

    return [fromLoc, toLoc, mode]

def parse_directions(fromLoc, toLoc, mode):

    response=requests.get("https://maps.googleapis.com/maps/api/directions/json?origin=" + fromLoc + "&destination=" + toLoc + "&mode=" + mode + "&key=" + google_api_key +"&region=ca")

    unparsed=response.json()

    time = unparsed["routes"][0]["legs"][0]["duration"]["text"]
    to =unparsed["routes"][0]["legs"][0]["end_address"]
    start =unparsed["routes"][0]["legs"][0]["start_address"]
    directions = []
    for step in unparsed["routes"][0]["legs"][0]["steps"]:
        direction = step["html_instructions"].replace('<b>','').replace('</b>','')
        directions.append(direction)
    returntext= "Here are your instructions from",(start),"to" ,(to), ". It will take",(time),  (directions)


    return returntext

def autocomplete_location(location):
    r = requests.get(
        "https://maps.googleapis.com/maps/api/place/autocomplete/json?key=" + google_api_key + "&input=" + location+"&region=ca")
    testing = json.loads(r.text)
    if (testing['status'] == 'ZERO_RESULTS'):
        return ''
    description = testing["predictions"][0]["description"]
    return description

def check_location(location):
    r = requests.get(
        "https://maps.googleapis.com/maps/api/place/findplacefromtext/json?key=" + google_api_key + "&input=" + location + "&inputtype=textquery"+"&region=ca"+"&fields=geometry,formatted_address,place_id")
    testing = json.loads(r.text)
    print("this is testing geo",testing)
    candidates = testing["candidates"]

    questionAddress = ''
    if(testing["status"] == "ZERO_RESULTS"):
        autoAddress = autocomplete_location(location)
        questionAddress = autoAddress
    else:
        for place in candidates:
            r = requests.get(
                "https://maps.googleapis.com/maps/api/place/details/json?key=" + google_api_key + "&placeid=" + place["place_id"])
            ploop = json.loads(r.text)
            questionAddress = ploop["result"]["formatted_address"]

    return questionAddress
