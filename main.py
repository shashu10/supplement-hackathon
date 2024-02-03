import requests
from consensus import query_consensus
import os
import json
import logging
from flask import Flask, jsonify
from llms.llm import LLM

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

SUMMARY_CACHE_DIR = "summary_cache"
GPT_4 = "gpt-4-1106-preview"
MISTRAL_MEDIUM = "mistral-medium"

def read_supplements(file_path='supplements.txt'):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file if line.strip()]

def write_summary_cache(supplement, data):
    if not os.path.exists(SUMMARY_CACHE_DIR):
        os.makedirs(SUMMARY_CACHE_DIR)
    cache_file = os.path.join(SUMMARY_CACHE_DIR, f"{supplement}.json")
    with open(cache_file, 'w') as file:
        json.dump(data, file)

def read_summary_cache(supplement):
    cache_file = os.path.join(SUMMARY_CACHE_DIR, f"{supplement}.json")
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as file:
            return json.load(file)
    return None

def get_supplement_info(supplement):
    logging.info(f"Summarizing {supplement}")
    cached_summary = read_summary_cache(supplement)
    if cached_summary:
        logging.info(f"Returning cached summary for {supplement}")
        
        return cached_summary

    aspects = ["benefits", "side effects", "dosage"]
    summary = {"supplement": supplement, "data": {}}

    for aspect in aspects:
        query = f"What are the {aspect} of {supplement}?"
        logging.info("Querying consensus: %s", query)
        result = query_consensus(query)

        if result and result.get("papers"):
            summary["data"][aspect] = [{"title": paper["title"],
                                        "summary": paper["display_text"],
                                        "year": paper["year"],
                                        "journal": paper["journal"]} for paper in result["papers"]]
        else:
            summary["data"][aspect] = "No data found"

    write_summary_cache(supplement, summary)
    return summary

# Example usage
# supplements = read_supplements()
# logging.info(f"Reading {len(supplements)} supplements.")
# summaries = [get_supplement_info(supplement) for supplement in supplements]


def summarize_with_gpt(supplement, supplement_data):
    summaries = {}
    aspects = ["dosage", "benefits", "side effects"]

    for aspect in aspects:
        # Construct a prompt for GPT-4 to summarize each aspect
        prompt = f"Summarize the key points about the {aspect} of {supplement}: \n\n"
        for item in supplement_data['data'][aspect]:
            prompt += f"- {item['summary']} ({item['journal']}, {item['year']})\n"

        # Use GPT-4 to generate the summary for each aspect
        summary_text = LLM.query(prompt, model='gpt-4')
        references = [f"{item['title']} ({item['journal']}, {item['year']})" for item in supplement_data['data'][aspect]]

        summaries[aspect] = {
            "summary": summary_text,
            "references": references
        }

    return summaries


@app.route('/supplement/<name>')
def get_supplement(name):
    supplement_data = get_supplement_info(name)
    if supplement_data:
        summary = summarize_with_gpt(name, supplement_data)
        return jsonify(summary)
    return jsonify({"error": "Summary not found"}), 404

app.run(debug=True)  
# if __name__ == '__main__':
#     app.run(debug=True)