from fastapi import FastAPI
from pydantic import BaseModel
from bson.codec_options import CodecOptions
from pymongo import MongoClient
from pymongo.encryption import Algorithm, ClientEncryption, QueryType
from pymongo.encryption_options import AutoEncryptionOpts
import os

app = FastAPI()

local_master_key = os.urandom(96)
kms_providers = {"local": {"key": local_master_key}}
key_vault_namespace = "keyvault.datakeys"
mongodb_url="mongodb+srv://<user's-database-name>:<user's-database-password>@mycluster.wa2cj.mongodb.net/?retryWrites=true&w=majority&appName=MyCluster"
key_vault_client = MongoClient(mongodb_url)

client_encryption = ClientEncryption(
    kms_providers, key_vault_namespace, key_vault_client, CodecOptions()
)

key_vault = key_vault_client["keyvault"]["datakeys"]
key_vault.drop()

# Ensure that two data keys cannot share the same keyAltName.
key_vault.create_index(
    "keyAltNames",
    unique=True,
    partialFilterExpression={"keyAltNames": {"$exists": True}},
)

key1_id = client_encryption.create_data_key("local", key_alt_names=["firstName"])
key2_id = client_encryption.create_data_key("local", key_alt_names=["lastName"])
key3_id = client_encryption.create_data_key("local", key_alt_names=["passportNumber"])

encrypted_fields_map = {
    "default.encryptedCollection": {
        "fields": [
            {
             	"path": "firstName",
                "bsonType": "string",
                "keyId": key1_id,
                "queries": [{"queryType": "equality"}],
            },
            {
             	"path": "lastName",
                "bsonType": "string",
                "keyId": key2_id,
                 "queries": [{"queryType": "equality"}],

            },
            {

              "path": "passportNumber",
              "bsonType": "string",
              "keyId": key3_id,
              "queries": [{"queryType": "equality"}]
            },
	],
    }
}
auto_encryption_opts = AutoEncryptionOpts(
    kms_providers,
    key_vault_namespace,
    encrypted_fields_map=encrypted_fields_map,
    crypt_shared_lib_path="/usr/local/lib/mongo_crypt_v1.so"

)

print(f"Auto Encryption Options: {auto_encryption_opts}")

client = MongoClient(mongodb_url,auto_encryption_opts=auto_encryption_opts)
client.default.drop_collection("encryptedCollection")
coll = client.default.create_collection("encryptedCollection")

print(f"MongoClient Issue: {client}")
print(f"Encrypted Conllection: {coll}")

class User(BaseModel):
    firstName: str
    lastName: str
    passportNumber: str

def user_helper(user: dict) -> dict:
    return {
         "id": str(user["_id"]),
         "fisrtName": user["firstName"],
         "lastName": user["lastName"],
         "passportNumber": user["passportNumber"]
}


@app.get("/get-user/{passportNumber}")
def get_user(passport_number: str):
    fetch_user = coll.find_one({"passportNumber": passport_number})
    if fetch_user:
        return user_helper(fetch_user)
    raise HTTPException(status_code=404, detail="User not found")

@app.post("/create-user")
def create_user(user: User):
    print(user)
    insert_result = coll.insert_one(user.dict())
    return {"message":"Document inserted successfully", "insert_id":str(insert_result.inserted_id)}
