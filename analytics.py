# analytics.py
import json
from datetime import datetime
import aiofiles
import os

class ResumebekAnalytics:
    def __init__(self):
        self.analytics_file = "resumebek_analytics.json"
    
    async def track_resume_analysis(self, user_id: int, language: str):
        """Track resume analysis event"""
        event = {
            'event': 'resume_analyzed',
            'user_id': user_id,
            'language': language,
            'timestamp': datetime.now().isoformat()
        }
        await self.log_event(event)
    
    async def track_photo_click(self, user_id: int, language: str):
        """Track ai photos button click"""
        event = {
            'event': 'photo_cta_clicked',
            'user_id': user_id,
            'language': language,
            'timestamp': datetime.now().isoformat()
        }
        await self.log_event(event)
    
    async def track_user_start(self, user_id: int, language: str):
        """Track user start event"""
        event = {
            'event': 'user_started',
            'user_id': user_id,
            'language': language,
            'timestamp': datetime.now().isoformat()
        }
        await self.log_event(event)
    
    async def log_event(self, event: dict):
        """Log event to file"""
        # Create analytics directory if it doesn't exist
        analytics_dir = "analytics"
        if not os.path.exists(analytics_dir):
            os.makedirs(analytics_dir)
        
        analytics_path = os.path.join(analytics_dir, self.analytics_file)
        
        # Use async file operations
        async with aiofiles.open(analytics_path, 'a') as f:
            await f.write(json.dumps(event) + '\n')
    
    async def get_daily_stats(self) -> dict:
        """Get daily statistics"""
        analytics_dir = "analytics"
        analytics_path = os.path.join(analytics_dir, self.analytics_file)
        
        if not os.path.exists(analytics_path):
            return {
                'total_users': 0,
                'total_analyses': 0,
                'photo_clicks': 0,
                'languages': {}
            }
        
        events = []
        async with aiofiles.open(analytics_path, 'r') as f:
            async for line in f:
                if line.strip():
                    events.append(json.loads(line))
        
        # Calculate statistics
        today = datetime.now().date()
        unique_users = set()
        total_analyses = 0
        photo_clicks = 0
        languages = {}
        
        for event in events:
            event_date = datetime.fromisoformat(event['timestamp']).date()
            if event_date == today:
                unique_users.add(event['user_id'])
                
                if event['event'] == 'resume_analyzed':
                    total_analyses += 1
                    lang = event.get('language', 'unknown')
                    languages[lang] = languages.get(lang, 0) + 1
                
                elif event['event'] == 'photo_cta_clicked':
                    photo_clicks += 1
        
        return {
            'date': today.isoformat(),
            'total_users': len(unique_users),
            'total_analyses': total_analyses,
            'photo_clicks': photo_clicks,
            'languages': languages
        }

# Global analytics instance
analytics = ResumebekAnalytics()