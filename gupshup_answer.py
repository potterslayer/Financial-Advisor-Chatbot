from flask import Flask, request, jsonify, make_response
from datetime import datetime
import random
import string
from pymongo import MongoClient
import requests
import os
import json
import requests
import openai
from openai import OpenAI
import requests
import logging
from transcribe.t2s import generate_audio, upload_audio_to_s3, generate_presigned_url, download_audio, delete_local_files
from utils.mongo_connection import (
    insert_data,
    get_user_tokens,
    update_user_tokens,
    history,
    update_user_tokens_unregistered,
    get_user_tokens_unregistered,
    is_payload_id_present
)
from utils.openai_connection_registered import CustomChatGPT_registered
from utils.openai_connection_unregistered import CustomChatGPT_unregistered
from check import check_user
import boto3
load_dotenv()
aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
bucket_name = os.getenv("S3_BUCKET_NAME")
S3_BUCKET_NAME = 'neoworld-stage-neomi-chatbot-audio-chats'
gupshup_api_key=os.getenv("GUPSHUP_KEY")


def generate_conversation_code():
    # Generate an 8-digit alphanumeric code
    alphanumeric = string.ascii_letters + string.digits
    code = ''.join(random.choice(alphanumeric) for _ in range(8))
    return code

def gupshup_api():
    try:
        data = request.get_json()
        logging.info(data)
        logging.info(data['payload']['type'])
        if "type" not in data:
            logging.info("payload is different and does not have type")
            return make_response('', 202)
        if 'type' in data:
            logging.info('type in data')
            list=['text','audio']
        if data['payload']['type'] not in list:
                logging.info("text or reaction not present in text of payload")
                return make_response('', 202)
        if data['payload']['type'] == 'text':
                app_id = data["app"]
                timestamp = data["timestamp"]
                version = data["version"]
                payload_type = data["type"]
                payload = data["payload"]
                #nested payload
                payload_id = payload["id"]
                source = payload["source"]
                question = payload["payload"]["text"]
                logging.info({'question':question})
                sender = payload["sender"]                             
                mobile_number_withinitial = sender["phone"]
                sender_name = sender["name"]
                country_code = sender["country_code"]
                mobile_number = sender["dial_code"]
                logging.info("just before check_id")
                payload_id_check=is_payload_id_present(payload_id)
                logging.info("just after check_id")
                if payload_id_check==True:
                    logging.info("hey payload already exsitst")
                    return make_response('', 202)
                else:
                     logging.info(mobile_number)
                     url = 'https://api.gupshup.io/wa/app/{}/msg/{}/read'.format(app_id,payload_id)
                     logging.info({'url':url})
                     headers = {"apikey": Gupshup_API_KEY}
                     logging.info("just before request")    

                     response = requests.put(url, headers=headers)
                     check = check_user(str(mobile_number))
                     logging.info(check)               
                     if check[0]=='registered_from_app' and check[1] == 'sufficient_tokens':
                        balance_tokens = get_user_tokens(mobile_number)
                        history_dict_1 = history(mobile_number)
                        #logging.info('after history')
                        reply, dictionary = CustomChatGPT_registered(question, history_dict_1)
                        conversation_code = generate_conversation_code()

                        total_tokens = dictionary['usage']['total_tokens']
                        #logging.info({'total tokens':total_tokens,'balance token':balance_tokens})
                        remaining_balance = balance_tokens - total_tokens
                        update_user_tokens(mobile_number, remaining_balance)

                        final_dict_new = {
                            'mobile_number': mobile_number,
                            'created_at': datetime.now().isoformat(),
                            'updated_at': datetime.now().isoformat(),
                            'conversation_code': conversation_code,
                            'abuse_reported': False,
                            'emoji': None,
                            'balance_tokens': remaining_balance,
                            'total_tokens': total_tokens,
                            'Gupshup_payload_id':payload_id
                        }

                        dictionary.update(final_dict_new)
                        dictionary_addMessageID=dict()
                        print(dictionary)
                        insert_data(dictionary)
                        
                        # Set your Gupshup API key
                        API_KEY = os.getenv("Gupshup API Key")

                        # Set the recipient's phone number
                        # RECIPIENT_PHONE_NUMBER = mobile_number
                        RECIPIENT_PHONE_NUMBER = mobile_number_withinitial

                        # Set the message content
                        MESSAGE_CONTENT = reply

                        # Create the HTTP request
                        headers = {
                        "apikey":API_KEY,
                        "Content-Type": "application/x-www-form-urlencoded"
                            }
                        data = {
                        "channel": "whatsapp",
                        "source": "919152288568",
                        "destination": RECIPIENT_PHONE_NUMBER,
                        "src.name": "91sSN3y0n4Wh0uy8exoVxSTK",
                        "message": MESSAGE_CONTENT,
                        "quotedMessageID":payload_id,
                        "tagged_in_reply": True
                                }

                        response = requests.post("https://api.gupshup.io/wa/api/v1/msg", headers=headers, data=data) 
                        #Check the response status code
                        if 200 <= response.status_code < 300:
                            print("Message sent successfully!")
                            logging.info("Message sent successfully! from registred user loop")
                        else:
                            print("Error sending message:", response.status_code)
                            logging.info("Error sending message from registred user loop",response.status_code)

                        return make_response('', 202)
                     
                     elif check[0]=='registered_from_whatsapptrial' and check[1] == 'sufficient_tokens':
                        logging.info("entered whatsapptrial loop")
                        balance_tokens = get_user_tokens_unregistered(mobile_number)
                        #print("Balance tokens",balance_tokens)
                        #if balance_tokens > threshold:
                        history_dict_1 = history(mobile_number)
                        reply, dictionary = CustomChatGPT_unregistered(question, history_dict_1)
                        #print(history_dict_1)
                        conversation_code = generate_conversation_code()
                        total_tokens = dictionary['usage']['total_tokens']

                        remaining_balance = balance_tokens - total_tokens
                        #print("check-1")
                        #print('remaining_balance',remaining_balance)
                        update_user_tokens_unregistered(mobile_number, remaining_balance)
                        final_dict_new = {
                            'mobile_number': mobile_number,
                            'created_at': datetime.now().isoformat(),
                            'updated_at': datetime.now().isoformat(),
                            'conversation_code': conversation_code,
                            'abuse_reported': False,
                            'emoji': None,
                            'balance_tokens': remaining_balance,
                            'total_tokens': total_tokens,
                            'Gupshup_payload_id':payload_id,
                        }
                        dictionary.update(final_dict_new)
                        insert_data(dictionary)
                        update_user_tokens_unregistered(mobile_number, remaining_balance)

                        # Set your Gupshup API key
                        API_KEY = os.getenv("Gupshup API Key")
                        RECIPIENT_PHONE_NUMBER = mobile_number_withinitial

                        # Set the message content
                        MESSAGE_CONTENT = reply
                        # Create the HTTP request
                        headers = {
                        "apikey":API_KEY,
                        "Content-Type": "application/x-www-form-urlencoded"
                            }

                        data = {
                        "channel": "whatsapp",
                        "source": "919152288568",
                        "destination": RECIPIENT_PHONE_NUMBER,
                        "src.name": "91sSN3y0n4Wh0uy8exoVxSTK",
                        "message": MESSAGE_CONTENT,
                        "quotedMessageID":payload_id,
                        "tagged_in_reply": True
                                }

                        response = requests.post("https://api.gupshup.io/wa/api/v1/msg", headers=headers, data=data)
                        response_data = json.loads(response.text)
                        #Check the response status code
                        if 200 <= response.status_code < 300:
                            print("Message sent successfully!")
                            logging.info("Message sent successfully! from unregistred user loop")

                        else:
                            print("Error sending message:", response.status_code)
                            logging.info("Error sending message from unregistred user loop",response.status_code)

                        # return jsonify({"success":True,"message":"message send successfully"}),200
                        return make_response('', 202)
                     
                     elif check[0]=='registered_from_app' and check[1] == 'unsufficient_tokens':
                        
                        # Set your Gupshup API key
                        API_KEY = os.getenv("Gupshup API Key")
                        RECIPIENT_PHONE_NUMBER = mobile_number_withinitial
                        # Set the message content
                        MESSAGE_CONTENT = "You do not have sufficient tokens please recharge from Neolife app."

                        # Create the HTTP request
                        headers = {
                        "apikey":API_KEY,
                        "Content-Type": "application/x-www-form-urlencoded"
                            }
                        
                        data = {
                        "channel": "whatsapp",
                        "source": "919152288568",
                        "destination": RECIPIENT_PHONE_NUMBER,
                        "src.name": "91sSN3y0n4Wh0uy8exoVxSTK",
                        "message": MESSAGE_CONTENT
                                }
                        # Send the request
                        response = requests.post("https://api.gupshup.io/wa/api/v1/msg", headers=headers, data=data)

                        #Check the response status code
                        if 200 <= response.status_code < 300:
                            print("Message sent successfully!")
                            logging.info("Message sent successfully! from registred user loop with trail token exhausted")

                        else:
                            print("Error sending message:", response.status_code)
                            logging.info("Error sending message from registred user loop with trail token exhausted",response.status_code)
                        return make_response('', 202)

                     elif check[0]=='registered_from_whatsapptrial' and check[1] == 'unsufficient_tokens':

                        # Set your Gupshup API key
                        API_KEY = os.getenv("Gupshup API Key")
                        RECIPIENT_PHONE_NUMBER = mobile_number_withinitial
                        # Set the message content
                        MESSAGE_CONTENT = "You are not registered and have used all your Trial balance."
                        # Create the HTTP request
                        headers = {
                        "apikey":API_KEY,
                        "Content-Type": "application/x-www-form-urlencoded"
                            }

                        data = {
                        "channel": "whatsapp",
                        "source": "919152288568",
                        "destination": RECIPIENT_PHONE_NUMBER,
                        "src.name": "91sSN3y0n4Wh0uy8exoVxSTK",
                        "message": MESSAGE_CONTENT
                                }
                        # Send the request
                        response = requests.post("https://api.gupshup.io/wa/api/v1/msg", headers=headers, data=data)

                        #Check the response status code
                        if 200 <= response.status_code < 300:
                            print("Message sent successfully!")
                            logging.info("Message sent successfully! from unregistred user loop with trail token exhausted.")

                        else:
                            print("Error sending message:", response.status_code)
                            logging.info("Error sending message from unregistred user loop with trail token exhausted.",response.status_code)

                        # return jsonify({}),202
                        return make_response('', 202) 
        elif data['payload']['type'] == 'audio':
            logging.info("entered audio loop")
            app_id = data["app"]
            payload = data["payload"]
            payload_id = payload["id"]
            type=payload['type']
            url = payload["payload"]["url"]
            contentType = payload["payload"]["contentType"]
            urlExpiry = payload["payload"]["urlExpiry"]
            sender = payload["sender"]["phone"]
            mobile_number = payload["sender"]["phone"]
            sender_name = payload["sender"]["name"]
            country_code = payload["sender"]["country_code"]
            dial_code = payload["sender"]["dial_code"]
            mobile_number_withinitial = payload["sender"]["phone"]
            logging.info("just before check_id")
            payload_id_check=is_payload_id_present(payload_id)
            logging.info("just after check_id") 
            if payload_id_check==True:
                print("hey payload already exsitst")
                logging.info("hey payload already exsitst")
                return make_response('', 202)    
            else:
                audio_url = url
                output_folder = "storage/temp"   
                downloaded_file_path = download_audio(audio_url, output_folder)
                # Transcribe the downloaded audio file
                with open(downloaded_file_path, "rb") as audio_file:
                    transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
                question = transcript
                print(question)
                delete_local_files(output_folder)  
                logging.info(mobile_number)
                url = 'https://api.gupshup.io/wa/app/{}/msg/{}/read'.format(app_id,payload_id)
                logging.info({'url':url})
                headers = {"apikey": gupshup_api}
                logging.info("just before request")
                response = requests.put(url, headers=headers)  
                check = check_user(str(mobile_number))
                logging.info(check)  
                if check[0]=='registered_from_app' and check[1] == 'sufficient_tokens':
                
                    balance_tokens = get_user_tokens(mobile_number)
                    history_dict_1 = history(mobile_number)
                    reply, dictionary = CustomChatGPT_registered(question, history_dict_1)
                    conversation_code = generate_conversation_code()

                    total_tokens = dictionary['usage']['total_tokens']
                    remaining_balance = balance_tokens - total_tokens
                    
                    update_user_tokens(mobile_number, remaining_balance)
                                 
                    final_dict_new = {
                        'mobile_number': mobile_number,
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat(),
                        'conversation_code': conversation_code,
                        'abuse_reported': False,
                        'emoji': None,
                        'balance_tokens': remaining_balance,
                        'total_tokens': total_tokens,
                        'Gupshup_payload_id':payload_id
                    }                                                           
                    dictionary.update(final_dict_new)
                    insert_data(dictionary)                                 
                    API_KEY = os.getenv("Gupshup API Key")
                    RECIPIENT_PHONE_NUMBER = mobile_number_withinitial
                    input_text = reply
                    print(input_text)
                    # Generate audio using OpenAI TTS
                    audio_data = generate_audio(input_text)
                    object_name = upload_audio_to_s3(S3_BUCKET_NAME, audio_data, object_name)
                    expiration_time = 5400
                    presigned_url = generate_presigned_url(S3_BUCKET_NAME, object_name, expiration_time)
                    msg={
                         "type":"audio",
                          "url":presigned_url
                                }     
                    MESSAGE_CONTENT = json.dumps(msg)
                    logging.info(MESSAGE_CONTENT)

                    headers = {
                        "apikey":API_KEY,
                        "Content-Type": "application/x-www-form-urlencoded"
                            }  
                    data = {
                    "type":"audio",
                    "channel": "whatsapp",
                    "source": "919152288568",
                    "destination": RECIPIENT_PHONE_NUMBER,
                    "src.name": "91sSN3y0n4Wh0uy8exoVxSTK",
                    "message": MESSAGE_CONTENT,
                    "quotedMessageID":payload_id,
                    "tagged_in_reply": True
                            }                               
                    response = requests.post("https://api.gupshup.io/wa/api/v1/msg", headers=headers, data=data)
                    if 200 <= response.status_code < 300:
                        print("Message sent successfully!")
                        logging.info("Message sent successfully! from registred user loop")
                    else:
                        print("Error sending message:", response.status_code)
                        logging.info("Error sending message from registred user loop",response.status_code)
                    return make_response('', 202)
                elif check[0]=='registered_from_whatsapptrial' and check[1] == 'sufficient_tokens':
                        logging.info("entered whatsapptrial loop")
                        balance_tokens = get_user_tokens_unregistered(mobile_number)
                        history_dict_1 = history(mobile_number)
                        reply, dictionary = CustomChatGPT_unregistered(question, history_dict_1)

                        conversation_code = generate_conversation_code()

                        total_tokens = dictionary['usage']['total_tokens']
                        remaining_balance = balance_tokens - total_tokens
                        update_user_tokens_unregistered(mobile_number, remaining_balance)


                        final_dict_new = {
                            'mobile_number': mobile_number,
                            'created_at': datetime.now().isoformat(),
                            'updated_at': datetime.now().isoformat(),
                            'conversation_code': conversation_code,
                            'abuse_reported': False,
                            'emoji': None,
                            'balance_tokens': remaining_balance,
                            'total_tokens': total_tokens,
                            'Gupshup_payload_id':payload_id,
                        }
                
                        dictionary.update(final_dict_new)
                        insert_data(dictionary)
                        # Set your Gupshup API key
                        API_KEY =gupshup_api
                        RECIPIENT_PHONE_NUMBER = mobile_number_withinitial
                        # Set the message content
                        MESSAGE_CONTENT =   presigned_url
                        # Create the HTTP request
                        headers = {
                        "apikey":API_KEY,
                        "Content-Type": "application/x-www-form-urlencoded"
                            }
                        data = {
                        "channel": "whatsapp",
                        "source": "919152288568",
                        "destination": RECIPIENT_PHONE_NUMBER,
                        "src.name": "91sSN3y0n4Wh0uy8exoVxSTK",
                        "message": MESSAGE_CONTENT,
                        "quotedMessageID":payload_id,
                        "tagged_in_reply": True
                                }

                        response = requests.post("https://api.gupshup.io/wa/api/v1/msg", headers=headers, data=data)
                        #Check the response status code
                        if 200 <= response.status_code < 300:
                            print("Message sent successfully!")
                            logging.info("Message sent successfully! from unregistred user loop")
                        else:
                            print("Error sending message:", response.status_code)
                            logging.info("Error sending message from unregistred user loop",response.status_code)
                        return make_response('', 202)     
                elif check[0]=='registered_from_app' and check[1] == 'unsufficient_tokens':
                    # Set your Gupshup API key
                    API_KEY =gupshup_api
                    RECIPIENT_PHONE_NUMBER = mobile_number_withinitial
                    # Set the message content
                    MESSAGE_CONTENT = "You do not have sufficient tokens please recharge from Neolife app."
                    # Create the HTTP request
                    headers = {
                    "apikey":API_KEY,
                    "Content-Type": "application/x-www-form-urlencoded"
                        }
                    data = {
                    "channel": "whatsapp",
                    "source": "919152288568",
                    "destination": RECIPIENT_PHONE_NUMBER,
                    "src.name": "91sSN3y0n4Wh0uy8exoVxSTK",
                    "message": MESSAGE_CONTENT
                            }
                    response = requests.post("https://api.gupshup.io/wa/api/v1/msg", headers=headers, data=data)
                    #Check the response status code
                    if 200 <= response.status_code < 300:
                        print("Message sent successfully!")
                        logging.info("Message sent successfully! from registred user loop with trail token exhausted")

                    else:
                        print("Error sending message:", response.status_code)
                        logging.info("Error sending message from registred user loop with trail token exhausted",response.status_code)

                    # return jsonify({"success":True,"message":"message send successfully with trail token exhausted"}),200
                    return make_response('', 202)              
                elif check[0]=='registered_from_whatsapptrial' and check[1] == 'unsufficient_tokens':
                    # Set your Gupshup API key
                    API_KEY =gupshup_api
                    # RECIPIENT_PHONE_NUMBER = mobile_number
                    RECIPIENT_PHONE_NUMBER = mobile_number_withinitial
                    # Set the message content
                    MESSAGE_CONTENT = "You are not registered and have used all your Trial balance."
                    # Create the HTTP request
                    headers = {
                    "apikey":API_KEY,
                    "Content-Type": "application/x-www-form-urlencoded"
                        }
                    data = {
                    "channel": "whatsapp",
                    "source": "919152288568",
                    "destination": RECIPIENT_PHONE_NUMBER,
                    "src.name": "91sSN3y0n4Wh0uy8exoVxSTK",
                    "message": MESSAGE_CONTENT
                            }
                    response = requests.post("https://api.gupshup.io/wa/api/v1/msg", headers=headers, data=data)
                    #Check the response status code
                    if 200 <= response.status_code < 300:
                        print("Message sent successfully!")
                        logging.info("Message sent successfully! from unregistred user loop with trail token exhausted.")
                    else:
                        print("Error sending message:", response.status_code)
                        logging.info("Error sending message from unregistred user loop with trail token exhausted.",response.status_code)
                    return make_response('', 202)         

    except Exception as e:
        print("An error occurred:", str(e))
        logging.info("Exception occured and comming out of complete loop")
        return make_response('', 202)
    
