# analytics_improved.py
import json
from datetime import datetime, date
import aiofiles
import asyncio
import os
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

class ImprovedResumebekAnalytics:
    def __init__(self):
        self.analytics_dir = "analytics"
        self.analytics_file = "resumebek_analytics.json"
        self.write_lock = asyncio.Lock()
        self._ensure_directory()
    
    def _ensure_directory(self):
        """Create analytics directory if it doesn't exist"""
        if not os.path.exists(self.analytics_dir):
            os.makedirs(self.analytics_dir)
    
    def _get_daily_file_path(self, date_obj: date = None) -> str:
        """Get file path for daily analytics"""
        if date_obj is None:
            date_obj = datetime.now().date()
        
        filename = f"resumebek_analytics_{date_obj.isoformat()}.json"
        return os.path.join(self.analytics_dir, filename)
    
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
        """Log event to file with locking and daily rotation"""
        analytics_path = self._get_daily_file_path()
        
        # Use lock to prevent concurrent writes
        async with self.write_lock:
            try:
                # Append to daily file
                async with aiofiles.open(analytics_path, 'a') as f:
                    await f.write(json.dumps(event) + '\n')
                
                logger.debug(f"Logged event: {event['event']} for user {event.get('user_id', 'unknown')}")
                
            except Exception as e:
                logger.error(f"Failed to log event: {e}")
    
    async def get_daily_stats(self, date_obj: date = None) -> dict:
        """Get daily statistics with improved performance"""
        if date_obj is None:
            date_obj = datetime.now().date()
        
        analytics_path = self._get_daily_file_path(date_obj)
        
        if not os.path.exists(analytics_path):
            return {
                'date': date_obj.isoformat(),
                'total_users': 0,
                'total_analyses': 0,
                'photo_clicks': 0,
                'languages': {},
                'hourly_distribution': {}
            }
        
        events = []
        try:
            async with aiofiles.open(analytics_path, 'r') as f:
                async for line in f:
                    if line.strip():
                        try:
                            events.append(json.loads(line))
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse line: {line}")
        except Exception as e:
            logger.error(f"Failed to read analytics file: {e}")
            return self._empty_stats(date_obj)
        
        # Calculate statistics
        unique_users = set()
        total_analyses = 0
        photo_clicks = 0
        languages = {}
        hourly_distribution = {}
        
        for event in events:
            unique_users.add(event.get('user_id'))
            event_hour = datetime.fromisoformat(event['timestamp']).hour
            
            # Track hourly distribution
            hourly_distribution[event_hour] = hourly_distribution.get(event_hour, 0) + 1
            
            if event['event'] == 'resume_analyzed':
                total_analyses += 1
                lang = event.get('language', 'unknown')
                languages[lang] = languages.get(lang, 0) + 1
            
            elif event['event'] == 'photo_cta_clicked':
                photo_clicks += 1
        
        return {
            'date': date_obj.isoformat(),
            'total_users': len(unique_users),
            'total_analyses': total_analyses,
            'photo_clicks': photo_clicks,
            'conversion_rate': (photo_clicks / total_analyses * 100) if total_analyses > 0 else 0,
            'languages': languages,
            'hourly_distribution': hourly_distribution
        }
    
    def _empty_stats(self, date_obj: date) -> dict:
        """Return empty stats structure"""
        return {
            'date': date_obj.isoformat(),
            'total_users': 0,
            'total_analyses': 0,
            'photo_clicks': 0,
            'conversion_rate': 0,
            'languages': {},
            'hourly_distribution': {}
        }
    
    async def get_weekly_stats(self) -> List[dict]:
        """Get statistics for the past 7 days"""
        stats = []
        today = datetime.now().date()
        
        for i in range(7):
            date_obj = today - timedelta(days=i)
            daily_stats = await self.get_daily_stats(date_obj)
            stats.append(daily_stats)
        
        return stats
    
    async def cleanup_old_files(self, days_to_keep: int = 30):
        """Clean up analytics files older than specified days"""
        try:
            cutoff_date = datetime.now().date() - timedelta(days=days_to_keep)
            
            for filename in os.listdir(self.analytics_dir):
                if filename.startswith("resumebek_analytics_") and filename.endswith(".json"):
                    try:
                        # Extract date from filename
                        date_str = filename.replace("resumebek_analytics_", "").replace(".json", "")
                        file_date = datetime.fromisoformat(date_str).date()
                        
                        if file_date < cutoff_date:
                            file_path = os.path.join(self.analytics_dir, filename)
                            os.remove(file_path)
                            logger.info(f"Removed old analytics file: {filename}")
                    
                    except Exception as e:
                        logger.warning(f"Failed to process file {filename}: {e}")
        
        except Exception as e:
            logger.error(f"Failed to cleanup old files: {e}")
    
    async def export_analytics(self, start_date: date, end_date: date, format: str = "json") -> str:
        """Export analytics for a date range"""
        all_stats = []
        current_date = start_date
        
        while current_date <= end_date:
            stats = await self.get_daily_stats(current_date)
            all_stats.append(stats)
            current_date += timedelta(days=1)
        
        if format == "json":
            return json.dumps(all_stats, indent=2)
        elif format == "csv":
            # Simple CSV export
            csv_lines = ["Date,Total Users,Total Analyses,Photo Clicks,Conversion Rate"]
            for stat in all_stats:
                csv_lines.append(
                    f"{stat['date']},{stat['total_users']},{stat['total_analyses']},"
                    f"{stat['photo_clicks']},{stat['conversion_rate']:.2f}"
                )
            return "\n".join(csv_lines)
        else:
            raise ValueError(f"Unsupported format: {format}")

# Import timedelta for date calculations
from datetime import timedelta

# Global analytics instance
analytics = ImprovedResumebekAnalytics()