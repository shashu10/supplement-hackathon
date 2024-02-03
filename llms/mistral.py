import os
import requests

def mistral(message, model='mistral-tiny'):
    api_key = os.environ.get('MISTRAL_API_KEY')
    if not api_key:
        raise ValueError("MISTRAL_API_KEY environment variable is not set")

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    data = {
        'model': model,
        'messages': [{'role': 'user', 'content': message}]
    }

    api_url = 'https://api.mistral.ai/v1/chat/completions'
    response = requests.post(api_url, headers=headers, json=data)

    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None