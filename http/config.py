from pymongo import MongoClient

WTF_CSRF_ENABLED = True
SECRET_KEY = 'devil in the sky'
DB_NAME = 'w4a'

# DATABASE = MongoClient("mongodb://ant-login7.linux.crg.es:27017")[DB_NAME]
DATABASE = MongoClient()[DB_NAME]
INTROS = DATABASE.intros
OBJECTS = DATABASE.objects
SPACES = DATABASE.chapters
CORE = DATABASE.core
MONGOEXP = "/opt/mongodb/bin/mongoexport"

CSV = set(['csv', 'txt'])

DEBUG = True
PROPAGATE_EXCEPTIONS = True
