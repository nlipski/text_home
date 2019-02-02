from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from flask import Flask, request, session
import googlemaps
from datetime import datetime


app = Flask(__name__)
app.config.from_object(__name__)

gmaps = googlemaps.Client(key='AIzaSyBUlQyHBJsv-GBooA_64cyA_9q-abYSehE')

account = "AC07e3abdcc5ca8ab68816022080fb9331"
token = "e50d782ec9b8c284db8ab0f537ed0fbc"
client = Client(account, token)


@app.route("/sms", methods=['GET', 'POST'])
def sms_reply():

    resp_body="Sucks to suck"

    body = request.values.get('Body', None)
    resp = MessagingResponse()

    now = datetime.now()
    directions_result = gmaps.directions("Sydney Town Hall",
                                         "Parramatta, NSW",
                                         mode="transit",
                                         departure_time=now)
    print (directions_result)
    if body != "I'm lost":
        resp_body = "Hmmm didn't get it"

    resp.message(resp_body)

    return str(resp)


if __name__ == "__main__":
    app.run(debug=True)
print(message.sid)