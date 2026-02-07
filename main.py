import sys
from productivity_tracker import ProductivityTracker
from Send_Email import EmailSender
from datetime import datetime

# Define the constants for file paths
current_date = datetime.now()
month_year_str = current_date.strftime("%m-%Y")
TASK_FILE = f"Tasks/tasks_{month_year_str}.csv"
MISC_FILE = f"Tasks/Misc_{month_year_str}.txt"

def main():
    """Starts the main application."""
    app = ProductivityTracker()
    app.mainloop()

if __name__ == "__main__":
    # Check for command-line arguments for the Scheduled task for sending email
    if len(sys.argv) > 1 and sys.argv[1] == 'send_email':  
        email_sender = EmailSender()
        manager_email, user_firstname, user_email = email_sender.read_manager_user_details()
        report_details = email_sender.format_report_details(TASK_FILE)
        misc_tasks_details = email_sender.format_misc_task(MISC_FILE)
        email_sender.send_report_email(manager_email, user_firstname, user_email, report_details, misc_tasks_details)
    else:
        main()
