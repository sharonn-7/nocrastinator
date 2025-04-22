"""
Focus score module for calculating productivity metrics.
"""

import os
import csv
import json
from datetime import datetime, timedelta
import config

class FocusScore:
    """
    Calculates productivity scores based on app usage data.
    Tracks daily scores and provides analysis over time.
    """
    
    def __init__(self):
        self.scores_file = config.FOCUS_SCORE_FILE
        
        # Create data directory if it doesn't exist
        os.makedirs(config.DATA_DIRECTORY, exist_ok=True)
        
        # Load existing scores or create new ones
        self.scores = self._load_scores()
        
        print("Focus score calculator initialized")
    
    def _load_scores(self):
        """Load focus scores from file"""
        if os.path.exists(self.scores_file):
            try:
                with open(self.scores_file, 'r') as file:
                    return json.load(file)
            except Exception as e:
                print(f"Error loading scores: {e}")
                return {}
        else:
            return {}
    
    def _save_scores(self):
        """Save focus scores to file"""
        try:
            with open(self.scores_file, 'w') as file:
                json.dump(self.scores, file, indent=2)
        except Exception as e:
            print(f"Error saving scores: {e}")
    
    def calculate_daily_score(self, date=None):
        """
        Calculate focus score for a given date.
        Score is based on productive vs. unproductive time.
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        # If we already calculated today's score, return it
        if date in self.scores:
            return self.scores[date]['score']
        
        # Calculate from activity log
        total_time = 0
        productive_time = 0
        unproductive_time = 0
        neutral_time = 0
        
        try:
            # Read activity data
            with open(config.ACTIVITY_LOG_FILE, 'r', newline='') as file:
                reader = csv.reader(file)
                next(reader)  # Skip header
                
                for row in reader:
                    if row[0].startswith(date):
                        duration = float(row[3])
                        is_productive = row[4]
                        
                        total_time += duration
                        
                        if is_productive == 'True':
                            productive_time += duration
                        elif is_productive == 'False':
                            unproductive_time += duration
                        else:
                            neutral_time += duration
        except Exception as e:
            print(f"Error reading activity data: {e}")
            return 0
        
        # Calculate score (0-100)
        if total_time < 60:  # Less than a minute of data
            score = 0
        else:
            # Weighted score - productive time increases score, unproductive decreases it
            weighted_productive = productive_time * config.PRODUCTIVE_TIME_WEIGHT
            weighted_unproductive = unproductive_time * config.UNPRODUCTIVE_TIME_WEIGHT
            
            if weighted_productive + weighted_unproductive > 0:
                score = (weighted_productive / (weighted_productive + weighted_unproductive)) * 100
            else:
                score = 50  # Neutral score if no data
            
            # Cap score between 0-100
            score = max(0, min(100, score))
        
        # Save score with details
        self.scores[date] = {
            'score': score,
            'total_time': total_time,
            'productive_time': productive_time,
            'unproductive_time': unproductive_time,
            'neutral_time': neutral_time
        }
        
        self._save_scores()
        return score
    
    def get_streak(self):
        """Calculate the current productivity streak"""
        min_score = 50  # Minimum score to count as productive day
        
        # Sort dates in reverse order (newest first)
        dates = sorted(self.scores.keys(), reverse=True)
        
        if not dates:
            return 0
        
        streak = 0
        today = datetime.now().date()
        
        for i, date_str in enumerate(dates):
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            score = self.scores[date_str]['score']
            
            # Check if this date is part of continuous streak
            expected_date = today - timedelta(days=i)
            
            if date == expected_date and score >= min_score:
                streak += 1
            else:
                break
        
        return streak
    
    def get_weekly_analysis(self):
        """Get analysis for the past week"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=6)  # 7 days including today
        
        dates = []
        scores = []
        productive_times = []
        unproductive_times = []
        
        # Get data for each day in the week
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            dates.append(date_str)
            
            # Calculate score if not already calculated
            if date_str not in self.scores:
                self.calculate_daily_score(date_str)
            
            # Add data if available
            if date_str in self.scores:
                data = self.scores[date_str]
                scores.append(data['score'])
                productive_times.append(data['productive_time'] / 3600)  # Convert to hours
                unproductive_times.append(data['unproductive_time'] / 3600)  # Convert to hours
            else:
                scores.append(0)
                productive_times.append(0)
                unproductive_times.append(0)
            
            current_date += timedelta(days=1)
        
        # Most productive day
        if scores:
            max_score_index = scores.index(max(scores))
            most_productive_day = dates[max_score_index]
        else:
            most_productive_day = None
        
        # Calculate improvement suggestions
        suggestions = self._generate_suggestions()
        
        return {
            'dates': dates,
            'scores': scores,
            'productive_times': productive_times,
            'unproductive_times': unproductive_times,
            'streak': self.get_streak(),
            'most_productive_day': most_productive_day,
            'average_score': sum(scores) / len(scores) if scores else 0,
            'suggestions': suggestions
        }
    
    def _generate_suggestions(self):
        """Generate improvement suggestions based on data"""
        suggestions = []
        
        # Get recent days
        now = datetime.now().date()
        recent_days = [now - timedelta(days=i) for i in range(7)]
        recent_day_strs = [d.strftime('%Y-%m-%d') for d in recent_days]
        
        # Get data for recent days
        recent_scores = []
        unproductive_apps = {}
        
        for date_str in recent_day_strs:
            if date_str in self.scores:
                recent_scores.append(self.scores[date_str]['score'])
            
            # Get app usage for that day
            try:
                with open(config.ACTIVITY_LOG_FILE, 'r', newline='') as file:
                    reader = csv.reader(file)
                    next(reader)  # Skip header
                    
                    for row in reader:
                        if row[0].startswith(date_str) and row[4] == 'False':
                            app_name = row[1]
                            duration = float(row[3])
                            
                            if app_name in unproductive_apps:
                                unproductive_apps[app_name] += duration
                            else:
                                unproductive_apps[app_name] = duration
            except Exception as e:
                print(f"Error reading app data: {e}")
        
        # Suggestion 1: Productivity trend
        if recent_scores and len(recent_scores) >= 3:
            avg_first_half = sum(recent_scores[:len(recent_scores)//2]) / (len(recent_scores)//2)
            avg_second_half = sum(recent_scores[len(recent_scores)//2:]) / (len(recent_scores) - len(recent_scores)//2)
            
            if avg_second_half > avg_first_half:
                suggestions.append("Your productivity is trending upward. Keep up the good work!")
            elif avg_second_half < avg_first_half:
                suggestions.append("Your productivity has been declining. Try to focus on more productive tasks.")
        
        # Suggestion 2: Most distracting apps
        if unproductive_apps:
            sorted_apps = sorted(unproductive_apps.items(), key=lambda x: x[1], reverse=True)
            top_distraction = sorted_apps[0][0]
            top_distraction_time = sorted_apps[0][1] / 3600  # Convert to hours
            
            if top_distraction_time > 1:
                suggestions.append(f"You spent {top_distraction_time:.1f} hours on {top_distraction}. Consider limiting time on this app.")
        
        # Suggestion 3: General suggestions
        if not recent_scores or sum(recent_scores) / len(recent_scores) < 50:
            suggestions.append("Try using the Pomodoro technique to improve focus and productivity.")
        
        return suggestions 