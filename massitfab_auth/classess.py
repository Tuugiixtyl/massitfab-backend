import datetime
import jwt
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

class Creator:
    def __init__(self, id):
        self.id = id

    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def __str__(self):
        return str(self.id)


class User:
    def __init__(self, username, password):
        self.username = username
        self.password = password

    def authenticate(self, username, password):
        return self.username == username and self.password == password

    def generate_token(self, secret_key):
        payload = {
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1),
            'iat': datetime.datetime.utcnow(),
            'sub': self.username,
            'test': 'sandy'
        }
        return jwt.encode(payload, secret_key, algorithm='HS256')
    
# # create an instance of the User class
# user = User('testuser', 'testpassword')

# # generate a token with a custom payload
# token = user.generate_token('secretkey')

# # obtain a token using the TokenObtainPairSerializer
# serializer = TokenObtainPairSerializer(data={'username': 'testuser', 'password': 'testpassword'})
# serializer.is_valid(raise_exception=True)
# token = serializer.validated_data['access']

# # modify the token payload
# decoded_token = jwt.decode(token, 'secretkey', algorithms=['HS256'])
# decoded_token['custom_payload'] = 'some value'
# modified_token = jwt.encode(decoded_token, 'secretkey', algorithm='HS256')