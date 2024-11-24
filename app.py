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
        
        # Updated for Pixtral-12B
        response = requests.post(
            'https://api.mistral.ai/v1/chat/completions',
            headers={
                'Authorization': f"Bearer {os.getenv('MISTRAL_API_KEY')}",
                'Content-Type': 'application/json'
            },
            json={
                'model': 'pixtral-12b',  # Changed model to pixtral-12b
                'messages': [
                    {
                        "role": "system",
                        "content": "You are a helpful AI assistant capable of understanding and processing both text and images."
                    },
                    {
                        "role": "user",
                        "content": message
                    }
                ],
                'temperature': 0.7,
                'max_tokens': 1000,  # Increased max tokens for longer responses
                'top_p': 0.9,
                'presence_penalty': 0.1,
                'frequency_penalty': 0.1
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