import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv('API_KEY')

client = OpenAI(api_key=api_key)

def classify_growth_OR_direct(question):
    content_info = """You are mutual fund classifier which will classify exactly what user is asking about mutual fund in provided question ,
    1)If user is mentoning nothing(only fund name and nothing else) in question or he is asking some detail for Direct Growth fund then return - Direct_Accumulated,
    2)If user is asking any detail of Direct Dividend or Direct  Income or Direct Dividend or Direct Income Reinvestment then return - Direct_Income,
    3)If user is asking any detail of Regulr Growth or Regular Fund then return - Normal_Accumulated,
    4)If user is asking any detail of Regular Dividend or Direct  Income or Regular Dividend or Direct Income Reinvestment then return - Normal_Income
    
    strictly you will return values out of these 4 classes ,Direct_Accumulated,Direct_Income,Normal_Accumulated,Normal_Income
    """
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content":content_info },
            {"role": "user", "content": question}
        ]
    )
    classification_detail = response.choices[0].message.content 
    if classification_detail == 'Direct_Accumulated':
        return 'Direct_Accumulated'
    elif classification_detail == 'Direct_Income':
        return "Direct_Income" 
    elif classification_detail == 'Normal_Accumulated':
        return "Normal_Accumulated"
    elif classification_detail == 'Normal_Income':
        return "Normal_Income"       
    else:
        return "Direct_Accumulated"
def classify_instrument(question):
    prompt = f"""
    Given a input text, classify it into one of the following four financial categories based on the presence of certain keywords and overall context:
 
    mutual_fund: If the question contains any of these keywords - 'mutual fund', 'mutual funds', 'fund', 'funds', 'mutual' (case-insensitive)
 
    indices: If the question contains any of these keywords 'S&P BSE' or 'Nifty' or 'BSE' or 'NSE' (case-insensitive)

    If the text have multiple keywords from different categories then make you descision based on the last detected keyword or overall context, if the text contains keywords like 'PMS' or 'AIF' and if the text does not contain keywords related to any of the above four categories, then classify it as "general_information".
 
    NOTE: Your response should be a single word, strictly chosen from:
    mutual_fund
    indices
    general_information
    """
    # Send the request to the OpenAI API.
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": question}
        ]
    )
    classification = response.choices[0].message.content 
    # Return the classification.
    if classification == 'mutual_fund':
        return 'Mutual_fund'
    elif classification == 'bonds':
        return "bonds" 
    elif classification == 'indices':
        return "indices"
    elif classification == 'equity':
        return "equity"         
    else:
        return "genral_information"