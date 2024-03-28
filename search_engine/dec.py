from cryptography.fernet import Fernet

def decrypt_data(encrypted_data,key):
    fernet = Fernet(key)
    
    # Decrypt data
    decrypted_data = fernet.decrypt(encrypted_data).decode()
    
    return decrypted_data

def main():
    # Prompt the user to input the encrypted message
    encrypted_message = input("Enter the encrypted message: ")
    key = input("Enter the Encryption key: ")
    
    # Since the encrypted message is expected to be in bytes, we need to convert it from string
    # If your encrypted message was encoded in base64 for storage or transmission, you'd need to decode it first
    encrypted_message_bytes = bytes(encrypted_message, 'utf-8')
    
    try:
        # Attempt to decrypt the message
        decrypted_message = decrypt_data(encrypted_message_bytes,key)
        print("Decrypted message:", decrypted_message)
    except Exception as e:
        print("An error occurred during decryption:", str(e))

if __name__ == "__main__":
    main()

