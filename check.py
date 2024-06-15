from pymongo import MongoClient
import os
from dotenv import load_dotenv
load_dotenv()

import logging
logging.basicConfig(level=logging.INFO)

# mongo_url = os.getenv("MONGO_URL")
# db = os.getenv("DB_NAME")
#collection_name1 = os.getenv("COLLECTION_NAME1")
#collection_name = os.getenv("COLLECTION_NAME")
#collection_name_unregistered = os.getenv("COLLECTION_NAME_UNREGISTERED")

mongo_url = os.getenv("MONGO_URL")
dbName = 'neoWorldLogger'
client = MongoClient(mongo_url))
db = client[dbName]



def check_user(mobile_number):
    registered_collection = db["ChatGPT3_User_Collection"]
    unregistered_collection = db["Unregistered_User"]

    # Query the registered collection
    document_check_registered = registered_collection.count_documents({'mobile_number': mobile_number})

    # Query the unregistered collection
    document_check_unregistered = unregistered_collection.count_documents({'mobile_number': mobile_number})

    regis_app = 'registered_from_app'
    regis_whatsapp = 'registered_from_whatsapptrial'
    suff_token = 'sufficient_tokens'
    unsuff_token = 'unsufficient_tokens'
    
    print('ducoments for unregistred',document_check_unregistered)
    print('documents for registered',document_check_registered)
    logging.info(document_check_registered)
    logging.info(document_check_unregistered)

    if document_check_registered > 0:
        user_data = registered_collection.find_one({'mobile_number': mobile_number})
        print('user_data',user_data)
        logging.info(user_data)
        print(user_data['tokens']['balance_tokens'] )
        logging.info(user_data['tokens']['balance_tokens'])
        if user_data['tokens']['balance_tokens'] > 0:
            return [regis_app, suff_token]
        else:
            return [regis_app, unsuff_token]

    elif document_check_unregistered > 0:
        user_data = unregistered_collection.find_one({'mobile_number': mobile_number})
        print('user_data',user_data)
        logging.info(user_data)
        print(user_data['tokens']['balance_tokens'] )
        logging.info(user_data['tokens']['balance_tokens'])
        if user_data['tokens']['balance_tokens'] > 0:
            return [regis_whatsapp, suff_token]
        else:
            return [regis_whatsapp, unsuff_token]

    else:
        # Insert a new document into the Unregistered_User collection
        unregistered_collection.insert_one({'mobile_number': mobile_number, 'tokens':{'total_used_neos': 0,'total_used_tokens': 0,'balance_tokens': 5000000 }, 'total_responses': 0,})
        return [regis_whatsapp, suff_token]