# follow_up.py
import asyncio
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from md2tgmd.src.md2tgmd import escape

async def schedule_followup(user_id: int, language: str, context, chat_id: int):
    """Schedule 24h follow-up message"""
    
    followup_messages = {
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
    
    # Schedule for 24 hours later
    await asyncio.sleep(86400)  # 24 hours
    
    message = followup_messages.get(language, followup_messages['ru'])
    
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
        from analytics import analytics
        await analytics.log_event({
            'event': 'followup_sent',
            'user_id': user_id,
            'language': language,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        print(f"Failed to send follow-up message: {e}")

def schedule_followup_task(user_id: int, language: str, context, chat_id: int):
    """Schedule follow-up message as a background task"""
    asyncio.create_task(schedule_followup(user_id, language, context, chat_id))