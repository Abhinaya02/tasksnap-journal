# views/to_do_view.py
from datetime import datetime
import sys
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from theme import Theme
from PIL import Image
import os
import json
from .data_utils import resource_path, get_user_data_path
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


class ToDoView(ctk.CTkFrame):
    """
    A view for the To-Do List screen, with file persistence in AppData.
    """
    def __init__(self, master, back_to_dashboard_callback):  # REMOVED: start_in_forced_mode parameter
        super().__init__(master, fg_color=Theme.BACKGROUND)
        self.back_to_dashboard = back_to_dashboard_callback
        
        self.tasks = []
        self.data_file = os.path.join(get_user_data_path(), "tasks.json")
        
        # --- Fonts ---
        self.title_font = Theme.FONT_HEADER
        self.default_task_font = ctk.CTkFont(family="Rubik", size=16, weight="bold")

        try:
            self.back_arrow_icon = load_png_image("assets/back_arrow_icon.png")
        except FileNotFoundError as e:
            print(f"Warning: Icon file not found in ToDoView: {e}")
            self.back_arrow_icon = None
            
        self.create_widgets()
        self.load_tasks()
        self.update_ui_colors()

    def create_widgets(self):
        # --- Header Frame ---
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=20, pady=20, anchor="n")
        
        # Back button
        self.back_button = ctk.CTkButton(self.header_frame, text="", image=self.back_arrow_icon, width=40, height=40,
                                         fg_color="transparent", corner_radius=10,
                                         command=self.back_to_dashboard)
        self.back_button.pack(side="left")

        # Title Label
        self.title_label = ctk.CTkLabel(self.header_frame, text="To-Do List", font=self.title_font)
        self.title_label.pack(side="left", padx=(10, 0))

        # --- Main UI Card Frame ---
        self.card_frame = ctk.CTkFrame(self, corner_radius=20, fg_color=Theme.CARD)
        self.card_frame.pack(pady=(0, 40), padx=40, fill="both", expand=True)

        # --- Input Frame ---
        self.input_frame = ctk.CTkFrame(self.card_frame, corner_radius=10)
        self.input_frame.pack(pady=(20, 10), padx=20, fill="x")

        # Entry field for new tasks
        self.task_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Add a new task...", border_width=0, corner_radius=10, font=Theme.FONT_NORMAL)
        self.task_entry.pack(side="left", padx=(10, 5), pady=10, fill="x", expand=True)
        self.task_entry.bind("<Return>", lambda event: self.add_task())

        # Button to add a new task
        self.add_button = ctk.CTkButton(self.input_frame, text="Add", command=self.add_task, corner_radius=10, width=80, font=Theme.FONT_NORMAL)
        self.add_button.pack(side="right", padx=(5, 10), pady=10)

        # --- Task List Frame (using scrollable frame) ---
        self.task_list_frame = ctk.CTkScrollableFrame(self.card_frame, corner_radius=10)
        self.task_list_frame.pack(pady=10, padx=20, fill="both", expand=True)

        # --- Clear Completed Button ---
        self.clear_button = ctk.CTkButton(self.card_frame, text="Clear Completed Tasks", command=self.clear_completed_tasks, corner_radius=10, font=Theme.FONT_NORMAL)
        self.clear_button.pack(pady=(10, 20), padx=20, fill="x")

    def load_tasks(self):
        """Loads tasks from the JSON file."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    tasks_data = json.load(f)
                
                for task in tasks_data:
                    self.add_task_to_list(task['text'], task['completed'])
            except Exception as e:
                print(f"Error loading tasks: {e}")
                messagebox.showerror("Data Error", "Could not load saved tasks.")

    def save_tasks(self):
        """Saves current tasks to the JSON file."""
        tasks_data = []
        for task in self.tasks:
            # Check if task already has a creation date
            existing_date = None
            if os.path.exists(self.data_file):
                try:
                    with open(self.data_file, 'r') as f:
                        old_tasks = json.load(f)
                        for old_task in old_tasks:
                            if old_task['text'] == task['checkbox'].cget("text"):
                                existing_date = old_task.get('created_date')
                                break
                except:
                    pass
                
            tasks_data.append({
                'text': task['checkbox'].cget("text"),
                'completed': bool(task['checkbox'].get()),
                'created_date': existing_date or datetime.now().strftime("%b %d, %Y")
            })
        
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, 'w') as f:
                json.dump(tasks_data, f, indent=4)
        except Exception as e:
            print(f"Error saving tasks: {e}")
            messagebox.showerror("Data Error", "Could not save tasks to file.")


    def add_task(self):
        task_text = self.task_entry.get().strip()
        if task_text:
            self.add_task_to_list(task_text, False)
            self.task_entry.delete(0, tk.END)
            self.save_tasks()
        else:
            messagebox.showwarning("Warning", "Task cannot be empty!")

    def add_task_to_list(self, task_text, completed=False):
        task_frame = ctk.CTkFrame(self.task_list_frame, corner_radius=10, fg_color="transparent")
        task_frame.pack(fill="x", pady=5)
        
        checkbox = ctk.CTkCheckBox(task_frame, text=task_text,
                                    font=self.default_task_font,
                                    command=lambda: self.toggle_task_completion(checkbox))
        
        if completed:
            checkbox.select()
            self.toggle_task_completion(checkbox, initial_load=True) # Apply strike-through immediately
        
        checkbox.pack(side="left", padx=10, pady=5)
        
        self.tasks.append({'frame': task_frame, 'checkbox': checkbox})

    def toggle_task_completion(self, checkbox, initial_load=False):
        if checkbox.get() == 1:
            new_font = ctk.CTkFont(family=self.default_task_font.cget("family"),
                                   size=self.default_task_font.cget("size"),
                                   weight="bold",
                                   overstrike=True)
            checkbox.configure(text_color=Theme.TEXT_SECONDARY)
        else:
            new_font = ctk.CTkFont(family=self.default_task_font.cget("family"),
                                   size=self.default_task_font.cget("size"),
                                   weight="bold",
                                   overstrike=False)
            checkbox.configure(text_color=Theme.TEXT)
            
        checkbox.configure(font=new_font)
        
        if not initial_load:
            self.save_tasks() # Save state when toggled by user

    def clear_completed_tasks(self):
        tasks_to_keep = []
        for task in self.tasks:
            if task['checkbox'].get() == 1:
                task['frame'].destroy()
            else:
                tasks_to_keep.append(task)
        self.tasks = tasks_to_keep
        self.save_tasks() # Save after clearing  

    def update_ui_colors(self):
        is_dark = ctk.get_appearance_mode() == "Dark"
        
        self.configure(fg_color=Theme.BACKGROUND)
        self.header_frame.configure(fg_color="transparent")
        self.back_button.configure(hover_color=Theme.ACCENT_BLUE_HOVER if not is_dark else Theme.ACCENT_BLUE)
        self.title_label.configure(text_color=Theme.TEXT)
        self.card_frame.configure(fg_color=Theme.CARD)
        self.input_frame.configure(fg_color=Theme.BACKGROUND)
        
        # Consistent border color for entry
        entry_border_color = Theme.ACCENT_BLUE if is_dark else Theme.TEXT_SECONDARY
        
        self.task_entry.configure(
            fg_color=Theme.BACKGROUND, 
            text_color=Theme.TEXT, 
            border_color=entry_border_color, 
            placeholder_text_color=Theme.TEXT_SECONDARY
        )
        self.add_button.configure(fg_color=Theme.ACCENT_BLUE, hover_color=Theme.ACCENT_BLUE_HOVER)
        self.clear_button.configure(fg_color=Theme.ACCENT_BLUE, hover_color=Theme.ACCENT_BLUE_HOVER)
        self.task_list_frame.configure(fg_color=Theme.CARD)
        
        # Update Checkbox colors and font state
        for task in self.tasks:
            is_checked = task['checkbox'].get()
            
            # Checkbox frame and hover colors
            task['checkbox'].configure(
                fg_color=Theme.ACCENT_GREEN, 
                hover_color=Theme.ACCENT_GREEN_HOVER
            )
            
            # Ensure text color and font style reflect completion state
            if is_checked:
                task['checkbox'].configure(text_color=Theme.TEXT_SECONDARY)
            else:
                task['checkbox'].configure(text_color=Theme.TEXT)
            
            # Re-apply font to refresh strike-through state if needed
            self.toggle_task_completion(task['checkbox'], initial_load=True)


# Add this class to to_do_view.py (after the ToDoView class)

class ToDoPopup(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        
        self.title("Daily Task Reminder")
        self.resizable(False, False)
        
        # FIX: Update icon path
        try:
            self.iconbitmap(resource_path("assets/TaskSnap.ico"))
        except Exception as e:
            print(f"Could not load icon: {e}")

        
        # Remove window decorations first
        self.overrideredirect(True)
        
        # Set size
        width = 500
        height = 620
        
        # Configure the toplevel with a background that will show rounded corners
        self.configure(fg_color="#000001")  # Almost black, will be made transparent
        
        # Set transparency
        self.attributes("-alpha", 0.96)
        self.attributes("-transparentcolor", "#000001")
        
        # REMOVED: self.attributes("-topmost", True)  # Don't force window to stay on top
        
        # Main container with rounded corners - this creates the visual rounded effect
        self.main_container = ctk.CTkFrame(
            self,
            corner_radius=20,
            fg_color=("#2A2D3A", "#1E2130"),
            border_width=2,
            border_color=Theme.ACCENT_BLUE
        )
        self.main_container.pack(fill="both", expand=True, padx=8, pady=8)
        
        # Custom title bar (draggable)
        title_bar = ctk.CTkFrame(
            self.main_container,
            height=50,
            corner_radius=0,
            fg_color=Theme.ACCENT_BLUE
        )
        title_bar.pack(fill="x", padx=0, pady=0, side="top")
        title_bar.pack_propagate(False)
        
        # Make title bar draggable
        title_bar.bind("<Button-1>", self.start_move)
        title_bar.bind("<B1-Motion>", self.do_move)
        
        title_label = ctk.CTkLabel(
            title_bar,
            text="📋 Your Tasks for Today",
            font=Theme.FONT_SUBTITLE,
            text_color="white"
        )
        title_label.pack(side="left", padx=20, pady=12)
        title_label.bind("<Button-1>", self.start_move)
        title_label.bind("<B1-Motion>", self.do_move)
        
        # Main content frame
        content_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=25, pady=20)
        
        # Instruction label
        instruction_label = ctk.CTkLabel(
            content_frame,
            text="Complete all your tasks to continue!",
            font=Theme.FONT_NORMAL,
            text_color="#E0E0E0"
        )
        instruction_label.pack(pady=(0, 15))
        
        # Task list frame (scrollable)
        self.task_list_frame = ctk.CTkScrollableFrame(
            content_frame,
            corner_radius=15,
            fg_color=("#3A3D4A", "#2A2D3A"),
            height=400
        )
        self.task_list_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        # Button frame at bottom
        button_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        button_frame.pack(fill="x")
        
        # Mark All Complete button
        self.complete_all_button = ctk.CTkButton(
            button_frame,
            text="✓ Mark All Complete",
            command=self.mark_all_complete,
            corner_radius=12,
            font=Theme.FONT_NORMAL,
            fg_color=Theme.ACCENT_GREEN,
            hover_color=Theme.ACCENT_GREEN_HOVER,
            height=45,
            width=210
        )
        self.complete_all_button.pack(side="left", padx=5, expand=True)
        
        # Done button (only enabled when all tasks complete OR no tasks)
        self.done_button = ctk.CTkButton(
            button_frame,
            text="✅ All Done!",
            command=self.close_window,
            corner_radius=12,
            font=Theme.FONT_NORMAL,
            fg_color=Theme.ACCENT_PURPLE,
            hover_color=("#9D77E8", Theme.ACCENT_PURPLE),
            height=45,
            width=210,
            state="disabled"
        )
        self.done_button.pack(side="right", padx=5, expand=True)
        
        # Position and show window
        self.update_idletasks()
        self.geometry(f'{width}x{height}')
        
        # Center the window
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
        
        # Initialize data
        self.tasks = []
        self.data_file = os.path.join(get_user_data_path(), "tasks.json")
        
        # Load tasks
        self.load_tasks()
        
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
    
    def load_tasks(self):
        """Loads incomplete tasks from the JSON file and groups them by date."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    tasks_data = json.load(f)
                
                # Only load incomplete tasks
                incomplete_tasks = [task for task in tasks_data if not task.get('completed', False)]
                
                if not incomplete_tasks:
                    # No tasks to show - enable done button immediately
                    self.show_no_tasks_message()
                    return
                
                # Group tasks by date
                tasks_by_date = {}
                for task in incomplete_tasks:
                    date = task.get('created_date', 'Unknown date')
                    if date not in tasks_by_date:
                        tasks_by_date[date] = []
                    tasks_by_date[date].append(task)
                
                # Display tasks grouped by date
                for date, tasks in sorted(tasks_by_date.items(), reverse=True):
                    self.add_date_header(date)
                    for task in tasks:
                        self.add_task_to_list(
                            task['text'],
                            task.get('completed', False)
                        )
                    
            except Exception as e:
                print(f"Error loading tasks: {e}")
                # On error, enable done button so user can close
                self.show_no_tasks_message()
        else:
            # File doesn't exist - enable done button immediately
            self.show_no_tasks_message()
    
    def add_date_header(self, date_str):
        """Adds a date header to group tasks."""
        date_frame = ctk.CTkFrame(
            self.task_list_frame,
            fg_color="transparent"
        )
        date_frame.pack(fill="x", pady=(15, 5), padx=15)
        
        ctk.CTkLabel(
            date_frame,
            text=f"📅 {date_str}",
            font=ctk.CTkFont(family="Rubik", size=13, weight="bold"),
            text_color=Theme.ACCENT_BLUE,
            anchor="w"
        ).pack(side="left", padx=5)
        
        # Separator line
        separator = ctk.CTkFrame(date_frame, height=2, fg_color=("#4A4D5A", "#3A3D4A"))
        separator.pack(side="left", fill="x", expand=True, padx=10)
    
    def show_no_tasks_message(self):
        """Shows a success message when there are no pending tasks."""
        # Clear existing widgets
        for widget in self.task_list_frame.winfo_children():
            widget.destroy()
        
        success_frame = ctk.CTkFrame(self.task_list_frame, fg_color="transparent")
        success_frame.pack(expand=True, pady=80)
        
        ctk.CTkLabel(
            success_frame,
            text="🎉",
            font=("Rubik", 64)
        ).pack(pady=15)
        
        ctk.CTkLabel(
            success_frame,
            text="All Caught Up!",
            font=Theme.FONT_HEADER,
            text_color=Theme.ACCENT_GREEN
        ).pack(pady=5)
        
        ctk.CTkLabel(
            success_frame,
            text="You have no pending tasks.",
            font=Theme.FONT_NORMAL,
            text_color="#E0E0E0"
        ).pack(pady=5)
        
        # ALWAYS enable done button when no tasks
        self.done_button.configure(state="normal")
        
        # Hide the "Mark All Complete" button since there are no tasks
        self.complete_all_button.configure(state="disabled")
    
    def add_task_to_list(self, task_text, completed=False):
        """Adds a task to the popup list."""
        task_frame = ctk.CTkFrame(
            self.task_list_frame,
            corner_radius=10,
            fg_color=("#3A3D4A", "#2A2D3A"),
            border_width=2,
            border_color=("#4A4D5A", "#3A3D4A") if not completed else Theme.ACCENT_GREEN
        )
        task_frame.pack(fill="x", pady=5, padx=15)
        
        # Main task content frame
        task_content = ctk.CTkFrame(task_frame, fg_color="transparent")
        task_content.pack(fill="x", padx=12, pady=10)
        
        # Checkbox
        checkbox = ctk.CTkCheckBox(
            task_content,
            text=task_text,
            font=ctk.CTkFont(family="Rubik", size=14, weight="bold"),
            command=lambda: self.toggle_task_completion(checkbox, task_frame),
            text_color="white",
            fg_color=Theme.ACCENT_GREEN,
            hover_color=Theme.ACCENT_GREEN_HOVER,
            border_color=("#5A5D6A", "#4A4D5A")
        )
        
        if completed:
            checkbox.select()
        
        checkbox.pack(side="left", anchor="w", fill="x", expand=True)
        
        self.tasks.append({
            'frame': task_frame,
            'checkbox': checkbox,
            'text': task_text
        })
        
        # Apply initial styling
        self.toggle_task_completion(checkbox, task_frame, initial_load=True)
    
    def toggle_task_completion(self, checkbox, task_frame, initial_load=False):
        """Updates the visual state when a task is toggled."""
        is_completed = checkbox.get() == 1
        
        if is_completed:
            # Strike-through font
            new_font = ctk.CTkFont(
                family="Rubik",
                size=14,
                weight="bold",
                overstrike=True
            )
            checkbox.configure(
                text_color="#A0A0A0",
                font=new_font
            )
            task_frame.configure(border_color=Theme.ACCENT_GREEN)
        else:
            # Normal font
            new_font = ctk.CTkFont(
                family="Rubik",
                size=14,
                weight="bold",
                overstrike=False
            )
            checkbox.configure(
                text_color="white",
                font=new_font
            )
            task_frame.configure(border_color=("#4A4D5A", "#3A3D4A"))
        
        if not initial_load:
            self.save_tasks()
            self.check_all_complete()
    
    def mark_all_complete(self):
        """Marks all tasks as complete."""
        for task in self.tasks:
            if task['checkbox'].get() == 0:
                task['checkbox'].select()
                self.toggle_task_completion(
                    task['checkbox'],
                    task['frame']
                )
    
    def check_all_complete(self):
        """Checks if all tasks are complete and enables the done button."""
        if len(self.tasks) == 0:
            # No tasks at all - enable done button
            self.done_button.configure(state="normal")
            self.complete_all_button.configure(state="disabled")
        else:
            all_complete = all(task['checkbox'].get() == 1 for task in self.tasks)
            
            if all_complete:
                self.done_button.configure(state="normal")
            else:
                self.done_button.configure(state="disabled")
    
    def save_tasks(self):
        """Saves the current task states back to the JSON file."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    all_tasks = json.load(f)
                
                # Update completion status
                for task in self.tasks:
                    task_text = task['text']
                    is_completed = task['checkbox'].get() == 1
                    
                    for saved_task in all_tasks:
                        if saved_task['text'] == task_text:
                            saved_task['completed'] = is_completed
                            break
                
                # Write back to file
                with open(self.data_file, 'w') as f:
                    json.dump(all_tasks, f, indent=4)
                    
            except Exception as e:
                print(f"Error saving tasks: {e}")
    
    def close_window(self):
        """Closes the popup window and exits the application."""
        try:
            self.destroy()
            self.master.quit()
        except:
            pass
        finally:
            # Force exit the entire Python process
            sys.exit(0)


def launch_todo_popup():
    """Launches the compact To-Do popup window as a standalone application."""
    import customtkinter as ctk
    from theme import Theme
    
    root = ctk.CTk()
    root.withdraw()
    
    # FIX: Set icon for root window too
    try:
        from .data_utils import resource_path
        root.iconbitmap(resource_path("assets/TaskSnap.ico"))
    except Exception as e:
        print(f"Could not load icon: {e}")
    
    ctk.set_appearance_mode("System")
    Theme.set_mode(ctk.get_appearance_mode())
    
    try:
        popup = ToDoPopup(root)
        root.mainloop()
    except Exception as e:
        print(f"Error launching ToDo popup: {e}")