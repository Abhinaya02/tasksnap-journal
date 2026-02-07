# main.py
import customtkinter as ctk
import datetime
import random
import sys
import os
from theme import Theme
from views.dashboard_view import DashboardView
from views.update_info_view import UpdateInfoView
from views.productivity_view import ProductivityView
from views.to_do_view import ToDoView, launch_todo_popup
from views.screen_time_view import ScreenTimeView
from views.data_utils import read_config, get_user_data_path
from views.Task_Scheduler import create_logon_task, create_daily_task
from views.tray_manager import TrayManager
from views.startup_manager import setup_startup_automatically
from views.productivity_view import launch_productivity_popup  # FIX: Correct function name


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class TaskSnapApp(ctk.CTk):
    def __init__(self, start_minimized=False):
        super().__init__()

        # --- Window Configuration ---
        self.title("TaskSnap Journal")
        try:
            self.iconbitmap(resource_path("assets/TaskSnap.ico"))
        except Exception as e:
            print(f"Could not load icon: {e}")
        self.minsize(800, 600)
        
        # Check if this is first run
        self.first_run_file = os.path.join(get_user_data_path(), ".first_run")
        self.is_first_run = not os.path.exists(self.first_run_file)
        
        # Initialize Theme based on system setting
        self.is_dark_mode = ctk.get_appearance_mode() == "Dark"
        new_mode = "Dark" if self.is_dark_mode else "Light"
        ctk.set_appearance_mode(new_mode)
        Theme.set_mode(new_mode)

        # Set initial background color
        self.configure(fg_color=Theme.BACKGROUND)

        # --- View Management ---
        self.current_view = None

        # --- Dynamic Content & Config ---
        self.config = read_config()
        
        user_name = self.config.get('User First Name', '')
        user_email = self.config.get('User Email', '')
        
        greeting = self.get_greeting()
        quote = self.get_random_quote()

        # --- Initialize Views ---
        self.dashboard_view = DashboardView(self, user_name, greeting, quote, self.show_update_info, self.show_productivity, self.show_todo, self.show_screen_time, self.toggle_theme)
        self.update_info_view = UpdateInfoView(self, self.show_dashboard)
        self.productivity_view = ProductivityView(self, self.show_dashboard)
        self.to_do_view = ToDoView(self, self.show_dashboard)
        self.screen_time_view = ScreenTimeView(self, self.show_dashboard)
        
        # Load initial data into the Update Info view
        self.update_info_view.load_current_data(self.config)

        # --- Initialize System Tray ---
        self.tray_manager = TrayManager(self)
        self.tray_manager.start()  # Always start the tray

        # --- Show initial view ---
        if not user_name or not user_email:
            self.show_update_info()
        else:
            self.show_dashboard()
        
        # --- Event Bindings ---
        self.bind("<Configure>", self.on_resize)
        self.protocol("WM_DELETE_WINDOW", self.on_minimize_to_tray)
        
        # Handle minimize to tray
        if start_minimized:
            self.after(100, self.withdraw)
        
        # First run setup
        if self.is_first_run:
            self.after(500, self.handle_first_run)

    # In main.py, replace the handle_first_run method:


    def handle_first_run(self):
        """Handles first-run setup & startup configuration."""
        try:
            with open(self.first_run_file, 'w') as f:
                f.write("1")
        except:
            pass
        
        # Enable startup automatically
        result = setup_startup_automatically()
        
        if result:
            print("✓ TaskSnap configured to start with Windows")
            # Show notification that app will auto-start
            if self.tray_manager and self.tray_manager.is_running:
                self.tray_manager.icon.notify(
                    "TaskSnap will now start automatically with Windows at login.\nYou can disable this in Settings.",
                    "TaskSnap Setup Complete"
                )

    def on_minimize_to_tray(self):
        """Handles window close - minimizes to tray or exits."""
        # If tray is running, minimize to tray
        if self.tray_manager and self.tray_manager.is_running:
            self.withdraw()

            # Show notification on first minimize
            if not hasattr(self, '_shown_tray_notification'):
                self.tray_manager.icon.notify(
                    "TaskSnap is still running in the background.\nRight-click the tray icon for options.",
                    "TaskSnap Minimized"
                )
                self._shown_tray_notification = True
        else:
            # No tray running, so fully exit
            if self.screen_time_view:
                self.screen_time_view.stop_tracking()
            self.destroy()
            sys.exit(0)



    def toggle_theme(self):
        """Central function to toggle the theme for the entire application."""
        self.is_dark_mode = not self.is_dark_mode
        new_mode = "Dark" if self.is_dark_mode else "Light"
        
        ctk.set_appearance_mode(new_mode)
        Theme.set_mode(new_mode)
        
        self.configure(fg_color=Theme.BACKGROUND)
        try:
            self.iconbitmap(resource_path("assets/TaskSnap.ico"))
        except Exception as e:
            print(f"Could not reapply icon after theme change: {e}")
            
        self.dashboard_view.update_ui_colors()
        self.update_info_view.update_ui_colors()
        self.productivity_view.update_ui_colors()
        self.to_do_view.update_ui_colors()
        self.screen_time_view.update_ui_colors()

    def show_dashboard(self):
        """Hides other views and shows the dashboard."""
        if self.current_view:
            self.current_view.pack_forget()
            if self.current_view == self.productivity_view:
                self.unbind("<Button-1>")

        if self.current_view == self.update_info_view:
            try:
                self.config = read_config()
                create_logon_task(self.config)
                create_daily_task(self.config)
            except Exception as e:
                print(f"Failed to create scheduled tasks: {e}")

        self.configure(fg_color=Theme.BACKGROUND)
        self.current_view = self.dashboard_view
        self.current_view.pack(fill="both", expand=True)
        self.dashboard_view.update_ui_colors()

    def show_update_info(self):
        """Hides other views and shows the update info screen."""
        if self.current_view:
            self.current_view.pack_forget()
            if self.current_view == self.productivity_view:
                self.unbind("<Button-1>")

        self.configure(fg_color=Theme.CARD)
        self.current_view = self.update_info_view
        self.current_view.pack(fill="both", expand=True)
        self.update_info_view.update_ui_colors()

    def show_productivity(self):
        """Hides other views and shows the productivity screen."""
        if self.current_view:
            self.current_view.pack_forget()
            
        self.configure(fg_color=Theme.BACKGROUND) 
        self.current_view = self.productivity_view
        self.current_view.pack(fill="both", expand=True)
        self.productivity_view.update_ui_colors()

    def show_todo(self):
        """Hides other views and shows the to-do screen."""
        if self.current_view:
            self.current_view.pack_forget()
            if self.current_view == self.productivity_view:
                self.unbind("<Button-1>")
            
        self.configure(fg_color=Theme.BACKGROUND) 
        self.current_view = self.to_do_view
        self.current_view.pack(fill="both", expand=True)
        self.to_do_view.update_ui_colors()

    def show_screen_time(self):
        """Hides other views and shows the screen time screen."""
        if self.current_view:
            self.current_view.pack_forget()
            if self.current_view == self.productivity_view:
                self.unbind("<Button-1>")

        self.configure(fg_color=Theme.BACKGROUND) 
        self.current_view = self.screen_time_view
        self.current_view.pack(fill="both", expand=True)
        self.screen_time_view.update_ui_colors()

    def on_resize(self, event=None):
        if self.dashboard_view.winfo_exists() and self.dashboard_view.winfo_ismapped():
            self.dashboard_view.update_font_sizes(self.winfo_width())

    def get_greeting(self):
        current_hour = datetime.datetime.now().hour
        if 5 <= current_hour < 12: return "Good morning"
        elif 12 <= current_hour < 18: return "Good afternoon"
        else: return "Good evening"

    def get_random_quote(self):
        try:
            quotes = ["The secret of getting ahead is getting started.", "The best way to predict the future is to create it.", "Don't watch the clock; do what it does. Keep going.", "Well begun is half done.", "The journey of a thousand miles begins with a single step."]
            return random.choice(quotes)
        except Exception:
            return "Stay motivated!"


if __name__ == "__main__":
    start_minimized = False
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--tray":
            start_minimized = True
            
        elif sys.argv[1] == "--todo-popup":
            launch_todo_popup()  # This one is correct
            sys.exit(0)
            
        elif sys.argv[1] == "--productivity-popup":
            # FIX: Use the correct function name
            launch_productivity_popup()
            sys.exit(0)
    
    app = TaskSnapApp(start_minimized=start_minimized)
    app.mainloop()
