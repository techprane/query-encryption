from fastapi import FastAPI
import os
from pymongo import MongoClient
from dotenv import load_dotenv
from pymongo.encryption_options import AutoEncryptionOpts
from pymongo.encryption import ClientEncryption
from bson.codec_options import CodecOptions
from bson.binary import STANDARD

load_dotenv()


app = FastAPI()

kms_provider_name = "local"


uri = os.getenv("MONGODB_URI")

key_vault_database_name = "encryption"
key_vault_collection_name = "__keyVault"
key_vault_namespace = f"{key_vault_database_name}.{key_vault_collection_name}"
encrypted_database_name = "medicalRecords"
encrypted_collection_name = "patients"

# Create a Customer Master Key. You must create a Customer Master Key (CMK) to perform Queryable Encryption.
path = "customer-master-key.txt"
file_bytes = os.urandom(96)
with open(path, "wb") as file:
    file.write(file_bytes)
    
path = "./customer-master-key.txt"
with open(path, "rb") as file:
    local_master_key = file.read()
    kms_provider_credentials = {
        "local": {
            "key": local_master_key
        },
    }

# The path to your Automatic Encryption Shared Library
auto_encryption_options = AutoEncryptionOpts(
    kms_provider_credentials,
    key_vault_namespace,
    # crypt_shared_lib_path=shared_lib_path, 
    # Path to your Automatic Encryption Shared Library
    mongocryptd_uri=os.getenv("mongodb://localhost:27020"),
    mongocryptd_bypass_spawn=False,
    mongocryptd_spawn_path="mongocryptd",
)

# Create a Client to Set Up an Encrypted Collection
encrypted_client = MongoClient(uri, auto_encryption_opts=auto_encryption_options)

# Specify Fields to Encrypt
encrypted_fields_map = {
    "fields": [
        {
            "path": "patientRecord.ssn",
            "bsonType": "string",
            "queries": [{"queryType": "equality"}]
        },
        {
            "path": "patientRecord.billing",
            "bsonType": "object",
        }
    ]
}

client_encryption = ClientEncryption(
    kms_providers=kms_provider_name,
    key_vault_namespace=key_vault_namespace,
    key_vault_client=encrypted_client,
    codec_options=CodecOptions(uuid_representation=STANDARD)
)

customer_master_key_credentials = {"local": {"key": local_master_key}}

client_encryption.create_encrypted_collection(
    encrypted_client[encrypted_database_name],
    encrypted_collection_name,
    encrypted_fields_map,
    kms_provider_credentials, 
    customer_master_key_credentials,
)

encrypted_collection = encrypted_client[encrypted_database_name][encrypted_collection_name]
@app.post("/user")
async def create_user(patientName: str, patientId: int, patientRecord: object):
    insert_id = encrypted_collection.insert_one({"patientName": patientName, "patientId": patientId, "patientRecord": patientRecord}).inserted_id
    return {"message": "User created successfully", "insert_id": insert_id}
