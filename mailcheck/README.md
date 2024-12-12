# Email Deprecation Autoresponder Check

This script is designed to check if users have setup email deprecation autoresponders. If they don't, it will send them an email reminder.

## Setup

1. Create a config.json file with the following fields:
    - smtpServer: The SMTP server to use for sending emails.
    - imapServer: The IMAP server to use for checking email responses.
    - emailAddress: The email address to use for sending and checking emails.
    - emailPassword: The password for the email address to send from.
    - messageContains: The text that the email must contain to be considered complete.
    - messageTemplate: The template for the email message to send reminding users to set this up.
    - messageSubject: The subject of the email message to send reminding users to set this up.
    - usersToCheck: A list of email addresses to check.

2. Run the script.

3. The script will check the email addresses in the config.json file and send an email to each user if they have not responded to the email.    
