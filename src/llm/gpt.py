import os
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv('MAKEASTORY_GPT_API_KEY')
)

def submit_round(input_array):
    response = client.chat.completions.create(
        model = "gpt-5-nano",
        messages = input_array,
        

    )

    return response.choices[0].message.content