from flask import Flask
import os
from dotenv import load_dotenv 
from gupshup_answer import gupshup_api
load_dotenv()
api_key = os.getenv('API_KEY_GUPSHUP')

app = Flask(__name__)

@app.route('/neomichatbot/CoversationGupshup',methods=['POST'])
def conversationGupshup():
    return gupshup_api()

if __name__ == '__main__':
    app.run(host="0.0.0.0",port=5000)