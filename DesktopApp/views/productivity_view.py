# views/productivity_view.py
import csv
import sys
import os
import threading
from collections import defaultdict
import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from PIL import Image, ImageTk, ImageOps # ADD ImageOps for coloring
from theme import Theme
from .Summary_Window import MatplotlibPlotter
from .Edit_Details import EditableDataDialog
from .Misc_Window import Misc_Window
from .Send_Email import EmailSender
# IMPORT FIX: Added get_misc_file_path to ensure it's available for Misc_Window
from .data_utils import read_config, resource_path, get_user_data_path, TASK_DATA_FOLDER, CONFIG_FILE, update_google_sheet, get_misc_file_path 

def launch_productivity_popup():
    """Launch productivity view as standalone popup window"""
    import sys
    import customtkinter as ctk
    from theme import Theme
    
    root = ctk.CTk()
    root.title("Productivity Report - TaskSnap")
    
    try:
        root.iconbitmap(resource_path("assets/TaskSnap.ico"))
    except:
        pass
    
    root.geometry("900x700")
    root.minsize(800, 600)
    
    ctk.set_appearance_mode(ctk.get_appearance_mode())
    Theme.set_mode(ctk.get_appearance_mode())
    
    config = read_config()
    view = ProductivityView(root, config)
    view.pack(fill="both", expand=True)
    
    # Add exit handler
    def on_close():
        root.quit()
        root.destroy()
        sys.exit(0)
    
    root.protocol("WM_DELETE_WINDOW", on_close)
    
    try:
        root.mainloop()
    except:
        pass
    finally:
        sys.exit(0)

    
    
    productivity_view = ProductivityView(root, back_to_dashboard_callback=on_close)
    productivity_view.pack(fill="both", expand=True)
    
    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()

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

class EmailThread(threading.Thread):
    """A thread to send the email in the background."""
    def __init__(self, app, manager_email, user_firstname, user_email, report_details, misc_tasks_details):
        super().__init__()
        self.app = app
        self.manager_email = manager_email
        self.user_firstname = user_firstname
        self.user_email = user_email
        self.report_details = report_details
        self.misc_tasks_details = misc_tasks_details

    def run(self):
        """Call the email sending method."""
        email_sender = EmailSender()
        task_file = os.path.join(TASK_DATA_FOLDER, f"tasks_{datetime.now().strftime('%m-%Y')}.csv")
        misc_file = os.path.join(TASK_DATA_FOLDER, f"Misc_{datetime.now().strftime('%m-%Y')}.txt")

        report_details = email_sender.format_report_details(task_file)
        misc_tasks_details = email_sender.format_misc_task(misc_file)
        
        success = email_sender.send_report_email(
            self.manager_email, self.user_firstname, self.user_email, report_details, misc_tasks_details
        )
        self.app.after(0, self.app.on_report_sent, success)

class ProductivityView(ctk.CTkFrame):
    def __init__(self, master, back_to_dashboard_callback):
        super().__init__(master, fg_color=Theme.BACKGROUND)
        
        os.makedirs(TASK_DATA_FOLDER, exist_ok=True)
        
        self.back_to_dashboard_callback = back_to_dashboard_callback
        self.master = master

        self.summary_window = None
        self.edit_window = None
        self.misc_window_obj = None # Store the Misc_Window object here
        self.sidebar_frame = None
        self.sidebar_visible = False
        self.is_animating = False
        self.slide_speed = 10
        self.slide_step = 0.03
        self.animation_id = None
        self.sidebar_start_y = 0.0 
        self.sidebar_height_factor = 1.0

        self.header_font = Theme.FONT_HEADER
        self.section_title_font = Theme.FONT_SUBTITLE
        self.label_font = Theme.FONT_NORMAL
        self.input_font = Theme.FONT_NORMAL

        self.create_widgets()

    def create_widgets(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.top_frame = ctk.CTkFrame(self, fg_color=Theme.CARD)
        self.top_frame.grid(row=0, column=0, sticky="new", padx=20, pady=(20, 10))
        self.top_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Load icons using the updated dynamic coloring function
        menu_image = load_png_image("assets/menu.png")
        backarrow_image = load_png_image("assets/back_arrow_icon.png")

        self.backarrow_button = ctk.CTkButton(self.top_frame, image=backarrow_image, text="", width=40, height=40,
                                         command=self.back_to_dashboard_callback, fg_color="transparent")
        self.backarrow_button.grid(row=0, column=0, sticky="w", padx=10)

        self.month_label = ctk.CTkLabel(self.top_frame, text=datetime.now().strftime("%B"), font=self.header_font)
        self.month_label.grid(row=0, column=1)

        self.menu_button = ctk.CTkButton(self.top_frame, image=menu_image, text="", width=40, height=40,
                                         command=self.toggle_sidebar_menu, fg_color="transparent")
        self.menu_button.grid(row=0, column=2, sticky="e", padx=10)
        
        self.main_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.main_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.input_frames = []
        
        # --- Common Grid Configuration ---
        # Column 0 (Label) has a fixed width of 150px.
        # Column 1 (Input) takes the rest of the available space.
        def configure_grid_frame(frame):
            frame.grid_columnconfigure(0, minsize=150) # Fixed width for label column
            frame.grid_columnconfigure(1, weight=1)    # Dynamic width for input column
            return frame

        # QA Section
        qa_frame = ctk.CTkFrame(self.main_frame, corner_radius=10, fg_color=Theme.CARD)
        qa_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(qa_frame, text="QA", font=self.section_title_font).pack(pady=(10, 5))
        self.input_frames.append(qa_frame)
        
        qa_grid_frame = configure_grid_frame(ctk.CTkFrame(qa_frame, fg_color="transparent"))
        qa_grid_frame.pack(fill="x", padx=10, pady=5)
        
        # Labels are placed with sticky="w" (West/Left) and padding
        qa_simple_label = ctk.CTkLabel(qa_grid_frame, text="Simple", anchor="w", font=self.label_font)
        qa_simple_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.qa_simple_input = ctk.CTkEntry(qa_grid_frame, font=self.input_font, corner_radius=5)
        self.qa_simple_input.grid(row=0, column=1, sticky="ew", padx=5, pady=5) # Input fields expand fully
        
        qa_medium_label = ctk.CTkLabel(qa_grid_frame, text="Medium", anchor="w", font=self.label_font)
        qa_medium_label.grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.qa_medium_input = ctk.CTkEntry(qa_grid_frame, font=self.input_font, corner_radius=5)
        self.qa_medium_input.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        
        qa_complex_label = ctk.CTkLabel(qa_grid_frame, text="Complex", anchor="w", font=self.label_font)
        qa_complex_label.grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.qa_complex_input = ctk.CTkEntry(qa_grid_frame, font=self.input_font, corner_radius=5)
        self.qa_complex_input.grid(row=2, column=1, sticky="ew", padx=5, pady=5)

        # PACKAGES Section
        pkg_frame = ctk.CTkFrame(self.main_frame, corner_radius=10, fg_color=Theme.CARD)
        pkg_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(pkg_frame, text="PACKAGES", font=self.section_title_font).pack(pady=(10, 5))
        self.input_frames.append(pkg_frame)
        
        pkg_grid_frame = configure_grid_frame(ctk.CTkFrame(pkg_frame, fg_color="transparent"))
        pkg_grid_frame.pack(fill="x", padx=10, pady=5)
        
        pkg_simple_label = ctk.CTkLabel(pkg_grid_frame, text="Simple Package", anchor="w", font=self.label_font)
        pkg_simple_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.pkg_simple_input = ctk.CTkEntry(pkg_grid_frame, font=self.input_font, corner_radius=5)
        self.pkg_simple_input.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        pkg_medium_label = ctk.CTkLabel(pkg_grid_frame, text="Medium Package", anchor="w", font=self.label_font)
        pkg_medium_label.grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.pkg_medium_input = ctk.CTkEntry(pkg_grid_frame, font=self.input_font, corner_radius=5)
        self.pkg_medium_input.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        
        pkg_complex_label = ctk.CTkLabel(pkg_grid_frame, text="Complex Package", anchor="w", font=self.label_font)
        pkg_complex_label.grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.pkg_complex_input = ctk.CTkEntry(pkg_grid_frame, font=self.input_font, corner_radius=5)
        self.pkg_complex_input.grid(row=2, column=1, sticky="ew", padx=5, pady=5)

        # INCIDENTS MANAGED Section
        inc_frame = ctk.CTkFrame(self.main_frame, corner_radius=10, fg_color=Theme.CARD)
        inc_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(inc_frame, text="INCIDENTS MANAGED", font=self.section_title_font).pack(pady=(10, 5))
        self.input_frames.append(inc_frame)

        inc_grid_frame = configure_grid_frame(ctk.CTkFrame(inc_frame, fg_color="transparent"))
        inc_grid_frame.pack(fill="x", padx=10, pady=5)

        inc_simple_label = ctk.CTkLabel(inc_grid_frame, text="P1 Ticket", anchor="w", font=self.label_font)
        inc_simple_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.inc_simple_input = ctk.CTkEntry(inc_grid_frame, font=self.input_font, corner_radius=5)
        self.inc_simple_input.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        inc_medium_label = ctk.CTkLabel(inc_grid_frame, text="P2 Ticket", anchor="w", font=self.label_font)
        inc_medium_label.grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.inc_medium_input = ctk.CTkEntry(inc_grid_frame, font=self.input_font, corner_radius=5)
        self.inc_medium_input.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        inc_complex_label = ctk.CTkLabel(inc_grid_frame, text="P3 Ticket", anchor="w", font=self.label_font)
        inc_complex_label.grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.inc_complex_input = ctk.CTkEntry(inc_grid_frame, font=self.input_font, corner_radius=5)
        self.inc_complex_input.grid(row=2, column=1, sticky="ew", padx=5, pady=5)

        # PRF CREATIONS Section
        prf_frame = ctk.CTkFrame(self.main_frame, corner_radius=10, fg_color=Theme.CARD)
        prf_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(prf_frame, text="PRF CREATIONS", font=self.section_title_font).pack(pady=(10, 5))
        self.input_frames.append(prf_frame)

        prf_grid_frame = configure_grid_frame(ctk.CTkFrame(prf_frame, fg_color="transparent"))
        prf_grid_frame.pack(fill="x", padx=10, pady=5)

        prf_input_label = ctk.CTkLabel(prf_grid_frame, text="PRF Creations", anchor="w", font=self.label_font)
        prf_input_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.prf_input = ctk.CTkEntry(prf_grid_frame, font=self.input_font, corner_radius=5)
        self.prf_input.grid(row=0, column=1, sticky="ew", padx=5, pady=5)


        self.button_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.button_frame.grid(row=2, column=0, sticky="s", padx=20, pady=20)
        self.button_frame.grid_columnconfigure((0, 1), weight=1)

        self.save_button = ctk.CTkButton(self.button_frame, text="Save", command=self.close_and_save,
                                         fg_color=Theme.ACCENT_BLUE, hover_color=Theme.ACCENT_BLUE_HOVER, corner_radius=5)
        self.save_button.grid(row=0, column=0, padx=10, sticky="e")

        self.close_button = ctk.CTkButton(self.button_frame, text="Close", command=self.close_without_saving,
                                          fg_color="#f44336", hover_color="#d32f2f", corner_radius=5)
        self.close_button.grid(row=0, column=1, padx=10, sticky="w")
        
        self.update_ui_colors()

    def update_ui_colors(self):
        is_dark = ctk.get_appearance_mode() == "Dark"
        
        self.configure(fg_color=Theme.BACKGROUND)
        self.main_frame.configure(fg_color="transparent")
        
        self.top_frame.configure(fg_color=Theme.CARD)
        self.month_label.configure(text_color=Theme.TEXT)
        # Note: Icon color is now handled by load_png_image and CTkImage's light/dark images
        self.backarrow_button.configure(
            hover_color=Theme.ACCENT_BLUE_HOVER if not is_dark else Theme.ACCENT_BLUE
        )
        self.menu_button.configure(
            hover_color=Theme.ACCENT_BLUE_HOVER if not is_dark else Theme.ACCENT_BLUE
        )

        for frame in self.input_frames:
            frame.configure(fg_color=Theme.CARD)
            for widget in frame.winfo_children():
                if isinstance(widget, ctk.CTkLabel):
                    widget.configure(text_color=Theme.TEXT)
                
        input_fields = [
            self.qa_simple_input, self.qa_medium_input, self.qa_complex_input,
            self.pkg_simple_input, self.pkg_medium_input, self.pkg_complex_input,
            self.inc_simple_input, self.inc_medium_input, self.inc_complex_input,
            self.prf_input
        ]
        
        entry_bg = Theme.BACKGROUND
        entry_text = Theme.TEXT
        entry_border = Theme.TEXT_SECONDARY if not is_dark else Theme.ACCENT_BLUE_HOVER
        for entry in input_fields:
            entry.configure(
                fg_color=entry_bg,
                text_color=entry_text,
                border_color=entry_border
            )

        self.save_button.configure(
            fg_color=Theme.ACCENT_BLUE, 
            hover_color=Theme.ACCENT_BLUE_HOVER,
            text_color="white"
        )
        self.close_button.configure(
            fg_color="#f44336", 
            hover_color="#d32f2f", 
            text_color="white"
        )
        if self.sidebar_frame:
            self.sidebar_frame.configure(fg_color=Theme.CARD)
            for child in self.sidebar_frame.winfo_children():
                if isinstance(child, ctk.CTkFrame):
                    for button in child.winfo_children():
                        if isinstance(button, ctk.CTkButton):
                            button.configure(
                                fg_color="transparent",
                                hover_color=Theme.ACCENT_BLUE_HOVER if not is_dark else Theme.ACCENT_BLUE,
                                text_color=Theme.TEXT
                            )

    def slide_sidebar(self, start_relx, end_relx):
        if self.animation_id:
            self.master.after_cancel(self.animation_id)

        self.is_animating = True
        current_relx = start_relx
        direction = 1 if end_relx > start_relx else -1
        
        anchor_type = "nw"
        sidebar_rel_width = 0.35
        
        if start_relx > 0.9:
            self.sidebar_frame.place(
                relx=start_relx, 
                rely=self.sidebar_start_y, 
                anchor=anchor_type, 
                relwidth=sidebar_rel_width, 
                relheight=self.sidebar_height_factor
            )

        def animate():
            nonlocal current_relx
            is_done = (direction == 1 and current_relx >= end_relx) or \
                      (direction == -1 and current_relx <= end_relx)

            if is_done:
                self.sidebar_frame.place(
                    relx=end_relx, 
                    rely=self.sidebar_start_y, 
                    anchor=anchor_type, 
                    relwidth=sidebar_rel_width, 
                    relheight=self.sidebar_height_factor
                )
                self.animation_id = None
                self.is_animating = False
                
                if end_relx > 0.9:
                    self.master.unbind('<Button-1>')
                    self.sidebar_visible = False
                elif end_relx < 0.9:
                    self.master.bind('<Button-1>', self.check_and_hide_sidebar) 
                    self.sidebar_visible = True
                return

            current_relx += direction * self.slide_step
            
            if direction == 1:
                current_relx = min(current_relx, end_relx)
            else:
                current_relx = max(current_relx, end_relx)

            self.sidebar_frame.place(
                relx=current_relx, 
                rely=self.sidebar_start_y, 
                anchor=anchor_type, 
                relwidth=sidebar_rel_width, 
                relheight=self.sidebar_height_factor
            )
            self.animation_id = self.master.after(self.slide_speed, animate)
        animate()

    def toggle_sidebar_menu(self):
        if self.is_animating:
            return

        if not self.sidebar_frame:
            self.sidebar_frame = ctk.CTkFrame(self.master, fg_color=Theme.CARD, corner_radius=0)
            self.sidebar_frame.pack_propagate(False) 
            sidebar_content_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
            sidebar_content_frame.pack(fill="x", padx=10, pady=(40, 0))
            button_font = Theme.FONT_NORMAL
            
            # Load icons dynamically for sidebar buttons
            report_image = load_png_image("assets/send_report.png", size=(20, 20))
            edit_image = load_png_image("assets/edit.png", size=(20, 20))
            misc_image = load_png_image("assets/misc.png", size=(20, 20))
            summary_image = load_png_image("assets/summary.png", size=(20, 20))
            
            send_report_button = ctk.CTkButton(sidebar_content_frame, text="Send Report", image=report_image,
                                               command=lambda: [self.toggle_sidebar_menu(), self.show_confirmation_dialog()], compound="left", anchor="w",
                                               fg_color="transparent", text_color=Theme.TEXT, font=button_font)
            send_report_button.pack(fill="x", pady=10, padx=10)
            edit_button = ctk.CTkButton(sidebar_content_frame, text="Edit", image=edit_image,
                                        command=lambda: [self.toggle_sidebar_menu(), self.edit_saved_report()], compound="left", anchor="w",
                                        fg_color="transparent", text_color=Theme.TEXT, font=button_font)
            edit_button.pack(fill="x", pady=10, padx=10)
            add_misc_button = ctk.CTkButton(sidebar_content_frame, text="Miscellaneous", image=misc_image,
                                            command=lambda: [self.toggle_sidebar_menu(), self.open_misc_window()], compound="left", anchor="w",
                                            fg_color="transparent", text_color=Theme.TEXT, font=button_font)
            add_misc_button.pack(fill="x", pady=10, padx=10)
            show_summary_button = ctk.CTkButton(sidebar_content_frame, text="Summary", image=summary_image,
                                                command=lambda: [self.toggle_sidebar_menu(), self.show_summary_window()], compound="left", anchor="w",
                                                fg_color="transparent", text_color=Theme.TEXT, font=button_font)
            show_summary_button.pack(fill="x", pady=10, padx=10)
            self.update_ui_colors()
        
        if self.sidebar_visible:
            start_relx = 0.65
            end_relx = 1.05
        else:
            start_relx = 1.05
            end_relx = 0.65

        self.sidebar_frame.place(relx=start_relx, rely=self.sidebar_start_y, anchor="nw", relwidth=0.35, relheight=self.sidebar_height_factor)
        self.slide_sidebar(start_relx, end_relx)

    def check_and_hide_sidebar(self, event):
        x, y = self.master.winfo_pointerx() - self.master.winfo_rootx(), self.master.winfo_pointery() - self.master.winfo_rooty()
        
        # Check if click is outside the sidebar bounding box
        if self.sidebar_frame and self.sidebar_visible:
            frame_x_start = self.sidebar_frame.winfo_x()
            frame_y_start = self.sidebar_frame.winfo_y()
            frame_x_end = frame_x_start + self.sidebar_frame.winfo_width()
            frame_y_end = frame_y_start + self.sidebar_frame.winfo_height()

            if not (frame_x_start <= x <= frame_x_end and frame_y_start <= y <= frame_y_end):
                self.toggle_sidebar_menu()

    def show_confirmation_dialog(self):
        config = self.master.config # Access config from the main app instance
        manager_email = config.get('Manager Email', '')
        user_firstname = config.get('User First Name', 'User')
        user_email = config.get('User Email', '')

        if not manager_email or not user_email:
            messagebox.showwarning("Configuration Required", "Please update your Manager Email and User Email in the Update Info section before sending a report.")
            return

        response = messagebox.askyesno("Confirm Send", f"Are you sure you want to send the report to {manager_email}?")
        if response:
            try:
                # Placeholder data retrieval (Actual logic is inside EmailThread)
                report_details = "Generating Report..."
                misc_tasks_details = "Loading Miscellaneous Tasks..."

                # --- FIX 3: Pass 'self' (the ProductivityView instance) to the thread ---
                email_thread = EmailThread(
                    self, # Pass the ProductivityView instance
                    manager_email,
                    user_firstname,
                    user_email,
                    report_details,
                    misc_tasks_details
                )
                email_thread.start()
                messagebox.showinfo("Sending...", "Report sending started in the background. You will receive a notification when complete.")

            except Exception as e:
                messagebox.showerror("Thread Error", f"Could not start email thread: {e}")

    def send_report_in_thread(self):
        config = self.get_current_config()
        manager_email = config.get('Manager Email', '')
        user_firstname = config.get('User First Name', 'Team Member')
        user_email = config.get('User Email', '')
        
        if not manager_email or not user_email:
            messagebox.showerror("Configuration Error", "Please fill in User Email and Manager Email in the configuration section.")
            return

        # Use dummy data or gather real data if necessary
        report_details = "Daily Task Report Placeholder"
        misc_tasks_details = "Miscellaneous Tasks Placeholder"
        
        email_thread = EmailThread(self.master, manager_email, user_firstname, user_email, report_details, misc_tasks_details)
        email_thread.start()

    def on_report_sent(self, success):
        """Called by the EmailThread to show success/failure message on the main thread."""
        if success:
            messagebox.showinfo("Report Sent", "Productivity report sent successfully!")
        else:
            messagebox.showerror("Email Error", "Failed to send the productivity report. Check your email configuration.")


    def get_current_config(self):
        # Logic to read config (already handled by data_utils)
        return read_config()

    def edit_saved_report(self):
        if self.edit_window and self.edit_window.winfo_exists():
            self.edit_window.focus_set()
            return
        TASK_FILE = os.path.join(TASK_DATA_FOLDER, f"tasks_{datetime.now().strftime('%m-%Y')}.csv")
        # --- FIX: Pass update_callback for Google Sheets sync ---
        self.edit_window = EditableDataDialog(self.master, TASK_FILE, update_callback=self.sheets_update_wrapper)
        if self.edit_window and not self.edit_window.winfo_exists():
            self.edit_window = None

    def open_misc_window(self):
        if self.misc_window_obj and self.misc_window_obj.winfo_exists():
            self.misc_window_obj.focus_set()
            return
        
        # --- FIX for TypeError: Calculate and pass the required 'misc_file' argument ---
        misc_file_path = get_misc_file_path()
        self.misc_window_obj = Misc_Window(self.master, misc_file=misc_file_path)

    def show_summary_window(self):
        if self.summary_window and self.summary_window.winfo_exists():
            self.summary_window.focus_set()
            return
        self.summary_window = MatplotlibPlotter(TASK_DATA_FOLDER, self.master)
        
    def get_input_data(self):
        data = {
            "QA": {
                "Simple": self.qa_simple_input.get(),
                "Medium": self.qa_medium_input.get(),
                "Complex": self.qa_complex_input.get()
            },
            "Package": {
                "Simple": self.pkg_simple_input.get(),
                "Medium": self.pkg_medium_input.get(),
                "Complex": self.pkg_complex_input.get()
            },
            "Incident": {
                "P1 Ticket": self.inc_simple_input.get(),
                "P2 Ticket": self.inc_medium_input.get(),
                "P3 Ticket": self.inc_complex_input.get()
            },
            "PRF Creations": {
                "PRF Creations": self.prf_input.get()
            }
        }
        return data

    def clear_input_fields(self):
        self.qa_simple_input.delete(0, 'end')
        self.qa_medium_input.delete(0, 'end')
        self.qa_complex_input.delete(0, 'end')
        
        self.pkg_simple_input.delete(0, 'end')
        self.pkg_medium_input.delete(0, 'end')
        self.pkg_complex_input.delete(0, 'end')
        
        self.inc_simple_input.delete(0, 'end')
        self.inc_medium_input.delete(0, 'end')
        self.inc_complex_input.delete(0, 'end')

        self.prf_input.delete(0, 'end')

    def load_existing_data(self):
        TASK_FILE = os.path.join(TASK_DATA_FOLDER, f"tasks_{datetime.now().strftime('%m-%Y')}.csv")
        if not os.path.exists(TASK_FILE):
            return defaultdict(lambda: defaultdict(int))

        data = defaultdict(lambda: defaultdict(int))
        try:
            with open(TASK_FILE, 'r', newline='') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    category = row.get('Category')
                    if category:
                        for key in ['Simple', 'Medium', 'Complex']:
                            if key in row:
                                try:
                                    data[category][key] = int(row[key])
                                except ValueError:
                                    data[category][key] = 0
        except Exception as e:
            messagebox.showerror("Load Error", f"Error loading existing data: {e}")
        return data

    def close_and_save(self):
        try:
            new_data = self.get_input_data()
            TASK_FILE = os.path.join(TASK_DATA_FOLDER, f"tasks_{datetime.now().strftime('%m-%Y')}.csv")
            
            existing_values = self.load_existing_data()

            # 1. Process New Data and Update Cumulative Values
            for category, complexities in new_data.items():
                for complexity, value in complexities.items():
                    # Pass the name of the complexity as it appears in the input field
                    # e.g., 'P1 Ticket', 'Simple', 'PRF Creations'
                    self.update_cumulative_values(existing_values, category, complexity, value)

            # 2. Write the Combined Data back to CSV
            all_categories = ['QA', 'Package', 'Incident', 'PRF Creations']
            with open(TASK_FILE, 'w', newline='') as file:
                fieldnames = ['Category', 'Simple', 'Medium', 'Complex']
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                
                for category in all_categories:
                    values = existing_values.get(category, defaultdict(int))
                    
                    # Special mapping for Incident and PRF Creations back to CSV keys if needed
                    if category == 'Incident':
                         # Map Incident P-tickets back to Simple/Medium/Complex for local CSV structure
                         writer.writerow({
                            'Category': 'Incident',
                            'Simple': values.get('Simple', 0),
                            'Medium': values.get('Medium', 0),
                            'Complex': values.get('Complex', 0)
                        })
                    elif category == 'PRF Creations':
                         writer.writerow({
                            'Category': 'PRF Creations',
                            'Simple': values.get('Simple', 0),
                            'Medium': 0, # PRF Creations only has one input, so Medium/Complex are 0
                            'Complex': 0
                        })
                    else:
                        writer.writerow({
                            'Category': category,
                            'Simple': values.get('Simple', 0),
                            'Medium': values.get('Medium', 0),
                            'Complex': values.get('Complex', 0)
                        })
            
            self.sheets_update_wrapper()

            messagebox.showinfo("Success", "Data Updated Successfully!")
            self.clear_input_fields()
            self.back_to_dashboard_callback()
        except Exception as e:
            messagebox.showerror("Save Error", f"Error saving data: {e}")

    def close_without_saving(self):
        self.back_to_dashboard_callback()

    def sheets_update_wrapper(self):
        """Wrapper to call update_google_sheet and show error/warning messages."""
        google_sheets_result = update_google_sheet()
        if "Error" in google_sheets_result or "Warning" in google_sheets_result:
             messagebox.showwarning("Google Sheets Update", google_sheets_result)
        # We don't show success here, as success is handled by the main save function or the Edit dialog

    def update_cumulative_values(self, existing_values, category, complexity, value):
        if category not in existing_values:
            existing_values[category] = defaultdict(int)
        try:
            int_value = int(value) if value else 0
            
            # --- FIX: Standardize keys for Incident and PRF Creations Categories ---
            # Map P-Tickets back to Simple/Medium/Complex keys for internal data structure
            key_map = {
                'P1 Ticket': 'Simple', 
                'P2 Ticket': 'Medium', 
                'P3 Ticket': 'Complex',
                'PRF Creations': 'Simple' # PRF Creations maps to 'Simple' slot
            }
            
            if category == "Incident":
                 key = key_map.get(complexity, complexity) # complexity is the value of the label e.g., 'P1 Ticket'
            elif category == "PRF Creations":
                key = 'Simple'
            else:
                key = complexity # QA/Package complexities are already 'Simple', 'Medium', 'Complex'

            existing_values[category][key] += int_value
        except ValueError:
            messagebox.showerror("Invalid Input", f"Please enter a valid number for {category} {complexity}.")
