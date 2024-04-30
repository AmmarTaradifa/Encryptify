from cryptography.fernet import Fernet
import os

# Function to generate a unique encryption key for a file
def generate_key(file_path):
    key = Fernet.generate_key()
    key_file_path = file_path + '.key'
    with open(key_file_path, 'wb') as key_file:
        key_file.write(key)
    return key

# Function to read the encryption key from a file
def read_key(file_path):
    key_file_path = file_path + '.key'
    try:
        with open(key_file_path, 'rb') as key_file:
            return key_file.read()
    except FileNotFoundError:
        print(f"Key file '{key_file_path}' not found.")
        return None

# Function to encrypt a file using the provided key
def encrypt_file(file_path, key):
    if key:
        fernet = Fernet(key)
        with open(file_path, 'rb') as file:
            data = file.read()
        encrypted_data = fernet.encrypt(data)
        with open(file_path + '.encrypted', 'wb') as encrypted_file:
            encrypted_file.write(encrypted_data)
        print(f'File "{file_path}" encrypted successfully.')
    else:
        print("Encryption key not found.")

# Example usage:
if __name__ == "__main__":
    file_to_encrypt = input("Enter the path of the file to encrypt: ")

    # Generate or read the encryption key
    # key = read_key(file_to_encrypt)
    # if not key:
    key = generate_key(file_to_encrypt)

    # Encrypt the file
    encrypt_file(file_to_encrypt, key)
