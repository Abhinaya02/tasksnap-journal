# views/dashboard_view.py
import customtkinter as ctk
from PIL import Image, ImageOps
from theme import Theme # Use absolute import since theme.py is in the root
from .data_utils import resource_path # Use local import for data_utils



class DashboardView(ctk.CTkFrame):
    def __init__(self, master, user_name, greeting, quote, show_update_info_callback, show_productivity_callback, show_todo_callback, show_screen_time_callback, toggle_theme_callback):
        super().__init__(master, fg_color=Theme.BACKGROUND)
        self.show_update_info = show_update_info_callback
        self.show_productivity = show_productivity_callback
        self.show_todo = show_todo_callback
        self.show_screen_time = show_screen_time_callback
        self.toggle_theme_callback = toggle_theme_callback

        self.user_name = user_name
        self.greeting = greeting
        self.quote = quote
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1) 

        # CRITICAL FIX 1: Create actual CTkFont objects using the CORRECT Theme constant names.
        self.font_bold = ctk.CTkFont(*Theme.FONT_TITLE) 
        
        # CRITICAL FIX: Handle slant/italic explicitly as CTkFont uses 'slant', not 'weight'.
        quote_family, quote_size, quote_style = Theme.FONT_QUOTE
        self.font_quote = ctk.CTkFont(family=quote_family, size=quote_size, slant=quote_style) 
        
        self.font_card_title = ctk.CTkFont(*Theme.FONT_CARD_TITLE)
        self.font_card_subtitle = ctk.CTkFont(*Theme.FONT_CARD_SUBTITLE)
        
        # Store initial sizes (integer) for scaling reference
        self._initial_font_size = Theme.FONT_TITLE[1] 
        self._initial_quote_size = quote_size 
        self._initial_card_title_size = Theme.FONT_CARD_TITLE[1]
        self._initial_card_subtitle_size = Theme.FONT_CARD_SUBTITLE[1]

        # Initialize widget variables to None before creation (Safety for update_ui_colors)
        self.greeting_label = None 
        self.quote_label = None
        self.theme_toggle_btn = None
        self.cards = []

        try:
            self.sun_icon = ctk.CTkImage(Image.open(resource_path("assets/sun.png")), size=(22, 22))
            self.moon_icon = ctk.CTkImage(Image.open(resource_path("assets/moon.png")), size=(22, 22))
        except FileNotFoundError as e:
            print(f"Warning: Icon file not found: {e}.")
            self.sun_icon = self.moon_icon = None

        # CRITICAL FIX 2: Ensure widgets are created before any color update logic runs
        self.create_widgets() 

    def update_user_name(self, new_name):
        """Updates the user name displayed on the dashboard."""
        self.user_name = new_name
        if self.greeting_label:
            self.greeting_label.configure(text=f"{self.greeting}, {self.user_name}!")

    def tint_icon(self, image_path, color_hex, size=(40, 40)):
        try:
            original_img = Image.open(resource_path(image_path)).convert("RGBA")
            # Calculate RGB tuple from hex
            rgb_tuple = tuple(int(color_hex.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
            
            tinted_img = Image.new("RGBA", original_img.size, rgb_tuple)
            alpha_mask = original_img.split()[-1]
            final_img = Image.new("RGBA", original_img.size)
            final_img.paste(tinted_img, (0, 0), mask=alpha_mask)
            
            return ctk.CTkImage(light_image=final_img, dark_image=final_img, size=size)
        except Exception as e:
            print(f"Error tinting icon {image_path}: {e}")
            return None

    def create_widgets(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0, height=100)
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        header_frame.grid_propagate(False)

        header_left = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_left.pack(side="left", fill="x", expand=True, padx=20)

        # Widget creation defines the attributes!
        self.greeting_label = ctk.CTkLabel(header_left, text=f"{self.greeting}, {self.user_name}!", font=self.font_bold)
        self.greeting_label.pack(anchor="w", pady=(0, 5))
        
        self.quote_label = ctk.CTkLabel(header_left, text=f'"{self.quote}"', font=self.font_quote, wraplength=600, justify="left")
        self.quote_label.pack(anchor="w")
        
        self.is_dark_mode = ctk.get_appearance_mode() == "Dark"
        initial_icon = self.sun_icon if self.is_dark_mode else self.moon_icon
        
        self.theme_toggle_btn = ctk.CTkButton(header_frame, text="", image=initial_icon, width=44, height=44, fg_color="transparent", corner_radius=22, command=self.toggle_theme_callback)
        self.theme_toggle_btn.pack(side="right", anchor="ne", padx=(0, 20), pady=(0, 10))

        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.main_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

        # Populate cards list here
        # Increased padding on grid placement remains a good idea to create a buffer
        self.cards.append(self.create_dashboard_card(self.main_frame, 0, "Update Info", "Manage your profile", "assets/user_icon.png", Theme.ACCENT_BLUE, self.show_update_info))
        self.cards.append(self.create_dashboard_card(self.main_frame, 1, "Productivity", "Track your progress", "assets/chart_icon.png", Theme.ACCENT_GREEN, self.show_productivity))
        self.cards.append(self.create_dashboard_card(self.main_frame, 2, "To-Do List", "Organize your tasks", "assets/list_icon.png", Theme.ACCENT_YELLOW,  self.show_todo))
        self.cards.append(self.create_dashboard_card(self.main_frame, 3, "Screen Time", "Monitor your usage", "assets/monitor_icon.png", Theme.ACCENT_PURPLE, self.show_screen_time))

    def create_dashboard_card(self, parent, col, title, subtitle, icon_path, accent_color, command):
        # FIX: Set corner_radius to 17 instead of 18 to potentially fix rendering bug.
        card = ctk.CTkFrame(parent, corner_radius=17, border_width=0)
        # Increased padding from 15/10 to 18/13 on the card grid placement
        card.grid(row=0, column=col, padx=18, pady=13, sticky="nsew") 
        
        card.grid_rowconfigure(0, weight=1) 
        card.grid_rowconfigure(4, weight=1) 
        card.grid_columnconfigure(0, weight=1)

        tinted_icon = self.tint_icon(icon_path, accent_color)
        
        icon_label = ctk.CTkLabel(card, image=tinted_icon, text="●" if tinted_icon is None else "", font=("Segoe UI", 40, "bold"), fg_color="transparent")
        if tinted_icon is None:
            icon_label.configure(text_color=accent_color)

        icon_label.grid(row=1, column=0, pady=(0,10))
        
        title_label = ctk.CTkLabel(card, text=title, font=self.font_card_title, fg_color="transparent")
        title_label.grid(row=2, column=0, pady=(0, 5))

        subtitle_label = ctk.CTkLabel(card, text=subtitle, font=self.font_card_subtitle, fg_color="transparent")
        subtitle_label.grid(row=3, column=0)

        for widget in [card, icon_label, title_label, subtitle_label]:
            widget.bind("<Button-1>", lambda e: command())

        return {"frame": card, "icon_label": icon_label, "title": title_label, "subtitle": subtitle_label, "icon_path": icon_path}

    def update_ui_colors(self):
        if not self.greeting_label:
            return

        self.is_dark_mode = ctk.get_appearance_mode() == "Dark"

        self.configure(fg_color=Theme.BACKGROUND)
        self.greeting_label.configure(text_color=Theme.TEXT)
        # FIX: Change from Theme.TEXT_SECONDARY to the correct name
        self.quote_label.configure(text_color=Theme.TEXT_SECONDARY)  # This is correct!

        new_icon = self.sun_icon if self.is_dark_mode else self.moon_icon
        hover_color = Theme.ACCENT_BLUE_HOVER if not self.is_dark_mode else Theme.ACCENT_BLUE
        self.theme_toggle_btn.configure(image=new_icon, hover_color=hover_color)

        self.main_frame.configure(fg_color="transparent")

        accent_colors = [Theme.ACCENT_BLUE, Theme.ACCENT_GREEN, Theme.ACCENT_YELLOW, Theme.ACCENT_PURPLE]

        for i, card_widgets in enumerate(self.cards):
            card_widgets['frame'].configure(
                fg_color=Theme.CARD,
                border_width=0,
                corner_radius=17
            )
            card_widgets['title'].configure(text_color=Theme.TEXT)
            # FIX: Change here too
            card_widgets['subtitle'].configure(text_color=Theme.TEXT_SECONDARY)

            # Regenerate tinted icon for the card
            new_tinted_icon = self.tint_icon(card_widgets['icon_path'], accent_colors[i])
            if new_tinted_icon:
                card_widgets['icon_label'].configure(image=new_tinted_icon)
                card_widgets['tinted_icon_ref'] = new_tinted_icon
            else:
                card_widgets['icon_label'].configure(text_color=accent_colors[i])


        
        new_icon = self.sun_icon if self.is_dark_mode else self.moon_icon
        
        # Use theme colors for hover effect consistency
        hover_color = Theme.ACCENT_BLUE_HOVER if not self.is_dark_mode else Theme.ACCENT_BLUE 
        self.theme_toggle_btn.configure(image=new_icon, hover_color=hover_color)
        
        self.main_frame.configure(fg_color="transparent")

        accent_colors = [Theme.ACCENT_BLUE, Theme.ACCENT_GREEN, Theme.ACCENT_YELLOW, Theme.ACCENT_PURPLE]
        for i, card_widgets in enumerate(self.cards):
            # FIX: Ensure border is completely disabled (border_width=0) and use corner_radius=17.
            card_widgets["frame"].configure(
                fg_color=Theme.CARD, 
                border_width=0,
                corner_radius=17
            )
            card_widgets["title"].configure(text_color=Theme.TEXT)
            card_widgets["subtitle"].configure(text_color=Theme.TEXT_SECONDARY)
            
            new_tinted_icon = self.tint_icon(card_widgets["icon_path"], accent_colors[i])
            if new_tinted_icon:
                card_widgets["icon_label"].configure(image=new_tinted_icon)
            else:
                card_widgets["icon_label"].configure(text_color=accent_colors[i])

    def update_font_sizes(self, window_width):
        # Safety check: All fonts must be configured before resizing
        if not self.greeting_label:
            return
            
        max_scale = 1.5
        scale_factor = min(window_width / 900, max_scale)

        # Use stored initial sizes (integer) for base calculation.
        bold_size = max(18, int(self._initial_font_size * scale_factor))
        quote_size = max(10, int(self._initial_quote_size * scale_factor))
        title_size = max(12, int(self._initial_card_title_size * scale_factor))
        subtitle_size = max(8, int(self._initial_card_subtitle_size * scale_factor))
        
        # Configure the fonts to reflect new sizes
        self.font_bold.configure(size=bold_size)
        self.font_quote.configure(size=quote_size)
        self.font_card_title.configure(size=title_size)
        self.font_card_subtitle.configure(size=subtitle_size)

        self.quote_label.configure(wraplength=window_width * 0.6)
