import pyttsx3
import threading
import queue
import base64
import requests
from config import API_KEY
from googleapiclient.discovery import build
from google_auth import get_google_auth
from email.mime.text import MIMEText

class PersonalizedChatbot:
    def __init__(self, name="ismael"):
        # Mistral API configuration
        self.api_key = API_KEY
        self.api_url = "https://api.mistral.ai/v1/chat/completions"  # Verify this URL
        self.model = "mistral-tiny"  # Use mistral-tiny for testing
        
        self.engine = pyttsx3.init()
        self.name = "smail"
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

        # Initialize Google services
        self.google_creds = get_google_auth()
        self.gmail_service = build('gmail', 'v1', credentials=self.google_creds)
        self.docs_service = build('docs', 'v1', credentials=self.google_creds)
        self.sheets_service = build('sheets', 'v4', credentials=self.google_creds)

    def _setup_voice(self):
        voices = self.engine.getProperty('voices')
        voice_index = 0 if self.voice_config['gender'] == 'male' else 1
        self.engine.setProperty('voice', voices[voice_index].id)
        self.engine.setProperty('rate', self.voice_config['rate'])
        self.engine.setProperty('volume', self.voice_config['volume'])

    def send_email(self, to, subject, body):
        try:
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            self.gmail_service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            return True, "Email sent successfully!"
        except Exception as e:
            return False, f"Error sending email: {str(e)}"

    def create_doc(self, title, content):
        try:
            doc = self.docs_service.documents().create(
                body={"title": title}
            ).execute()
            
            self.docs_service.documents().batchUpdate(
                documentId=doc['documentId'],
                body={
                    'requests': [{
                        'insertText': {
                            'location': {'index': 1},
                            'text': content
                        }
                    }]
                }
            ).execute()
            
            return True, f"Document created: https://docs.google.com/document/d/{doc['documentId']}"
        except Exception as e:
            return False, f"Error creating document: {str(e)}"

    def update_sheet(self, spreadsheet_id, range_name, values):
        try:
            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                body={'values': values}
            ).execute()
            return True, "Sheet updated successfully!"
        except Exception as e:
            return False, f"Error updating sheet: {str(e)}"

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

    def set_voice_properties(self, gender='male', rate=150, volume=0.9):
        self.voice_config.update({
            'gender': gender,
            'rate': rate,
            'volume': volume
        })
        self._setup_voice()