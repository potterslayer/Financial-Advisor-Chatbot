from langchain.agents import load_tools
from langchain.agents import initialize_agent
from langchain_community.llms import OpenAI
import os 
from openai import OpenAI

api_key = os.getenv('OPENAI_API_KEY')

client = OpenAI(api_key=api_key)
def classify_real_time_question(question):
    # Send the request to the OpenAI API.
    response = client.chat.completions.create(
        model="gpt-4",
        # response_format={ "type": "json_object" },
        messages=[
        {"role": "system", "content": "Classify this question as related to realtime data or no  , if no give me: 'Non Real-time',if question is asking information regarding Mutual Fund or Bonds or indices for example what is todays nav value of HDFC top fund or any fund ,what is current value of  Nifti or S&P or BSE then strictly give classifiction as 'Non Real-time'"},
            {"role": "user", "content": question}
        ]
    )
    classification = response.choices[0].message.content
    if classification == 'Non Real-time':
        return "Non_Real_time"       
    else:
        return "Real_time"