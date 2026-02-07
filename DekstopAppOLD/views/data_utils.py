# views/data_utils.py
import sys
import os
import csv
from tkinter import messagebox
from datetime import datetime, date
import gspread
import pandas as pd
from collections import defaultdict
import json
import gspread.utils # Explicitly imported to be available for column letter calculation
import sys
import os

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
# --- Environment Pathing ---

def get_user_data_path(app_name="TaskSnapJournal"):
    """
    Returns the appropriate path for user-specific data (config, tasks) 
    depending on the operating system, often pointing to AppData on Windows.
    """
    if sys.platform == "win32":
        app_data_path = os.path.join(os.environ['LOCALAPPDATA'], app_name)
    else:
        app_data_path = os.path.join(os.path.expanduser('~'), f'.{app_name}')

    os.makedirs(app_data_path, exist_ok=True)
    return app_data_path

def resource_path(relative_path):
    """Get the absolute path to a bundled resource (assets)."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# --- Data File Constants ---

DATA_ROOT = get_user_data_path()
CONFIG_FILE = os.path.join(DATA_ROOT, 'config.csv')
TASK_DATA_FOLDER = os.path.join(DATA_ROOT, 'Tasks')
# NEW: Folder for miscellaneous text files
MISC_DATA_FOLDER = os.path.join(DATA_ROOT, 'Misc') 
SCREEN_TIME_FILE = os.path.join(DATA_ROOT, "screen_time_data.json")
GSPREAD_CREDENTIALS_FILE = resource_path("assets/gspread_credentials.json")


# --- Helper for monthly misc file path ---
def get_misc_file_path():
    """Returns the monthly file path for miscellaneous tasks (e.g., Misc/misc_05-2025.txt)."""
    os.makedirs(MISC_DATA_FOLDER, exist_ok=True)
    month_year_str = datetime.now().strftime("%m-%Y")
    return os.path.join(MISC_DATA_FOLDER, f"misc_{month_year_str}.txt")

# --- Config Read/Write Helpers ---

def read_config(file_path=CONFIG_FILE):
    """Reads the configuration from the config.csv file, creating it if necessary."""
    config = {}
    if not os.path.exists(file_path):
        initial_data = {
            'User First Name': '', 
            'User Email': '', 
            'Shift Start Time': '9:00 AM', 
            'Shift End Time': '5:00 PM', 
            'Week Offs': 'Sat, Sun', 
            'Manager Email': ''
        }
        write_config(initial_data, file_path)
        return initial_data
        
    try:
        with open(file_path, 'r', newline='') as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) >= 2:
                    config[row[0].strip()] = ','.join(row[1:]).strip()
    except Exception as e:
        messagebox.showerror("Config Error", f"Error reading config file: {e}")
        
    return config

def write_config(config_dict, file_path=CONFIG_FILE):
    """Writes the configuration dictionary back to the config.csv file."""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', newline='') as file:
            writer = csv.writer(file)
            for key, value in config_dict.items():
                writer.writerow([key, value])
    except Exception as e:
        messagebox.showerror("Config Error", f"Error writing config file: {e}")

# --- Google Sheets Integration Helper (Productivity Report - Fixed) ---

def update_google_sheet(sheet_name="TaskSnapJournal", base_worksheet_name="Productivity Report"):
    """
    Authenticates with Google Sheets, reads the local CSV, and updates the shared sheet.
    It now creates a new worksheet monthly based on the current date.
    """
    try:
        if not os.path.exists(GSPREAD_CREDENTIALS_FILE):
            return "Error: Google Sheets credentials file not found. Please follow setup instructions."
            
        gc = gspread.service_account(filename=GSPREAD_CREDENTIALS_FILE)

        try:
            sh = gc.open(sheet_name)
        except gspread.exceptions.SpreadsheetNotFound:
            sh = gc.create(sheet_name)
        
        current_date = datetime.now()
        # --- NEW: Dynamic Worksheet Name ---
        worksheet_name = f"{base_worksheet_name} - {current_date.strftime('%b %Y')}"

        try:
            worksheet = sh.worksheet(worksheet_name)
        except gspread.exceptions.WorksheetNotFound:
            # If the monthly sheet doesn't exist, create it
            worksheet = sh.add_worksheet(title=worksheet_name, rows=1, cols=1)
            
        month_year_str = current_date.strftime("%m-%Y")
        local_csv_path = os.path.join(TASK_DATA_FOLDER, f"tasks_{month_year_str}.csv")

        if not os.path.exists(local_csv_path):
            return "No local data to upload."
            
        df = pd.read_csv(local_csv_path)

        if df.empty:
            return "No data to upload."

        config = read_config()
        employee_name = config.get('User First Name', 'Unknown User')
        
        # --- Data Transformation: Robust Flattening and Renaming ---
        
        # 1. Melt the DataFrame to long format (Category, Complexity, Value)
        df_long = pd.melt(df, id_vars='Category', var_name='Complexity', value_name='Value')
        
        # 2. Define the exact mappings for renaming columns to match the Sheets
        def map_header(row):
            category = row['Category']
            complexity = row['Complexity']
            
            # 2a. Category Renaming
            if category == 'Package':
                category = 'Packages'
            elif category == 'PRF Creations':
                category = 'PRF Creation'
            
            # 2b. Incident Complexity Renaming (Simple/Medium/Complex -> P1/P2/P3)
            if category == 'Incident':
                complexity_map = {'Simple': 'P1', 'Medium': 'P2', 'Complex': 'P3'}
                complexity = complexity_map.get(complexity, complexity)
            
            # 2c. Combine to form the final header key
            return f"{category} - {complexity}"

        # Apply the mapping function to create the final, standardized column name
        df_long['Sheet_Header'] = df_long.apply(map_header, axis=1)
        
        # 3. Pivot back to wide format, using the new Sheet_Header as columns
        # Aggregate any potential duplicates (though there shouldn't be any)
        df_final_wide = df_long.pivot_table(index='Category', columns='Sheet_Header', values='Value', aggfunc='sum').fillna(0)

        # Drop the index since we only need one row of totals
        final_series = df_final_wide.sum(axis=0)

        # 4. Define the exact headers expected by the Google Sheet (Master Key)
        standard_headers_data = [
            'Packages - Simple', 'Packages - Medium', 'Packages - Complex',
            'QA - Simple', 'QA - Medium', 'QA - Complex',
            'Incident - P1', 'Incident - P2', 'Incident - P3',
            'PRF Creation - Simple'
        ]
        
        # 5. Use reindex to get the correct order and fill missing values with 0
        final_series = final_series.reindex(standard_headers_data, fill_value=0)
        
        # Prepare the final list of data for Google Sheets
        cleaned_row = final_series.tolist()
        
        # Insert the metadata at the start of the list
        cleaned_row.insert(0, employee_name)
        cleaned_row.insert(1, current_date.strftime("%Y-%m-%d %H:%M:%S"))
        
        # Recalculate the Total based on the final, correct counts
        total_value = sum(cleaned_row[2:])
        cleaned_row.append(total_value) # This makes the row length 13 (A-M)

        # --- Check for existing headers and create them if necessary ---
        existing_data = worksheet.get_all_values()
        
        headers_exist = len(existing_data) >= 2 and existing_data[0][0] == 'Employee Name'

        if not headers_exist:
            # Corrected header layout to match 13 columns (A-M)
            header_row_1 = ['Employee Name', 'Data Submitted', 'Packages', 'Packages', 'Packages', 'QA', 'QA', 'QA', 'Incident', 'Incident', 'Incident', 'PRF Creation', 'Total']
            header_row_2 = ['', '', 'Simple', 'Medium', 'Complex', 'Simple', 'Medium', 'Complex', 'P1', 'P2', 'P3', 'Simple', '']
            worksheet.update('A1', [header_row_1, header_row_2])

            # ===== FORMAT THE HEADER ROWS =====
            worksheet.format('A1:M2', {
                'backgroundColor': {'red': 0.26, 'green': 0.52, 'blue': 0.96},
                'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
                'horizontalAlignment': 'CENTER',
                'verticalAlignment': 'MIDDLE'
            })

            # Merge cells for main category headers
            worksheet.merge_cells('A1:A2')
            worksheet.merge_cells('B1:B2')
            worksheet.merge_cells('C1:E1')
            worksheet.merge_cells('F1:H1')
            worksheet.merge_cells('I1:K1')
            worksheet.merge_cells('L1:L2')
            worksheet.merge_cells('M1:M2')

            existing_data = worksheet.get_all_values()

        # --- Check for existing row and update instead of appending ---
        update_row_index = -1
        
        # Start checking from row 3 (index 2) onwards to skip the two header rows
        # --- FIX: Match ONLY Employee Name ---
        # NOTE: We iterate over the entire dataset starting from the first potential data row (index 2)
        for i, row in enumerate(existing_data[2:]):
            # We assume a single row per employee per month for repeated updates.
            if len(row) > 0 and row[0] == employee_name:
                update_row_index = i + 3 # +3 accounts for 0-based index and 2 header rows skipped (A1, A2)
                break
        
        if update_row_index != -1:
            # Corrected the cell range to M to match the 13 columns (A to M)
            cell_range = f'A{update_row_index}:M{update_row_index}'
            worksheet.update(cell_range, [cleaned_row], value_input_option='USER_ENTERED')

            # Format the updated row with center alignment
            worksheet.format(cell_range, {
                'horizontalAlignment': 'CENTER',
                'verticalAlignment': 'MIDDLE'
            })

            return f"Success: Data for {current_date.strftime('%b %d')} updated in '{worksheet_name}'."
        else:
            # If the employee is not found, append a new row
            worksheet.append_row(cleaned_row, value_input_option='USER_ENTERED')

            # Format the newly appended row
            new_row_num = len(worksheet.get_all_values())
            worksheet.format(f'A{new_row_num}:M{new_row_num}', {
                'horizontalAlignment': 'CENTER',
                'verticalAlignment': 'MIDDLE'
            })

            return f"Success: New data row appended to '{worksheet_name}'."

    except FileNotFoundError:
        return "Error: Google Sheets credentials file not found. Please follow setup instructions."
    except gspread.exceptions.WorksheetNotFound as e:
        # This should only catch the case where the base sheet name is wrong, but the dynamic name logic should handle the monthly creation
        return f"Error: Worksheet '{worksheet_name}' not found. Please check the name or retry."
    except gspread.exceptions.SpreadsheetNotFound:
        return f"Error: Spreadsheet '{sheet_name}' not found. Please check the name and sharing permissions."
    except Exception as e:
        # This catches generic errors like DimensionMismatch
        messagebox.showerror("Google Sheets Warning", f"An unexpected error occurred during Google Sheets update:\n{e.__class__.__name__}: {e}")
        return f"An unexpected error occurred during Google Sheets update: {e.__class__.__name__}: {e}"

# --- Screen Time Report Update (Wide/Daily Column Format - FINAL FIX) ---

def update_google_sheet_screen_time(sheet_name="TaskSnapJournal", base_worksheet_name="Screen Time Report", user_screen_time_data=None):
    """
    Authenticates with Google Sheets and updates the shared screen time sheet in a wide format:
    Employee Name | Last Updated On | Date 1 | Date 2 | ...
    """
    
    if user_screen_time_data is None:
        return "Error: No screen time data provided."
    
    # --- Define Fixed Structure ---
    HEADERS_BASE = ['Employee Name', 'Last Updated On']
    MIN_COLS = len(HEADERS_BASE) + 10 # Ensure at least 12 columns for future dates
    
    try:
        if not os.path.exists(GSPREAD_CREDENTIALS_FILE):
            return "Error: Google Sheets credentials file not found."
            
        gc = gspread.service_account(filename=GSPREAD_CREDENTIALS_FILE)

        try:
            sh = gc.open(sheet_name)
        except gspread.exceptions.SpreadsheetNotFound:
            sh = gc.create(sheet_name)

        try:
            worksheet = sh.worksheet(base_worksheet_name)
        except gspread.exceptions.WorksheetNotFound:
            # Create a new sheet with initial headers and enough columns
            worksheet = sh.add_worksheet(title=base_worksheet_name, rows=1, cols=MIN_COLS)
            worksheet.update('A1', [HEADERS_BASE])

            # ===== FORMAT THE HEADER ROW =====
            worksheet.format('A1:L1', {
                'backgroundColor': {'red': 0.26, 'green': 0.52, 'blue': 0.96},  # Blue color
                'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},  # White text
                'horizontalAlignment': 'CENTER',
                'verticalAlignment': 'MIDDLE'
            })
        
        config = read_config()
        employee_name = config.get('User First Name', 'Unknown User')
        
        # Prepare data for today
        current_date_obj = date.today()
        # Use simple date format (e.g., 10/4, 10/5) for column header as shown in the image
        date_header_str = current_date_obj.strftime("%#m/%#d").replace('#', '') 
        
        # 1. Calculate Total App Time in Hours (App Usage Only)
        total_app_time_seconds = sum(user_screen_time_data.get("usage", {}).values())
        total_time_hrs_str = f"{round(total_app_time_seconds / 3600, 2)}hrs"
        
        # 2. Get all existing headers and data
        existing_headers = worksheet.row_values(1) # CRITICAL FIX: Get headers from Row 1
        existing_data = worksheet.get_all_values()
        
        # CRITICAL: Ensure the sheet has enough columns right now.
        if worksheet.col_count < MIN_COLS:
             worksheet.resize(cols=MIN_COLS)
             # Refetch to be safe
             existing_headers = worksheet.row_values(1)
             existing_data = worksheet.get_all_values()

        # --- Find or Create Date Column (Today's Date) ---
        
        date_col_index = -1 # 0-based index
        
        try:
            # Safely try to find the column index of today's date header (e.g., '10/4')
            date_col_index = existing_headers.index(date_header_str)
        except ValueError:
            # Date column doesn't exist, so we must add it as the last column
            
            # 1. Get the new column index (1-based for gspread update)
            new_col_index = len(existing_headers) + 1
            
            # 2. Update the header row using update_cell (SAFEST METHOD)
            worksheet.update_cell(1, new_col_index, date_header_str)
            
            # 3. Update internal header list and column index
            existing_headers.append(date_header_str)
            date_col_index = len(existing_headers) - 1 # 0-based index

            # Check for worksheet resize needed if we've gone past the MIN_COLS buffer
            if new_col_index > worksheet.col_count:
                 worksheet.resize(cols=new_col_index)
        
        # --- Find or Create Employee Row ---
        
        employee_row_index = -1 # 1-based index (row 1 is header)
        
        # Search for employee row starting from row 2 (index 1 in existing_data)
        for i, row in enumerate(existing_data[1:]):
            if row and row[0] == employee_name:
                employee_row_index = i + 2 # +2 because we skipped the header row (index 0)
                break
        
        if employee_row_index == -1:
            # Employee not found, append a new row
            timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # CRITICAL FIX: Pad the new row with empty strings up to the required column count
            # This prevents the 'Invalid value' API error when trying to update a new, short row.
            padded_row = [employee_name, timestamp_str] + [''] * (len(existing_headers) - 2)
            
            worksheet.append_row(padded_row, value_input_option='USER_ENTERED')
            
            # Get the new row index (last row number)
            existing_data = worksheet.get_all_values()
            employee_row_index = len(existing_data)
        
        # --- Update the Specific Cell ---
        
        # 1. Update the total time cell
        # Column index is 0-based, gspread cell operations are 1-based.
        worksheet.update_cell(employee_row_index, date_col_index + 1, total_time_hrs_str)
        
        # 2. Update the "Last Updated On" cell (Column B)
        worksheet.update_cell(employee_row_index, 2, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        return f"Success: Screen time data for {date_header_str} updated in wide format."

    except Exception as e:
        error_message = f"An unexpected error occurred during Google Sheets update:\n{e.__class__.__name__}: {e}"
        messagebox.showerror("Google Sheets Warning", error_message)
        return error_message
