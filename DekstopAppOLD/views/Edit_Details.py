# views/Edit_Details.py
import sys
import os
import csv
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

class EditableDataDialog(ctk.CTkToplevel):
    # --- CHANGE 1: Added update_callback argument ---
    def __init__(self, master, csv_file_path, update_callback=None):
        super().__init__(master)
        self.csv_file_path = csv_file_path
        self.update_callback = update_callback # Store the callback function
        self.title("Edit")
        self.iconbitmap("assets/TaskSnap.ico")
        self.geometry("550x400")
        self.transient(master)
        self.grab_set()
        self.resizable(True, True)

        # Load and set window icon using PNG with error handling
        icon_path = 'assets/edit.png'
        icon_photo = load_png_icon(icon_path)
        if icon_photo:
            self.wm_iconphoto(True, icon_photo)
        else:
            print("Warning: Edit window icon could not be set.")

        self.init_ui()

    def init_ui(self):
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        data = self.read_csv_file()
        if not data:
            self.destroy()
            return

        # Simple table implementation using CTkEntry widgets
        self.entries = []
        for r, row in enumerate(data):
            row_entries = []
            for c, cell_data in enumerate(row):
                entry = ctk.CTkEntry(main_frame, font=Theme.FONT_NORMAL)
                entry.insert(0, str(cell_data))
                
                # Make header (row 0) and first column (Category) non-editable
                if r == 0 or c == 0:
                    entry.configure(state="readonly", font=Theme.FONT_SUBTITLE)
                
                entry.grid(row=r, column=c, padx=5, pady=5, sticky="ew")
                row_entries.append(entry)
            self.entries.append(row_entries)

        for col in range(len(data[0])):
            main_frame.grid_columnconfigure(col, weight=1)

        # Use Theme Font
        save_button = ctk.CTkButton(main_frame, text="Save", command=self.save_changes,
                                   fg_color=Theme.ACCENT_BLUE, hover_color=Theme.ACCENT_BLUE_HOVER, font=Theme.FONT_NORMAL)
        save_button.grid(row=len(data), column=0, columnspan=len(data[0]), pady=10)

    def read_csv_file(self):
        if not os.path.exists(self.csv_file_path):
            messagebox.showwarning(
                "No Data Found",
                f"No saved productivity data is available for editing this month: {os.path.basename(self.csv_file_path)}"
            )
            return []
            
        try:
            with open(self.csv_file_path, 'r', newline='') as file:
                reader = csv.reader(file)
                return list(reader)
        except Exception as e:
            messagebox.showerror("Error Reading File", f"Error reading CSV file: {e}")
            return []

    def save_changes(self):
        edited_data = []
        for r in range(len(self.entries)):
            row_data = []
            for c in range(len(self.entries[r])):
                entry_value = self.entries[r][c].get()
                
                # Validate numerical data (all cells except header row and category column)
                if r > 0 and c > 0:
                    try:
                        # Ensure value is an integer or empty string (which is okay, interpreted as 0)
                        if entry_value.strip() and not entry_value.isdigit():
                             raise ValueError("Must be a number.")
                    except ValueError:
                        messagebox.showwarning("Warning", f"Invalid data in row {r+1}, column {c+1}. Please enter an integer.")
                        return
                row_data.append(entry_value)
            edited_data.append(row_data)

        try:
            with open(self.csv_file_path, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerows(edited_data)

            # --- CHANGE 2: Call the callback function after successful local save ---
            if self.update_callback:
                self.update_callback()
                
            messagebox.showinfo("Success", "Changes saved successfully!")
            self.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"Error saving changes: {e}")
