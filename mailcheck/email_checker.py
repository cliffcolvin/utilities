import smtplib
import imaplib
import email
import json
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

class EmailChecker:
    def __init__(self):
        # Load config from JSON
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
                self.smtp_server = config.get('smtpServer', 'smtp.gmail.com')
                self.imap_server = config.get('imapServer', 'imap.gmail.com')
                self.email_address = config.get('emailAddress') or os.getenv("EMAIL_ADDRESS")
                self.email_password = config.get('emailPassword') or os.getenv("EMAIL_PASSWORD")
                self.message_contains = config.get('messageContains', '')
                self.message_template = config.get('messageTemplate', '')
                self.message_subject = config.get('messageSubject', 'Email Deprecation Autoresponder Check')
                self.users_to_check = config.get('usersToCheck', [])
        except FileNotFoundError:
            print("Error: config.json not found. Please create it with required fields.")
            raise

        # Status file
        self.status_file = "email_status.json"
        self.users = self.load_status()

    def load_status(self):
        """Load or create status file"""
        if os.path.exists(self.status_file):
            with open(self.status_file, 'r') as f:
                return json.load(f)
        
        # If file doesn't exist, initialize status for all users
        initial_status = {}
        for email in self.users_to_check:  # Now using users from config
            if email:  # Skip empty entries
                initial_status[email] = {
                    "status": "pending",
                    "last_checked": None
                }
        
        # Save the initial status
        with open(self.status_file, 'w') as f:
            json.dump(initial_status, f, indent=4)
        
        return initial_status

    def save_status(self):
        """Save current status to file"""
        with open(self.status_file, 'w') as f:
            json.dump(self.users, f, indent=4)

    def send_emails(self, users_list):
        """Send emails to pending users"""
        smtp_connection = smtplib.SMTP(self.smtp_server, 587)
        smtp_connection.starttls()
        smtp_connection.login(self.email_address, self.email_password)

        for user_email in users_list:
            if user_email not in self.users:
                self.users[user_email] = {"status": "pending", "last_checked": None}
            
            if self.users[user_email]["status"] == "pending":
                msg = MIMEMultipart()
                msg['From'] = self.email_address
                msg['To'] = user_email
                msg['Subject'] = self.message_subject
                
                msg.attach(MIMEText(self.message_template.format(email_address=user_email), 'plain'))
                
                smtp_connection.send_message(msg)
                self.users[user_email]["last_checked"] = datetime.now().isoformat()

        smtp_connection.quit()
        self.save_status()

    def check_responses(self):
        """Check email responses for autoresponders"""
        imap_connection = imaplib.IMAP4_SSL(self.imap_server)
        imap_connection.login(self.email_address, self.email_password)
        imap_connection.select('INBOX')

        # Search for all emails since last check
        _, messages = imap_connection.search(None, 'ALL')

        for msg_num in messages[0].split():
            _, msg_data = imap_connection.fetch(msg_num, '(RFC822)')
            email_body = msg_data[0][1]
            email_message = email.message_from_bytes(email_body)
            
            # Check if it's an auto-response and contains the specified domain
            if self._is_auto_response(email_message) and self.message_contains in str(email_message):
                from_email = email.utils.parseaddr(email_message['From'])[1]
                if from_email in self.users:
                    self.users[from_email]["status"] = "complete"

        imap_connection.close()
        imap_connection.logout()
        self.save_status()

    def _is_auto_response(self, email_message):
        """Check if email is an auto-response"""
        auto_response_headers = [
            'Auto-Submitted',
            'X-Auto-Response-Suppress',
            'X-AutoReply',
        ]
        
        return any(email_message.get(header) for header in auto_response_headers)

def main():
    checker = EmailChecker()
    
    # Run the process
    checker.check_responses()  # First check for any responses
    checker.send_emails(checker.users_to_check)  # Using users from config

    # Display pending users
    pending_users = [email for email, data in checker.users.items() 
                    if data["status"] == "pending"]
    
    if pending_users:
        print("\nThe following users are still pending:")
        for user in pending_users:
            print(f"- {user}")
        print(f"\nTotal pending users: {len(pending_users)}")
    else:
        print("\nNo pending users remaining!")

if __name__ == "__main__":
    main() 