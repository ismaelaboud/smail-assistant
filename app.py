from flask import Flask, render_template, request, jsonify
from chatbot import PersonalizedChatbot
import os
from dotenv import load_dotenv
import requests
from google_auth import get_google_auth
from googleapiclient.discovery import build

# Load environment variables
load_dotenv()

app = Flask(__name__)
chatbot = PersonalizedChatbot(name="ismael")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        message = request.json.get('message')
        
        # Get timeout from env or use default
        timeout = int(os.getenv('REQUEST_TIMEOUT', 30))
        
        # Update API call with timeout and required parameters
        response = requests.post(
            'https://api.mistral.ai/v1/chat/completions',
            headers={
                'Authorization': f"Bearer {os.getenv('MISTRAL_API_KEY')}",
                'Content-Type': 'application/json'
            },
            json={
                'model': 'mistral-tiny',  # Specify the model
                'messages': [
                    {"role": "system", "content": chatbot.system_prompt},  # Add system prompt
                    {"role": "user", "content": message}
                ],
                'temperature': 0.7,  # Add temperature
                'max_tokens': 500  # Add max_tokens
            },
            timeout=timeout
        )
        
        # Handle API errors
        response.raise_for_status()
        
        return jsonify({
            'text': response.json()['choices'][0]['message']['content'],
            'audio': ''  # Add audio processing as needed
        })

    except requests.Timeout:
        return jsonify({
            'text': 'I apologize, but the request timed out. Please try again.',
            'audio': ''
        }), 504
        
    except requests.RequestException as e:
        return jsonify({
            'text': f'I apologize, but there was an error: {str(e)}',
            'audio': ''
        }), 500

@app.route('/open-workspace', methods=['POST'])
def open_workspace():
    workspace = request.json.get('workspace')
    
    try:
        creds = get_google_auth()
        
        urls = {
            'gmail': 'https://mail.google.com',
            'docs': 'https://docs.google.com',
            'sheets': 'https://sheets.google.com',
            'drive': 'https://drive.google.com'
        }
        
        if workspace in urls:
            return jsonify({'url': urls[workspace]})
        
        return jsonify({'error': 'Invalid workspace type'}), 400
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 