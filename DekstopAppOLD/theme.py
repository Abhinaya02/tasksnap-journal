# views/theme.py
# This file contains the shared theme settings for the application.

class Theme:
    # --- Light Mode (Default) ---
    BACKGROUND = "#F9FAFB"
    CARD = "#FFFFFF"
    TEXT = "#1F2937"
    TEXT_SECONDARY = "#6B7280"
    
    ACCENT_BLUE = "#3B82F6"
    ACCENT_BLUE_HOVER = "#2563EB"
    ACCENT_GREEN = "#22C55E"
    ACCENT_GREEN_HOVER = "#15803D" # ADDED: Hover color for green
    ACCENT_YELLOW = "#F59E0B"
    ACCENT_PURPLE = "#8B5CF6"
    
    # --- Fonts (Used across all layouts for consistency) ---
    FONT_TITLE = ("Rubik", 28, "bold")
    FONT_HEADER = ("Rubik", 24, "bold")
    FONT_SUBTITLE = ("Rubik", 16, "bold")
    FONT_NORMAL = ("Rubik", 14)
    FONT_QUOTE = ("Rubik", 16, "italic")
    FONT_CARD_TITLE = ("Rubik", 18, "bold")
    FONT_CARD_SUBTITLE = ("Rubik", 14)    

    @classmethod
    def set_mode(cls, mode):
        if mode == "Dark":
            cls.BACKGROUND = "#18181B" # Your darker background
            cls.CARD = "#23272F"       # Your lighter card color
            cls.TEXT = "#F3F4F6"
            cls.TEXT_SECONDARY = "#A1A1AA"
            cls.ACCENT_BLUE = "#60A5FA"
            cls.ACCENT_BLUE_HOVER = "#3B82F6"
            cls.ACCENT_GREEN = "#4ADE80"
            cls.ACCENT_GREEN_HOVER = "#22C55E" # Dark mode green hover
            cls.ACCENT_YELLOW = "#FACC15"
            cls.ACCENT_PURPLE = "#A78BFA"
        else: # Default to Light mode
            cls.BACKGROUND = "#F9FAFB"
            cls.CARD = "#FFFFFF"
            cls.TEXT = "#1F2937"
            cls.TEXT_SECONDARY = "#6B7280"
            cls.ACCENT_BLUE = "#3B82F6"
            cls.ACCENT_BLUE_HOVER = "#2563EB"
            cls.ACCENT_GREEN = "#22C55E"
            cls.ACCENT_GREEN_HOVER = "#15803D"
            cls.ACCENT_YELLOW = "#F59E0B"
            cls.ACCENT_PURPLE = "#8B5CF6"
