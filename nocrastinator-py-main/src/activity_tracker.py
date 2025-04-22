"""
Activity tracker module for monitoring application and website usage.
"""

import csv
import os
import time
import psutil
import win32gui
import win32process
from datetime import datetime
from plyer import notification
import threading
import config
import re

class ActivityTracker:
    """
    Tracks user activity, including applications and websites visited.
    Records usage time and categorizes activities as productive or unproductive.
    """
    
    def __init__(self):
        self.current_app = None
        self.current_window_title = None
        self.app_start_time = None
        
        # For unproductive time tracking
        self.unproductive_start_time = None
        self.total_unproductive_time = 0
        self.is_currently_unproductive = False
        self.alert_triggered = False
        self.last_productive_timestamp = time.time()
        
        self.on_unproductive_alert = None  # Callback for UI updates
        
        # Create data directory if it doesn't exist
        os.makedirs(config.DATA_DIRECTORY, exist_ok=True)
        
        # Create or load activity log file
        self.init_activity_log()
        
        # Thread for tracking activities
        self.tracking_thread = None
        self.is_tracking = False
        
        # Browser process names
        self.browsers = ["chrome.exe", "msedge.exe", "firefox.exe", "opera.exe", "brave.exe", "safari.exe"]
        
        print("Activity tracker initialized")
    
    def init_activity_log(self):
        """Initialize activity log file with headers if it doesn't exist"""
        if not os.path.exists(config.ACTIVITY_LOG_FILE):
            with open(config.ACTIVITY_LOG_FILE, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([
                    'timestamp', 
                    'app_name', 
                    'window_title', 
                    'duration_seconds', 
                    'is_productive'
                ])
    
    def get_active_window_info(self):
        """Get information about the currently active window"""
        try:
            hwnd = win32gui.GetForegroundWindow()
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            app_name = process.name().lower()
            window_title = win32gui.GetWindowText(hwnd)
            return app_name, window_title
        except Exception as e:
            print(f"Error getting active window: {e}")
            return None, None
    
    def extract_website_from_title(self, app_name, window_title):
        """
        Extract website information from browser window titles
        Returns the extracted website domain or None if not found
        """
        if not window_title or app_name not in self.browsers:
            return None
            
        # Common title patterns in browsers:
        # 1. "Page Title - Website - Browser"
        # 2. "Website - Page Title"
        # 3. "Page Title | Website"
        # 4. "Page Title - Website"
        
        # Try to extract using common patterns
        patterns = [
            r'(?:https?://)?(?:www\.)?([a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)',  # Extract domain from URL
            r'(?:.*?)(?:[-|]\s*)((?:www\.)?[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)(?:\s*[-|])',  # Middle of the title
            r'(?:.*?)(?:[-|]\s*)((?:www\.)?[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)(?:\s*)$',  # End of the title
        ]
        
        window_title_lower = window_title.lower()
        
        # Check for specific website names (more reliable than regex for some sites)
        known_sites = {
            'facebook': 'facebook.com',
            'twitter': 'twitter.com',
            'x.com': 'twitter.com',
            'instagram': 'instagram.com',
            'reddit': 'reddit.com',
            'youtube': 'youtube.com',
            'netflix': 'netflix.com',
            'tiktok': 'tiktok.com',
            'twitch': 'twitch.tv',
            'github': 'github.com',
            'stackoverflow': 'stackoverflow.com',
            'stack overflow': 'stackoverflow.com',
            'linkedin': 'linkedin.com',
            'udemy': 'udemy.com',
            'coursera': 'coursera.org',
            'edx': 'edx.org',
            'kaggle': 'kaggle.com'
        }
        
        for site, domain in known_sites.items():
            if site in window_title_lower:
                print(f"Website detected: {domain} (from title: {window_title})")
                return domain
                
        # Try regex patterns if no known site found
        for pattern in patterns:
            match = re.search(pattern, window_title)
            if match:
                domain = match.group(1)
                print(f"Website detected: {domain} (from title: {window_title})")
                return domain
                
        return None
    
    def is_productive(self, app_name, window_title):
        """
        Determine if an app or website is productive.
        
        Returns:
        - True: Productive
        - False: Unproductive
        - None: Neutral
        """
        app_name = app_name.lower()
        
        # First check if app is a browser
        if app_name in self.browsers:
            # Extract website from browser window title
            website = self.extract_website_from_title(app_name, window_title)
            
            if website:
                # Check if website is in productive or unproductive lists
                for prod_site in config.PRODUCTIVE_WEBSITES:
                    if prod_site in website:
                        print(f"Productive website detected: {website}")
                        return True
                
                for unprod_site in config.UNPRODUCTIVE_WEBSITES:
                    if unprod_site in website:
                        print(f"Unproductive website detected: {website}")
                        return False
                        
                # If website is found but not categorized, log it for future categorization
                print(f"Uncategorized website detected: {website}")
        
        # Check if app is in productive or unproductive lists
        if app_name in (app.lower() for app in config.PRODUCTIVE_APPS):
            return True
        elif app_name in (app.lower() for app in config.UNPRODUCTIVE_APPS):
            return False
        
        # If not determined yet, check window title for website names
        window_title = window_title.lower()
        for website in config.PRODUCTIVE_WEBSITES:
            if website in window_title:
                return True
        
        for website in config.UNPRODUCTIVE_WEBSITES:
            if website in window_title:
                return False
        
        # Default to neutral
        return None
    
    def start_tracking(self):
        """Start tracking user activity in a separate thread"""
        if self.tracking_thread and self.tracking_thread.is_alive():
            print("Tracking already active")
            return
        
        self.is_tracking = True
        self.tracking_thread = threading.Thread(target=self._track_activity_loop)
        self.tracking_thread.daemon = True
        self.tracking_thread.start()
        print("Activity tracking started")
    
    def stop_tracking(self):
        """Stop tracking user activity"""
        self.is_tracking = False
        if self.tracking_thread:
            self.tracking_thread.join(timeout=1)
        print("Activity tracking stopped")
    
    def _track_activity_loop(self):
        """Main loop for tracking activity"""
        while self.is_tracking:
            app_name, window_title = self.get_active_window_info()
            
            if app_name:
                current_time = time.time()
                
                # If app has changed
                if app_name != self.current_app or window_title != self.current_window_title:
                    # Log previous app session if it exists
                    if self.current_app and self.app_start_time:
                        duration = current_time - self.app_start_time
                        is_productive = self.is_productive(self.current_app, self.current_window_title)
                        self.log_activity(self.current_app, self.current_window_title, duration, is_productive)
                    
                    # Start tracking new app
                    self.current_app = app_name
                    self.current_window_title = window_title
                    self.app_start_time = current_time
                    
                    # Check if the new app is productive/unproductive/neutral
                    is_productive = self.is_productive(app_name, window_title)
                    
                    # Track unproductive time across multiple apps
                    if is_productive is False:  # Explicitly unproductive
                        print(f"Using unproductive app: {app_name}")
                        
                        # If this is the first unproductive app in this session
                        if not self.is_currently_unproductive:
                            self.unproductive_start_time = current_time
                            self.is_currently_unproductive = True
                            self.alert_triggered = False
                            print(f"Started tracking unproductive time at {datetime.fromtimestamp(self.unproductive_start_time).strftime('%H:%M:%S')}")
                    
                    elif is_productive is True:  # Explicitly productive
                        # Reset unproductive tracking when switching to a productive app
                        if self.is_currently_unproductive:
                            print(f"Switching to productive app: {app_name}. Unproductive session ended.")
                            elapsed_unproductive = current_time - self.unproductive_start_time
                            print(f"Unproductive time: {elapsed_unproductive:.1f} seconds")
                            
                            self.is_currently_unproductive = False
                            self.unproductive_start_time = None
                            self.total_unproductive_time = 0
                            self.alert_triggered = False
                            self.last_productive_timestamp = current_time
                
                # Check for unproductive time threshold
                if (self.is_currently_unproductive and 
                    self.unproductive_start_time and 
                    current_time - self.unproductive_start_time >= config.UNPRODUCTIVE_TIME_THRESHOLD and 
                    not self.alert_triggered):
                    self._trigger_unproductive_alert()
                    self.alert_triggered = True
                
            time.sleep(1)  # Check every second
    
    def log_activity(self, app_name, window_title, duration, is_productive):
        """Log app activity to CSV file"""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            with open(config.ACTIVITY_LOG_FILE, 'a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([
                    timestamp,
                    app_name,
                    window_title,
                    round(duration, 2),
                    str(is_productive)
                ])
        except Exception as e:
            print(f"Error logging activity: {e}")
    
    def _trigger_unproductive_alert(self):
        """Trigger an alert for unproductive app usage"""
        print(f"Triggering unproductive time alert")
        current_time = time.time()
        unproductive_minutes = (current_time - self.unproductive_start_time) / 60
        
        # Send desktop notification
        notification.notify(
            title="Productivity Alert",
            message=f"You've been unproductive for over {int(unproductive_minutes)} minute(s). Consider switching to a productive task.",
            timeout=10
        )
        
        # Call the UI callback if registered
        if self.on_unproductive_alert:
            self.on_unproductive_alert("unproductive time")
        
        # Mark alert as triggered to prevent repeated alerts
        self.alert_triggered = True
        print(f"Unproductive time alert triggered after {unproductive_minutes:.1f} minutes")
    
    def force_alert(self):
        """Force an alert for testing purposes"""
        print("Forcing productivity alert")
        app_name, _ = self.get_active_window_info()
        self._trigger_unproductive_alert()
    
    def get_daily_summary(self, date=None):
        """
        Get a summary of activity for a specific date.
        If date is None, uses today's date.
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        total_time = 0
        productive_time = 0
        unproductive_time = 0
        app_usage = {}
        
        try:
            with open(config.ACTIVITY_LOG_FILE, 'r', newline='') as file:
                reader = csv.reader(file)
                next(reader)  # Skip header
                
                for row in reader:
                    if row[0].startswith(date):
                        app_name = row[1]
                        duration = float(row[3])
                        is_productive = row[4]
                        
                        total_time += duration
                        
                        # Count productive and unproductive time
                        if is_productive == 'True':
                            productive_time += duration
                        elif is_productive == 'False':
                            unproductive_time += duration
                        
                        # Track app usage time
                        if app_name in app_usage:
                            app_usage[app_name] += duration
                        else:
                            app_usage[app_name] = duration
        except Exception as e:
            print(f"Error getting daily summary: {e}")
            return None
        
        # Sort apps by usage time
        sorted_apps = sorted(app_usage.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'date': date,
            'total_time': total_time,
            'productive_time': productive_time,
            'unproductive_time': unproductive_time,
            'productive_percentage': (productive_time / total_time * 100) if total_time > 0 else 0,
            'apps': dict(sorted_apps[:10])  # Top 10 apps
        } 