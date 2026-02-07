import tkinter as tk
import customtkinter as ctk
import time
import threading
import pygetwindow as gw
import json
import os
from datetime import date, timedelta, datetime
import math
from theme import Theme
from PIL import Image
from .data_utils import get_user_data_path, resource_path, SCREEN_TIME_FILE, read_config, update_google_sheet_screen_time
from tkinter import messagebox  # Ensure messagebox is imported

# Windows API imports for rounded corners (Windows-specific) - Add this after your existing imports
import ctypes
from ctypes import wintypes

# Windows API constants and functions for rounded window clipping
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x80000
WS_EX_TRANSPARENT = 0x20  # Optional: Makes window click-through if needed (not used here)

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

def create_rounded_region(hwnd, radius):
    """Creates a rounded rectangle region and sets it as the window's region."""
    # Get the actual window dimensions
    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    
    # Calculate width and height
    width = rect.right - rect.left
    height = rect.bottom - rect.top
    
    # Create a rounded rectangle region with actual dimensions
    hRgn = gdi32.CreateRoundRectRgn(0, 0, width, height, radius, radius)
    
    if not hRgn:
        return False
    
    # Apply the region to the window
    result = user32.SetWindowRgn(hwnd, hRgn, True)
    
    # Note: Don't delete the region - Windows owns it after SetWindowRgn
    return result != 0


# --- CONFIGURATION ---
# Time (in seconds) after which a break reminder will pop up
WORK_THRESHOLD_SECONDS = 600  # 600 # 60 minutes
# ---------------------


def tint_icon(image_path, color_hex, size=(40, 40)):
    """
    Tints a PNG icon to match the theme color.
    Similar to the function used in dashboard_view.py
    """
    try:
        from PIL import ImageOps

        # Load the image and convert to RGBA
        original_img = Image.open(resource_path(image_path)).convert('RGBA')

        # Convert hex color to RGB tuple
        rgb_tuple = tuple(int(color_hex.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))

        # Create a tinted version
        tinted_img = Image.new('RGBA', original_img.size, rgb_tuple)
        alpha_mask = original_img.split()[-1]

        # Composite the images
        final_img = Image.new('RGBA', original_img.size)
        final_img.paste(tinted_img, (0, 0), mask=alpha_mask)

        return ctk.CTkImage(light_image=final_img, dark_image=final_img, size=size)
    except Exception as e:
        print(f"Error tinting icon {image_path}: {e}")
        return None


class BreakReminder(ctk.CTkToplevel):
    def __init__(self, master, message, on_take_break):
        super().__init__(master)
        self.master = master
        self.on_take_break = on_take_break
        
        self.title("Break Reminder")
        self.resizable(False, False)
        
        # FIX: Add icon with resource_path
        try:
            self.iconbitmap(resource_path("assets/TaskSnap.ico"))
        except Exception as e:
            print(f"Could not load icon: {e}")
        
        # Remove window decorations first
        self.overrideredirect(True)
        
        # Set size
        width = 500
        height = 380
        
        # Configure the toplevel with a background that will show rounded corners
        self.configure(fg_color="#000001")  # Almost black, will be made transparent
        
        # Set transparency
        self.attributes("-alpha", 0.96)
        self.attributes("-transparentcolor", "#000001")
        
        # Main container with rounded corners - this creates the visual rounded effect
        self.main_container = ctk.CTkFrame(
            self,
            corner_radius=20,
            fg_color=("#2A2D3A", "#1E2130"),
            border_width=2,
            border_color=Theme.ACCENT_PURPLE
        )
        self.main_container.pack(fill="both", expand=True, padx=8, pady=8)
        
        # Custom title bar (draggable)
        title_bar = ctk.CTkFrame(
            self.main_container,
            height=50,
            corner_radius=0,
            fg_color=Theme.ACCENT_PURPLE
        )
        title_bar.pack(fill="x", padx=0, pady=0, side="top")
        title_bar.pack_propagate(False)
        
        # Make title bar draggable
        title_bar.bind("<Button-1>", self.start_move)
        title_bar.bind("<B1-Motion>", self.do_move)
        
        title_label = ctk.CTkLabel(
            title_bar,
            text="⏰ Break Reminder",
            font=Theme.FONT_SUBTITLE,
            text_color="white"
        )
        title_label.pack(side="left", padx=20, pady=12)
        title_label.bind("<Button-1>", self.start_move)
        title_label.bind("<B1-Motion>", self.do_move)
        
        # Content frame
        content_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=25, pady=20)
        
        ctk.CTkLabel(
            content_frame,
            text="Time to Rest!",
            font=Theme.FONT_HEADER,
            text_color="white"
        ).pack(pady=(5, 10))
        
        ctk.CTkLabel(
            content_frame,
            text=message,
            font=Theme.FONT_NORMAL,
            wraplength=400,
            text_color="#E0E0E0"
        ).pack(pady=10)
        
        # Dropdown for snooze options
        snooze_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        snooze_frame.pack(pady=15)
        
        ctk.CTkLabel(
            snooze_frame,
            text="Remind me in:",
            font=Theme.FONT_NORMAL,
            text_color="white"
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.snooze_options = ["5 minutes", "10 minutes", "15 minutes", "30 minutes"]
        self.snooze_dropdown = ctk.CTkComboBox(
            snooze_frame,
            values=self.snooze_options,
            state="readonly",
            width=140,
            font=Theme.FONT_NORMAL,
            fg_color=("#3A3D4A", "#2A2D3A"),
            button_color=Theme.ACCENT_PURPLE,
            button_hover_color=Theme.ACCENT_PURPLE,
            border_color=Theme.ACCENT_PURPLE
        )
        self.snooze_dropdown.set("5 minutes")
        self.snooze_dropdown.pack(side=tk.LEFT)
        
        # Button frame
        button_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        button_frame.pack(pady=20, fill="x")
        
        ctk.CTkButton(
            button_frame,
            text="Take a Break Now",
            command=self.take_break_action,
            fg_color=Theme.ACCENT_PURPLE,
            hover_color=("#9D77E8", Theme.ACCENT_PURPLE),
            width=190,
            height=45,
            font=Theme.FONT_NORMAL,
            corner_radius=12
        ).pack(side=tk.LEFT, padx=5, expand=True)
        
        ctk.CTkButton(
            button_frame,
            text="Snooze",
            command=self.ignore_action,
            fg_color=("#4A4D5A", "#3A3D4A"),
            hover_color=("#5A5D6A", "#4A4D5A"),
            width=190,
            height=45,
            font=Theme.FONT_NORMAL,
            corner_radius=12
        ).pack(side=tk.RIGHT, padx=5, expand=True)
        
        # Position and show window
        self.update_idletasks()
        self.geometry(f'{width}x{height}')
        
        # Center the window
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
        
        # Make window topmost
        self.attributes("-topmost", True)
        
        # Final visibility
        self.deiconify()
        self.lift()
        self.focus_force()
    
    def start_move(self, event):
        self.x = event.x
        self.y = event.y
    
    def do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.winfo_x() + deltax
        y = self.winfo_y() + deltay
        self.geometry(f"+{x}+{y}")
    
    def take_break_action(self):
        """Action when the user chooses to take a break."""
        self.withdraw()
        self.on_take_break(start_break=True, snooze_minutes=0)
        self.after(100, self.destroy)
    
    def ignore_action(self):
        """Action when the user chooses to snooze the reminder."""
        self.withdraw()
        selected = self.snooze_dropdown.get()
        snooze_minutes = int(selected.split()[0])
        self.on_take_break(start_break=False, snooze_minutes=snooze_minutes)
        self.after(100, self.destroy)


class LiveTimersPopup(ctk.CTkToplevel):
    def __init__(self, master, mainview):
        super().__init__(master)
        self.mainview = mainview
        
        self.title("Timers Active")
        self.resizable(False, False)
        
        # FIX: Add icon with resource_path
        try:
            self.iconbitmap(resource_path("assets/TaskSnap.ico"))
        except Exception as e:
            print(f"Could not load icon: {e}")
        
        # Remove window decorations first
        self.overrideredirect(True)
        
        # Set size
        width = 400
        height = 450
        
        # Configure the toplevel with a background that will show rounded corners
        self.configure(fg_color="#000001")  # Almost black, will be made transparent
        
        # Set transparency
        self.attributes("-alpha", 0.96)
        self.attributes("-transparentcolor", "#000001")
        
        # Main container with rounded corners
        self.main_container = ctk.CTkFrame(
            self,
            corner_radius=20,
            fg_color=("#2A2D3A", "#1E2130"),
            border_width=2,
            border_color=Theme.ACCENT_PURPLE
        )
        self.main_container.pack(fill="both", expand=True, padx=8, pady=8)
        
        # Custom title bar (draggable)
        title_bar = ctk.CTkFrame(
            self.main_container,
            height=50,
            corner_radius=0,
            fg_color=Theme.ACCENT_PURPLE
        )
        title_bar.pack(fill="x", padx=0, pady=0, side="top")
        title_bar.pack_propagate(False)
        
        # Make title bar draggable
        title_bar.bind("<Button-1>", self.start_move)
        title_bar.bind("<B1-Motion>", self.do_move)
        
        title_label = ctk.CTkLabel(
            title_bar,
            text="⏱️ Break Mode Active",
            font=Theme.FONT_SUBTITLE,
            text_color="white"
        )
        title_label.pack(side="left", padx=20, pady=10)
        title_label.bind("<Button-1>", self.start_move)
        title_label.bind("<B1-Motion>", self.do_move)
        
        # Content area
        content_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Daily Screen Time Card
        screen_time_card = ctk.CTkFrame(
            content_frame,
            corner_radius=15,
            fg_color=("#3A3D4A", "#2A2D3A"),
            border_width=1,
            border_color=("#4A4D5A", "#3A3D4A")
        )
        screen_time_card.pack(fill="x", pady=(0, 15))
        
        # Header with monitor icon
        header_frame = ctk.CTkFrame(screen_time_card, fg_color="transparent")
        header_frame.pack(pady=(20, 5))

        monitor_icon = tint_icon("assets/monitor_icon.png", "#5DADE2", size=(24, 24))
        if monitor_icon:
            icon_label = ctk.CTkLabel(header_frame, image=monitor_icon, text="")
            icon_label.pack(side="left", padx=(0, 8))
            self.monitor_icon_img = monitor_icon

        ctk.CTkLabel(
            header_frame,
            text="Daily Screen Time",
            font=Theme.FONT_SUBTITLE,
            text_color="white"
        ).pack(side="left")
        
        self.total_screen_time_label = ctk.CTkLabel(
            screen_time_card,
            text="00:00:00",
            font=mainview.title_number_font,
            text_color=Theme.ACCENT_BLUE
        )
        self.total_screen_time_label.pack(pady=(5, 20))
        
        # Break Timer Card (emphasized)
        break_timer_card = ctk.CTkFrame(
            content_frame,
            corner_radius=15,
            fg_color=("#3A3D4A", "#2A2D3A"),
            border_width=2,
            border_color=Theme.ACCENT_PURPLE
        )
        break_timer_card.pack(fill="x", pady=(0, 20))
        
        # Header with coffee icon
        header_frame2 = ctk.CTkFrame(break_timer_card, fg_color="transparent")
        header_frame2.pack(pady=(20, 5))

        coffee_icon = tint_icon("assets/coffee.png", Theme.ACCENT_PURPLE, size=(24, 24))
        if coffee_icon:
            icon_label2 = ctk.CTkLabel(header_frame2, image=coffee_icon, text="")
            icon_label2.pack(side="left", padx=(0, 8))
            self.coffee_icon_img = coffee_icon

        ctk.CTkLabel(
            header_frame2,
            text="Break Timer",
            font=Theme.FONT_SUBTITLE,
            text_color=Theme.ACCENT_PURPLE
        ).pack(side="left")
        
        self.break_timer_label = ctk.CTkLabel(
            break_timer_card,
            text="00:00:00",
            font=mainview.title_number_font,
            text_color=Theme.ACCENT_PURPLE
        )
        self.break_timer_label.pack(pady=(5, 20))
        
        # End Break Button
        check_icon = tint_icon("assets/check.png", "white", size=(20, 20))

        ctk.CTkButton(
            content_frame,
            text=" End Break & Return to Work",
            image=check_icon if check_icon else None,
            command=mainview.start_work,
            corner_radius=12,
            font=Theme.FONT_NORMAL,
            fg_color=Theme.ACCENT_PURPLE,
            hover_color=("#9D77E8", Theme.ACCENT_PURPLE),
            height=50,
            width=340
        ).pack(pady=(0, 10))
        
        # Position and show window
        self.update_idletasks()
        self.geometry(f'{width}x{height}')
        
        # Center the window
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
        
        # Make window topmost
        self.attributes("-topmost", True)
        
        # Final visibility
        self.deiconify()
        self.lift()
        self.focus_force()
    
    def start_move(self, event):
        self.x = event.x
        self.y = event.y
    
    def do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.winfo_x() + deltax
        y = self.winfo_y() + deltay
        self.geometry(f"+{x}+{y}")
    
    def update_timers(self, total_time_str, break_time_str):
        """Method to update the labels from the main thread."""
        self.total_screen_time_label.configure(text=total_time_str)
        self.break_timer_label.configure(text=break_time_str)


# Function to load PNG icon for window title bar
def load_png_image(path, size=(25, 25)):
    """
    Loads a PNG image asset and returns a CTkImage object with theme-dependent colors.
    The function now ensures the image is properly converted to a luminance mask 
    to preserve transparency before coloring.
    """
    try:
        # 1. Load and Resize
        pil_image = Image.open(resource_path(path)).resize(size, Image.Resampling.LANCZOS)
        
        # 2. Separate Alpha Channel (Transparency)
        # This is critical for icons to prevent them from looking like solid squares.
        if pil_image.mode != 'RGBA':
            pil_image = pil_image.convert('RGBA')
        
        # Create a luminance mask (L mode) from the icon content
        icon_mask = pil_image.split()[-1] # Get the Alpha channel (mask)

        # Define the colors for light and dark modes (matching typical text color)
        LIGHT_ICON_COLOR = (51, 51, 51)  # Dark gray (for light mode background)
        DARK_ICON_COLOR = (238, 238, 238) # Light gray (for dark mode background)

        # 3. Create the Light Mode Icon (Dark Color)
        light_colorized = Image.new('RGB', pil_image.size, LIGHT_ICON_COLOR)
        light_pil = light_colorized.putalpha(icon_mask) or light_colorized.convert("RGBA")

        # 4. Create the Dark Mode Icon (Light Color)
        dark_colorized = Image.new('RGB', pil_image.size, DARK_ICON_COLOR)
        dark_pil = dark_colorized.putalpha(icon_mask) or dark_colorized.convert("RGBA")
        
        # 5. Return CTkImage with separate images for light and dark themes
        return ctk.CTkImage(light_image=light_pil, dark_image=dark_pil, size=size)
        
    except FileNotFoundError:
        print(f"Image asset not found at: {path}")
        return None
    except Exception as e:
        print(f"Error loading PNG image from {path}: {e}")
        return None
# Hardcoded application categories for demonstration.
APP_CATEGORIES = {
    "Work": ["visual studio code", "jira", "excel", "slack", "outlook", "github", "word"],
    "Social Media": ["facebook", "twitter", "instagram", "tiktok", "whatsapp"],
    "Learning": ["youtube", "udemy", "coursera", "stack overflow"],
    "Entertainment": ["spotify", "vlc media player", "netflix", "prime video", "steam", "valorant", "league of legends"],
    "File/System": ["file explorer", "notepad", "edit"],
    "Communication": ["zoom", "discord", "skype", "teams"],
    "Browsing": ["chrome", "firefox", "edge", "opera", "brave"],
    "Design": ["photoshop", "illustrator", "figma", "canva"]
}

def get_category(app_title):
    """Assigns an app to a predefined category."""
    title_lower = app_title.lower()
    for category, keywords in APP_CATEGORIES.items():
        for keyword in keywords:
            if keyword.lower() in title_lower:
                return category
    return "Other"

class ScreenTimeView(ctk.CTkFrame):
    def __init__(self, master, back_to_dashboard_callback):
        super().__init__(master, fg_color=Theme.BACKGROUND)
        self.back_to_dashboard = back_to_dashboard_callback
        self.master_window = master 
        self.last_gui_update = time.time()  # Track last GUI update time
        self.gui_update_counter = 0  # Counter for less frequent updates
        
        self.DATA_FOLDER = get_user_data_path()

        try:
            self.back_arrow_icon = load_png_image("assets/back_arrow_icon.png")
        except FileNotFoundError as e:
            print(f"Warning: Icon file not found in ScreenTimeView: {e}")
            self.back_arrow_icon = None

        self.title_number_font = ctk.CTkFont(*Theme.FONT_TITLE) 
        
        self.tracking = True
        self.weekly_data = []
        
        os.makedirs(self.DATA_FOLDER, exist_ok=True)
        self.load_data()

        self.start_time = time.time()
        self.last_update_time = time.time()
        self.chart_colors = ["#60A5FA", "#4ADE80", "#FACC15", "#A78BFA", "#F87171", "#34D399", "#8B5CF6", "#F59E0B"]

        self.is_on_break = False
        self.break_start_time = None
        
        # --- NEW: Break Reminder State ---
        self.continuous_work_time = 0.0
        self.is_reminder_active = False
        self.reminder_window = None
        self.popup_timer_window = None # Stores the LiveTimersPopup instance
        # --- END NEW ---
        
        self.setup_ui()
        
        # Schedule the initial render to run shortly after the widgets have settled and been sized.
        self.master_window.after(10, self.initial_render)

        self.start_tracking()
        
        # New: Get "Week Offs" from config - Note: this is still used for the bar graph logic, 
        # but NOT for the upload status check anymore.
        self.week_offs = read_config().get('Week Offs', 'Sat, Sun').split(',')
        self.week_offs = [day.strip()[:3] for day in self.week_offs]


    def initial_render(self):
        """A one-time call to render the charts immediately after the UI is mapped."""
        self.draw_pie_chart()
        self.draw_bar_graph()
        self.update_app_list()

    def load_data(self):
        """Loads historical screen time data and today's session data from JSON file."""
        today_str = str(date.today())
        
        if os.path.exists(SCREEN_TIME_FILE):
            try:
                with open(SCREEN_TIME_FILE, "r") as f:
                    self.weekly_data = json.load(f)
            except json.JSONDecodeError as e:
                print(f"Error decoding screen time data: {e}. Starting with empty data.")
                self.weekly_data = []
        else:
            self.weekly_data = []

        # --- Data Persistence Logic ---
        self.app_times = {}
        self.break_time = 0
        self.last_saved_timestamp = time.time() # Default to current time

        # Check if today's data exists in the historical log and load it
        for entry in self.weekly_data:
            if entry["date"] == today_str:
                entry_usage = entry.get("usage", {})
                if isinstance(entry_usage, dict):
                    self.app_times = entry_usage
                self.break_time = entry.get("break_time", 0)
                # Load the timestamp of the last save
                self.last_saved_timestamp = entry.get("last_timestamp", time.time())
                break
        
        if not isinstance(self.app_times, dict):
            self.app_times = {}

        # --- Resume Logic: Account for time elapsed while the app was closed ---
        if str(date.fromtimestamp(self.last_saved_timestamp)) == today_str:
            time_since_closed = time.time() - self.last_saved_timestamp
            
            self.last_update_time = time.time() 
        else:
            # If the loaded data is from a previous day, reset counters for a fresh start today
            self.app_times = {}
            self.break_time = 0
            self.last_update_time = time.time()

    def save_data(self):
        """Saves current daily data to the JSON file."""
        today_str = str(date.today())
        
        found = False
        for entry in self.weekly_data:
            if entry["date"] == today_str:
                entry["usage"] = self.app_times
                entry["break_time"] = self.break_time
                entry["last_timestamp"] = time.time() # Save the timestamp right before saving
                found = True
                break
        if not found:
            self.weekly_data.append({
                "date": today_str, 
                "usage": self.app_times, 
                "break_time": self.break_time,
                "last_timestamp": time.time() # Save the timestamp
            })
        
        self.weekly_data = sorted(self.weekly_data, key=lambda x: x['date'], reverse=False)[-7:]
        
        try:
            with open(SCREEN_TIME_FILE, "w") as f:
                json.dump(self.weekly_data, f, indent=4)
        except Exception as e:
            print(f"Error saving screen time data to {SCREEN_TIME_FILE}: {e}")

    def start_tracking(self):
        """Starts the background tracking thread and GUI update loop."""
        self.update_thread = threading.Thread(target=self.track_time_loop, daemon=True)
        self.update_thread.start()
        # The main GUI update is scheduled to start the regular refresh loop
        self.master_window.after(1000, self.update_gui)
    
    def popup_break_reminder(self, initial_remind=False):
        """Displays the break reminder window."""
        if self.is_reminder_active:
            return

        if initial_remind:
            message = "You've been working continuously for an hour. Your focus improves after short breaks. Ready to step away?"
        else:
            message = "Hey, still working hard! Your eyes and mind need a quick reset. Ready to step away?"

        self.is_reminder_active = True

        # Play notification sound
        try:
            import winsound
            # Play Windows notification sound
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception as e:
            print(f"Error playing notification sound: {e}")

        try:
            self.reminder_window = BreakReminder(self.master_window, message, self.handle_break_reminder_choice)
        except Exception as e:
            print(f"Error creating break reminder: {e}")
            self.is_reminder_active = False
            self.reminder_window = None

    def handle_break_reminder_choice(self, start_break, snooze_minutes=5):
        """Handles the user's choice from the reminder window."""
        self.is_reminder_active = False
        self.reminder_window = None

        if start_break:
            self.start_break()
        else:
            # Set the timer based on user's snooze selection
            snooze_seconds = snooze_minutes * 60
            self.continuous_work_time = WORK_THRESHOLD_SECONDS - snooze_seconds
            print(f"Reminder snoozed. Next check in {snooze_minutes} minutes.")


    def update_data_to_sheet(self):
        """Manually triggers the data upload to the Google Sheet."""
        self.save_data()
        
        # Prepare data for upload 
        current_day_data = next((item for item in self.weekly_data if item["date"] == str(date.today())), None)
        
        if not current_day_data:
            messagebox.showwarning("No Data", "No screen time data available for today.")
            return
        
        print("Uploading screen time data to Google Sheets...")
        upload_status = update_google_sheet_screen_time(user_screen_time_data=current_day_data)
        print(upload_status)
        
        # Show confirmation dialog ONLY when manually triggered
        if "Success" in upload_status:
            messagebox.showinfo("Success!", "Screen time data successfully updated on Google Sheets.")
        elif "Error" in upload_status:
            messagebox.showerror("Update Failed", f"Screen time update failed:\n\n{upload_status}")
        else:
            messagebox.showwarning("Update Status", upload_status)
            
    def stop_tracking(self):
        """Sets flag to stop the background thread gracefully and triggers final saves."""
        self.tracking = False
        # CRITICAL: Force a final save on shutdown
        self.save_data()

        # Silent auto-upload on app shutdown (no popup messages)
        try:
            current_day_data = next((item for item in self.weekly_data if item["date"] == str(date.today())), None)
            if current_day_data:
                print("Uploading screen time data to Google Sheets...")
                upload_status = update_google_sheet_screen_time(user_screen_time_data=current_day_data)
                print(upload_status)  # Only log to console
        except Exception as e:
            print(f"Silent upload error: {e}")

        print("Screen time tracking thread flagged for shutdown.")

    def track_time_loop(self):
        """A background thread to continuously check the active window and update time data."""
        last_day = date.today()
        while self.tracking:
            try:
                current_day = date.today()
                if current_day > last_day:
                    self.save_data()
                    self.load_data() 
                last_day = current_day

                elapsed_time = time.time() - self.last_update_time

                if not self.is_on_break:
                    active_window = gw.getActiveWindow()

                    if not self.is_reminder_active and self.continuous_work_time >= WORK_THRESHOLD_SECONDS:
                        self.master_window.after(0, self.popup_break_reminder, True)

                    if active_window and active_window.title:
                        app_title = active_window.title

                        if app_title not in self.app_times:
                            self.app_times[app_title] = 0

                        self.app_times[app_title] += elapsed_time
                        self.continuous_work_time += elapsed_time
                else:
                    # Reset continuous work timer during break
                    self.continuous_work_time = 0.0

                self.last_update_time = time.time()
                time.sleep(0.01)
            except Exception as e:
                pass


    def setup_ui(self):
        # --- Header ---
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=20, pady=20, anchor="n")

        self.back_button = ctk.CTkButton(self.header_frame, text="", image=self.back_arrow_icon, width=40, height=40, fg_color="transparent", command=self.back_to_dashboard)
        self.back_button.pack(side="left")

        self.title_label = ctk.CTkLabel(self.header_frame, text="Screen Time", font=Theme.FONT_TITLE)
        self.title_label.pack(side="left", padx=10, expand=True, anchor="w")
        
        # NEW: "Update Data" button
        self.update_button = ctk.CTkButton(self.header_frame, text="Update Data", command=self.update_data_to_sheet, font=Theme.FONT_NORMAL)
        self.update_button.pack(side="right", padx=10)

        # Main content frame (Scrollable)
        self.main_content_scroll_frame = ctk.CTkScrollableFrame(self, corner_radius=15, fg_color="transparent")
        self.main_content_scroll_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=(0, 25))
        
        # Inner Frame for Grid Layout
        main_content_frame = ctk.CTkFrame(self.main_content_scroll_frame, corner_radius=15, fg_color="transparent")
        main_content_frame.pack(fill="x", expand=True) 
        
        main_content_frame.grid_columnconfigure(0, weight=1, uniform="group1")
        main_content_frame.grid_columnconfigure(1, weight=1, uniform="group1")

        # Top-left: Bar Graph
        bar_graph_frame = ctk.CTkFrame(main_content_frame, corner_radius=15, height=350)
        bar_graph_frame.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        ctk.CTkLabel(bar_graph_frame, text="Weekly Usage Bar Graph", font=Theme.FONT_SUBTITLE).pack(pady=10)
        self.bar_graph_canvas = ctk.CTkCanvas(bar_graph_frame, highlightthickness=0)
        self.bar_graph_canvas.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Top-right: Pie Chart
        pie_chart_frame = ctk.CTkFrame(main_content_frame, corner_radius=15, height=350)
        pie_chart_frame.grid(row=0, column=1, padx=15, pady=15, sticky="nsew")
        ctk.CTkLabel(pie_chart_frame, text="Daily Category Usage", font=Theme.FONT_SUBTITLE).pack(pady=10)
        self.pie_chart_canvas = ctk.CTkCanvas(pie_chart_frame, highlightthickness=0)
        self.pie_chart_canvas.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        self.pie_chart_canvas.bind("<Motion>", self.on_pie_chart_hover)
        self.pie_chart_canvas.bind("<Leave>", self.on_pie_chart_leave)
        self.tooltip_text_id = None

        # Bottom-left: App List
        app_list_frame = ctk.CTkFrame(main_content_frame, corner_radius=15, height=350)
        app_list_frame.grid(row=1, column=0, padx=15, pady=15, sticky="nsew")
        ctk.CTkLabel(app_list_frame, text="App Usage List", font=Theme.FONT_SUBTITLE).pack(pady=(10, 5))
        self.app_list_scrollable_frame = ctk.CTkScrollableFrame(app_list_frame, corner_radius=10)
        self.app_list_scrollable_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Bottom-right: Timers and Break Buttons
        break_timer_frame = ctk.CTkFrame(main_content_frame, corner_radius=15, height=350)
        break_timer_frame.grid(row=1, column=1, padx=15, pady=15, sticky="nsew")

        screen_time_container = ctk.CTkFrame(break_timer_frame, corner_radius=10)
        screen_time_container.pack(fill=tk.X, padx=20, pady=(20, 10))
        ctk.CTkLabel(screen_time_container, text="Daily Screen Time", font=Theme.FONT_NORMAL).pack(pady=(10, 5))
        
        self.total_screen_time_label = ctk.CTkLabel(screen_time_container, text="00:00:00", font=self.title_number_font)
        self.total_screen_time_label.pack(pady=(0, 10))

        ctk.CTkFrame(break_timer_frame, height=2).pack(fill=tk.X, padx=20, pady=10)

        break_timer_container = ctk.CTkFrame(break_timer_frame, corner_radius=10)
        ctk.CTkLabel(break_timer_container, text="Break Timer", font=Theme.FONT_NORMAL).pack(pady=(10, 5))
        
        self.break_timer_label = ctk.CTkLabel(break_timer_container, text="00:00:00", font=self.title_number_font)
        self.break_timer_label.pack(pady=(0, 10))
        
        button_frame = ctk.CTkFrame(break_timer_frame, fg_color="transparent")
        button_frame.pack(pady=(0, 20))
        ctk.CTkButton(button_frame, text="Start Break", command=self.start_break, corner_radius=12, font=Theme.FONT_NORMAL).pack(side=tk.LEFT, padx=10)
        ctk.CTkButton(button_frame, text="Start Work", command=self.start_work, corner_radius=12, font=Theme.FONT_NORMAL).pack(side=tk.RIGHT, padx=10)
        
        self.update_ui_colors()
        
        break_timer_container.pack(fill=tk.X, padx=20, pady=(10, 20)) # Moved pack here after configuring all children

    def start_break(self):
        if not self.is_on_break:
            self.break_start_time = time.time()
            self.is_on_break = True
            # Reset continuous work timer during break
            self.continuous_work_time = 0.0

            if self.popup_timer_window is None or not self.popup_timer_window.winfo_exists():
                self.popup_timer_window = LiveTimersPopup(self.master_window, self)
            else:
                self.popup_timer_window.lift()

            print("Break started.")

    def reset_break_timer(self):
        """Resets the break time counters and updates the UI labels."""
        # Save the accumulated break time before resetting
        if self.break_start_time is not None:
            self.break_time += time.time() - self.break_start_time

        self.break_start_time = None
        self.break_timer_label.configure(text="00:00:00")
        if self.popup_timer_window and self.popup_timer_window.winfo_exists():
            self.popup_timer_window.break_timer_label.configure(text="00:00:00")

    def start_work(self):
        if self.is_on_break:
            self.is_on_break = False
            self.reset_break_timer()
            
            # --- NEW: Close the dedicated timer popup window ---
            if self.popup_timer_window and self.popup_timer_window.winfo_exists():
                self.popup_timer_window.destroy()
                self.popup_timer_window = None
            
            print("Break ended. Time to work.")

    def on_pie_chart_hover(self, event):
        """Displays a tooltip with category information on hover."""
        canvas_width = self.pie_chart_canvas.winfo_width()
        canvas_height = self.pie_chart_canvas.winfo_height()
        radius = min(canvas_width, canvas_height) * 0.4
        center_x = canvas_width / 2
        center_y = canvas_height / 2
        
        distance = math.sqrt((event.x - center_x)**2 + (event.y - center_y)**2)
        
        if distance > radius:
            self.on_pie_chart_leave(event)
            return

        item = self.pie_chart_canvas.find_closest(event.x, event.y)[0]
        
        if "pie_slice" in self.pie_chart_canvas.gettags(item):
            self.pie_chart_canvas.delete(self.tooltip_text_id)
            
            tags = self.pie_chart_canvas.itemcget(item, "tags").split(" ")
            if len(tags) >= 2:
                category = tags[0]
                try:
                    time_spent = float(tags[1])
                    time_str = self.format_time_string(time_spent)
                    tooltip_text = f"{category}: {time_str}"
                    
                    self.tooltip_text_id = self.pie_chart_canvas.create_text(event.x, event.y - 10, text=tooltip_text, font=("Helvetica", 10), fill=Theme.TEXT, anchor="s")
                except ValueError:
                    pass

    def on_pie_chart_leave(self, event):
        """Removes the tooltip when the mouse leaves the canvas."""
        if self.tooltip_text_id is not None:
            self.pie_chart_canvas.delete(self.tooltip_text_id)

    def draw_pie_chart(self):
        """Draws the circular usage chart on the canvas based on categories."""
        self.pie_chart_canvas.delete("all")

        canvas_width = self.pie_chart_canvas.winfo_width()
        canvas_height = self.pie_chart_canvas.winfo_height()
        
        # Critical Check: Return immediately if canvas is not yet sized
        if canvas_width < 10 or canvas_height < 10:
             return 

        radius = min(canvas_width, canvas_height) * 0.4
        center_x = canvas_width / 2
        center_y = canvas_height / 2
        
        x1 = center_x - radius
        y1 = center_y - radius
        x2 = center_x + radius
        y2 = center_y + radius
        
        category_usage = {"Break": self.break_time}
        for app, time_spent in self.app_times.items():
            category = get_category(app)
            if category not in category_usage:
                category_usage[category] = 0
            category_usage[category] += time_spent

        total_time = sum(category_usage.values())
        if total_time == 0:
            self.pie_chart_canvas.create_oval(x1, y1, x2, y2, outline=Theme.TEXT_SECONDARY, width=4)
            return

        angle_start = 0
        sorted_categories = sorted(category_usage.items(), key=lambda item: item[1], reverse=True)

        color_index = 0
        for category, time_spent in sorted_categories:
            angle = (time_spent / total_time) * 360
            angle_end = angle_start + angle
            
            fill_color = self.chart_colors[color_index % len(self.chart_colors)]
            
            tag_str = f"{category} {time_spent} pie_slice"
            self.pie_chart_canvas.create_arc(x1, y1, x2, y2, start=angle_start, extent=angle, fill=fill_color, outline=Theme.BACKGROUND, width=2, tags=tag_str)
            
            angle_start = angle_end
            color_index += 1

    def draw_bar_graph(self):
        """Draws the bar graph for weekly usage and average."""
        self.bar_graph_canvas.delete("all")
        
        # Define 'today' here
        today = date.today()
        
        weekly_totals = []
        # Load saved data, sorted by date
        sorted_weekly_data = sorted(self.weekly_data, key=lambda x: x['date'], reverse=False)

        # Populate weekly_totals from saved data
        for entry in sorted_weekly_data:
            total_seconds = sum(entry.get("usage", {}).values()) + entry.get("break_time", 0)
            weekly_totals.append(total_seconds)
        
        # --- FIX: Handle Today's Live Data ---
        
        # 1. Check if today's data is already in the SAVED list (only happens on day rollover/save)
        today_str = str(today)
        is_today_in_saved_data = any(entry['date'] == today_str for entry in self.weekly_data)
        
        # 2. Get the current, live session total
        live_today_total = sum(self.app_times.values()) + self.break_time

        if is_today_in_saved_data:
            # If today is already saved, we MUST update the *last* element of weekly_totals, not append.
            # This handles the case where the app re-opens and loads old data, then starts tracking.
            if weekly_totals and datetime.strptime(sorted_weekly_data[-1]['date'], '%Y-%m-%d').date() == today:
                 weekly_totals[-1] = live_today_total # Replace the saved total with the active live total
            else:
                 # Should not happen if data is clean, but safe to append if sorting failed.
                 weekly_totals.append(live_today_total)
        elif live_today_total > 0 or len(weekly_totals) < 7:
             # If today is NOT saved, append the live total to the list
             weekly_totals.append(live_today_total)

        # --- END FIX ---
             
        # Select the last 7 data points for the daily bars
        NUM_DAYS_TO_SHOW = 7
        daily_bars_data = weekly_totals[-NUM_DAYS_TO_SHOW:]
             
        if not daily_bars_data:
             return

        # Calculate the average based on the data displayed in the daily bars (up to 7 days)
        if not daily_bars_data:
             avg_seconds = 0
        else:
            avg_seconds = sum(daily_bars_data) / len(daily_bars_data)

        # Prepare all 8 pieces of data for visualization (7 days + 1 avg)
        data_for_display = daily_bars_data + [avg_seconds]
        
        max_time = max(data_for_display)
        
        canvas_width = self.bar_graph_canvas.winfo_width()
        canvas_height = self.bar_graph_canvas.winfo_height()
        
        if canvas_width < 10 or canvas_height < 10:
             return 

        # Total number of bars to draw is the number of daily bars + 1 (for average)
        num_bars = len(data_for_display)
        BAR_SPACING = 5 # Adjusted spacing for 8 bars total
        
        # Calculate bar width based on available space and spacing
        total_spacing_width = BAR_SPACING * (num_bars + 1)
        available_bar_width = canvas_width - total_spacing_width
        bar_width = available_bar_width / num_bars
        
        x_start = BAR_SPACING
        y_padding = 30
        
        # --- Draw Daily Bars (i < 7) ---
        for i, total_seconds in enumerate(daily_bars_data):
            height_ratio = total_seconds / max_time if max_time > 0 else 0
            bar_height = height_ratio * (canvas_height - 2 * y_padding)
            
            x1 = x_start + i * (bar_width + BAR_SPACING)
            y1 = canvas_height - y_padding - bar_height
            x2 = x1 + bar_width
            y2 = canvas_height - y_padding
            
            self.bar_graph_canvas.create_rectangle(x1, y1, x2, y2, fill=self.chart_colors[i % len(self.chart_colors)], outline="")
            
            # Date Label (X-Axis)
            # Find the date corresponding to this bar
            days_ago = len(daily_bars_data) - 1 - i 
            day_date = today - timedelta(days=days_ago)
            day_name = day_date.strftime("%d/%b") # e.g., 12/Sep
            self.bar_graph_canvas.create_text(x1 + bar_width/2, canvas_height - y_padding/2, text=day_name, font=("Rubik", 7), fill=Theme.TEXT)

            # Time Label (On top of the bar)
            time_str = self.format_time_string(total_seconds)
            self.bar_graph_canvas.create_text(x1 + bar_width/2, y1 - 10, text=time_str, font=("Rubik", 8), fill=Theme.TEXT_SECONDARY)

        # --- Draw Weekly Average Bar (i == 7) ---
        
        height_ratio = avg_seconds / max_time if max_time > 0 else 0
        bar_height = height_ratio * (canvas_height - 2 * y_padding)

        avg_index = len(daily_bars_data)
        x1 = x_start + avg_index * (bar_width + BAR_SPACING)
        x2 = x1 + bar_width
        y1 = canvas_height - y_padding - bar_height
        y2 = canvas_height - y_padding
        
        # Apply dashed outline and remove fill for distinction
        self.bar_graph_canvas.create_rectangle(x1, y1, x2, y2, 
                                               outline=Theme.ACCENT_PURPLE, 
                                               width=2, 
                                               dash=(4, 2), 
                                               fill="") # Use empty fill
        
        # Calculate the start and end dates of the period represented by the average
        
        # Determine the earliest date included in the average calculation (7 days ago)
        start_of_period = today - timedelta(days=NUM_DAYS_TO_SHOW - 1)
        end_of_period = today
        
        date_range_str_line1 = start_of_period.strftime('%b %d')
        date_range_str_line2 = end_of_period.strftime('%b %d')
        
        # Display the average date range across two lines
        self.bar_graph_canvas.create_text(x1 + bar_width/2, canvas_height - y_padding - 8, text=date_range_str_line1, font=("Rubik", 7), fill=Theme.TEXT)
        self.bar_graph_canvas.create_text(x1 + bar_width/2, canvas_height - y_padding/2 + 2, text=date_range_str_line2, font=("Rubik", 7), fill=Theme.TEXT)

        # Time Label (On top of the average bar)
        avg_time_str = self.format_time_string(avg_seconds)
        self.bar_graph_canvas.create_text(x1 + bar_width/2, y1 - 10, text=avg_time_str, font=("Rubik", 8), fill=Theme.TEXT_SECONDARY)


    def update_app_list(self):
        """Updates the list of apps and their usage."""
        for widget in self.app_list_scrollable_frame.winfo_children():
            widget.destroy()

        combined_times = self.app_times.copy()
        if self.break_time > 0:
            combined_times["Break"] = self.break_time

        sorted_times = sorted(combined_times.items(), key=lambda item: item[1], reverse=True)
        
        for name, seconds in sorted_times:
            time_str = self.format_time_string(seconds)
            
            row_frame = ctk.CTkFrame(self.app_list_scrollable_frame, fg_color="transparent")
            row_frame.pack(fill=tk.X, pady=2)
            
            category = get_category(name)
            category_color = Theme.ACCENT_BLUE if category == "Work" else Theme.TEXT_SECONDARY
            
            ctk.CTkLabel(row_frame, text=name, anchor="w", font=("Rubik", 11), padx=5, fg_color="transparent").pack(side=tk.LEFT, fill=tk.X, expand=True)
            ctk.CTkLabel(row_frame, text=f"[{category}]", anchor="e", font=("Rubik", 10), padx=5, text_color=category_color, fg_color="transparent").pack(side=tk.RIGHT)
            ctk.CTkLabel(row_frame, text=time_str, anchor="e", font=("Rubik", 11), padx=5, fg_color="transparent").pack(side=tk.RIGHT)

    def update_gui(self):
        """Updates the Tkinter GUI with the latest data and schedules the next update."""
        if not self.tracking:
            return

        current_time = time.time()

        # Always update timers (fast operation)
        total_seconds = sum(self.app_times.values())
        total_h, total_m, total_s = self.format_time(total_seconds)
        total_time_str = f"{total_h:02}:{total_m:02}:{total_s:02}"
        self.total_screen_time_label.configure(text=total_time_str)

        break_time_str = "00:00:00"
        if self.is_on_break and self.break_start_time is not None:
            # Calculate only the current break session time
            current_break_duration = current_time - self.break_start_time
            h, m, s = self.format_time(current_break_duration)
            break_time_str = f"{h:02}:{m:02}:{s:02}"
            self.break_timer_label.configure(text=break_time_str)

        # Update the popup window if it exists
        if self.popup_timer_window and self.popup_timer_window.winfo_exists():
            self.popup_timer_window.update_timers(total_time_str, break_time_str)

        # Update charts and lists less frequently (every 5 seconds)
        self.gui_update_counter += 1
        if self.gui_update_counter >= 5:
            self.draw_pie_chart()
            self.draw_bar_graph()
            self.update_app_list()
            self.gui_update_counter = 0

        if self.tracking:
            # Always schedule next update at exactly 1000ms
            self.master_window.after(1000, self.update_gui)


    def format_time(self, seconds):
        """Converts seconds into a formatted H:M:S tuple."""
        seconds = int(seconds)
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return h, m, s

    def format_time_string(self, seconds):
        """Formats seconds into a human-readable string (e.g., '1h 30m')."""
        seconds = int(seconds)
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        if h > 0:
            return f"{h}h {m}m"
        elif m > 0:
            return f"{m}m"
        else:
            return f"{s}s"

    def update_ui_colors(self):
        """Updates UI colors based on the current theme."""
        is_dark = ctk.get_appearance_mode() == "Dark"
        
        self.configure(fg_color=Theme.BACKGROUND)
        
        self.header_frame.configure(fg_color="transparent")
        self.back_button.configure(hover_color=Theme.ACCENT_BLUE_HOVER if not is_dark else Theme.ACCENT_BLUE)
        self.title_label.configure(text_color=Theme.TEXT)
        self.update_button.configure(fg_color=Theme.ACCENT_BLUE, hover_color=Theme.ACCENT_BLUE_HOVER)

        for widget in self.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                widget.configure(fg_color=Theme.BACKGROUND)
        
        for widget in self.main_content_scroll_frame.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                for child in widget.winfo_children():
                    if isinstance(child, ctk.CTkFrame):
                        child.configure(fg_color=Theme.CARD)
                        
        for widget in self.winfo_children():
            if isinstance(widget, ctk.CTkLabel):
                widget.configure(text_color=Theme.TEXT)
            elif isinstance(widget, ctk.CTkCanvas):
                widget.configure(bg=Theme.CARD)
        
        self.bar_graph_canvas.configure(bg=Theme.CARD)
        self.pie_chart_canvas.configure(bg=Theme.CARD)
        self.app_list_scrollable_frame.configure(fg_color=Theme.CARD)
        
        self.total_screen_time_label.configure(text_color=Theme.ACCENT_BLUE if not is_dark else Theme.ACCENT_BLUE_HOVER)
        self.break_timer_label.configure(text_color=Theme.ACCENT_PURPLE)

        self.update_app_list()
        self.draw_pie_chart()
        self.draw_bar_graph()