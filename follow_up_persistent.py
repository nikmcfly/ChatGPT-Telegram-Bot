# follow_up_persistent.py
import asyncio
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, JobQueue
from md2tgmd.src.md2tgmd import escape
import logging
import json
import os

logger = logging.getLogger(__name__)

FOLLOWUP_JOBS_FILE = "followup_jobs.json"

class PersistentFollowUp:
    def __init__(self):
        self.followup_messages = {
            'kk': """👋 Резюмеңізді жаңарттыңыз ба?

💡 **Кеңестер:**
- LinkedIn, HeadHunter, Naim.kz профильдерін жаңартыңыз
- Жаңа дағдыларыңызды қосуды ұмытпаңыз
- Кәсіби суретті резюмеге қосыңыз

📸 Кәсіби сурет әлі де керек болса - 990₸""",

            'ru': """👋 Обновили свое резюме?

💡 **Рекомендации:**
- Обновите профили в LinkedIn, HeadHunter, Naim.kz
- Не забудьте добавить новые навыки
- Добавьте профессиональное фото

📸 Если все еще нужно профессиональное фото - 990₸""",

            'en': """👋 Updated your resume?

💡 **Recommendations:**
- Update your LinkedIn, HeadHunter, Naim.kz profiles
- Don't forget to add new skills
- Add a professional photo

📸 Still need a professional photo? - 990₸"""
        }
    
    def save_job_data(self, job_data: dict):
        """Save job data to file for persistence"""
        jobs = self.load_job_data()
        job_id = f"{job_data['user_id']}_{job_data['timestamp']}"
        jobs[job_id] = job_data
        
        with open(FOLLOWUP_JOBS_FILE, 'w') as f:
            json.dump(jobs, f, indent=2)
        
        return job_id
    
    def load_job_data(self) -> dict:
        """Load job data from file"""
        if os.path.exists(FOLLOWUP_JOBS_FILE):
            try:
                with open(FOLLOWUP_JOBS_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load job data: {e}")
                return {}
        return {}
    
    def remove_job_data(self, job_id: str):
        """Remove completed job from persistence"""
        jobs = self.load_job_data()
        if job_id in jobs:
            del jobs[job_id]
            with open(FOLLOWUP_JOBS_FILE, 'w') as f:
                json.dump(jobs, f, indent=2)
    
    async def send_followup_callback(self, context: ContextTypes.DEFAULT_TYPE):
        """Callback function for scheduled follow-up"""
        job = context.job
        user_id = job.data['user_id']
        language = job.data['language']
        chat_id = job.data['chat_id']
        job_id = job.data['job_id']
        
        message = self.followup_messages.get(language, self.followup_messages['ru'])
        
        # Create AI photos button
        from resume_handler import create_ai_photos_button
        photo_button = create_ai_photos_button(user_id, language)
        
        try:
            # Send follow-up message with photo button
            await context.bot.send_message(
                chat_id=chat_id,
                text=escape(message, italic=False),
                parse_mode='MarkdownV2',
                reply_markup=photo_button
            )
            
            # Track follow-up sent
            from analytics_improved import analytics
            await analytics.log_event({
                'event': 'followup_sent',
                'user_id': user_id,
                'language': language,
                'timestamp': datetime.now().isoformat()
            })
            
            # Remove job from persistence after successful sending
            self.remove_job_data(job_id)
            
            logger.info(f"Follow-up message sent to user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to send follow-up message to user {user_id}: {e}")
    
    def schedule_followup(self, user_id: int, language: str, context: ContextTypes.DEFAULT_TYPE, 
                         chat_id: int, job_queue: JobQueue):
        """Schedule follow-up message using JobQueue"""
        # Create job data
        job_data = {
            'user_id': user_id,
            'language': language,
            'chat_id': chat_id,
            'timestamp': datetime.now().isoformat(),
            'scheduled_for': (datetime.now() + timedelta(hours=24)).isoformat()
        }
        
        # Save to persistence
        job_id = self.save_job_data(job_data)
        job_data['job_id'] = job_id
        
        # Schedule job for 24 hours later
        job_queue.run_once(
            self.send_followup_callback,
            when=timedelta(hours=24),
            data=job_data,
            name=f"followup_{user_id}_{chat_id}"
        )
        
        logger.info(f"Scheduled follow-up for user {user_id} in 24 hours")
    
    def restore_jobs(self, job_queue: JobQueue):
        """Restore jobs from persistence on bot restart"""
        jobs = self.load_job_data()
        restored_count = 0
        
        for job_id, job_data in jobs.items():
            try:
                scheduled_time = datetime.fromisoformat(job_data['scheduled_for'])
                now = datetime.now()
                
                if scheduled_time > now:
                    # Job is still in the future, reschedule it
                    delay = (scheduled_time - now).total_seconds()
                    job_data['job_id'] = job_id
                    
                    job_queue.run_once(
                        self.send_followup_callback,
                        when=delay,
                        data=job_data,
                        name=f"followup_{job_data['user_id']}_{job_data['chat_id']}"
                    )
                    restored_count += 1
                    logger.info(f"Restored follow-up job for user {job_data['user_id']}")
                else:
                    # Job should have already run, send it immediately
                    job_data['job_id'] = job_id
                    job_queue.run_once(
                        self.send_followup_callback,
                        when=0,  # Run immediately
                        data=job_data,
                        name=f"followup_{job_data['user_id']}_{job_data['chat_id']}"
                    )
                    restored_count += 1
                    logger.info(f"Sending overdue follow-up for user {job_data['user_id']}")
                    
            except Exception as e:
                logger.error(f"Failed to restore job {job_id}: {e}")
                self.remove_job_data(job_id)
        
        logger.info(f"Restored {restored_count} follow-up jobs")
        return restored_count

# Global instance
persistent_followup = PersistentFollowUp()

def schedule_followup_task_persistent(user_id: int, language: str, context: ContextTypes.DEFAULT_TYPE, 
                                    chat_id: int):
    """Schedule follow-up message with persistence"""
    if hasattr(context, 'job_queue') and context.job_queue:
        persistent_followup.schedule_followup(user_id, language, context, chat_id, context.job_queue)
    else:
        logger.error("JobQueue not available in context")