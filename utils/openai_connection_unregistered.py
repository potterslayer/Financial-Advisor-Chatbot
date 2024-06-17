import openai
import os
import numpy as np
from datetime import date
from datetime import datetime
import os
from dotenv import load_dotenv
from openai import OpenAI
import logging
from langchain_community.utilities import GoogleSearchAPIWrapper 
from pinecone import Pinecone
from dotenv import load_dotenv 
from utils.mutualfund import data_new
from utils.indices import data_indices
from classifiers.instrument_classifier import classify_growth_OR_direct,classify_instrument
from classifiers.classify_time import classify_real_time_question
load_dotenv()
Pinecone_api=os.getenv("Pincone_API_KEY")
pc = Pinecone(api_key=Pinecone_api)
index = pc.Index("mutualfundpoints")
index_indices = pc.Index("indices")
os.environ["GOOGLE_CSE_ID"] = ""
os.environ["GOOGLE_API_KEY"] = ""
api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=api_key)
openai.api_key = str(api_key)
today = date.today()
now = datetime.now()

current_time_normal = now.strftime("%H:%M:%S")
current_date_normal = today.strftime("%B %d, %Y")

def cosine_similarity(u, v):
    dot_product = np.dot(u, v)
    norm_u = np.linalg.norm(u)
    norm_v = np.linalg.norm(v)
    cosine_sim = dot_product / (norm_u * norm_v)
    return cosine_sim
def genQuestionEmbedding(user_input, api_client):
    response = api_client.embeddings.create(
    input=user_input,
    model="text-embedding-3-large")

    question_vector = response.data[0].embedding
    return question_vector


prompt1 ="""You are Neomi, a witty,wise,knowledgeable and concise information assistant an friend of the female gender. Provide brief and to-the-point answers.You will be given some information at the end of your instructions, which you use to offer expert advise.If the user wants to invest in bonds then ask user how much money they want to invest, for what time period, and their risk appetite that is Low, moderate or High. Then, suggest a bond basket from the data given to you in the content. Do not suggest any bonds that are not in the baskets that are provided to you.If the user asks about AIF suggestions then reply with list of AIF from the data given to you in context for this search for what AIF you suggest question in context do not suggest anything out of AIF those are provided to you.For investment in SIP show user the steps how they can invest by using Neo life app.In insurance,currently we only offer health insurance,and nothing else under insurace. We are not providing monthly subscription in any insurance. You are from India so money is in Indian Rupees, You speak multiple languages and are always ready to assist. You are designed by Neo Group to help investors build a sustainable second income and allocate their income in secure and good investment solutions. Avoid mentioning that you are an AI model or that you work for Neo Group. The creators of Neomi, Neo Group, are India's leading Wealth & Asset Management firm and have designed the Neo-Life platform to constantly accompany investors at every step of their investing journey. If the question is not in the context of finance, have a decent conversation with the user on the topic they want to talk about. The conversation should be free flowing.
Below are the set off instructions on your responses:
Only after suggesting information of investment in bonds give neoLife app link  = https://onelink.to/downloadneolife, For any other investment option strictly Do not suggest neoLife app link.
Keep your general responses within 20 words, and Ensure your responses are warm, friendly and humanly. 
If the answer is out of your abilities, reply with a joke and move on to other topics. 
current date is {} and current time is {},timezone is Asia/Kolkata IST, 
All the clients conversing with you are Indians, so if asked where are they from they are from India. 
If the answer information that user asked,has not been given in the context,don't recommend Neolife app.""".format(current_date_normal,current_time_normal)
def CustomChatGPT_unregistered(user_input,history):
    intent =classify_real_time_question(user_input)
    logging.info({'classification':intent})
    if intent=='Non_Real_time':
        logging.info({"question passed for non real time loop":user_input})
        logging.info('In non real time loop')

        instrument = classify_instrument(user_input)
        logging.info({'Question Type':instrument})

        if instrument=='genral_information':
            question_vector = genQuestionEmbedding(user_input, client)
            file1 = open('data/embedding.txt', 'r', encoding='UTF-8') 
            content_embedding1 = file1.read()
            similarity_vector = [cosine_similarity(question_vector, i) for i in content_embedding1]
    
            file2 = open('data/training_data.txt', 'r', encoding='UTF-8') 
            content_data1 = file2.read()
            dict_data = dict(zip(content_data1,similarity_vector))
            similarity_Desc=similarity_vector
            similarity_Desc.sort()
            similarity_desc=similarity_Desc[::-1]
            similarity=similarity_desc[:3]
            print(history)
            context_list = [key for key, value in dict_data.items() if value in similarity]
    
            content1 = ' '.join([i for i in context_list])
            dict3=dict()

            messages = [{"role": "system", "content":prompt1+content1+" "+"This is the previous coversations between Neomi and user"+" "+history}]
            messages.append({"role": "user", "content": user_input})

            response = client.chat.completions.create(
                model = "gpt-4",
                temperature=0.1,
                messages = messages
            )
            ChatGPT_reply = response.choices[0].message.content
            print(ChatGPT_reply)
            dict3['prompt'] = user_input
            dict3['completion'] = ChatGPT_reply
            dict3['model'] = response.model
            dict3['usage'] = {
                'completion_tokens': response.usage.completion_tokens,
                'prompt_tokens': response.usage.prompt_tokens,
                'total_tokens': response.usage.total_tokens
            }
            dict3['GPT_id'] = response.id
            dict3['GPT_object'] = response.object
            logging.info({"chatGPT reply":ChatGPT_reply})
            
            messages.append({"role": "assistant", "content": ChatGPT_reply})
            return ChatGPT_reply,dict3

        elif instrument=='Mutual_fund':

            classification_detail = classify_growth_OR_direct(user_input)
            logging.info({'Instrument Classification':classification_detail})
            if classification_detail=='Direct_Accumulated':
             
                question_vector = genQuestionEmbedding(user_input, client)
                file1 = open('data/embedding.txt', 'r', encoding='UTF-8') 
                content_embedding1 = file1.read()
                similarity_vector = [cosine_similarity(question_vector, i) for i in content_embedding1]

                file2 = open('data/training_data.txt', 'r', encoding='UTF-8') 
                content_data1 = file2.read()
                dict_data = dict(zip(content_data1,similarity_vector))
                
                similarity_Desc=similarity_vector
                similarity_Desc.sort()
                similarity_desc=similarity_Desc[::-1]
                similarity=similarity_desc[:3]

                context_list = [key for key, value in dict_data.items() if value in similarity]
                content1 = ' '.join([i for i in context_list])    
                pincone_vec = index.query(
                vector=question_vector,
                    top_k=1,include_metadata=True,
                    filter={
                    'Instrument_category': 'Mutual Fund',
                    'schemePlan':'DIRECT',
                    'distributionStatus':'Accumulated',
                    'dividendReinvestmentFlag':'Z'
                    })
                id = pincone_vec['matches'][0]['id']
                mutualfund_instrument = data_new[int(id)]['values']
                messages = [{"role": "system", "content":prompt1+"This is the comoplete real time information of fund please use this to genrate the answers of specific fund"+mutualfund_instrument+" "+"This is the previous coversations between Neomi and user"+" "+history+"always mension that this is direct growth along with fund name"}]
                messages.append({"role": "user", "content": user_input})
                response = client.chat.completions.create(
                    model = "gpt-4",
                    temperature=0.1,
                    messages = messages
                )
                dict3=dict()

                dict3['completion'] = response.choices[0].message.content
                dict3['model'] = response.model
                dict3['usage'] = {
                    'completion_tokens': response.usage.completion_tokens,
                    'prompt_tokens': response.usage.prompt_tokens,
                    'total_tokens': response.usage.total_tokens
                }
                dict3['GPT_id'] = response.id
                dict3['GPT_object'] = response.object
                dict3['MF_instrument'] = mutualfund_instrument
                dict3['Instrument_type']='Direct_Accumulated'      
                ChatGPT_reply = response.choices[0].message.content
                return ChatGPT_reply,dict3
            elif classification_detail=='Direct_Income':
                question_vector = genQuestionEmbedding(user_input, client)
                file1 = open('data/embedding.txt', 'r', encoding='UTF-8') 
                content_embedding1 = file1.read()
                similarity_vector = [cosine_similarity(question_vector, i) for i in content_embedding1]

                file2 = open('data/training_data.txt', 'r', encoding='UTF-8') 
                content_data1 = file2.read()
                dict_data = dict(zip(content_data1,similarity_vector))
                
                similarity_Desc=similarity_vector
                similarity_Desc.sort()
                similarity_desc=similarity_Desc[::-1]
                similarity=similarity_desc[:3]

                context_list = [key for key, value in dict_data.items() if value in similarity]
                content1 = ' '.join([i for i in context_list])    
                pincone_vec = index.query(
                vector=question_vector,
                    top_k=1,include_metadata=True,
                    filter={
                    'Instrument_category': 'Mutual Fund',
                    'schemePlan':'DIRECT',
                    'distributionStatus':'Income',
                    })
                id = pincone_vec['matches'][0]['id']
                mutualfund_instrument = data_new[int(id)]['values']
                messages = [{"role": "system", "content":prompt1+"This is the comoplete real time information of fund please use this to genrate the answers of specific fund"+mutualfund_instrument+" "+"This is the previous coversations between Neomi and user"+" "+history+"always mension that this is direct growth along with fund name"}]
                messages.append({"role": "user", "content": user_input})
                response = client.chat.completions.create(
                    model = "gpt-4",
                    temperature=0.1,
                    messages = messages
                )
                dict3=dict()

                dict3['completion'] = response.choices[0].message.content
                dict3['model'] = response.model
                dict3['usage'] = {
                    'completion_tokens': response.usage.completion_tokens,
                    'prompt_tokens': response.usage.prompt_tokens,
                    'total_tokens': response.usage.total_tokens
                }
                dict3['GPT_id'] = response.id
                dict3['GPT_object'] = response.object
                dict3['MF_instrument'] = mutualfund_instrument
                dict3['Instrument_type']='Direct_Income'      
                ChatGPT_reply = response.choices[0].message.content
                return ChatGPT_reply,dict3
            elif classification_detail=='Normal_Accumulated':
                question_vector = genQuestionEmbedding(user_input, client)
                file1 = open('data/embedding.txt', 'r', encoding='UTF-8') 
                content_embedding1 = file1.read()
                similarity_vector = [cosine_similarity(question_vector, i) for i in content_embedding1]

                file2 = open('data/training_data.txt', 'r', encoding='UTF-8') 
                content_data1 = file2.read()
                dict_data = dict(zip(content_data1,similarity_vector))
                
                similarity_Desc=similarity_vector
                similarity_Desc.sort()
                similarity_desc=similarity_Desc[::-1]
                similarity=similarity_desc[:3]

                context_list = [key for key, value in dict_data.items() if value in similarity]
                content1 = ' '.join([i for i in context_list])    
                pincone_vec = index.query(
                vector=question_vector,
                    top_k=1,include_metadata=True,
                    filter={
                    'Instrument_category': 'Mutual Fund',
                    'schemePlan':'NORMAL',
                    'distributionStatus':'Accumulated',
                    'dividendReinvestmentFlag':'Z'
                    })
                id = pincone_vec['matches'][0]['id']
                mutualfund_instrument = data_new[int(id)]['values']
                messages = [{"role": "system", "content":prompt1+"This is the comoplete real time information of fund please use this to genrate the answers of specific fund"+mutualfund_instrument+" "+"This is the previous coversations between Neomi and user"+" "+history+"always mension that this is direct growth along with fund name"}]
                messages.append({"role": "user", "content": user_input})
                response = client.chat.completions.create(
                    model = "gpt-4",
                    temperature=0.1,
                    messages = messages
                )
                dict3=dict()

                dict3['completion'] = response.choices[0].message.content
                dict3['model'] = response.model
                dict3['usage'] = {
                    'completion_tokens': response.usage.completion_tokens,
                    'prompt_tokens': response.usage.prompt_tokens,
                    'total_tokens': response.usage.total_tokens
                }
                dict3['GPT_id'] = response.id
                dict3['GPT_object'] = response.object
                dict3['MF_instrument'] = mutualfund_instrument
                dict3['Instrument_type']='Normal_Accumulated'      
                ChatGPT_reply = response.choices[0].message.content
                return ChatGPT_reply,dict3
            elif classification_detail=='Normal_Income':
                question_vector = genQuestionEmbedding(user_input, client)
                file1 = open('data/embedding.txt', 'r', encoding='UTF-8') 
                content_embedding1 = file1.read()
                similarity_vector = [cosine_similarity(question_vector, i) for i in content_embedding1]

                file2 = open('data/training_data.txt', 'r', encoding='UTF-8') 
                content_data1 = file2.read()
                dict_data = dict(zip(content_data1,similarity_vector))
                
                similarity_Desc=similarity_vector
                similarity_Desc.sort()
                similarity_desc=similarity_Desc[::-1]
                similarity=similarity_desc[:3]

                context_list = [key for key, value in dict_data.items() if value in similarity]
                content1 = ' '.join([i for i in context_list])    
                pincone_vec = index.query(
                vector=question_vector,
                    top_k=1,include_metadata=True,
                    filter={
                    'Instrument_category': 'Mutual Fund',
                    'schemePlan':'NORMAL',
                    'distributionStatus':'Income',
                    })
                id = pincone_vec['matches'][0]['id']
                mutualfund_instrument = data_new[int(id)]['values']
                messages = [{"role": "system", "content":prompt1+"This is the comoplete real time information of fund please use this to genrate the answers of specific fund"+mutualfund_instrument+" "+"This is the previous coversations between Neomi and user"+" "+history+"always mension that this is direct growth along with fund name"}]
                messages.append({"role": "user", "content": user_input})
                response = client.chat.completions.create(
                    model = "gpt-4",
                    temperature=0.1,
                    messages = messages
                )
                dict3=dict()

                dict3['completion'] = response.choices[0].message.content
                dict3['model'] = response.model
                dict3['usage'] = {
                    'completion_tokens': response.usage.completion_tokens,
                    'prompt_tokens': response.usage.prompt_tokens,
                    'total_tokens': response.usage.total_tokens
                }
                dict3['GPT_id'] = response.id
                dict3['GPT_object'] = response.object
                dict3['MF_instrument'] = mutualfund_instrument
                dict3['Instrument_type']='Normal_Income'      
                ChatGPT_reply = response.choices[0].message.content
                return ChatGPT_reply,dict3
        elif instrument=='indices':
            question_vector = genQuestionEmbedding(user_input, client)
            file1 = open('data/embedding.txt', 'r', encoding='UTF-8') 
            content_embedding1 = file1.read()
            similarity_vector = [cosine_similarity(question_vector, i) for i in content_embedding1]

            file2 = open('data/training_data.txt', 'r', encoding='UTF-8') 
            content_data1 = file2.read()
            dict_data = dict(zip(content_data1,similarity_vector))
            
            similarity_Desc=similarity_vector
            similarity_Desc.sort()
            similarity_desc=similarity_Desc[::-1]
            similarity=similarity_desc[:3]

            context_list = [key for key, value in dict_data.items() if value in similarity]
            content1 = ' '.join([i for i in context_list]) 

            pincone_vec = index_indices.query(
            vector=question_vector,
                top_k=1,include_metadata=True,
                filter={
                'Instrument_category': 'Indices',
                })        
            id = pincone_vec['matches'][0]['id']
            indices_instrument = data_indices[int(id)]['values']
            messages = [{"role": "system", "content":prompt1+"This is the comoplete real time information of fund please use this to genrate the answers of specific fund"+indices_instrument+" "+"This is the previous coversations between Neomi and user"+" "+history}]

            messages.append({"role": "user", "content": user_input})
            response = client.chat.completions.create(
                model = "gpt-4",
                temperature=0.1,
                messages = messages
            )
            dict3=dict()

            dict3['completion'] = response.choices[0].message.content
            dict3['model'] = response.model
            dict3['usage'] = {
                'completion_tokens': response.usage.completion_tokens,
                'prompt_tokens': response.usage.prompt_tokens,
                'total_tokens': response.usage.total_tokens
            }
            dict3['GPT_id'] = response.id
            dict3['GPT_object'] = response.object
            dict3['indices_instrument'] = indices_instrument
            dict3['Instrument_type']='Direct_Accumulated'
        
            ChatGPT_reply = response.choices[0].message.content        
            return ChatGPT_reply,dict3

        elif intent=='Real_time':
            logging.info("entered Real time loop")
            logging.info({"question passed for real time loop":user_input})
    
            current_time = now.strftime("%H:%M:%S")
            current_date = today.strftime("%B %d, %Y")
    
            prompt ="""You are Neomi, a witty,wise,knowledgeable and concise information assistant an friend of the female gender. Provide brief and to-the-point answers.You will be given some information at the end of your instructions, which you use to offer expert advise.If the user wants to invest in bonds then ask user how much money they want to invest, for what time period, and their risk appetite that is Low, moderate or High. Then, suggest a bond basket from the data given to you in the content. Do not suggest any bonds that are not in the baskets that are provided to you.If the user asks about PMS recomendations, then ask user whether they want information about general PMS or small cap and mid cap PMS or Flexi Cap and multi cap PMS segment then reply with list of PMS from the data given to you in context for this search for what PMS you recommend question in context do not suggest anything out of pms those are provided to you.If the user asks about AIF suggestions, then ask user whether they want information about AIF or CAT || AIF or Cap ||| AIF or Alternate segment AIF or Large Cap segment AIF or Flexi Cap segment AIF then reply with list of AIF from the data given to you in context for this search for what AIF you suggest question in context do not suggest anything out of AIF those are provided to you.For investment in SIP show user the steps how they can invest by using Neo life app.In insurance,currently we only offer health insurance,and nothing else under insurace. We are not providing monthly subscription in any insurance. You are from India so money is in Indian Rupees, You speak multiple languages and are always ready to assist. You are designed by Neo Group to help investors build a sustainable second income and allocate their income in secure and good investment solutions. Avoid mentioning that you are an AI model or that you work for Neo Group. The creators of Neomi, Neo Group, are India's leading Wealth & Asset Management firm and have designed the Neo-Life platform to constantly accompany investors at every step of their investing journey. If the question is not in the context of finance, have a decent conversation with the user on the topic they want to talk about. The conversation should be free flowing.
    Below are the set off instructions on your responses:
    Only after suggesting information of investment in bonds give neoLife app link  = https://onelink.to/downloadneolife, For any other investment option strictly Do not suggest neoLife app link.
    Keep your general responses within 20 words, and Ensure your responses are warm, friendly and humanly. 
    If the answer is out of your abilities, reply with a joke and move on to other topics. 
    current date is {} and current time is {},timezone is Asia/Kolkata IST, 
    All the clients conversing with you are Indians, so if asked where are they from they are from India. 
    If the answer information that user asked,has not been given in the context,don't recommend Neolife app.""".format(current_date,current_time)
            search = GoogleSearchAPIWrapper()
            google_result=search.run(user_input)
            messages = [{"role": "system", "content":prompt+ "I am giving you real time data and this information is obtained from google search use this to answer about real time information and after giving real time answers for any investment instrument like Nifity 50 always mension date in answer along with value"+' '+google_result}]
            messages.append({"role": "user", "content": user_input})
            #print(messages)

            response = client.chat.completions.create(
                model = "gpt-4",
                temperature=0.1,
                messages = messages
            )
            ChatGPT_reply = response.choices[0].message.content 
            logging.info({'name':'ChatGPT_reply','content':ChatGPT_reply})
            
            dict3=dict()
    
            dict3['prompt']=user_input
            dict3['completion']=ChatGPT_reply
            dict3['model']='GPT-4'
            dict3['usage']={"completion_tokens": 500,"prompt_tokens": 500,"total_tokens": 1000}
            dict3['GPT_id']= 'chatcmpl-7b2FAXwIkKcNrhzXwoQrAjZWKu8Uh'
            dict3['GPT_object']='chat.completion'
            #logging.info(dict3)
    
            return ChatGPT_reply,dict3    