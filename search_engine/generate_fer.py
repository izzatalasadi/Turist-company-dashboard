
from cryptography.fernet import Fernet


# to-do make a function for later
key = Fernet.generate_key()
# Write the key to a file
with open("secret.key", "wb") as key_file:
    key_file.write(key)
