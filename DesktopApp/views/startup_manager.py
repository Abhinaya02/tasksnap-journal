# startup_manager.py
import os
import sys
import winreg

def is_startup_enabled():
    """Checks if TaskSnap is set to run at startup."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_READ
        )
        try:
            winreg.QueryValueEx(key, "TaskSnap")
            winreg.CloseKey(key)
            return True
        except WindowsError:
            winreg.CloseKey(key)
            return False
    except Exception as e:
        print(f"Error checking startup: {e}")
        return False

def enable_startup():
    """Adds TaskSnap to Windows startup (Registry method - simpler than Task Scheduler)."""
    try:
        # Get executable path
        if getattr(sys, 'frozen', False):
            # Running as EXE
            exe_path = sys.executable
            startup_command = f'"{exe_path}" --tray'
        else:
            # Running as script
            exe_path = "pythonw.exe"
            main_path = os.path.abspath("main.py")
            startup_command = f'"{exe_path}" "{main_path}" --tray'
        
        # Open registry key
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )
        
        # Set the value
        winreg.SetValueEx(key, "TaskSnap", 0, winreg.REG_SZ, startup_command)
        winreg.CloseKey(key)
        
        print("TaskSnap added to startup successfully!")
        return True
        
    except Exception as e:
        print(f"Error enabling startup: {e}")
        return False


def disable_startup():
    """Removes TaskSnap from Windows startup."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )
        
        try:
            winreg.DeleteValue(key, "TaskSnap")
            print("✅ TaskSnap removed from startup successfully!")
        except WindowsError:
            pass  # Value doesn't exist
        
        winreg.CloseKey(key)
        return True
    except Exception as e:
        print(f"Error disabling startup: {e}")
        return False

def setup_startup_automatically():
    """Automatically enables startup on first run without asking."""
    if not is_startup_enabled():
        success = enable_startup()
        if success:
            print("🚀 TaskSnap will now start automatically with Windows!")
        return success
    return True