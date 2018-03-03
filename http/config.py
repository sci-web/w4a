from pymongo import MongoClient

WTF_CSRF_ENABLED = True
SECRET_KEY = 'devil in the sky'
DB_NAME = 'w4a'

# DATABASE = MongoClient("mongodb://ant-login7.linux.crg.es:27017")[DB_NAME]
DATABASE = MongoClient()[DB_NAME]
INTROS = DATABASE.intros
INTROS_EN = DATABASE.intros_en
OBJECTS = DATABASE.objects
SPACES = DATABASE.chapters
SPACES_EN = DATABASE.chapters_en
CORE = DATABASE.core
MONGOEXP = "/opt/mongodb/bin/mongoexport"
GEOCITY = "/home/jes/Code/w4a/geo/GeoLite2-City_20180206/GeoLite2-City.mmdb"

CSV = set(['csv', 'txt'])

DEBUG = True
PROPAGATE_EXCEPTIONS = True
