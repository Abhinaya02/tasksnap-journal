# views/productivity_view.py
import customtkinter as ctk
from theme import Theme
from PIL import Image

class ProductivityView(ctk.CTkFrame):
    """
    A view for tracking productivity with a cleaner, menu-based layout.
    """
    def __init__(self, master, back_to_dashboard_callback):
        super().__init__(master, fg_color=Theme.BACKGROUND)
        self.back_to_dashboard = back_to_dashboard_callback

        try:
            self.back_arrow_icon = ctk.CTkImage(Image.open("assets/back_arrow_icon.png"), size=(24, 24))
            self.menu_icon = ctk.CTkImage(Image.open("assets/menu_icon.png"), size=(24, 24))
        except FileNotFoundError as e:
            print(f"Warning: Icon file not found in ProductivityView: {e}")
            self.back_arrow_icon = None
            self.menu_icon = None

        self.entries = {}
        self.category_cards = [] # To store card widgets for color updates
        self.create_widgets()

    def create_widgets(self):
        # --- Header ---
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=20, pady=20, anchor="n")

        self.back_button = ctk.CTkButton(self.header_frame, text="", image=self.back_arrow_icon, width=40, height=40, fg_color="transparent", command=self.back_to_dashboard)
        self.back_button.pack(side="left")

        self.title_label = ctk.CTkLabel(self.header_frame, text="Productivity Tracker", font=("Rubik", 28, "bold"))
        self.title_label.pack(side="left", padx=10, expand=True, anchor="w")

        # --- Hamburger Menu Button ---
        self.menu_button = ctk.CTkButton(self.header_frame, text="", image=self.menu_icon, width=40, height=40, fg_color="transparent", command=self.toggle_more_options)
        self.menu_button.pack(side="right")
        
        # --- Main Content Area ---
        self.content_frame = ctk.CTkScrollableFrame(self, corner_radius=12)
        self.content_frame.pack(fill="both", expand=True, padx=60, pady=(0, 20))
        
        self.form_title_label = ctk.CTkLabel(self.content_frame, text="Daily Productivity Log", font=("Rubik", 24, "bold"))
        self.form_title_label.pack(pady=(20, 20), anchor="w", padx=20)

        # --- FIX: Removed the extra container and packing the grid directly ---
        self.form_grid = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.form_grid.pack(fill="x", expand=True, padx=20) # expand and fill
        self.form_grid.grid_columnconfigure(0, weight=2) # Label column
        self.form_grid.grid_columnconfigure((1,2,3), weight=1) # Entry columns

        categories = ["Packaging", "QA", "Troubleshooting", "Defects"]
        for i, category in enumerate(categories):
            if category == "Defects":
                self.create_single_field(self.form_grid, category, row=i)
            else:
                self.create_category_row(self.form_grid, category, row=i)

        # --- Action Buttons ---
        button_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(30, 20), padx=20)
        button_frame.grid_columnconfigure((0, 1), weight=1)

        self.update_button = ctk.CTkButton(button_frame, text="Update", font=("Rubik", 16, "bold"), height=40, command=self.update_data)
        self.update_button.grid(row=0, column=0, padx=10, pady=5, sticky="ew")

        self.clear_button = ctk.CTkButton(button_frame, text="Clear", font=("Rubik", 16, "bold"), height=40, command=self.clear_fields)
        self.clear_button.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        self.create_dropdown_menu()
        self.update_ui_colors()

    def create_category_row(self, parent, category_name, row):
        label = ctk.CTkLabel(parent, text=category_name, font=Theme.FONT_CARD_TITLE, anchor="w")
        label.grid(row=row, column=0, padx=(0, 10), pady=8, sticky="w")

        self.entries[category_name] = {}
        complexities = ["Simple", "Medium", "Complex"]
        for i, complexity in enumerate(complexities):
            entry = ctk.CTkEntry(parent, placeholder_text=complexity, font=Theme.FONT_NORMAL, height=35)
            entry.grid(row=row, column=i+1, padx=5, pady=8, sticky="ew")
            self.entries[category_name][complexity] = entry

    def create_single_field(self, parent, label_text, row):
        label = ctk.CTkLabel(parent, text=label_text, font=Theme.FONT_CARD_TITLE, anchor="w")
        label.grid(row=row, column=0, padx=(0, 10), pady=8, sticky="w")

        entry = ctk.CTkEntry(parent, placeholder_text="Defects Count", font=Theme.FONT_NORMAL, height=35)
        entry.grid(row=row, column=1, columnspan=3, padx=5, pady=8, sticky="ew")
        self.entries[label_text] = {"count": entry}

    def create_dropdown_menu(self):
        self.dropdown_frame = ctk.CTkFrame(self.master, corner_radius=8, border_width=1)
        
        options = ["View Summary", "Miscellaneous", "Send Email"]
        for option in options:
            btn = ctk.CTkButton(self.dropdown_frame, text=option, font=("Rubik", 14), anchor="w", command=lambda o=option: self.handle_menu_selection(o))
            btn.pack(fill="x", padx=5, pady=5)

    def toggle_more_options(self):
        if self.dropdown_frame.winfo_viewable():
            self.dropdown_frame.place_forget()
            self.master.unbind("<Button-1>")
        else:
            x = self.menu_button.winfo_rootx() - self.dropdown_frame.winfo_width() + self.menu_button.winfo_width()
            y = self.menu_button.winfo_rooty() + self.menu_button.winfo_height()
            self.dropdown_frame.place(x=x, y=y)
            self.master.bind("<Button-1>", lambda event: self.dropdown_frame.place_forget(), add="+")

    def handle_menu_selection(self, choice):
        print(f"Menu option selected: {choice}")
        self.dropdown_frame.place_forget()

    def update_data(self):
        print("\n--- Updating Productivity Data ---")
        for category, data in self.entries.items():
            if "count" in data:
                 value = data["count"].get()
                 if value: print(f"{category}: {value}")
            else:
                for complexity, entry in data.items():
                    value = entry.get()
                    if value: print(f"{category} - {complexity}: {value}")
        print("---------------------------------\n")

    def clear_fields(self):
        for data in self.entries.values():
            if "count" in data:
                data["count"].delete(0, 'end')
            else:
                for entry in data.values():
                    entry.delete(0, 'end')

    def update_ui_colors(self):
        is_dark = ctk.get_appearance_mode() == "Dark"
        
        self.configure(fg_color=Theme.BACKGROUND)
        self.header_frame.configure(fg_color="transparent")
        self.back_button.configure(hover_color="#E5E7EB" if not is_dark else "#2A2A2A")
        self.title_label.configure(text_color=Theme.TEXT)
        self.content_frame.configure(fg_color=Theme.CARD)
        self.form_title_label.configure(text_color=Theme.TEXT)
        
        self.menu_button.configure(hover_color="#E5E7EB" if not is_dark else "#2A2A2A")

        self.update_button.configure(fg_color=Theme.ACCENT_BLUE, hover_color=Theme.ACCENT_BLUE_HOVER)
        self.clear_button.configure(fg_color=Theme.TEXT_SECONDARY, hover_color=Theme.TEXT)

        # Update dropdown colors
        self.dropdown_frame.configure(fg_color=Theme.CARD, border_color="#D1D5DB" if not is_dark else "#4B5563")
        for btn in self.dropdown_frame.winfo_children():
            btn.configure(fg_color="transparent", text_color=Theme.TEXT, hover_color="#E5E7EB" if not is_dark else "#2A2A2A")
        
        # Update category labels and entries
        for widget in self.form_grid.winfo_children():
            if isinstance(widget, ctk.CTkLabel):
                widget.configure(text_color=Theme.TEXT)
            elif isinstance(widget, ctk.CTkEntry):
                widget.configure(text_color=Theme.TEXT, fg_color=Theme.BACKGROUND, border_color="#D1D5DB" if not is_dark else "#4B5563")
