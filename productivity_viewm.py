import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import csv
import os
from datetime import datetime, date
import threading
import smtplib
from email.mime.text import MIMEText
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import webbrowser
from collections import defaultdict

# Placeholder for Theme, replace with your actual theme file
class Theme:
    BACKGROUND = "#F4F5F7"
    CARD = "#FFFFFF"
    TEXT = "#2D3748"
    ACCENT_BLUE = "#3B82F6"
    ACCENT_BLUE_HOVER = "#2563EB"
    TEXT_SECONDARY = "#6B7280"
    FONT_CARD_TITLE = ("Rubik", 16, "bold")
    FONT_NORMAL = ("Rubik", 14)

# Constants for filenames
TASKS_DIR = "Tasks"
CONFIG_FILE = "config.csv"
TASKSNAP_EMAIL = "tasksnapjournal@gmail.com"
TASKSNAP_PASSWORD = "inxw gskm nqls grai"

class ProductivityView(ctk.CTkFrame):
    """
    A comprehensive and robust view for tracking productivity with integrated functionalities.
    """
    def __init__(self, master, back_to_dashboard_callback):
        super().__init__(master, fg_color=Theme.BACKGROUND)
        self.back_to_dashboard = back_to_dashboard_callback
        self.master_window = master
        self.entries = {}
        self.dropdown_menu = None
        self.load_assets()
        self.create_ui()

    def load_assets(self):
        try:
            self.icons = {
                "back": ctk.CTkImage(Image.open("assets/back_arrow_icon.png"), size=(24, 24)),
                "menu": ctk.CTkImage(Image.open("assets/menu_icon.png"), size=(24, 24)),
                "misc": ctk.CTkImage(Image.open("assets/misc.svg"), size=(24, 24)),
                "summary": ctk.CTkImage(Image.open("assets/summary.svg"), size=(24, 24)),
                "email": ctk.CTkImage(Image.open("assets/send_report.svg"), size=(24, 24)),
            }
        except FileNotFoundError as e:
            print(f"Warning: Icon file not found in ProductivityView: {e}")
            self.icons = {k: None for k in ["back", "menu", "misc", "summary", "email"]}

    def create_ui(self):
        # --- Header Frame ---
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=20, anchor="n")

        ctk.CTkButton(header_frame, text="", image=self.icons["back"], width=40, height=40, fg_color="transparent", hover_color=Theme.TEXT_SECONDARY, command=self.back_to_dashboard).pack(side="left")

        ctk.CTkLabel(header_frame, text="Productivity Tracker", font=("Rubik", 28, "bold"), text_color=Theme.TEXT).pack(side="left", padx=10, expand=True, anchor="w")

        self.menu_button = ctk.CTkButton(header_frame, text="", image=self.icons["menu"], width=40, height=40, fg_color="transparent", hover_color=Theme.TEXT_SECONDARY, command=self.toggle_dropdown_menu)
        self.menu_button.pack(side="right")

        # --- Content Frame ---
        content_frame = ctk.CTkScrollableFrame(self, corner_radius=12, fg_color=Theme.CARD)
        content_frame.pack(fill="both", expand=True, padx=60, pady=(0, 20))
        
        ctk.CTkLabel(content_frame, text="Daily Productivity Log", font=("Rubik", 24, "bold"), text_color=Theme.TEXT).pack(pady=(20, 20), anchor="w", padx=20)

        self.create_entry_grid(content_frame)

        # --- Action Buttons ---
        button_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(30, 20), padx=20)
        button_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(button_frame, text="Update", font=("Rubik", 16, "bold"), height=40, fg_color=Theme.ACCENT_BLUE, hover_color=Theme.ACCENT_BLUE_HOVER, command=self.update_data).grid(row=0, column=0, padx=10, pady=5, sticky="ew")

        ctk.CTkButton(button_frame, text="Clear", font=("Rubik", 16, "bold"), height=40, fg_color=Theme.TEXT_SECONDARY, hover_color=Theme.TEXT, command=self.clear_fields).grid(row=0, column=1, padx=10, pady=5, sticky="ew")

    def create_entry_grid(self, parent_frame):
        grid = ctk.CTkFrame(parent_frame, fg_color="transparent")
        grid.pack(fill="x", expand=True, padx=20)
        grid.grid_columnconfigure(0, weight=2)
        grid.grid_columnconfigure((1, 2, 3), weight=1)

        self.create_category_row(grid, "Packaging", 0, ["Simple", "Medium", "Complex"])
        self.create_category_row(grid, "QA", 1, ["Simple", "Medium", "Complex"])
        self.create_category_row(grid, "Troubleshooting", 2, ["P1", "P2", "P3"])
        self.create_single_field(grid, "Defects", 3)

    def create_category_row(self, parent_frame, category_name, row, complexities):
        ctk.CTkLabel(parent_frame, text=category_name, font=Theme.FONT_CARD_TITLE, anchor="w", text_color=Theme.TEXT).grid(row=row, column=0, padx=(0, 10), pady=8, sticky="w")
        self.entries[category_name] = {}
        for i, complexity in enumerate(complexities):
            entry = ctk.CTkEntry(parent_frame, placeholder_text=complexity, font=Theme.FONT_NORMAL, height=35, text_color=Theme.TEXT, fg_color=Theme.BACKGROUND)
            entry.grid(row=row, column=i + 1, padx=5, pady=8, sticky="ew")
            self.entries[category_name][complexity] = entry

    def create_single_field(self, parent_frame, label_text, row):
        ctk.CTkLabel(parent_frame, text=label_text, font=Theme.FONT_CARD_TITLE, anchor="w", text_color=Theme.TEXT).grid(row=row, column=0, padx=(0, 10), pady=8, sticky="w")
        entry = ctk.CTkEntry(parent_frame, placeholder_text="Count", font=Theme.FONT_NORMAL, height=35, text_color=Theme.TEXT, fg_color=Theme.BACKGROUND)
        entry.grid(row=row, column=1, columnspan=3, padx=5, pady=8, sticky="ew")
        self.entries[label_text] = {"count": entry}

    def toggle_dropdown_menu(self):
        # Destroy the menu if it already exists
        if self.dropdown_menu and self.dropdown_menu.winfo_exists():
            self.dropdown_menu.destroy()
            self.dropdown_menu = None
            return

        # Create the dropdown menu as a new top-level window
        self.dropdown_menu = ctk.CTkToplevel(self.master_window)
        self.dropdown_menu.overrideredirect(True) # Removes window decorations
        self.dropdown_menu.attributes("-alpha", 0.0) # Start transparent for fade-in effect
        self.dropdown_menu.grab_set()

        # Place the menu correctly
        self.master_window.update_idletasks()
        x = self.menu_button.winfo_rootx() + self.menu_button.winfo_width() - 150 # Adjust width
        y = self.menu_button.winfo_rooty() + self.menu_button.winfo_height()
        self.dropdown_menu.geometry(f"150x120+{x}+{y}") # Set geometry and position

        self.create_dropdown_buttons(self.dropdown_menu)

        # Animate the fade-in and bind the hide function
        self.fade_in(self.dropdown_menu)
        self.dropdown_menu.bind("<FocusOut>", self.hide_dropdown_menu)
        self.dropdown_menu.bind("<Escape>", self.hide_dropdown_menu)

    def create_dropdown_buttons(self, parent):
        frame = ctk.CTkFrame(parent, fg_color=Theme.CARD, corner_radius=8, border_color=Theme.TEXT_SECONDARY, border_width=1)
        frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        button_options = [
            ("View Summary", self.show_summary_window, self.icons["summary"]),
            ("Miscellaneous", self.misc_window, self.icons["misc"]),
            ("Send Report", self.show_confirmation_dialog, self.icons["email"])
        ]
        
        for text, command, icon in button_options:
            btn = ctk.CTkButton(frame, text=text, image=icon, compound="left", anchor="w", fg_color="transparent", hover_color=Theme.BACKGROUND, text_color=Theme.TEXT, command=lambda cmd=command: (self.hide_dropdown_menu(None), cmd()))
            btn.pack(fill="x", padx=5, pady=5)

    def hide_dropdown_menu(self, event):
        if self.dropdown_menu and self.dropdown_menu.winfo_exists():
            # Check if the click is outside the menu
            if event and hasattr(event, 'x_root') and self.dropdown_menu.winfo_containing(event.x_root, event.y_root):
                return
            
            # Animate fade-out and then destroy
            self.fade_out(self.dropdown_menu)
            
    def fade_in(self, window):
        alpha = window.attributes("-alpha")
        if alpha < 1.0:
            alpha += 0.1
            window.attributes("-alpha", alpha)
            window.after(10, lambda: self.fade_in(window))
        else:
            window.attributes("-alpha", 1.0)
            
    def fade_out(self, window):
        alpha = window.attributes("-alpha")
        if alpha > 0.0:
            alpha -= 0.1
            window.attributes("-alpha", alpha)
            window.after(10, lambda: self.fade_out(window))
        else:
            window.destroy()
            self.dropdown_menu = None

    def update_data(self):
        current_date = date.today()
        month_year_str = current_date.strftime("%m-%Y")
        folder_path = TASKS_DIR
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        filename = os.path.join(folder_path, f"tasks_{month_year_str}.csv")

        # Load existing data or create an empty structure
        if os.path.exists(filename):
            try:
                df = pd.read_csv(filename)
                existing_data = df.set_index('Category').T.to_dict('list')
                existing_data = {k: {col: existing_data[k][i] for i, col in enumerate(df.columns) if col != 'Category'} for k in existing_data}
            except Exception:
                existing_data = {}
        else:
            existing_data = {}

        # Update or add new data from UI entries
        for category, data in self.entries.items():
            if category not in existing_data:
                existing_data[category] = {k: 0 for k in data.keys()}
            for complexity, entry in data.items():
                value = entry.get()
                if value:
                    try:
                        int_value = int(value)
                        existing_data[category][complexity] = existing_data[category].get(complexity, 0) + int_value
                    except ValueError:
                        pass
        
        # Convert back to DataFrame and save
        df_new = pd.DataFrame.from_dict(existing_data, orient='index').reset_index().rename(columns={'index': 'Category'})
        df_new.to_csv(filename, index=False)
        
        messagebox.showinfo("Success", "Data Updated Successfully!", parent=self.master_window)
        self.clear_fields()

    def show_summary_window(self):
        if self.dropdown_menu: self.dropdown_menu.destroy()
        directory_path = TASKS_DIR
        if not os.path.exists(directory_path) or not any(fname.endswith('.csv') for fname in os.listdir(directory_path)):
            messagebox.showerror("Error", "No data found to generate a summary.")
            return

        summary_window = ctk.CTkToplevel(self.master_window, fg_color=Theme.BACKGROUND)
        summary_window.title("Productivity Summary")
        summary_window.geometry("800x600")
        summary_window.grab_set()

        try:
            dfs = []
            for filename in os.listdir(directory_path):
                if filename.endswith('.csv'):
                    file_path = os.path.join(directory_path, filename)
                    df = pd.read_csv(file_path)
                    month_name = datetime.strptime(filename.split('_')[1].split('.')[0], "%m-%Y").strftime("%b-%y")
                    df['Month'] = month_name
                    dfs.append(df)

            combined_df = pd.concat(dfs, ignore_index=True).fillna(0)
            numeric_cols = combined_df.select_dtypes(include=['int64', 'float64']).columns.tolist()
            combined_df['Total'] = combined_df[numeric_cols].sum(axis=1)
            pivot_df = combined_df.pivot_table(index='Month', columns='Category', values='Total', aggfunc='sum').fillna(0)

            # Create the matplotlib figure
            fig = Figure(figsize=(6, 5), dpi=100, facecolor=Theme.BACKGROUND)
            ax = fig.add_subplot(111)
            pivot_df.plot(kind='bar', stacked=False, ax=ax, colormap="tab20")
            ax.set_title("Productivity Summary", color=Theme.TEXT)
            ax.set_xlabel("Month", color=Theme.TEXT)
            ax.set_ylabel("Total Count", color=Theme.TEXT)
            ax.tick_params(colors=Theme.TEXT)
            fig.tight_layout()
            
            canvas = FigureCanvasTkAgg(fig, master=summary_window)
            canvas_widget = canvas.get_tk_widget()
            canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

            ctk.CTkButton(summary_window, text="OK", command=summary_window.destroy, fg_color=Theme.ACCENT_BLUE, hover_color=Theme.ACCENT_BLUE_HOVER).pack(pady=10)

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while generating the summary: {e}")
            summary_window.destroy()

    def show_confirmation_dialog(self):
        if self.dropdown_menu: self.dropdown_menu.destroy()
        month_name = date.today().strftime("%B")
        if messagebox.askyesno("Confirmation", f"Do you want to send the report for {month_name}?"):
            self.send_email_threaded()

    def misc_window(self):
        if self.dropdown_menu: self.dropdown_menu.destroy()
        misc_window = ctk.CTkToplevel(self.master_window, fg_color=Theme.BACKGROUND)
        misc_window.title("Miscellaneous")
        misc_window.geometry("500x400")
        misc_window.grab_set()
        
        misc_file = os.path.join(TASKS_DIR, f"Misc_{date.today().strftime('%m-%Y')}.txt")
        if not os.path.exists(TASKS_DIR):
            os.makedirs(TASKS_DIR)

        text_edit = ctk.CTkTextbox(misc_window, wrap="word", text_color=Theme.TEXT, fg_color=Theme.CARD)
        text_edit.pack(fill="both", expand=True, padx=10, pady=10)
        
        try:
            with open(misc_file, 'r') as file:
                text_edit.insert("1.0", file.read())
        except FileNotFoundError:
            text_edit.insert("1.0", "")
        
        def save_text():
            try:
                with open(misc_file, 'w') as file:
                    file.write(text_edit.get("1.0", "end-1c"))
                messagebox.showinfo("Success", "Miscellaneous notes saved successfully!", parent=misc_window)
                misc_window.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Error saving notes: {e}", parent=misc_window)

        ctk.CTkButton(misc_window, text="Save", command=save_text, fg_color=Theme.ACCENT_BLUE, hover_color=Theme.ACCENT_BLUE_HOVER).pack(pady=(0, 10))

    def send_email_threaded(self):
        manager_email, user_firstname, user_email = self.read_config()
        if not all([manager_email, user_firstname, user_email]):
            messagebox.showerror("Error", "Please update your details in the settings first.")
            return

        report_details = self.format_report_details()
        misc_tasks_details = self.format_misc_task()
        
        if report_details is None:
            messagebox.showerror("Error", "No productivity data found to send.")
            return
        
        progress_window = ctk.CTkToplevel(self.master_window, fg_color=Theme.BACKGROUND)
        progress_window.title("Sending Email")
        progress_window.geometry("300x100")
        ctk.CTkLabel(progress_window, text="Sending email...", text_color=Theme.TEXT).pack(pady=20)
        progress_window.grab_set()

        threading.Thread(target=self._send_email, args=(progress_window, manager_email, user_firstname, user_email, report_details, misc_tasks_details)).start()
        
    def _send_email(self, progress_window, manager_email, user_firstname, user_email, report_details, misc_tasks_details):
        try:
            subject = f"{user_firstname}'s Productivity Report - {date.today().strftime('%B %Y')}"
            body = f'''<div style="color: black !important;">Dear Manager,<br><br>Please find the productivity details of {user_firstname} for the month of {date.today().strftime('%B')}.<br>{report_details}<br><br>Please find the other miscellaneous tasks done:<br>{misc_tasks_details}<br><br>Best regards,<br>Your TASKSNAP JOURNAL</div>'''
            msg = MIMEText(body, 'html')
            msg['Subject'] = subject
            msg['From'] = TASKSNAP_EMAIL
            msg['To'] = manager_email
            msg['Cc'] = user_email

            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(TASKSNAP_EMAIL, TASKSNAP_PASSWORD)
                recipients = [manager_email, user_email]
                server.sendmail(TASKSNAP_EMAIL, recipients, msg.as_string())

            self.master_window.after(0, lambda: progress_window.destroy())
            self.master_window.after(0, lambda: messagebox.showinfo("Success", "Report sent successfully!"))
        except Exception as e:
            self.master_window.after(0, lambda: progress_window.destroy())
            self.master_window.after(0, lambda: messagebox.showerror("Error", f"Error sending report: {e}\nCheck your email settings."))

    def format_report_details(self):
        try:
            month_year_str = date.today().strftime("%m-%Y")
            task_file = os.path.join(TASKS_DIR, f"tasks_{month_year_str}.csv")
            if not os.path.exists(task_file):
                return "<br>No productivity data found for this month."
            
            df = pd.read_csv(task_file).fillna(0)
            numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
            
            if not numeric_cols:
                return "<br>Productivity data exists but is not in a valid format."

            total_row = {'Category': 'Total'}
            for col in numeric_cols:
                total_row[col] = df[col].sum()
            
            total_df = pd.DataFrame([total_row])
            df = pd.concat([df, total_df], ignore_index=True)
            
            html_report = df.to_html(index=False)
            return html_report
        except Exception as e:
            print(f"Error formatting report: {e}")
            return None

    def format_misc_task(self):
        try:
            misc_file = os.path.join(TASKS_DIR, f"Misc_{date.today().strftime('%m-%Y')}.txt")
            if os.path.exists(misc_file):
                with open(misc_file, 'r') as f:
                    content = f.read()
                    return content.replace('\n', '<br>')
            return "<br>No miscellaneous notes found."
        except Exception as e:
            print(f"Error formatting misc tasks: {e}")
            return "<br>Error loading miscellaneous notes."
            
    def clear_fields(self):
        for data in self.entries.values():
            for entry in data.values():
                entry.delete(0, 'end')

    def read_config(self):
        manager_email = None
        user_firstname = None
        user_email = None
        try:
            config_path = os.path.join(TASKS_DIR, CONFIG_FILE)
            if not os.path.exists(config_path):
                return None, None, None
            with open(config_path, 'r') as config_file:
                reader = csv.reader(config_file)
                for row in reader:
                    if len(row) > 1:
                        if row[0].strip() == 'Manager Email': manager_email = row[1].strip()
                        elif row[0].strip() == 'User First Name': user_firstname = row[1].strip()
                        elif row[0].strip() == 'User Email': user_email = row[1].strip()
        except Exception as e:
            print(f"Error reading config: {e}")
            return None, None, None
        return manager_email, user_firstname, user_email