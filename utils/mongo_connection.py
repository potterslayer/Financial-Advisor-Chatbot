import os
from pymongo import MongoClient
from dotenv import load_dotenv

from functools import wraps
from flask import request, abort

import logging
load_dotenv()
mongo_url = os.getenv("MONGO_URL")
db_name = os.getenv("DB_NAME")
collection_name = os.getenv("COLLECTION_NAME")
collection_name_unregistered = os.getenv("COLLECTION_NAME_UNREGISTERED")
collection_GupshupLogs =os.getenv("collection_gupshupLogs")

def is_payload_id_present(gupshup_payload_id):
    logging.info("Before mongo in check function")
    client = MongoClient(mongo_url)
    db = client[db_name]
    collection = db[collection_GupshupLogs]
    logging.info("after initialising client and before quary")

    result = bool(collection.find_one({'Gupshup_payload_id': gupshup_payload_id}))
    if result==True:
        client.close()
    else:
        client = MongoClient(mongo_url)
        db = client[db_name]
        collection = db[collection_GupshupLogs]
        collection.insert_one({'Gupshup_payload_id':gupshup_payload_id})
        client.close()

        return result
    
def get_user_tokens(mobile_number):
    client = MongoClient(mongo_url)
    db = client[db_name]
    user_collection = db[collection_name]
    logging.info(user_collection)
    user = user_collection.find_one({'mobile_number': mobile_number})
    logging.info(user)
    logging.info(user.get('tokens', {}).get('balance_tokens', 0))
    return user.get('tokens', {}).get('balance_tokens', 0)    
    
def history(mobile_number):
    client = MongoClient(mongo_url)
    db = client[db_name]
    conversation_collection = db[collection_name]
    # Query to fetch the latest document
    query = {'mobile_number': mobile_number}
    documents = conversation_collection.find(query).sort('_id', -1).limit(4)
    # Get the latest document
    list_history = [i for i in documents]
    #print(list_history)
    #print()
    revevse_list = [i for i in reversed(list_history)]
    print('Len of documents',len(list_history))
    history_len = len(list_history)
    str_history = ''
    for i in revevse_list:
        print(i)
        question = 'user:'+i['prompt']
        responce1 = 'Neomi:'+i['completion']
        str_history += str(question+' '+responce1+' ')
    print('string getting passed','\n',str_history)
    return str_history
    
def update_user_tokens(mobile_number, new_balance):
    client = MongoClient(mongo_url)
    db = client[db_name]
    user_collection = db[collection_name]
    user_collection.update_one(
        {'mobile_number': mobile_number},
        {'$set': {'tokens.balance_tokens': new_balance}}
    )
def update_user_tokens_unregistered(mobile_number, new_balance):
    client = MongoClient(mongo_url)
    db = client[db_name]
    user_collection = db[collection_name_unregistered]
    print('user_collection from update tokens',user_collection)
    user_collection.update_one(
        {'mobile_number': mobile_number},
        {'$set': {'tokens.balance_tokens': new_balance}}
    )
    
def get_user_tokens(mobile_number):
    client = MongoClient(mongo_url)
    db = client[db_name]
    user_collection = db[collection_name]
    logging.info(user_collection)
    user = user_collection.find_one({'mobile_number': mobile_number})
    logging.info(user)
    logging.info(user.get('tokens', {}).get('balance_tokens', 0))
    return user.get('tokens', {}).get('balance_tokens', 0) 

def get_user_tokens_unregistered(mobile_number):
    client = MongoClient(mongo_url)
    db = client[db_name]
    user_collection = db[collection_name_unregistered]
    user = user_collection.find_one({'mobile_number': mobile_number})

    print('user details from get tokens',user)
    return user.get('tokens', {}).get('balance_tokens', 0)

def history(mobile_number):
    client = MongoClient(mongo_url)
    db = client[db_name]
    conversation_collection = db[collection_name]
    # Query to fetch the latest document
    query = {'mobile_number': mobile_number}
    documents = conversation_collection.find(query).sort('_id', -1).limit(4)
    # Get the latest document
    list_history = [i for i in documents]
    revevse_list = [i for i in reversed(list_history)]
    print('Len of documents',len(list_history))
    history_len = len(list_history)
    str_history = ''
    for i in revevse_list:
        print(i)
        question = 'user:'+i['prompt']
        responce1 = 'Neomi:'+i['completion']
        str_history += str(question+' '+responce1+' ')
    print('string getting passed','\n',str_history)
    return str_history

def insert_data(data_dict):
    client = MongoClient(mongo_url)
    print('Connected to MongoDB')
    db = client[db_name]
    conversation_collection = db[collection_name]
    conversation_collection.insert_one(data_dict)