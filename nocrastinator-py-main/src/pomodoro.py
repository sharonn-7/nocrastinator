"""
Pomodoro timer module for productivity tracking.
"""

import time
import threading
from datetime import datetime, timedelta
from plyer import notification
import config

class PomodoroTimer:
    """
    Implements a Pomodoro timer with work sessions and breaks.
    Supports pausing, resuming, and notifications.
    """
    
    def __init__(self):
        self.work_duration = config.POMODORO_WORK_DURATION * 60  # Convert to seconds
        self.short_break_duration = config.POMODORO_SHORT_BREAK_DURATION * 60
        self.long_break_duration = config.POMODORO_LONG_BREAK_DURATION * 60
        self.cycles_before_long_break = config.POMODORO_CYCLES_BEFORE_LONG_BREAK
        
        self.current_cycle = 0
        self.time_remaining = self.work_duration
        self.current_phase = "Ready"
        self.is_running = False
        self.is_paused = False
        self.timer_thread = None
        
        # Callback functions
        self.on_tick = None  # Called every second with time update
        self.on_phase_change = None  # Called when phase changes (work → break)
        self.on_complete = None  # Called when a full pomodoro cycle completes
        
        print("Pomodoro timer initialized")
    
    def start(self):
        """Start the Pomodoro timer"""
        if self.is_running:
            print("Timer already running")
            return
        
        self.is_running = True
        self.is_paused = False
        self.current_phase = "Work"
        self.time_remaining = self.work_duration
        
        # Start timer in a separate thread
        self.timer_thread = threading.Thread(target=self._timer_loop)
        self.timer_thread.daemon = True
        self.timer_thread.start()
        
        print("Pomodoro timer started")
    
    def pause(self):
        """Pause the timer"""
        if self.is_running and not self.is_paused:
            self.is_paused = True
            print("Pomodoro timer paused")
    
    def resume(self):
        """Resume the timer"""
        if self.is_running and self.is_paused:
            self.is_paused = False
            print("Pomodoro timer resumed")
    
    def stop(self):
        """Stop the timer"""
        self.is_running = False
        if self.timer_thread:
            self.timer_thread.join(timeout=1)
        
        self.current_cycle = 0
        self.time_remaining = self.work_duration
        self.current_phase = "Ready"
        
        print("Pomodoro timer stopped")
    
    def _timer_loop(self):
        """Main timer loop"""
        while self.is_running:
            if not self.is_paused:
                # Update time remaining
                if self.time_remaining > 0:
                    self.time_remaining -= 1
                
                # Call the tick callback
                if self.on_tick:
                    self.on_tick()
                
                # Check if phase completed
                if self.time_remaining <= 0:
                    self._handle_phase_complete()
            
            time.sleep(1)
    
    def _handle_phase_complete(self):
        """Handle completion of a Pomodoro phase"""
        # Determine the next phase
        if self.current_phase == "Work":
            self.current_cycle += 1
            
            # Decide if we need a long break or short break
            if self.current_cycle % self.cycles_before_long_break == 0:
                self.current_phase = "Long Break"
                self.time_remaining = self.long_break_duration
                self._notify("Time for a long break!", "Take a longer break to recharge.")
            else:
                self.current_phase = "Short Break"
                self.time_remaining = self.short_break_duration
                self._notify("Time for a short break!", "Take a quick break to refresh.")
        
        elif self.current_phase in ["Short Break", "Long Break"]:
            self.current_phase = "Work"
            self.time_remaining = self.work_duration
            self._notify("Break over!", "Time to get back to work.")
        
        # Call phase change callback
        if self.on_phase_change:
            self.on_phase_change(self.current_phase)
        
        # Call complete callback if we finished a full cycle
        if self.current_phase == "Work" and self.on_complete:
            self.on_complete(self.current_cycle)
    
    def _notify(self, title, message):
        """Send a notification about Pomodoro phase change"""
        notification.notify(
            title=title,
            message=message,
            timeout=10
        )
        print(f"Notification: {title} - {message}")
    
    def get_time_remaining_str(self):
        """Get the remaining time as a formatted string (MM:SS)"""
        minutes = self.time_remaining // 60
        seconds = self.time_remaining % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    def get_progress(self):
        """Get the progress as a percentage (0-100)"""
        if self.current_phase == "Work":
            total_time = self.work_duration
        elif self.current_phase == "Short Break":
            total_time = self.short_break_duration
        elif self.current_phase == "Long Break":
            total_time = self.long_break_duration
        else:
            return 0
        
        time_elapsed = total_time - self.time_remaining
        return (time_elapsed / total_time) * 100 if total_time > 0 else 0 