# tray_manager.py
import pystray
from PIL import Image, ImageDraw
import threading
import os
import sys

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class TrayManager:
    """Manages the system tray icon and menu for TaskSnap."""
    
    def __init__(self, app_instance):
        self.app = app_instance
        self.icon = None
        self.is_running = False
        
    def load_icon_image(self):
        """Loads or creates the tray icon."""
        # Get the full path using resource_path FIRST
        icon_path = resource_path("assets/TaskSnap.ico")
        
        try:
            # Now check if the resolved path exists
            if os.path.exists(icon_path):
                img = Image.open(icon_path)  # Use icon_path directly, not resource_path again
                # Resize to standard tray icon size
                img = img.resize((64, 64), Image.Resampling.LANCZOS)
                return img
        except Exception as e:
            print(f"Could not load icon: {e}")
        
        # Create a simple icon if file doesn't exist
        width = 64
        height = 64
        image = Image.new('RGB', (width, height), color='#8B5CF6')
        dc = ImageDraw.Draw(image)
        dc.ellipse([10, 10, 54, 54], fill='white', outline='#8B5CF6')
        dc.text((22, 20), "TS", fill='#8B5CF6', font=None)
        
        return image

    def create_menu(self):
        """Creates the system tray menu."""
        return pystray.Menu(
            pystray.MenuItem("📊 Show TaskSnap", self.show_main_window, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("📈 Dashboard", lambda: self.show_view('dashboard')),
            pystray.MenuItem("📋 To-Do List", lambda: self.show_view('todo')),
            pystray.MenuItem("⏱️ Screen Time", lambda: self.show_view('screentime')),
            pystray.MenuItem("📊 Productivity", lambda: self.show_view('productivity')),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("☕ Take a Break", self.take_break),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("⚙️ Settings", lambda: self.show_view('settings')),
            pystray.MenuItem("❌ Exit TaskSnap", self.quit_app)
        )
    
    def show_main_window(self, icon=None, item=None):
        """Shows the main application window."""
        self.app.after(0, self._show_window)
    
    def _show_window(self):
        """Internal method to show window from main thread."""
        self.app.deiconify()
        self.app.lift()
        self.app.focus_force()
        
        # Restore window state if it was minimized
        self.app.state('normal')
    
    def show_view(self, view_name):
        """Shows a specific view in the main window."""
        self.app.after(0, lambda: self._switch_view(view_name))
    
    def _switch_view(self, view_name):
        """Internal method to switch views from main thread."""
        self.app.deiconify()
        self.app.lift()
        self.app.focus_force()
        self.app.state('normal')
        
        # Switch to the requested view
        if view_name == 'dashboard':
            self.app.show_dashboard()
        elif view_name == 'todo':
            self.app.show_todo()
        elif view_name == 'screentime':
            self.app.show_screen_time()
        elif view_name == 'productivity':
            self.app.show_productivity()
        elif view_name == 'settings':
            self.app.show_update_info()
    
    def take_break(self, icon=None, item=None):
        """Triggers a break."""
        if hasattr(self.app, 'screen_time_view'):
            if not self.app.screen_time_view.is_on_break:
                self.app.after(0, self.app.screen_time_view.start_break)
                self.icon.notify("Break started. Take your time to rest! ☕", "TaskSnap")
            else:
                self.icon.notify("You're already on a break! 😊", "TaskSnap")
    

    
    def quit_app(self, icon=None, item=None):
        """Exits the entire application."""
        # Stop tracking and save data
        if hasattr(self.app, 'screen_time_view'):
            self.app.screen_time_view.stop_tracking()
        
        # Stop the icon
        if self.icon:
            self.icon.stop()
        
        # Quit the application
        self.app.after(0, self.app.quit)
    
    def start(self):
        """Starts the system tray icon."""
        if self.is_running:
            return
        
        image = self.load_icon_image()
        menu = self.create_menu()
        
        self.icon = pystray.Icon("TaskSnap", image, "TaskSnap Journal", menu)
        self.is_running = True
        
        # Run icon in separate thread
        icon_thread = threading.Thread(target=self.icon.run, daemon=True)
        icon_thread.start()
    
    def stop(self):
        """Stops the system tray icon."""
        if self.icon and self.is_running:
            self.icon.stop()
            self.is_running = False