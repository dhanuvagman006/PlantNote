import requests
import json
import markdown

def send_message(user_input):
    url = 'https://openrouter.ai/api/v1/chat/completions'
    
    # API key directly from the uploaded code
    API_KEY = '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'

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
        
        # Check if the response is successful
        response.raise_for_status()  # Raises an error for bad responses (4xx, 5xx)
        
        # Extract markdown content from the response
        data = response.json()
        markdown_text = data.get('choices', [{}])[0].get('message', {}).get('content', 'No response received.')
        
        # Convert markdown text to HTML
        html_response = markdown.markdown(markdown_text)
        
        return html_response
    
    except requests.exceptions.HTTPError as e:
        return f"HTTP error occurred: {e}"
    except requests.exceptions.RequestException as e:
        return f"Request error occurred: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"