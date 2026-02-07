# TaskSnap Journal

📝 A Python desktop application for intelligent task management and personal journaling.

## 🎯 Overview

TaskSnap Journal is a comprehensive desktop application designed to help users manage tasks, track productivity, and maintain a personal journal all in one unified interface. Built with Python and CustomTkinter for a modern, intuitive user experience.

## ✨ Key Features

- **Task Management**: Create, organize, and prioritize tasks with deadlines and categories
- **Journal Entries**: Write and maintain personal journal entries with timestamps
- **Productivity Tracking**: Monitor productivity metrics and generate productivity reports
- **Data Visualization**: View productivity insights with visual charts and statistics
- **Cross-Platform**: Works seamlessly on Windows, macOS, and Linux
- **Data Persistence**: All data is saved locally for offline access and privacy

## 🛠 Tech Stack

- **Language**: Python 3.x
- **GUI Framework**: CustomTkinter (Modern Tkinter)
- **Data Storage**: JSON/SQLite
- **Additional Libraries**:
  - pandas - Data analysis and manipulation
  - matplotlib - Data visualization
  - pyinstaller - Desktop executable generation

## 📦 Project Structure

```
TaskSnapJournal/
├── main.py                 # Application entry point
├── DesktopApp/            # Main application module
│   ├── views/            # UI views and layouts
│   ├── models/           # Data models
│   └── utils/            # Utility functions
├── UI/TaskSnapUI/         # UI components and styling
├── Images/                # Application assets and icons
├── DOCS/                  # Documentation
└── requirements.txt       # Python dependencies
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Abhinaya02/tasksnap-journal.git
cd tasksnap-journal
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running the Application

```bash
python main.py
```

## 💡 Usage

### Creating Tasks
1. Open the application
2. Navigate to the Tasks tab
3. Click "Add Task" and fill in the details
4. Set priority and deadline as needed
5. Save the task

### Writing Journal Entries
1. Go to the Journal tab
2. Click "New Entry"
3. Write your thoughts and reflections
4. Entries are auto-saved with timestamps

### Viewing Productivity
1. Open the Productivity tab
2. View charts showing task completion rates
3. Analyze productivity trends over time

## 📊 Building an Executable

To create a standalone executable (.exe on Windows):

```bash
pip install pyinstaller
pyinstaller --onefile --windowed main.py
```

The executable will be in the `dist/` folder.

## 🔒 Privacy & Security

- All data is stored locally on your machine
- No data is transmitted to external servers
- Complete control over your personal information

## 📝 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest new features
- Submit pull requests

## 📬 Contact

For questions or feedback, please reach out through GitHub issues.

---

**Built with ❤️ by Abhinaya02**
