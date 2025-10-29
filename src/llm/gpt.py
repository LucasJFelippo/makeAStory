import os
import openai

openai.api_key = os.getenv('MAKEASTORY_GPT_API_KEY')

def submit_round(input_array):
    response = openai.Completion.create(
        model = "gpt-5-nano",
        prompt = input_array,
        
        reasoning = {"effort": "minimal"},
        service_tier = "flex",
        store = False,
        
        temperature = 0.7
    )

    return response