"""
Configuration settings for Productivity Tracker application.
"""

# List of productive applications
PRODUCTIVE_APPS = [
    "code.exe",              # VS Code
    "pycharm64.exe",         # PyCharm
    "idea64.exe",            # IntelliJ IDEA
    "excel.exe",             # Microsoft Excel
    "word.exe",              # Microsoft Word
    "powerpoint.exe",        # Microsoft PowerPoint
    "outlook.exe",           # Microsoft Outlook
    "onenote.exe",           # Microsoft OneNote
    "notepad.exe",           # Notepad
    "notepad++.exe",         # Notepad++
    "cmd.exe",               # Command Prompt
    "powershell.exe",        # PowerShell
    "WindowsTerminal.exe",   # Windows Terminal
    "chrome.exe",            # Chrome (when being used for work)
    "msedge.exe",            # Edge (when being used for work)
    "firefox.exe",           # Firefox (when being used for work)
]

# List of unproductive applications
UNPRODUCTIVE_APPS = [
    "discord.exe",           # Discord
    "slack.exe",             # Slack (can be productive but often distracting)
    "spotify.exe",           # Spotify
    "steam.exe",             # Steam
    "epicgameslauncher.exe", # Epic Games
    "vlc.exe",               # VLC Media Player
    "netflix.exe",           # Netflix
    "msn.exe",               # MSN
    "telegram.exe",          # Telegram
    "whatsapp.exe",          # WhatsApp
]

# Unproductive websites
UNPRODUCTIVE_WEBSITES = [
    "facebook.com",
    "twitter.com",
    "instagram.com",
    "reddit.com",
    "youtube.com",
    "netflix.com",
    "tiktok.com",
    "twitch.tv",
]

# Productive websites
PRODUCTIVE_WEBSITES = [
    "github.com",
    "stackoverflow.com",
    "docs.python.org",
    "linkedin.com",
    "udemy.com",
    "coursera.org",
    "edx.org",
    "kaggle.com",
]

# Time threshold for unproductive app alert (in seconds)
UNPRODUCTIVE_TIME_THRESHOLD = 60  # 1 minute

# Pomodoro timer settings (in minutes)
POMODORO_WORK_DURATION = 10
POMODORO_SHORT_BREAK_DURATION = 5
POMODORO_LONG_BREAK_DURATION = 15
POMODORO_CYCLES_BEFORE_LONG_BREAK = 4

# Focus score settings
MIN_FOCUS_SCORE = 0
MAX_FOCUS_SCORE = 100
PRODUCTIVE_TIME_WEIGHT = 0.7
UNPRODUCTIVE_TIME_WEIGHT = 0.3

# Data storage
DATA_DIRECTORY = "data"
ACTIVITY_LOG_FILE = f"{DATA_DIRECTORY}/activity_log.csv"
FOCUS_SCORE_FILE = f"{DATA_DIRECTORY}/focus_scores.json" 