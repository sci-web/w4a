from werkzeug.security import check_password_hash


class Auth():

    def __init__(self, email, access, author):
        self.email = email
        self.access = access
        self.author = author

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.email)

    def author(self):
        return unicode(self.author)

    def access(self):
        return unicode(self.access)

    @staticmethod
    def validate_login(password_hash, password):
        return check_password_hash(password_hash, password)
