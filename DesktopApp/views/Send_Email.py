# views/Send_Email.py
import csv, os, sys
import smtplib
from email.mime.text import MIMEText
import pandas as pd
from datetime import datetime
from .data_utils import read_config, resource_path, CONFIG_FILE, TASK_DATA_FOLDER


# Get the current month and year for file naming and subject lines
today = datetime.now()
month = today.strftime("%B")
year = today.strftime("%Y")

class EmailSender:
    """Handles all logic related to reading data and sending the productivity report via email."""
    
    def read_manager_user_details(self):
        """Reads the manager's email, user's name, and user's email from the config file."""
        config = read_config(CONFIG_FILE)
        
        manager_email = config.get('Manager Email')
        user_firstname = config.get('User First Name')
        user_email = config.get('User Email')

        return manager_email, user_firstname, user_email

    def format_report_details(self, task_file_path):
        """
        Reads a CSV file, calculates a 'Total' column, and formats the data into an HTML table.
        Replaces NaN values with 0 before formatting.
        """
        try:
            # Read the CSV file into a DataFrame
            df = pd.read_csv(task_file_path)
            
            # --- FIX 2: Replace NaN with 0 to prevent "NaN" strings in email ---
            numeric_cols = ['Simple', 'Medium', 'Complex']
            df[numeric_cols] = df[numeric_cols].fillna(0).astype(int) 

            # Calculate the total column
            df['Total'] = df[numeric_cols].sum(axis=1)
            
            # Set display style for table and convert to HTML
            html_table = df.to_html(index=False, classes='table table-striped', justify='left')
            
            # Basic styling for the table in the email
            css_style = """
            <style>
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
                .table-striped tbody tr:nth-of-type(odd) { background-color: #f9f9f9; }
            </style>
            """
            
            return css_style + html_table
        
        except FileNotFoundError:
            return "Productivity data file not found."
        except Exception as e:
            print(f"Error formatting report details: {e}")
            return f"Error generating report table: {e.__class__.__name__}"


    def format_misc_task(self, misc_file_path):
        """Reads the miscellaneous tasks from a text file and formats them for the email body."""
        try:
            with open(misc_file_path, 'r') as f:
                content = f.read()
                # Format text content for HTML, preserving line breaks
                html_content = content.replace('\n', '<br>')
                return f"<p>{html_content}</p>"
        except FileNotFoundError:
            return "<p>No miscellaneous tasks recorded for this month.</p>"
        except Exception as e:
            return f"<p>Error reading miscellaneous tasks: {e}</p>"


    def send_report_email(self, manager_email, user_firstname, user_email, report_details, misc_tasks_details):
        """Connects to SMTP and sends the email."""
        # Constants for email credentials
        TASKSNAP_EMAIL = "tasksnapjournal@gmail.com"
        TASKSNAP_PASSWORD = "inxw gskm nqls grai"
        
        if not TASKSNAP_EMAIL or not TASKSNAP_PASSWORD:
            print("Email aborted: TaskSnap credentials missing from config.")
            return False
        
        if not manager_email or not user_email:
            print("Email aborted: Manager or User email missing.")
            return False

        try:
            # Compose the email message
            subject = f"{user_firstname}'s Productivity Report - {month} {year}"
            body = f'''<div style=\"color: black !important;\">
            Dear Manager, <br><br>

            Please find the productivity details of {user_firstname} for the month of {month}.<br>
            {report_details}<br><br>

            Please find the other miscellaneous tasks done:<br>
            {misc_tasks_details}<br><br>
            
            Best regards,<br>
            Your TaskSnap Journal
            </div>'''

            msg = MIMEText(body, 'html')
            msg['Subject'] = subject
            msg['From'] = TASKSNAP_EMAIL
            msg['To'] = manager_email
            msg['Cc'] = user_email

            # Connect to the SMTP server (e.g., Gmail)
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(TASKSNAP_EMAIL, TASKSNAP_PASSWORD)
                recipients = [manager_email, user_email]
                server.sendmail(TASKSNAP_EMAIL, recipients, msg.as_string())
            
            print("Report sent successfully!")
            return True

        except Exception as e:
            print(f"Error sending email: {e}")
            return False
