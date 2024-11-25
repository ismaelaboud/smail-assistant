import pyttsx3
import threading
import queue
import base64
import requests
from config import API_KEY

class PersonalizedChatbot:
    def __init__(self, name="ismael"):
        # Mistral API configuration
        self.api_key = API_KEY
        self.api_url = "https://api.mistral.ai/v1/chat/completions"  # Verify this URL
        self.model = "mistral-tiny"  # Use mistral-tiny for testing
        
        self.engine = pyttsx3.init()
        self.name = name
        self.voice_config = {
            'gender': 'male',
            'rate': 150,
            'volume': 0.9
        }
        self._setup_voice()
        self.conversation_history = []
        
        # Simplified system prompt
        self.system_prompt = """You are smail, an AI assistant with Google Workspace integration. 
Commands available:
- /email to@example.com Subject | Body
- /doc Title | Content
- /sheet spreadsheet_id range_name | value1,value2

Always respond as smail and be helpful and friendly."""

        # Remove Google services initialization
        self.google_creds = None
        self.gmail_service = None
        self.docs_service = None
        self.sheets_service = None

    def _setup_voice(self):
        voices = self.engine.getProperty('voices')
        voice_index = 0 if self.voice_config['gender'] == 'male' else 1
        self.engine.setProperty('voice', voices[voice_index].id)
        self.engine.setProperty('rate', self.voice_config['rate'])
        self.engine.setProperty('volume', self.voice_config['volume'])

    def send_email(self, to, subject, body):
        return False, "Email functionality is currently disabled"

    def create_doc(self, title, content):
        return False, "Document creation is currently disabled"

    def update_sheet(self, spreadsheet_id, range_name, values):
        return False, "Sheet updates are currently disabled"

    def chat(self, user_input):
        try:
            # Check for Google-specific commands
            if user_input.startswith('/email'):
                # Format: /email to@example.com Subject | Body
                parts = user_input.split('|')
                if len(parts) == 2:
                    email_parts = parts[0].split(' ')
                    to = email_parts[1]
                    subject = ' '.join(email_parts[2:])
                    body = parts[1].strip()
                    success, message = self.send_email(to, subject, body)
                    return {'text': message, 'audio': ''}

            elif user_input.startswith('/doc'):
                # Format: /doc Title | Content
                parts = user_input.split('|')
                if len(parts) == 2:
                    title = parts[0].replace('/doc', '').strip()
                    content = parts[1].strip()
                    success, message = self.create_doc(title, content)
                    return {'text': message, 'audio': ''}

            elif user_input.startswith('/sheet'):
                # Format: /sheet spreadsheet_id range_name | value1,value2
                parts = user_input.split('|')
                if len(parts) == 2:
                    sheet_parts = parts[0].split(' ')
                    spreadsheet_id = sheet_parts[1]
                    range_name = sheet_parts[2]
                    values = [parts[1].strip().split(',')]
                    success, message = self.update_sheet(spreadsheet_id, range_name, values)
                    return {'text': message, 'audio': ''}

            # Regular chat processing using Mistral API
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_input}
            ]

            # Add conversation history
            if self.conversation_history:
                for i in range(0, len(self.conversation_history), 2):
                    if i+1 < len(self.conversation_history):
                        messages.append({"role": "user", "content": self.conversation_history[i].split("User: ")[1]})
                        messages.append({"role": "assistant", "content": self.conversation_history[i+1].split(f"{self.name}: ")[1]})

            # Make API request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 500
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=10
            )
            response.raise_for_status()
            
            bot_response = response.json()['choices'][0]['message']['content']
            
            # Update conversation history
            self.conversation_history.append(f"User: {user_input}")
            self.conversation_history.append(f"{self.name}: {bot_response}")
            
            # Generate audio response
            audio_queue = queue.Queue()
            def save_audio():
                engine = pyttsx3.init()
                engine.save_to_file(bot_response, 'temp.mp3')
                engine.runAndWait()
                with open('temp.mp3', 'rb') as audio_file:
                    audio_data = audio_file.read()
                    audio_queue.put(base64.b64encode(audio_data).decode())

            audio_thread = threading.Thread(target=save_audio)
            audio_thread.start()
            audio_thread.join()
            
            audio_base64 = audio_queue.get()
            
            return {
                'text': bot_response,
                'audio': audio_base64
            }

        except Exception as e:
            print(f"Error in chat method: {str(e)}")
            return {
                'text': f"I apologize, but I encountered an error. Please try again. Error: {str(e)}",
                'audio': ''
            }

    def text_to_speech(self, text):
        try:
            # Create a queue for the audio data
            audio_queue = queue.Queue()
            
            def save_audio():
                self.engine.save_to_file(text, 'temp.mp3')
                self.engine.runAndWait()
                with open('temp.mp3', 'rb') as audio_file:
                    audio_data = audio_file.read()
                    audio_queue.put(base64.b64encode(audio_data).decode())

            # Run audio generation in a separate thread
            audio_thread = threading.Thread(target=save_audio)
            audio_thread.start()
            audio_thread.join()
            
            # Get the audio data from the queue
            audio_base64 = audio_queue.get()
            return audio_base64
            
        except Exception as e:
            print(f"Error in text_to_speech: {str(e)}")
            return ''

    def set_voice_properties(self, gender='male', rate=150, volume=0.9):
        self.voice_config.update({
            'gender': gender,
            'rate': rate,
            'volume': volume
        })
        self._setup_voice()