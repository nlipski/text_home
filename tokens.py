from twilio.rest import Client

SECRET_KEY = os.environ['SECRET_KEY']
GOOGLE_API_KEY = os.environ['GOOGLE_API_KEY']
TWILIO_ACCOUNT = os.environ['TWILIO_ACCOUNT']
TWILIO_TOKEN = os.environ['TWILIO_TOKEN']

client = Client(TWILIO_ACCOUNT, TWILIO_TOKEN)