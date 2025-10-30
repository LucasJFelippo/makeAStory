from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv('MAKEASTORY_GPT_API_KEY'))

response = client.responses.create(
  model="gpt-5-nano",
  input="Answer me with 'ok'."
)

print(response)