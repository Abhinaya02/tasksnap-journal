# Task_Scheduler.py
import datetime
import os
import platform
import sys

try:
    import win32com.client
    HAS_SCHEDULER = (platform.system() == "Windows")
except ImportError:
    print("Warning: 'win32com.client' module not found. Scheduled tasks will not be created.")
    HAS_SCHEDULER = False

from .data_utils import read_config

def create_logon_task(config):
    """Creates or updates a scheduled task to launch ToDo popup 1 hour after shift starts."""
    if not HAS_SCHEDULER:
        print("Skipping ToDo task creation: win32com.client not available.")
        return
    
    try:
        scheduler = win32com.client.Dispatch("Schedule.Service")
        scheduler.Connect()
        root_folder = scheduler.GetFolder("\\")
        
        TASK_NAME = "TaskSnap-ToDoViewLaunch"
        
        # Delete existing task if it exists
        try:
            root_folder.DeleteTask(TASK_NAME, 0)
        except Exception:
            pass
        
        task_def = scheduler.NewTask(0)

        shift_start_time_str = config.get('Shift Start Time', '09:00 AM')
        shift_start_time = datetime.datetime.strptime(shift_start_time_str, '%I:%M %p').time()
        
        # Launch 1 hour (60 minutes) after start time
        launch_time = (datetime.datetime.combine(datetime.date.today(), shift_start_time) + datetime.timedelta(hours=1)).time()

        week_offs_str = config.get('Week Offs', '')
        week_off_days = [day.strip().lower() for day in week_offs_str.split(',') if day.strip()] 
        
        # Using a weekly trigger
        TASK_TRIGGER_WEEKLY = 3
        trigger = task_def.Triggers.Create(TASK_TRIGGER_WEEKLY)
        
        trigger.StartBoundary = datetime.datetime.combine(datetime.date.today(), launch_time).isoformat()
        
        # Define days of week
        days_of_week_map = {
            'monday': 1, 'tuesday': 2, 'wednesday': 4, 'thursday': 8, 
            'friday': 16, 'saturday': 32, 'sunday': 64
        }
        
        days_to_run = 0
        for day in days_of_week_map.keys():
            if day not in week_off_days:
                days_to_run |= days_of_week_map[day]
        
        if days_to_run > 0:
            trigger.DaysOfWeek = days_to_run

        # Create action
        TASK_ACTION_EXEC = 0
        action = task_def.Actions.Create(TASK_ACTION_EXEC)
        action.ID = "Launch TaskSnap ToDo Popup"
        
        # FIXED: Correct executable path detection
        if getattr(sys, 'frozen', False):
            # Running as EXE - use the executable directly
            action.Path = sys.executable
            action.Arguments = "--todo-popup"
        else:
            # Running as script - use python
            action.Path = "pythonw.exe"
            action.Arguments = f'"{os.path.abspath(__file__.replace("Task_Scheduler.py", "main.py"))}" --todo-popup'
        
        
        
        # Only set arguments if running as EXE
        if getattr(sys, 'frozen', False):
            action.Arguments = '--todo-popup'
        
        # Set task parameters
        task_def.RegistrationInfo.Description = "Launch TaskSnap ToDo popup 1 hour after shift starts."
        task_def.Settings.Enabled = True
        task_def.Settings.StopIfGoingOnBatteries = False
        task_def.Settings.MultipleInstances = 2  # Allow multiple instances
        task_def.Settings.Hidden = False

        TASK_CREATE_OR_UPDATE = 6
        TASK_LOGON_NONE=0
        root_folder.RegisterTaskDefinition(
            TASK_NAME,
            task_def,
            TASK_CREATE_OR_UPDATE,
            "",
            "",
            TASK_LOGON_NONE
        )
        print(f"✓ Scheduled task '{TASK_NAME}' created successfully")
        
    except Exception as e:
        print(f"Error creating ToDo scheduled task: {e}")


def create_daily_task(config):
    """Creates or updates a scheduled task to launch TaskSnap main window 1 hour before shift ends."""
    if not HAS_SCHEDULER:
        print("Skipping daily task creation: win32com.client not available.")
        return
    
    try:
        scheduler = win32com.client.Dispatch("Schedule.Service")
        scheduler.Connect()
        root_folder = scheduler.GetFolder("\\")
        
        TASK_NAME = "TaskSnap-ProductivityReminder"

        # Delete existing task if it exists
        try:
            root_folder.DeleteTask(TASK_NAME, 0)
        except:
            pass

        task_def = scheduler.NewTask(0)
        shift_end_time_str = config.get('Shift End Time', '05:00 PM')
        shift_end_time = datetime.datetime.strptime(shift_end_time_str, '%I:%M %p').time()
        
        # Launch 1 hour (60 minutes) before end time
        launch_time = (datetime.datetime.combine(datetime.date.today(), shift_end_time) - datetime.timedelta(hours=1)).time()

        week_offs_str = config.get('Week Offs', '')
        week_off_days = [day.strip().lower() for day in week_offs_str.split(',') if day.strip()] 
        
        # Using a weekly trigger
        TASK_TRIGGER_WEEKLY = 3
        trigger = task_def.Triggers.Create(TASK_TRIGGER_WEEKLY)
        
        trigger.StartBoundary = datetime.datetime.combine(datetime.date.today(), launch_time).isoformat()
        
        # Define days of week
        days_of_week_map = {
            'monday': 1, 'tuesday': 2, 'wednesday': 4, 'thursday': 8, 
            'friday': 16, 'saturday': 32, 'sunday': 64
        }
        
        days_to_run = 0
        for day in days_of_week_map.keys():
            if day not in week_off_days:
                days_to_run |= days_of_week_map[day]
        
        if days_to_run > 0:
            trigger.DaysOfWeek = days_to_run

        TASK_ACTION_EXEC = 0
        action = task_def.Actions.Create(TASK_ACTION_EXEC)
        action.ID = "Launch TaskSnap Productivity Reminder"
        
        # FIXED: Correct executable path detection
        if getattr(sys, 'frozen', False):
            # Running as EXE - use the executable directly
            action.Path = sys.executable
            action.Arguments = "--productivity-popup"
        else:
            # Running as script - use python
            action.Path = "pythonw.exe"
            action.Arguments = f'"{os.path.abspath(__file__.replace("Task_Scheduler.py", "main.py"))}" --productivity-popup'
        

        
        # Set task parameters
        task_def.RegistrationInfo.Description = "Launch TaskSnap main window 1 hour before shift ends for productivity reporting."
        task_def.Settings.Enabled = True
        task_def.Settings.StopIfGoingOnBatteries = False
        task_def.Settings.MultipleInstances = 2  # Allow multiple instances
        task_def.Settings.Hidden = False

        TASK_CREATE_OR_UPDATE = 6
        TASK_LOGON_NONE = 0
        root_folder.RegisterTaskDefinition(
            TASK_NAME,
            task_def,
            TASK_CREATE_OR_UPDATE,
            '',
            '',
            TASK_LOGON_NONE
        )
        
        print(f"✅ Scheduled task '{TASK_NAME}' created successfully for {launch_time.strftime('%I:%M %p')}")

    except Exception as e:
        print(f"Error creating productivity reminder task: {e}")