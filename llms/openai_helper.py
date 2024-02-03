import os
from openai import OpenAI

client = OpenAI()

def call_openai(message, model='gpt-4'):
    response = client.chat.completions.create(model=model,
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": message}
    ])
    return response.choices[0].message.content