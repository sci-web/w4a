from werkzeug.security import check_password_hash


class Auth():

    def __init__(self, email, access, first_name, surname):
        self.email = email
        self.access = access
        self.name = name

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.email)

    def name(self):
        return unicode(self.name)

    def access(self):
        return unicode(self.access)

    @staticmethod
    def validate_login(password_hash, password):
        return check_password_hash(password_hash, password)
