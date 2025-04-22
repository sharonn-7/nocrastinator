"""
Main application for the Productivity Tracker.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os
import json
import sys
import time
from datetime import datetime, timedelta

# Import our modules
from activity_tracker import ActivityTracker
from focus_score import FocusScore
from pomodoro import PomodoroTimer
import config

class ProductivityTrackerApp:
    """Main application class for the Productivity Tracker."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Productivity Tracker")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # Set up logging to file
        self.setup_logging()
        
        # Create data directory if it doesn't exist
        os.makedirs(config.DATA_DIRECTORY, exist_ok=True)
        
        # Initialize components
        self.activity_tracker = ActivityTracker()
        self.focus_score = FocusScore()
        self.pomodoro = PomodoroTimer()
        
        # Set callbacks
        self.pomodoro.on_tick = self.update_pomodoro_display
        self.pomodoro.on_phase_change = self.handle_phase_change
        self.activity_tracker.on_unproductive_alert = self.handle_unproductive_alert
        
        # Set up UI
        self.setup_ui()
        
        # Start activity tracking
        self.start_tracking()
        
        # Update UI periodically
        self.update_ui()
        
        print("Application initialized")
    
    def setup_logging(self):
        """Set up logging to a file for debugging"""
        try:
            log_file = os.path.join(config.DATA_DIRECTORY, "productivity_tracker.log")
            sys.stdout = open(log_file, "a")
            print(f"\n--- Log started at {datetime.now()} ---")
        except Exception as e:
            print(f"Error setting up logging: {e}")
    
    def setup_ui(self):
        """Set up the main UI"""
        # Style configuration
        self.style = ttk.Style()
        self.style.configure("TNotebook", background="#f0f0f0")
        self.style.configure("Alert.TLabel", foreground="red", font=("Arial", 12, "bold"))
        self.style.configure("Header.TLabel", font=("Arial", 16, "bold"))
        self.style.configure("Subheader.TLabel", font=("Arial", 12, "bold"))
        self.style.configure("Timer.TLabel", font=("Arial", 36, "bold"))
        self.style.configure("Phase.TLabel", font=("Arial", 14))
        self.style.configure("Score.TLabel", font=("Arial", 24, "bold"))
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Create main dashboard tab
        self.create_dashboard_tab()
        
        # Create analysis tab
        self.create_analysis_tab()
        
        # Create settings tab
        self.create_settings_tab()
        
        # Bind tab change event
        self.notebook.bind("<<NotebookTabChanged>>", self.handle_tab_change)
    
    def create_dashboard_tab(self):
        """Create the main dashboard tab"""
        dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(dashboard_frame, text="Dashboard")
        
        # Top section - Focus score and current activity
        top_frame = ttk.Frame(dashboard_frame)
        top_frame.pack(fill="x", pady=10)
        
        # Focus score display
        score_frame = ttk.LabelFrame(top_frame, text="Today's Focus Score")
        score_frame.pack(side="left", padx=10, fill="x", expand=True)
        
        self.score_label = ttk.Label(score_frame, text="0", style="Score.TLabel")
        self.score_label.pack(pady=5)
        
        self.streak_label = ttk.Label(score_frame, text="Current streak: 0 days")
        self.streak_label.pack(pady=5)
        
        # Current activity display
        activity_frame = ttk.LabelFrame(top_frame, text="Current Activity")
        activity_frame.pack(side="left", padx=10, fill="x", expand=True)
        
        self.activity_label = ttk.Label(activity_frame, text="None", style="Subheader.TLabel")
        self.activity_label.pack(pady=5)
        
        self.activity_type_label = ttk.Label(activity_frame, text="")
        self.activity_type_label.pack(pady=5)
        
        # Middle section - Pomodoro timer
        pomodoro_frame = ttk.LabelFrame(dashboard_frame, text="Pomodoro Timer")
        pomodoro_frame.pack(fill="x", pady=10, padx=10)
        
        # Timer display
        timer_display_frame = ttk.Frame(pomodoro_frame)
        timer_display_frame.pack(pady=10)
        
        self.timer_label = ttk.Label(timer_display_frame, text=f"{config.POMODORO_WORK_DURATION}:00", style="Timer.TLabel")
        self.timer_label.pack()
        
        self.phase_label = ttk.Label(timer_display_frame, text="Ready", style="Phase.TLabel")
        self.phase_label.pack(pady=5)
        
        # Progress bar
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            pomodoro_frame, 
            orient="horizontal", 
            length=400, 
            mode="determinate",
            variable=self.progress_var
        )
        self.progress_bar.pack(pady=10, padx=20, fill="x")
        
        # Buttons frame
        pomodoro_buttons_frame = ttk.Frame(pomodoro_frame)
        pomodoro_buttons_frame.pack(pady=10)
        
        self.start_button = ttk.Button(
            pomodoro_buttons_frame, 
            text="Start", 
            command=self.toggle_pomodoro,
            width=15
        )
        self.start_button.pack(side="left", padx=5)
        
        self.pause_button = ttk.Button(
            pomodoro_buttons_frame, 
            text="Pause", 
            command=self.pause_resume_pomodoro,
            width=15,
            state="disabled"
        )
        self.pause_button.pack(side="left", padx=5)
        
        self.reset_button = ttk.Button(
            pomodoro_buttons_frame, 
            text="Reset", 
            command=self.reset_pomodoro,
            width=15,
            state="disabled"
        )
        self.reset_button.pack(side="left", padx=5)
        
        # Bottom section - Alerts and productivity tips
        bottom_frame = ttk.Frame(dashboard_frame)
        bottom_frame.pack(fill="both", expand=True, pady=10)
        
        # Alerts frame
        self.alerts_frame = ttk.LabelFrame(bottom_frame, text="Productivity Alerts")
        self.alerts_frame.pack(side="left", padx=10, fill="both", expand=True)
        
        self.alert_label = ttk.Label(
            self.alerts_frame, 
            text="No alerts", 
            wraplength=300
        )
        self.alert_label.pack(pady=10)
        
        # Test button for alerts (hidden in production)
        self.test_alert_button = ttk.Button(
            self.alerts_frame,
            text="Test Alert",
            command=self.activity_tracker.force_alert
        )
        self.test_alert_button.pack(pady=5)
        
        # Tips frame
        tips_frame = ttk.LabelFrame(bottom_frame, text="Productivity Tips")
        tips_frame.pack(side="left", padx=10, fill="both", expand=True)
        
        self.tip_label = ttk.Label(
            tips_frame, 
            text="Start the Pomodoro timer to boost your productivity!",
            wraplength=300
        )
        self.tip_label.pack(pady=10)
    
    def create_analysis_tab(self):
        """Create the analysis tab"""
        analysis_frame = ttk.Frame(self.notebook)
        self.notebook.add(analysis_frame, text="Analysis")
        
        # Weekly overview section (using text instead of matplotlib)
        overview_frame = ttk.LabelFrame(analysis_frame, text="Weekly Overview")
        overview_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Text widget for data display
        self.weekly_data_text = tk.Text(overview_frame, height=12, wrap="none")
        self.weekly_data_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Add scrollbars
        x_scrollbar = ttk.Scrollbar(overview_frame, orient="horizontal", command=self.weekly_data_text.xview)
        x_scrollbar.pack(side="bottom", fill="x")
        y_scrollbar = ttk.Scrollbar(overview_frame, orient="vertical", command=self.weekly_data_text.yview)
        y_scrollbar.pack(side="right", fill="y")
        
        self.weekly_data_text.configure(xscrollcommand=x_scrollbar.set, yscrollcommand=y_scrollbar.set)
        
        # Bottom section - Stats and suggestions
        bottom_frame = ttk.Frame(analysis_frame)
        bottom_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Stats frame
        stats_frame = ttk.LabelFrame(bottom_frame, text="Statistics")
        stats_frame.pack(side="left", fill="both", expand=True, padx=5)
        
        # Most used apps
        ttk.Label(stats_frame, text="Most Used Apps:", style="Subheader.TLabel").pack(anchor="w", padx=10, pady=5)
        
        self.apps_frame = ttk.Frame(stats_frame)
        self.apps_frame.pack(fill="both", expand=True, padx=10)
        
        # Create labels for top 5 apps
        self.app_labels = []
        for i in range(5):
            label = ttk.Label(self.apps_frame, text=f"{i+1}. No data")
            label.pack(anchor="w", pady=2)
            self.app_labels.append(label)
        
        # Productivity stats
        ttk.Label(stats_frame, text="Productivity Stats:", style="Subheader.TLabel").pack(anchor="w", padx=10, pady=5)
        
        self.stats_text = tk.Text(stats_frame, height=8, width=30, wrap="word", state="disabled")
        self.stats_text.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Suggestions frame
        suggestions_frame = ttk.LabelFrame(bottom_frame, text="Improvement Suggestions")
        suggestions_frame.pack(side="left", fill="both", expand=True, padx=5)
        
        self.suggestions_text = tk.Text(suggestions_frame, height=15, width=40, wrap="word", state="disabled")
        self.suggestions_text.pack(fill="both", expand=True, padx=10, pady=10)
    
    def create_settings_tab(self):
        """Create the settings tab"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="Settings")
        
        # App categorization
        categorization_frame = ttk.LabelFrame(settings_frame, text="App Categorization")
        categorization_frame.pack(fill="x", padx=10, pady=10)
        
        # Display current productive apps
        ttk.Label(categorization_frame, text="Productive Apps:", style="Subheader.TLabel").pack(anchor="w", padx=10, pady=5)
        
        productive_text = ", ".join([app for app in config.PRODUCTIVE_APPS[:10]])
        ttk.Label(categorization_frame, text=productive_text + "...").pack(anchor="w", padx=10)
        
        # Display current unproductive apps
        ttk.Label(categorization_frame, text="Unproductive Apps:", style="Subheader.TLabel").pack(anchor="w", padx=10, pady=5)
        
        unproductive_text = ", ".join([app for app in config.UNPRODUCTIVE_APPS[:10]])
        ttk.Label(categorization_frame, text=unproductive_text + "...").pack(anchor="w", padx=10)
        
        # Note about editing configuration
        note_text = "To change app categorization or other settings, edit the config.py file."
        ttk.Label(categorization_frame, text=note_text).pack(anchor="w", padx=10, pady=10)
        
        # Pomodoro settings
        pomodoro_frame = ttk.LabelFrame(settings_frame, text="Pomodoro Timer Settings")
        pomodoro_frame.pack(fill="x", padx=10, pady=10)
        
        settings_text = f"""
        Work Duration: {config.POMODORO_WORK_DURATION} minutes
        Short Break: {config.POMODORO_SHORT_BREAK_DURATION} minutes
        Long Break: {config.POMODORO_LONG_BREAK_DURATION} minutes
        Cycles Before Long Break: {config.POMODORO_CYCLES_BEFORE_LONG_BREAK}
        """
        
        ttk.Label(pomodoro_frame, text=settings_text).pack(anchor="w", padx=10, pady=10)
        
        # Data management
        data_frame = ttk.LabelFrame(settings_frame, text="Data Management")
        data_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(data_frame, text=f"Data Directory: {os.path.abspath(config.DATA_DIRECTORY)}").pack(anchor="w", padx=10, pady=5)
        
        # Add a button to reset the application data
        reset_button = ttk.Button(
            data_frame,
            text="Reset Application Data",
            command=self.confirm_reset_data
        )
        reset_button.pack(anchor="w", padx=10, pady=10)
    
    def start_tracking(self):
        """Start the activity tracking"""
        self.activity_tracker.start_tracking()
    
    def toggle_pomodoro(self):
        """Toggle the Pomodoro timer on/off"""
        if not self.pomodoro.is_running:
            self.pomodoro.start()
            self.start_button.configure(text="Stop")
            self.pause_button.configure(state="normal")
            self.reset_button.configure(state="normal")
        else:
            self.pomodoro.stop()
            self.start_button.configure(text="Start")
            self.pause_button.configure(text="Pause", state="disabled")
            self.reset_button.configure(state="disabled")
            self.timer_label.configure(text=f"{config.POMODORO_WORK_DURATION:02d}:00")
            self.phase_label.configure(text="Ready")
            self.progress_var.set(0)
    
    def pause_resume_pomodoro(self):
        """Pause or resume the Pomodoro timer"""
        if self.pomodoro.is_running:
            if self.pomodoro.is_paused:
                self.pomodoro.resume()
                self.pause_button.configure(text="Pause")
            else:
                self.pomodoro.pause()
                self.pause_button.configure(text="Resume")
    
    def reset_pomodoro(self):
        """Reset the Pomodoro timer"""
        self.pomodoro.stop()
        self.pomodoro.start()
        self.pause_button.configure(text="Pause")
    
    def update_pomodoro_display(self):
        """Update the Pomodoro timer display"""
        self.timer_label.configure(text=self.pomodoro.get_time_remaining_str())
        self.phase_label.configure(text=self.pomodoro.current_phase)
        self.progress_var.set(self.pomodoro.get_progress())
    
    def handle_phase_change(self, phase):
        """Handle Pomodoro phase changes"""
        if phase == "Work":
            self.tip_label.configure(text="Focus on your task. Avoid distractions.")
        elif phase == "Short Break":
            self.tip_label.configure(text="Take a short break. Stand up and stretch.")
        elif phase == "Long Break":
            self.tip_label.configure(text="Take a longer break. Rest your eyes and mind.")
    
    def handle_unproductive_alert(self, app_name):
        """Handle alerts for unproductive app usage"""
        alert_text = f"⚠️ Productivity Alert: You've been unproductive for over {config.UNPRODUCTIVE_TIME_THRESHOLD//60} minute(s).\nConsider switching to a more productive task."
        self.alert_label.configure(text=alert_text, style="Alert.TLabel")
        
        # Get the current app for more context
        current_app, _ = self.activity_tracker.get_active_window_info()
        
        # Update the tip label with advice
        self.tip_label.configure(
            text=f"Try switching to a productive app instead of using unproductive apps like {current_app}."
        )
        
        # Schedule the alert to disappear after 30 seconds
        self.root.after(30000, self.clear_alert)
    
    def clear_alert(self):
        """Clear the productivity alert"""
        self.alert_label.configure(text="No alerts", style="TLabel")
        
        # Reset the tip label
        self.tip_label.configure(
            text="Start the Pomodoro timer to boost your productivity!"
        )
    
    def handle_tab_change(self, event):
        """Handle notebook tab changes"""
        selected_tab = self.notebook.index(self.notebook.select())
        
        # If analysis tab is selected, refresh the analysis
        if selected_tab == 1:  # Analysis tab
            self.update_analysis_tab()
    
    def update_analysis_tab(self):
        """Update the analysis tab with current data"""
        # Get weekly analysis data
        analysis = self.focus_score.get_weekly_analysis()
        
        # Update the weekly data text display
        self.weekly_data_text.config(state="normal")
        self.weekly_data_text.delete(1.0, tk.END)
        
        # Add header
        header = f"{'Date':^10} | {'Focus Score':^12} | {'Productive Hours':^18} | {'Unproductive Hours':^20}\n"
        separator = "-" * 70 + "\n"
        
        self.weekly_data_text.insert(tk.END, header)
        self.weekly_data_text.insert(tk.END, separator)
        
        # Add data for each day
        dates = analysis['dates']
        scores = analysis['scores']
        productive_hours = analysis['productive_times']
        unproductive_hours = analysis['unproductive_times']
        
        for i in range(len(dates)):
            date_str = dates[i]
            date_display = f"{date_str[-2:]}/{date_str[5:7]}"  # Format as DD/MM
            score = scores[i]
            prod_hours = productive_hours[i]
            unprod_hours = unproductive_hours[i]
            
            row = f"{date_display:^10} | {score:^12.1f} | {prod_hours:^18.2f} | {unprod_hours:^20.2f}\n"
            self.weekly_data_text.insert(tk.END, row)
        
        # Add trend summary
        if len(scores) >= 3:
            trend = "⬆️ Improving" if scores[-1] > scores[0] else "⬇️ Declining" if scores[-1] < scores[0] else "➡️ Stable"
            self.weekly_data_text.insert(tk.END, f"\nFocus Score Trend: {trend}\n")
        
        # Add total summary
        total_productive = sum(productive_hours)
        total_unproductive = sum(unproductive_hours)
        avg_score = sum(scores) / len(scores) if scores else 0
        
        summary = f"\nWeekly Summary:\n"
        summary += f"Total Productive Time: {total_productive:.2f} hours\n"
        summary += f"Total Unproductive Time: {total_unproductive:.2f} hours\n"
        summary += f"Average Focus Score: {avg_score:.1f}\n"
        
        self.weekly_data_text.insert(tk.END, summary)
        self.weekly_data_text.config(state="disabled")
        
        # Update most used apps
        # Get today's summary
        summary = self.activity_tracker.get_daily_summary()
        
        if summary and 'apps' in summary:
            apps = summary['apps']
            sorted_apps = sorted(apps.items(), key=lambda x: x[1], reverse=True)
            
            for i, label in enumerate(self.app_labels):
                if i < len(sorted_apps):
                    app_name, duration = sorted_apps[i]
                    hours = duration / 3600
                    minutes = (duration % 3600) / 60
                    
                    if hours >= 1:
                        time_str = f"{hours:.1f}h"
                    else:
                        time_str = f"{minutes:.0f}m"
                    
                    productive = self.activity_tracker.is_productive(app_name, "")
                    if productive is True:
                        prod_str = "(Productive)"
                        label.configure(foreground="green")
                    elif productive is False:
                        prod_str = "(Unproductive)"
                        label.configure(foreground="red")
                    else:
                        prod_str = "(Neutral)"
                        label.configure(foreground="black")
                    
                    label.configure(text=f"{i+1}. {app_name} - {time_str} {prod_str}")
                else:
                    label.configure(text=f"{i+1}. No data")
        
        # Update statistics
        self.update_stats_text(analysis, summary)
        
        # Update suggestions
        self.update_suggestions_text(analysis['suggestions'])
    
    def update_stats_text(self, analysis, summary):
        """Update the statistics text area"""
        stats_text = ""
        
        if summary:
            total_time = summary.get('total_time', 0) / 3600  # Convert to hours
            productive_time = summary.get('productive_time', 0) / 3600
            unproductive_time = summary.get('unproductive_time', 0) / 3600
            productive_pct = summary.get('productive_percentage', 0)
            
            stats_text += f"Today's Stats:\n"
            stats_text += f"- Total tracked: {total_time:.1f} hours\n"
            stats_text += f"- Productive: {productive_time:.1f} hours ({productive_pct:.1f}%)\n"
            stats_text += f"- Unproductive: {unproductive_time:.1f} hours\n\n"
        
        stats_text += f"Weekly Stats:\n"
        stats_text += f"- Average score: {analysis['average_score']:.1f}\n"
        stats_text += f"- Current streak: {analysis['streak']} days\n"
        
        if analysis['most_productive_day']:
            date = analysis['most_productive_day']
            formatted_date = f"{date.split('-')[2]}/{date.split('-')[1]}"
            stats_text += f"- Most productive: {formatted_date}\n"
        
        # Update the text widget
        self.stats_text.configure(state="normal")
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(tk.END, stats_text)
        self.stats_text.configure(state="disabled")
    
    def update_suggestions_text(self, suggestions):
        """Update the suggestions text area"""
        self.suggestions_text.configure(state="normal")
        self.suggestions_text.delete(1.0, tk.END)
        
        if suggestions:
            for i, suggestion in enumerate(suggestions):
                self.suggestions_text.insert(tk.END, f"{i+1}. {suggestion}\n\n")
        else:
            self.suggestions_text.insert(tk.END, "No suggestions available yet. Keep using the app to get personalized recommendations.")
        
        self.suggestions_text.configure(state="disabled")
    
    def confirm_reset_data(self):
        """Confirm and reset application data"""
        result = messagebox.askyesno(
            "Reset Data",
            "Are you sure you want to reset all application data? This action cannot be undone."
        )
        
        if result:
            try:
                # Remove data files
                data_files = [
                    config.ACTIVITY_LOG_FILE,
                    config.FOCUS_SCORE_FILE
                ]
                
                for file in data_files:
                    if os.path.exists(file):
                        os.remove(file)
                
                messagebox.showinfo(
                    "Reset Complete",
                    "Application data has been reset. The application will now restart."
                )
                
                # Restart the application
                self.root.destroy()
                os.execl(sys.executable, sys.executable, *sys.argv)
            except Exception as e:
                messagebox.showerror(
                    "Reset Failed",
                    f"Failed to reset application data: {str(e)}"
                )
    
    def update_ui(self):
        """Update the UI periodically"""
        # Update current activity
        app_name, window_title = self.activity_tracker.get_active_window_info()
        if app_name:
            self.activity_label.configure(text= f"{app_name} - {window_title}")
            is_productive = self.activity_tracker.is_productive(app_name, window_title)
            if is_productive is True:
                self.activity_type_label.configure(text="(Productive)", foreground="green")
            elif is_productive is False:
                self.activity_type_label.configure(text="(Unproductive)", foreground="red")
            else:
                self.activity_type_label.configure(text="(Neutral)", foreground="black")
        else:
            self.activity_label.configure(text="None")
            self.activity_type_label.configure(text="")
        
        # Update focus score
        score = self.focus_score.calculate_daily_score()
        self.score_label.configure(text=f"{score:.1f}")
        
        # Update streak
        streak = self.focus_score.get_streak()
        self.streak_label.configure(text=f"Current streak: {streak} days")
        
        # Schedule the next update
        self.root.after(1000, self.update_ui)

def main():
    """Main entry point for the application"""
    root = tk.Tk()
    app = ProductivityTrackerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main() 