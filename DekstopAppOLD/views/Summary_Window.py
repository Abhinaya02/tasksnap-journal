# views/Summary_Window.py
from datetime import datetime
import os
import sys
import re
import pandas as pd
import matplotlib.pyplot as plt
import customtkinter as ctk
from tkinter import messagebox
from PIL import Image, ImageTk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import mplcursors
from .data_utils import resource_path 
from theme import Theme

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


class MatplotlibPlotter(ctk.CTkToplevel):
    def __init__(self, directory_path, master=None):
        super().__init__(master)
        self.directory_path = directory_path
        self.title("Summary")
        self.iconbitmap("assets/TaskSnap.ico")
        self.geometry("700x500")
        self.transient(master)
        self.grab_set()
        self.resizable(True, True)

        # Load and set window icon using PNG with error handling
        icon_path = 'assets/summary.png'
        icon_photo = load_png_icon(icon_path)
        if icon_photo:
            self.wm_iconphoto(True, icon_photo)
        else:
            print("Warning: Summary window icon could not be set.")

        self.combined_df = self.load_and_combine_data()
        
        if self.combined_df is None or self.combined_df.empty:
            messagebox.showinfo("No Data", "No monthly productivity data files found to generate a summary, or data files are invalid.")
            self.destroy()
            return

        self.create_widgets()

    def create_widgets(self):
        main_frame = ctk.CTkFrame(self, fg_color=Theme.BACKGROUND)
        main_frame.pack(fill="both", expand=True)

        ctk.CTkLabel(main_frame, text="Monthly Productivity Summary", font=Theme.FONT_TITLE).pack(pady=10)

        plot_frame = ctk.CTkFrame(main_frame, fg_color=Theme.CARD, corner_radius=10)
        plot_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.plot_data(plot_frame)

    def load_and_combine_data(self):
        all_data = []
        # Expected column structure for reading all CSV files consistently
        EXPECTED_COLS = ['Category', 'Simple', 'Medium', 'Complex']
        
        pattern = re.compile(r'tasks_(\d{2}-\d{4})\.csv$')

        for filename in os.listdir(self.directory_path):
            match = pattern.match(filename)
            if match:
                month_year_str = match.group(1)
                file_path = os.path.join(self.directory_path, filename)
                
                try:
                    # Read the CSV file
                    df = pd.read_csv(file_path)

                    # --- FIX: Ensure all expected columns exist, filling missing with 0 ---
                    for col in EXPECTED_COLS:
                        if col not in df.columns:
                            # If a column (like 'Complex') is missing, create it and set to 0
                            df[col] = 0
                        
                    # Drop any unexpected columns to standardize the structure
                    df = df[EXPECTED_COLS]
                    # Convert the numerical columns to numeric type, coercing errors to NaN and filling with 0
                    df['Simple'] = pd.to_numeric(df['Simple'], errors='coerce').fillna(0)
                    df['Medium'] = pd.to_numeric(df['Medium'], errors='coerce').fillna(0)
                    df['Complex'] = pd.to_numeric(df['Complex'], errors='coerce').fillna(0)
                    
                    # Add Month and Year columns
                    df['File_Month'] = month_year_str
                    df['Month'] = datetime.strptime(month_year_str, '%m-%Y').strftime('%b %Y')

                    # Melt the numerical columns only
                    df_long = pd.melt(df, 
                                      id_vars=['Category', 'File_Month', 'Month'], 
                                      value_vars=['Simple', 'Medium', 'Complex'], 
                                      var_name='Complexity', 
                                      value_name='Value')
                    
                    # Aggregate value by Category and Month
                    df_sum = df_long.groupby(['Month', 'Category']).agg({'Value': 'sum'}).reset_index()
                    df_sum.rename(columns={'Value': 'Total'}, inplace=True)
                    
                    all_data.append(df_sum)

                except pd.errors.EmptyDataError:
                    print(f"Warning: File {filename} is empty.")
                except Exception as e:
                    print(f"Error reading or processing {filename}: {e}")

        if not all_data:
            return None
        
        # Combine all monthly data into one DataFrame
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Sort the data by Month (using the internal File_Month key) to ensure correct plotting order
        # We need the File_Month from the *original* data for accurate sorting
        month_order_map = {}
        for filename in os.listdir(self.directory_path):
            match = re.match(r'tasks_(\d{2}-\d{4})\.csv$', filename)
            if match:
                month_year_str = match.group(1)
                month_name = datetime.strptime(month_year_str, '%m-%Y').strftime('%b %Y')
                month_order_map[month_name] = month_year_str


        # Create a temporary sort key column using the raw YYYY-MM string for correct chronology
        combined_df['Sort_Key'] = combined_df['Month'].map(lambda x: month_order_map.get(x, '01-1900'))
        combined_df.sort_values(by='Sort_Key', inplace=True)
        
        # Final cleanup and return
        return combined_df.drop(columns=['Sort_Key'])


    def plot_data(self, parent_frame):
        # Pivot by Month and Category, summing the total count
        pivot_df = self.combined_df.pivot_table(index='Month', columns='Category', values='Total', aggfunc='sum')
        
        # Setup plot style
        plt.style.use('dark_background' if ctk.get_appearance_mode() == "Dark" else 'default')
        
        fig, ax = plt.subplots(figsize=(7, 4))
        # Plotting returns an array of artists (containers for the bars)
        pivot_df.plot(kind='bar', stacked=False, ax=ax)
        
        # Get the handles and labels for the legend
        handles, labels = ax.get_legend_handles_labels()
        
        # --- Using index 1 to get font size from the theme tuple ---
        ax.set_title('Grouped Bar Chart for All Months', fontdict={'fontsize': Theme.FONT_SUBTITLE[1]})
        ax.set_xlabel('Month', fontdict={'fontsize': Theme.FONT_NORMAL[1]})
        ax.set_ylabel('Total Count', fontdict={'fontsize': Theme.FONT_NORMAL[1]})
        ax.tick_params(axis='x', rotation=0)

        # Remove scientific notation on y-axis
        ax.ticklabel_format(style='plain', axis='y')

        # Add hover functionality
        # We use handles.index(sel.artist) to find the index of the bar series,
        # and then use that index to get the corresponding label from the `labels` list.
        mplcursors.cursor(handles, hover=True).connect(
            "add", lambda sel: sel.annotation.set_text(
                f'Category: {labels[handles.index(sel.artist)]}\nMonth: {self.combined_df["Month"].unique()[int(sel.target[0])]}\nTotal: {sel.target[1]:.0f}'
            )
        )
        # Ensure the legend is visible for clarity
        ax.legend(title='Category', handles=handles, labels=labels)

        # Embed the plot in the CTkFrame
        canvas = FigureCanvasTkAgg(fig, master=parent_frame)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True)
        canvas.draw()
