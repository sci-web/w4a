from pymongo import MongoClient, errors
import uuid, os
import logging
logging.basicConfig(filename='./controls.log',level=logging.DEBUG, format='%(asctime)s %(message)s')

LOGS = logging
# errors.ServerSelectionTimeoutMS = 5
WTF_CSRF_ENABLED = True
SECRET_KEY = 'devil in the sky'
DB_NAME = 'w4a'
DB = MongoClient()[DB_NAME]
INTROS = DB.intros
INTROS_EN = DB.intros_en
INTROS_HE = DB.intros_he
OBJECTS = DB.objects
SPACES = DB.chapters
SPACES_EN = DB.chapters_en
SPACES_HE = DB.chapters_he
CORE = DB.core
CONTACTS = DB.contacts

# for export name of vars = collections: i.e. chapters = collection chapters in DB

MAIL_SERVER = os.getenv('MAIL_SERVER', 'localhost')
MAIL_PORT = int(os.getenv('MAIL_PORT', '25'))
MAIL_USE_SSL = int(os.getenv('MAIL_USE_SSL', False))
MAIL_USERNAME = os.getenv('MAIL_USERNAME', 'noreply@server')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@server')
EMAIL_1 = 'toni.amantonio@gmail.com'
EMAIL_2 = 'jescid@gmail.com'

# captcha
SECRET_KEY = str(uuid.uuid4())
CAPTCHA_ENABLE = True
CAPTCHA_NUMERIC_DIGITS = 7
SESSION_TYPE = 'mongodb'
SESSION_MONGODB_DB = 'w4a'

MONGOEXP = "/opt/mongodb/bin/mongoexport"
GEOCITY = "/home/jes/Code/w4a/geo/GeoLite2-City_20180206/GeoLite2-City.mmdb"

CSV = set(['csv', 'txt'])


# DEBUG = True
# PROPAGATE_EXCEPTIONS = True
