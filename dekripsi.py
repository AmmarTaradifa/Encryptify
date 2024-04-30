from cryptography.fernet import Fernet
import os

# Function to read the encryption key from a file
def read_key(file_path):
    key_file_path = file_path
    try:
        with open(key_file_path, 'rb') as key_file:
            return key_file.read()
    except FileNotFoundError:
        print(f"Key file '{key_file_path}' not found.")
        return None

# Function to decrypt a file using the provided key
def decrypt_file(file_path, key):
    if key:
        fernet = Fernet(key)
        with open(file_path, 'rb') as encrypted_file:
            encrypted_data = encrypted_file.read()
        decrypted_data = fernet.decrypt(encrypted_data)
        decrypted_file_path = file_path[:-len('.encrypted')]
        with open(decrypted_file_path, 'wb') as decrypted_file:
            decrypted_file.write(decrypted_data)
        print(f'File "{file_path}" decrypted successfully.')
    else:
        print("Encryption key not found.")

# Example usage:
if __name__ == "__main__":

    file_to_decrypt = input("Enter the path of the file to decrypt: ")
    file_key = input("Enter key file : ")
    key = read_key(file_key)
    if key:
            decrypt_file(file_to_decrypt, key)