
import asyncio
from flask import Flask, render_template, request
import aiohttp
import os
from dotenv import load_dotenv
import json

app = Flask(__name__)
from dotenv import load_dotenv

app = Flask(__name__)

# Load environment variables from .env file
load_dotenv()

# Now you can use the API key
openai_api_key = os.getenv('OPENAI_API_KEY') # Fetch the API key from environment variables

async def fetch_with_backoff(session, url, payload, headers, retries=5, backoff_factor=1):
    for attempt in range(retries):
        async with session.post(url, json=payload, headers=headers) as response:
            if response.status == 429:
                wait = backoff_factor * (2 ** attempt)
                print(f"Rate limit hit, retrying in {wait} seconds...")
                await asyncio.sleep(wait)
            elif response.status == 200:
                return await response.json()
            else:
                response_text = await response.text()
                print(f"Error: {response.status}, Body: {response_text}")
                return None
    raise Exception("Request failed after retries with rate limit errors.")

async def generate_idea_async(session, principle, user_inputs):
    # Constructing the prompt for idea generation
    prompt_text = [{"role":"system","content":f"Generate a unique idea applying the TRIZ inventive principle of {principle}. After describing the idea for {json.dumps(user_inputs)}, evaluate its utility and novelty on a scale from 1 to 10. Ensure the idea is distinct, with a brief description in 25 words, its utility, novelty, and how it addresses specific objectives and contradictions. Combine all of this into a SINGLE LINE OUTPUT."}]
    
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": prompt_text,
        "max_tokens": 200,
        "temperature": 0.7,
        "n": 2
    }
    headers = {
        "Authorization": f"Bearer {openai_api_key}",
        "Content-Type": "application/json"
    }
    url = 'https://api.openai.com/v1/chat/completions'

    response = await fetch_with_backoff(session, url, payload, headers)
    if response:
        ideas = []
        for choice in response['choices']:
            # Extracting the text and formatting as per your requirement
            content = choice['message']['content'].strip()
            ideas.append(content)
        return ideas
    else:
        return []

def generate_idea(principle, user_inputs):
    async def generate():
        async with aiohttp.ClientSession() as session:
            return await generate_idea_async(session, principle, user_inputs)
    return asyncio.run(generate())

@app.route('/', methods=['GET', 'POST'])
def index():
    ideas_output = []
    if request.method == 'POST':
        user_inputs = request.form.to_dict()
        triz_principles =  [
            "Segmentation",
            "Taking out",
            "Local quality",
            "Asymmetry",
            "Merging",
            "Universality",
            "Nesting",
            "Anti-weight",
            "Preliminary anti-action",
            "Preliminary action",
            "Beforehand cushioning",
            "Equipotentiality",
            "The other way round",
            "Spheroidality - Curvature",
            "Dynamics",
            "Partial or excessive actions",
            "Another dimension",
            "Mechanical vibration",
            "Periodic action",
            "Continuity of useful action",
            "Skipping",
            "Blessing in disguise or Turn lemons into lemonade",
            "Feedback",
            "Intermediary",
            "Self-service",
            "Copying",
            "Cheap short-living objects",
            "Replacing mechanical system",
            "Pneumatics and hydraulics",
            "Flexible shells and thin films",
            "Porous materials",
            "Color changes",
            "Homogeneity",
            "Discarding and recovering",
            "Parameter changes",
            "Phase transitions",
            "Thermal expansion",
            "Accelerated oxidation",
            "Inert atmosphere",
            "Composite materials"
        ]
        for principle in triz_principles:
            ideas = generate_idea(principle, user_inputs)
            if ideas:
                for idea in ideas:
                    ideas_output.append(f"Principle {principle}: {idea}")
    
    return render_template('index.html', ideas=ideas_output)

if __name__ == '__main__':
    app.run(debug=True)

