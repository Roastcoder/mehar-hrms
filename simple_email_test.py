#!/usr/bin/env python3
"""
Simple email test for Horilla HRMS
Run this on your server to test email functionality
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import ssl

def test_email():
    print("🧪 Testing Email Configuration...")
    
    # Email settings from database
    smtp_server = "smtp.hostinger.com"
    port = 465
    sender_email = "noreply@marketvry.com"
    password = "Root@637811"
    receiver_email = "yogendra6378@gmail.com"
    
    # Create message
    message = MIMEMultipart("alternative")
    message["Subject"] = "🧪 Horilla HRMS - System Email Test"
    message["From"] = f"Mehar Advisory <{sender_email}>"
    message["To"] = receiver_email
    
    # Create HTML content
    html = f"""
    <html>
      <body>
        <h2>✅ Email System Test - SUCCESS</h2>
        <p>Dear Team,</p>
        <p>This email confirms that your Horilla HRMS email system is working correctly!</p>
        
        <h3>📧 Configuration Details:</h3>
        <ul>
            <li><strong>SMTP Server:</strong> {smtp_server}</li>
            <li><strong>Port:</strong> {port}</li>
            <li><strong>From:</strong> {sender_email}</li>
            <li><strong>SSL:</strong> Enabled</li>
        </ul>
        
        <h3>🎯 What This Means:</h3>
        <p>Your system can now send:</p>
        <ul>
            <li>📧 Employee notifications</li>
            <li>🔑 Password reset emails</li>
            <li>📝 Leave approval notifications</li>
            <li>📊 Reports and alerts</li>
            <li>📋 Template-based emails</li>
        </ul>
        
        <p><strong>Best regards,</strong><br>
        Horilla HRMS System</p>
      </body>
    </html>
    """
    
    # Convert to MIMEText
    part = MIMEText(html, "html")
    message.attach(part)
    
    try:
        # Create secure connection and send email
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        
        print("✅ SUCCESS: Email sent successfully!")
        print(f"📨 Sent to: {receiver_email}")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    test_email()