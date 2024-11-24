from flask import Flask, render_template, request, jsonify
from chatbot import PersonalizedChatbot
import os
from dotenv import load_dotenv
import requests

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
        
        # Get response from Mistral AI
        response = requests.post(
            'https://api.mistral.ai/v1/chat/completions',
            headers={
                'Authorization': f"Bearer {os.getenv('MISTRAL_API_KEY')}",
                'Content-Type': 'application/json'
            },
            json={
                'model': 'mistral-tiny',
                'messages': [{"role": "user", "content": message}],
                'temperature': 0.7,
                'max_tokens': 500
            },
            timeout=int(os.getenv('REQUEST_TIMEOUT', 30))
        )
        
        response.raise_for_status()
        bot_response = response.json()['choices'][0]['message']['content']
        
        # Generate audio response
        audio_response = chatbot.text_to_speech(bot_response)
        
        return jsonify({
            'text': bot_response,
            'audio': audio_response
        })

    except Exception as e:
        return jsonify({
            'text': f'I apologize, but there was an error: {str(e)}',
            'audio': ''
        }), 500

@app.route('/update-voice', methods=['POST'])
def update_voice():
    config = request.json
    chatbot.set_voice_properties(
        gender=config.get('gender', 'male'),
        rate=int(config.get('rate', 150)),
        volume=float(config.get('volume', 0.9))
    )
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(debug=True) 