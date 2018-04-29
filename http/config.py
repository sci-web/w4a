from pymongo import MongoClient
import uuid, os


WTF_CSRF_ENABLED = True
# SECRET_KEY = 'devil in the sky'
DB_NAME = 'w4a'

DATABASE = MongoClient()[DB_NAME]
INTROS = DATABASE.intros
INTROS_EN = DATABASE.intros_en
OBJECTS = DATABASE.objects
SPACES = DATABASE.chapters
SPACES_EN = DATABASE.chapters_en
CORE = DATABASE.core
CONTACTS = DATABASE.contacts

# for export name of vars = collections: i.e. chapters = collection chapters in DATABASE

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

DEBUG = True
PROPAGATE_EXCEPTIONS = True
