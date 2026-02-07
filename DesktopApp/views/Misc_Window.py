# views/Misc_Window.py
import sys
import os
import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from PIL import Image, ImageTk
import io
from .data_utils import resource_path # Import resource_path for assets
from theme import Theme

# Function to load PNG icon for window title bar
def load_png_icon(path):
    """
    Loads a PNG icon and returns a PhotoImage object.
    """
    try:
        pil_image = Image.open(resource_path(path))
        return ImageTk.PhotoImage(pil_image)
    except FileNotFoundError:
        print(f"Icon file not found at: {path}")
        return None
    except Exception as e:
        print(f"Error loading PNG icon from {path}: {e}")
        return None
        
class Misc_Window(ctk.CTkToplevel):
    def __init__(self, master, misc_file):
        super().__init__(master)
        self.misc_file = misc_file
        self.title("Miscellaneous")
        self.iconbitmap("assets/TaskSnap.ico")
        self.geometry("700x600")
        self.transient(master)
        self.grab_set()
        self.resizable(True, True)

        # Load and set window icon using PNG with error handling
        icon_path = 'assets/misc.png'
        icon_photo = load_png_icon(icon_path)
        if icon_photo:
            self.wm_iconphoto(True, icon_photo)
        else:
            print("Warning: Miscellaneous window icon could not be set.")
        
        self.init_ui()

    def init_ui(self):
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        month = datetime.now().strftime("%B")
        # Use Theme Font
        label = ctk.CTkLabel(main_frame, text=f"Miscellaneous Tasks for {month}", font=Theme.FONT_SUBTITLE)
        label.pack(pady=(0, 10))

        existing_text = self.load_text()
        self.text_edit = ctk.CTkTextbox(main_frame, font=Theme.FONT_NORMAL) # Use Theme Font for text area
        self.text_edit.insert("0.0", existing_text)
        self.text_edit.pack(fill="both", expand=True, padx=10, pady=10)

        # Use Theme Font
        save_button = ctk.CTkButton(main_frame, text="Save", command=self.save_text,
                                    fg_color=Theme.ACCENT_BLUE, hover_color=Theme.ACCENT_BLUE_HOVER, font=Theme.FONT_NORMAL)
        save_button.pack(pady=(10, 0))

    def load_text(self):
        try:
            # Ensure folder exists
            os.makedirs(os.path.dirname(self.misc_file), exist_ok=True)
            with open(self.misc_file, 'r') as file:
                existing_text = file.read()
                return existing_text
        except FileNotFoundError:
            return ''

    def save_text(self):
        text_to_save = self.text_edit.get("0.0", "end-1c") # Remove trailing newline from CTkTextbox
        try:
            with open(self.misc_file, 'w') as file:
                file.write(text_to_save)
            messagebox.showinfo("Success", "Changes saved successfully!")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Error saving changes: {e}")
