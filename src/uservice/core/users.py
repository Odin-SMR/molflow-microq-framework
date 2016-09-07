from passlib.apps import custom_app_context as pwd_context
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)
from flask.ext.httpauth import HTTPBasicAuth
auth = HTTPBasicAuth()


def get_user_db(user_db, app):
    class User(user_db.Model):
        __tablename__ = 'users'
        id = user_db.Column(user_db.Integer, primary_key=True)
        username = user_db.Column(user_db.String(32), index=True)
        password_hash = user_db.Column(user_db.String(128))

        def hash_password(self, password):
            self.password_hash = pwd_context.encrypt(password)

        def verify_password(self, password):
            return pwd_context.verify(password, self.password_hash)

        def generate_auth_token(self, expiration=600):
            s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
            return s.dumps({'id': self.id})

        @staticmethod
        def verify_auth_token(token):
            s = Serializer(app.config['SECRET_KEY'])
            try:
                data = s.loads(token)
            except SignatureExpired:
                return None    # valid token, but expired
            except BadSignature:
                return None    # invalid token
            user = User.query.get(data['id'])
            return user

    return User
