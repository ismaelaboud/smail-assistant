from google_auth import get_google_auth
from googleapiclient.discovery import build

def test_google_services():
    try:
        # Get credentials
        creds = get_google_auth()
        
        # Test Gmail API
        gmail = build('gmail', 'v1', credentials=creds)
        gmail_profile = gmail.users().getProfile(userId='me').execute()
        print(f"Gmail connected for: {gmail_profile['emailAddress']}")
        
        # Test Docs API
        docs = build('docs', 'v1', credentials=creds)
        print("Docs API connected")
        
        # Test Sheets API
        sheets = build('sheets', 'v4', credentials=creds)
        print("Sheets API connected")
        
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    test_google_services() 