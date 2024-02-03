import hashlib
import os

CACHE_DIRECTORY = 'cache'

def sha256(msg):
    return hashlib.sha256(msg.encode()).hexdigest()

def write_cache(cache_directory, filename, data):
    if data is None or data is "":
        print("Error writing to cache due to empty data")
        return

    if not os.path.exists(cache_directory):
        os.makedirs(cache_directory)
    cache_filepath = os.path.join(cache_directory, filename)
    
    with open(cache_filepath, 'w') as file:
        file.write(data)

def get_cache_data(cache_filepath):
    if not os.path.exists(cache_filepath):
        return None

    with open(cache_filepath, 'r') as file:
        return file.read()