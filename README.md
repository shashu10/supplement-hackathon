# supplement-hackathon


The goal of the hackathon is to create a website that is information about the top common supplements. I have been able to load the information about the supplements into a file in the `summary_cache` folder.  I want to feed this data into GPT-4 and get a summary of the dosage, benefits, and side-effects.  But I want to keep the original source data so a user can query it.  Can you modify the code to leverage GPT-4 to summarize each of these supplements, and store each of the data in a cache so it can be queried by flash later for a website.

Below are the files I have so far:

main.py
```
import requests
from consensus import query_consensus
import os
import json
import logging
from flask import Flask, jsonify

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
supplements = read_supplements()
logging.info(f"Reading {len(supplements)} supplements.")
summaries = [get_supplement_info(supplement) for supplement in supplements]


@app.route('/supplement/<name>')
def get_supplement(name):
    summary = get_supplement_info(name)
    if summary:
        return jsonify(summary)
    return jsonify({"error": "Summary not found"}), 404

app.run(debug=True)  
# if __name__ == '__main__':
#     app.run(debug=True)
```

consensus.py
```
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

```

```llm.py
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
```

```mistral.py
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
```

```openai_helper.py
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
```

Here is an example of the summary_cache for a single supplement

```
{"supplement": "Antioxidants", "data": {"benefits": [{"title": "Antioxidant Phytochemicals for the Prevention and Treatment of Chronic Diseases", "summary": "Antioxidant phytochemicals in vegetables and fruits are responsible for reducing the risk of many chronic diseases, as they possess strong antioxidant and free radical scavenging abilities, as well as anti-inflammatory action.", "year": 2015, "journal": "Molecules"}, {"title": "Improving public health?: The role of antioxidant-rich fruit and vegetable beverages", "summary": "Antioxidant-rich foods may have health benefits in CVD, cancer, neurological decline, and diabetes, but the evidence for specific health benefits is still limited.", "year": 2011, "journal": "Food Research International"}, {"title": "The role of antioxidant supplement in immune system, neoplastic, and neurodegenerative disorders: a point of view for an assessment of the risk/benefit profile", "summary": "Dietary antioxidants, such as glutathione and vitamins, may counteract oxidative damage and modulate oxidative phenomena in chronic diseases like atherosclerosis, diabetes, and cancer.", "year": 2008, "journal": "Nutrition Journal"}, {"title": "Solvent effects on the antioxidant capacity of lipophilic and hydrophilic antioxidants measured by CUPRAC, ABTS/persulphate and FRAP methods.", "summary": "Antioxidants protect cells and macromolecules from the damage of reactive oxygen species (ROS), making them health beneficial compounds.", "year": 2010, "journal": "Talanta"}, {"title": "Why have antioxidants failed in clinical trials?", "summary": "Antioxidant therapies have shown acute benefits in clinical trials, such as N-acetylcysteine.", "year": 2008, "journal": "The American journal of cardiology"}, {"title": "Use of antioxidant supplements and its association with cognitive function in a rural elderly cohort: the MoVIES Project. Monongahela Valley Independent Elders Survey.", "summary": "Antioxidant use was initially associated with better performance on cognitive tests, but after accounting for age, education, and sex, no significant differences were found.", "year": 1998, "journal": "American journal of epidemiology"}, {"title": "Antioxidants: Differing Meanings in Food Science and Health Science.", "summary": "Antioxidants are lauded for quenching reactive oxygen species and preventing chronic diseases, but strong evidence for their beneficial effects is lacking.", "year": 2018, "journal": "Journal of agricultural and food chemistry"}, {"title": "Antioxidant capacity of Brazilian fruit, vegetables and commercially-frozen fruit pulps", "summary": "A high intake of foods rich in natural antioxidants increases the antioxidant capacity and reduces the risk of cancers, heart diseases, and stroke.", "year": 2009, "journal": "Journal of Food Composition and Analysis"}, {"title": "Antioxidants and Skeletal Muscle Performance: \u201cCommon Knowledge\u201d vs. Experimental Evidence", "summary": "Antioxidants are assumed to provide benefits such as better health, reduced aging rate, and improved exercise performance.", "year": 2012, "journal": "Frontiers in Physiology"}, {"title": "Pet food additives.", "summary": "Antioxidants, like vitamins C and E, can promote good health and combat free radical damage in the body.", "year": 1993, "journal": "Journal of the American Veterinary Medical Association"}], "side effects": [{"title": "Antioxidants Accelerate Lung Cancer Progression in Mice", "summary": "Antioxidants like acetylcysteine and vitamin E may have a particularly detrimental effect in lung cancer development by disrupting the ROS-p53 axis.", "year": 2014, "journal": "Science Translational Medicine"}, {"title": "Risks and benefits of antioxidant dietary supplement use during cancer treatment: protocol for a scoping review", "summary": "Oral antioxidant supplementation may reduce side effects and improve patient survival, but other studies suggest it may interfere with chemotherapy and reduce its curative effects.", "year": 2021, "journal": "BMJ Open"}, {"title": "The Double-edged Sword of Antioxidant Supplements on Metabolic Diseases, A Necessity for Quantification of Oxidative Status", "summary": "Over-supplementation of antioxidants can cause imbalanced oxidant homeostasis, potentially causing metabolic diseases.", "year": 2023, "journal": "Archives of Epidemiology &amp; Public Health Research"}, {"title": "Dietary Antioxidants and Human Cancer", "summary": "Antioxidants like selenium, vitamin E, and carotenoids have been shown to reduce the risk of some forms of cancer, such as prostate and colon cancer, and have potential roles as adjuvants in cancer therapy.", "year": 2004, "journal": "Integrative Cancer Therapies"}, {"title": "The Involvement of the Oxidative Stress Status in Cancer Pathology: A Double View on the Role of the Antioxidants", "summary": "Antioxidant protection treatments neutralize harmful effects of ROS, but excessive supplementation can lead to harmful effects and even increase the risk of cancer.", "year": 2021, "journal": "Oxidative Medicine and Cellular Longevity"}, {"title": "Antioxidant Modulation of Hematological Toxicity during Chemotherapy for Breast Cancer", "summary": "Antioxidant drugs may help correct violations occurring in cancer patients by reducing organism resistance and damage to vital organs and systems.", "year": 2017, "journal": "Journal of Cytology and Histology"}, {"title": "Impact of antioxidant supplementation on chemotherapeutic toxicity: A systematic review of the evidence from randomized controlled trials", "summary": "Antioxidant supplementation during chemotherapy holds potential for reducing dose-limiting toxicities.", "year": 2008, "journal": "International Journal of Cancer"}, {"title": "Dietary Antioxidants During Cancer Chemotherapy: Impact on Chemotherapeutic Effectiveness and Development of Side Effects", "summary": "Antioxidants can reduce or prevent many side effects of anticancer drugs, but may also interfere with the anticancer effects of chemotherapy.", "year": 2000, "journal": "Nutrition and Cancer"}, {"title": "Use of antioxidant supplements during breast cancer treatment: a comprehensive review", "summary": "Antioxidant supplements might decrease side effects associated with breast cancer treatment, but the evidence is currently insufficient to inform guidelines.", "year": 2009, "journal": "Breast Cancer Research and Treatment"}, {"title": "Antioxidants in Arrhythmia Treatment\u2014Still a Controversy? A Review of Selected Clinical and Laboratory Research", "summary": "Antioxidants like vitamins C and E can reduce the recurrence of atrial fibrillation after successful electrical cardioversion and protect against AF after cardiac surgery.", "year": 2022, "journal": "Antioxidants"}], "dosage": [{"title": "Plasma-Saturating Intakes of Vitamin C Confer Maximal Antioxidant Protection to Plasma", "summary": "The antioxidant protection afforded by short-term vitamin C supplementation is maximal at the 500\u20131000 mg dosage range.", "year": 2001, "journal": "Journal of the American College of Nutrition"}, {"title": "Bioavailability and antioxidant activity of some food supplements in men and women using the D-Roms test as a marker of oxidative stress.", "summary": "Antioxidants taken in combination at low dosages reduce oxidative stress, with little relevant prooxidant activity detectable.", "year": 2001, "journal": "The Journal of nutrition"}, {"title": "Effects of beta-carotene, vitamin C and E on antioxidant status in hyperlipidemic smokers.", "summary": "Combined antioxidant supplements with 15 mg beta-carotene/day, 500 mg vitamin C/day, and 400 mg alpha-tocopherol equivalent/day increased plasma antioxidant levels and antioxidative enzyme activities in male hyperlipidemic smokers.", "year": 2002, "journal": "The Journal of nutritional biochemistry"}, {"title": "Safety of antioxidant vitamins.", "summary": "Antioxidant vitamins are generally safe, with rare toxic reactions at dosages less than 3200 mg/d for vitamin E and ascorbic acid, and less than 4 g/d for ascorbic acid.", "year": 1996, "journal": "Archives of internal medicine"}, {"title": "Orange Juice Ingestion and Supplemental Vitamin C Are Equally Effective at Reducing Plasma Lipid Peroxidation in Healthy Adult Women", "summary": "Regular consumption of 8 fl. oz. orange juice or supplemental vitamin C (70 mg/day) effectively reduced a marker of lipid peroxidation in plasma.", "year": 2003, "journal": "Journal of the American College of Nutrition"}, {"title": "Development and Validation of an Analytical Method for Carnosol, Carnosic Acid and Rosmarinic Acid in Food Matrices and Evaluation of the Antioxidant Activity of Rosemary Extract as a Food Additive", "summary": "Rosemary extract can be used as an antioxidant, with a limit of detection and quantification of 0.22 to 1.73 g/mL.", "year": 2019, "journal": "Antioxidants"}, {"title": "Life\u2010long supplementation with a low dosage of coenzyme Q10 in the rat: Effects on antioxidant status and DNA damage", "summary": "Lifelong intake of 0.7 mg/kg/day of CoQ10 enhances plasma levels of CoQQ9, CoQ10, \u00ce2-tocopherol, and retinol, and attenuates age-related declines in total antioxidant capacity and DNA damage.", "year": 2005, "journal": "BioFactors"}, {"title": "In vivo antioxidant effect of green tea", "summary": "Total antioxidant capacity of plasma was significantly increased after taking green tea in amounts of 300 and 450 ml.", "year": 2000, "journal": "European Journal of Clinical Nutrition"}, {"title": "Daily quercetin supplementation dose-dependently increases plasma quercetin concentrations in healthy humans.", "summary": "Quercetin supplementation dose-dependently increased plasma quercetin concentrations from 50 to 150 mg/d for 2 weeks in healthy humans.", "year": 2008, "journal": "The Journal of nutrition"}, {"title": "Vitamin C and E supplementation blunts increases in total lean body mass in elderly men after strength training", "summary": "High-dose vitamin C and E supplementation (500 mg of vitamin C and 117.5 mg of vitamin E) blunted muscular adaptations to strength training in elderly men.", "year": 2016, "journal": "Scandinavian Journal of Medicine & Science in Sports"}]}}
```
