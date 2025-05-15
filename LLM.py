import requests
import json
import markdown
import os
from dotenv import load_dotenv
import re
load_dotenv()
def send_message(user_input):
    url = 'https://openrouter.ai/api/v1/chat/completions'
    user_input = """Provide agricultural info on a given species covering:

Types (scientific & common names)

Common diseases

Nutrient needs

Best harvest season

Farming needs & cost

Market price in India

Ideal temperature & climate """+user_input
    # API key directly from the uploaded code
    API_KEY = os.getenv('LLM_API_KEY') 

    if not API_KEY:
        return "Error: API Key is missing."

    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'HTTP-Referer': 'https://www.sitename.com',
        'X-Title': 'SiteName',
        'Content-Type': 'application/json',
    }
    
    body = {
        'model': 'deepseek/deepseek-r1:free',
        'messages': [{'role': 'user', 'content': user_input}],
    }

    try:
        # Use the json parameter for automatic JSON encoding
        response = requests.post(url, headers=headers, json=body)
        
        response.raise_for_status()  # Raises an error for bad responses (4xx, 5xx)
        
        # Extract markdown content from the response
        data = response.json()
        markdown_text = data.get('choices', [{}])[0].get('message', {}).get('content', 'No response received.')
        # return(markdown_text)
        # Convert markdown text to HTML
        html_response = markdown.markdown(markdown_text)
        html_response = re.sub(r'<hr\s*/?>', '<div class="mt-4"></div>', html_response)

        
        return html_response
    
    except requests.exceptions.HTTPError as e:
        return f"HTTP error occurred: {e}"
    except requests.exceptions.RequestException as e:   
        return f"Request error occurred: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"