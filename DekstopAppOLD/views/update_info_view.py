# views/update_info_view.py
import customtkinter as ctk
from tkinter import messagebox
from theme import Theme
from PIL import Image
import csv
import os
import re
from .data_utils import read_config, write_config, CONFIG_FILE, resource_path

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

class UpdateInfoView(ctk.CTkFrame):
    """
    A view for updating user profile information.
    """
    def __init__(self, master, back_to_dashboard_callback):
        super().__init__(master, fg_color=Theme.BACKGROUND)
        self.back_to_dashboard = back_to_dashboard_callback
        
        self.main_app_master = master 

        try:
            self.back_arrow_icon = load_png_image("assets/back_arrow_icon.png")
            self.avatar_image = ctk.CTkImage(Image.open(resource_path("assets/user_icon.png")), size=(100, 100))
            self.clock_icon = ctk.CTkImage(Image.open(resource_path("assets/clock_icon.png")), size=(20, 20))
        except FileNotFoundError as e:
            print(f"Warning: Icon file not found in UpdateInfoView: {e}")
            self.back_arrow_icon = None
            self.avatar_image = None
            self.clock_icon = None

        self.title_font = Theme.FONT_TITLE
        self.label_font = Theme.FONT_SUBTITLE
        self.entry_font = Theme.FONT_NORMAL
        self.hint_font = Theme.FONT_CARD_SUBTITLE

        self.config_data = {}

        self.create_widgets()
        self.load_current_data(read_config())
        self.update_ui_colors()
        
    def create_widgets(self):
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=20, pady=(10, 8), anchor="n")

        self.back_button = ctk.CTkButton(self.header_frame, text="", image=self.back_arrow_icon, width=40, height=40, fg_color="transparent", command=self.back_to_dashboard)
        self.back_button.pack(side="left")

        self.title_label = ctk.CTkLabel(self.header_frame, text="Update Info", font=self.title_font)
        self.title_label.pack(side="left", padx=10)
        
        self.content_frame = ctk.CTkScrollableFrame(self)
        self.content_frame.pack(fill="both", expand=True, padx=0, pady=0)

        avatar_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        avatar_frame.pack(pady=(20, 10))
        
        avatar_label = ctk.CTkLabel(avatar_frame, image=self.avatar_image, text="")
        avatar_label.pack()

        self.name_label = ctk.CTkLabel(avatar_frame, text="Loading...", font=Theme.FONT_SUBTITLE)
        self.name_label.pack(pady=(8,0))
        
        self.email_label = ctk.CTkLabel(avatar_frame, text="Loading...", font=Theme.FONT_NORMAL)
        self.email_label.pack()

        self.form_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.form_frame.pack(fill="x", expand=True, padx=60, pady=10)

        self.form_labels = []
        self.form_entries = {}
        
        self.create_form_field("User Name", "User First Name")
        self.create_form_field("User Mail", "User Email")
        self.create_shift_time_field()
        self.create_week_offs_field()
        self.create_form_field("Manager's Email", "Manager Email")

        self.save_button = ctk.CTkButton(self.form_frame, text="Save Changes", font=Theme.FONT_SUBTITLE, height=44, width=280, corner_radius=20, command=self.save_changes)
        self.save_button.pack(pady=(32, 28), padx=10, anchor="center")
        
    def create_form_field(self, label_text, key):
        label = ctk.CTkLabel(self.form_frame, text=label_text, font=self.label_font, anchor="w")
        self.form_labels.append(label)
        label.pack(fill="x", pady=(15, 2))

        entry = ctk.CTkEntry(self.form_frame, placeholder_text=f"Enter {label_text.lower()}", font=self.entry_font, height=40, border_width=1)
        self.form_entries[key] = entry
        entry.pack(fill="x")
        
    def create_shift_time_field(self):
        label = ctk.CTkLabel(self.form_frame, text="Shift Time", font=self.label_font, anchor="w")
        self.form_labels.append(label)
        label.pack(fill="x", pady=(15, 2))
        
        shift_time_frame = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        shift_time_frame.pack(fill="x", pady=(0, 2))
        
        self.clock_icon_label = ctk.CTkLabel(shift_time_frame, image=self.clock_icon, text="")
        if self.clock_icon:
            self.clock_icon_label.pack(side="left", padx=(0, 8))

        self.start_entry = ctk.CTkEntry(shift_time_frame, placeholder_text="00:00", font=self.entry_font, height=40, width=120)
        self.form_entries["Shift Start Time"] = self.start_entry
        self.start_entry.pack(side="left")

        self.start_ampm = ctk.CTkOptionMenu(shift_time_frame, values=["AM", "PM"], width=70, font=self.entry_font)
        self.start_ampm.set("AM")
        self.start_ampm.pack(side="left", padx=4)

        self.to_label = ctk.CTkLabel(shift_time_frame, text="to", font=self.entry_font)
        self.to_label.pack(side="left", padx=10)

        self.end_entry = ctk.CTkEntry(shift_time_frame, placeholder_text="00:00", font=self.entry_font, height=40, width=120)
        self.form_entries["Shift End Time"] = self.end_entry
        self.end_entry.pack(side="left")

        self.end_ampm = ctk.CTkOptionMenu(shift_time_frame, values=["AM", "PM"], width=70, font=self.entry_font)
        self.end_ampm.set("PM")
        self.end_ampm.pack(side="left", padx=4)

    def create_week_offs_field(self):
        week_offs_row = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        week_offs_row.pack(fill="x", pady=(20, 0))
        
        self.week_offs_label = ctk.CTkLabel(week_offs_row, text="Week Offs", font=self.label_font, anchor="w")
        self.week_offs_label.pack(side="left")
        self.week_offs_hint = ctk.CTkLabel(week_offs_row, text="(Select up to 2)", font=self.hint_font, anchor="w")
        self.week_offs_hint.pack(side="left", padx=8)

        # --- FIX: Use a grid layout for responsive checkboxes ---
        self.week_offs_frame = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        self.week_offs_frame.pack(fill="x", pady=(2, 10))
        self.week_offs_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5, 6), weight=1, uniform="weekdays")
        
        weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        self.week_off_vars = [ctk.BooleanVar() for _ in weekdays]
        self.week_off_checkboxes = []

        for i, day in enumerate(weekdays):
            cb = ctk.CTkCheckBox(self.week_offs_frame, text=day, variable=self.week_off_vars[i], command=self.on_week_off_change, font=self.entry_font) 
            cb.grid(row=0 if i < 5 else 1, column=i if i < 5 else i-5, padx=8, pady=2, sticky="ew") # Place M-F on row 0, S-S on row 1
            self.week_off_checkboxes.append(cb)
            
    def on_week_off_change(self):
        checked_count = sum(var.get() for var in self.week_off_vars)
        for cb, var in zip(self.week_off_checkboxes, self.week_off_vars):
            if not var.get():
                cb.configure(state="normal" if checked_count < 2 else "disabled")

    def load_current_data(self, config_data):
        self.config_data = config_data

        for key, entry in self.form_entries.items():
            entry.delete(0, 'end')
            if key in config_data:
                entry.insert(0, config_data[key])
        
        start_time_str = config_data.get("Shift Start Time", "9:00 AM")
        end_time_str = config_data.get("Shift End Time", "5:00 PM")
        
        if ' ' in start_time_str:
            time_part, ampm_part = start_time_str.split(' ')
            self.form_entries["Shift Start Time"].delete(0, 'end')
            self.form_entries["Shift Start Time"].insert(0, time_part)
            self.start_ampm.set(ampm_part)

        if ' ' in end_time_str:
            time_part, ampm_part = end_time_str.split(' ')
            self.form_entries["Shift End Time"].delete(0, 'end')
            self.form_entries["Shift End Time"].insert(0, time_part)
            self.end_ampm.set(ampm_part)

        week_offs_str = config_data.get("Week Offs", "")
        week_offs = [day.strip() for day in week_offs_str.split(', ') if day.strip()]
        
        weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        
        for i, day in enumerate(weekdays):
            var = self.week_off_vars[i]
            if day in week_offs:
                var.set(True)
            else:
                var.set(False)
        
        self.on_week_off_change()
        
        self.name_label.configure(text=config_data.get('User First Name', 'User Name Missing'))
        self.email_label.configure(text=config_data.get('User Email', 'Email Missing'))

    def validate_email(self, email):
        return re.match(r"[^@]+@[^@]+\.[^@]+", email)
    
    def validate_time(self, time_str):
        return re.match(r"^\d{1,2}:\d{2}$", time_str)
        
    def save_changes(self):
        new_config = self.config_data.copy()
        
        user_name = self.form_entries['User First Name'].get().strip()
        user_mail = self.form_entries['User Email'].get().strip()
        manager_mail = self.form_entries['Manager Email'].get().strip()
        
        start_time = self.form_entries["Shift Start Time"].get().strip()
        start_ampm = self.start_ampm.get()
        end_time = self.form_entries["Shift End Time"].get().strip()
        end_ampm = self.end_ampm.get()
        
        weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        selected_week_offs = [day for i, day in enumerate(weekdays) if self.week_off_vars[i].get()]
        
        if not user_name:
            messagebox.showwarning("Validation Error", "User Name is required.")
            return
        
        if not user_mail or not self.validate_email(user_mail):
            messagebox.showwarning("Validation Error", "A valid User Mail address is required.")
            return

        if not manager_mail or not self.validate_email(manager_mail):
            messagebox.showwarning("Validation Error", "A valid Manager's Email address is required.")
            return

        if not start_time or not self.validate_time(start_time):
            messagebox.showwarning("Validation Error", "Shift Start Time must be in HH:MM format (e.g., 9:00 or 09:30).")
            return
        
        if not end_time or not self.validate_time(end_time):
            messagebox.showwarning("Validation Error", "Shift End Time must be in HH:MM format (e.g., 5:00 or 17:30).")
            return
            
        if not selected_week_offs:
             messagebox.showwarning("Validation Error", "Please select at least one Week Off day.")
             return
            
        if len(selected_week_offs) > 2:
            messagebox.showwarning("Validation Error", "Please select a maximum of 2 Week Off days.")
            return

        new_config['User First Name'] = user_name
        new_config['User Email'] = user_mail
        new_config['Manager Email'] = manager_mail
        new_config['Shift Start Time'] = f"{start_time} {start_ampm}"
        new_config['Shift End Time'] = f"{end_time} {end_ampm}"
        new_config['Week Offs'] = ', '.join(selected_week_offs)
        
        try:
            write_config(new_config)
            
            messagebox.showinfo("Success", "Changes saved successfully!")
            
            self.main_app_master.config = new_config
            self.main_app_master.dashboard_view.update_user_name(user_name) 
            
            self.back_to_dashboard()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error saving configuration: {e}")

    def update_ui_colors(self):
        is_dark = ctk.get_appearance_mode() == "Dark"
        self.configure(fg_color=Theme.BACKGROUND)
        self.header_frame.configure(fg_color="transparent")
        self.back_button.configure(hover_color=Theme.ACCENT_BLUE_HOVER if not is_dark else Theme.ACCENT_BLUE)
        self.title_label.configure(text_color=Theme.TEXT)
        self.content_frame.configure(fg_color=Theme.CARD, scrollbar_button_color=Theme.CARD)
        self.form_frame.configure(fg_color="transparent")
        self.name_label.configure(text_color=Theme.TEXT)
        self.email_label.configure(text_color=Theme.TEXT_SECONDARY)
        
        for label in self.form_labels:
            label.configure(text_color=Theme.TEXT)
        self.to_label.configure(text_color=Theme.TEXT_SECONDARY)
        self.week_offs_label.configure(text_color=Theme.TEXT)
        self.week_offs_hint.configure(text_color=Theme.TEXT_SECONDARY)

        entry_border_color = Theme.ACCENT_BLUE if is_dark else Theme.TEXT_SECONDARY

        for entry in self.form_entries.values():
            entry.configure(fg_color=Theme.BACKGROUND, text_color=Theme.TEXT, border_color=entry_border_color)
        
        for dropdown in [self.start_ampm, self.end_ampm]:
            dropdown.configure(button_color=Theme.BACKGROUND, button_hover_color=Theme.ACCENT_BLUE_HOVER if not is_dark else Theme.ACCENT_BLUE_HOVER)

        for cb in self.week_off_checkboxes:
            cb.configure(text_color=Theme.TEXT_SECONDARY, fg_color=Theme.ACCENT_BLUE, border_color=Theme.TEXT_SECONDARY, hover_color=Theme.ACCENT_BLUE_HOVER)
        
        self.save_button.configure(fg_color=Theme.ACCENT_BLUE, hover_color=Theme.ACCENT_BLUE_HOVER)