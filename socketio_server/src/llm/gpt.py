import os
import openai

openai.api_key = os.getenv('MAKEASTORY_GPT_API_KEY')

def submit_round(input_array):
    response = openai.responses.create(
        model = "gpt-5-nano",
        input = input_array,
        
        reasoning = {"effort": "minimal"},
        service_tier = "flex",
        store = False
    )

    response_text = response.output[1].content[0].text
    return response_text