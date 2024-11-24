from flask import Flask, render_template, request, jsonify
from chatbot import PersonalizedChatbot
import os

app = Flask(__name__)
chatbot = PersonalizedChatbot(name="ismael")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    response = chatbot.chat(user_message)
    return jsonify(response)

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