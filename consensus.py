import requests
import json
import os
import hashlib
import time

# Cache settings
CACHE_DIR = "cache_consensus"
CACHE_EXPIRY = 86400  # Cache expiry time in seconds (e.g., 86400 seconds = 24 hours)

def get_cache_filename(query):
    # Create a hashed filename for the query to avoid issues with file naming
    query_hash = hashlib.md5(query.encode('utf-8')).hexdigest()
    return os.path.join(CACHE_DIR, f"{query_hash}.json")

def is_cache_valid(cache_file):
    # Check if the cache file exists and is not expired
    if os.path.exists(cache_file):
        file_time = os.path.getmtime(cache_file)
        if (time.time() - file_time) < CACHE_EXPIRY:
            return True
    return False

def read_cache(cache_file):
    # Read data from the cache file
    with open(cache_file, 'r') as file:
        return json.load(file)

def write_cache(cache_file, data):
    # Write data to the cache file
    os.makedirs(os.path.dirname(cache_file), exist_ok=True)
    with open(cache_file, 'w') as file:
        json.dump(data, file)

def query_consensus(query):
    base_url = "https://consensus.app/api/paper_search/"
    params = {
        "query": query,
        "page": 0,
        "size": 10
    }

    cache_file = get_cache_filename(query)

    if is_cache_valid(cache_file):
        return read_cache(cache_file)

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raises an error for bad responses
        data = response.json()
        write_cache(cache_file, data)  # Update cache
        return data

    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return None

# Example usage
result = query_consensus("What are the benefits of vitamin D?")
print(result)
