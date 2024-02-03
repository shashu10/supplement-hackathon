import os
from llms.mistral import mistral
from llms.openai_helper import call_openai
from utils import sha256, get_cache_data, write_cache

class LLM:
    cache_directory = 'cache'

    # Mapping of models to their respective functions
    model_mapping = {
        'gpt-4': call_openai,
        'gpt-4-1106-preview': call_openai,
        'gpt-3.5-turbo': call_openai,
        'mistral-medium': mistral,
        'mistral-tiny': mistral,
        # Add more models here as needed
    }

    @staticmethod
    def query(message, model='gpt-4'):
        if model not in LLM.model_mapping:
            raise ValueError(f"Model '{model}' not supported")

        cache_filename = sha256(message + model)
        cache_filepath = os.path.join(LLM.cache_directory, cache_filename)
        cached_response = get_cache_data(cache_filepath)

        if cached_response:
            return cached_response

        response_function = LLM.model_mapping[model]
        response = response_function(message, model)

        if response:
            write_cache(LLM.cache_directory, cache_filename, response)

        return response