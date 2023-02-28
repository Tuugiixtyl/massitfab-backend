import secrets
import string

alphabet = string.ascii_letters + string.digits + string.punctuation
key = ''.join(secrets.choice(alphabet) for i in range(54))
print(key)