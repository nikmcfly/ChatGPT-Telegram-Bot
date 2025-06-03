# resume_handler.py
from resume_detector import ResumeDetector
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from md2tgmd.src.md2tgmd import escape
from utils.scripts import GetMesageInfo, Document_extract
from config import Users, get_robot, RESUME_PROMPTS, AI_PHOTOS_URL
import utils.decorators as decorators

resume_detector = ResumeDetector()

async def extract_document_text(document):
    """Extract text from document using existing extraction logic"""
    # This will use the existing Document_extract function
    file_url = await document.get_file()
    file_path = file_url.file_path
    text = await Document_extract(file_path, None, "gpt")
    return text

async def track_resume_analysis(user_id: int, language: str):
    """Track resume analysis event"""
    from analytics import analytics
    await analytics.track_resume_analysis(user_id, language)

async def track_user_start(user_id: int, language: str):
    """Track user start event"""
    from analytics import analytics
    await analytics.track_user_start(user_id, language)

async def generate_gpt_response(prompt: str, model: str = "gpt-4o"):
    """Generate GPT response using the existing bot infrastructure"""
    from config import ChatGPTbot
    response = await ChatGPTbot.ask_async(prompt, model=model, pass_history=0)
    return response

def create_ai_photos_button(user_id: int, language: str) -> InlineKeyboardMarkup:
    """Create localized ai photos button"""
    button_texts = {
        'kk': "📸 Кәсіби сурет алу - 990₸",
        'ru': "📸 Получить профессиональное фото - 990₸",
        'en': "📸 Get Professional Photo - 990₸"
    }
    
    utm_url = f"{AI_PHOTOS_URL}?utm_source=resumebek&utm_medium=telegram&user_id={user_id}&lang={language}&promo=STUDENT"
    
    button_text = button_texts.get(language, button_texts['ru'])
    keyboard = [[InlineKeyboardButton(button_text, url=utm_url)]]
    
    return InlineKeyboardMarkup(keyboard)

async def get_resume_analysis(text: str, language: str, convo_id: str) -> str:
    """Get GPT analysis using resume-specific prompt"""
    prompt = RESUME_PROMPTS.get(language, RESUME_PROMPTS['ru'])
    
    # Use existing GPT function but with custom prompt
    robot, role, api_key, api_url = get_robot(convo_id)
    engine = Users.get_config(convo_id, "engine")
    
    response = await robot.ask_async(
        prompt.format(resume_text=text[:3000]),  # Limit text length
        convo_id=convo_id,
        model=engine,
        api_url=api_url,
        api_key=api_key,
        pass_history=0
    )
    
    # Add photo CTA to response
    cta_texts = {
        'kk': "\n\n📸 **Резюмеңізге кәсіби сурет қосыңыз!**\nСтудент пакеті: 990₸ (80% жеңілдік)\n👆 Тапсырыс беру үшін төмендегі батырманы басыңыз",
        'ru': "\n\n📸 **Добавьте профессиональное фото к резюме!**\nСтуденческий пакет: 990₸ (скидка 80%)\n👆 Нажмите кнопку ниже для заказа",
        'en': "\n\n📸 **Add a professional photo to your resume!**\nStudent Package: 990₸ (80% discount)\n👆 Click the button below to order"
    }
    
    cta = cta_texts.get(language, cta_texts['ru'])
    return response + cta

@decorators.GroupAuthorization
@decorators.Authorization
async def handle_document_resumebek(update, context):
    """Modified document handler for resume analysis"""
    _, _, image_url, chatid, _, _, _, message_thread_id, convo_id, file_url, _, voice_text = await GetMesageInfo(update, context)
    
    # Extract text from document (use existing extraction logic)
    if file_url:
        robot, role, api_key, api_url = get_robot(convo_id)
        engine = Users.get_config(convo_id, "engine")
        from aient.src.aient.core.utils import get_engine
        engine_type, _ = get_engine({"base_url": api_url}, endpoint=None, original_model=engine)
        if robot.__class__.__name__ == "chatgpt":
            engine_type = "gpt"
        text = await Document_extract(file_url, image_url, engine_type)
    else:
        await update.message.reply_text("❌ Не удалось прочитать файл. Попробуйте другой формат.")
        return
    
    if not text:
        await update.message.reply_text("❌ Не удалось прочитать файл. Попробуйте другой формат.")
        return
    
    # Check if it's a resume
    if not resume_detector.is_resume(text):
        # Fall back to regular document handling
        robot.add_to_conversation(text, role, convo_id)
        if Users.get_config(convo_id, "FILE_UPLOAD_MESS"):
            from utils.i18n import strings
            from config import get_current_lang
            message = await context.bot.send_message(
                chat_id=chatid, 
                message_thread_id=message_thread_id, 
                text=escape(strings['message_doc'][get_current_lang(convo_id)]), 
                parse_mode='MarkdownV2', 
                disable_web_page_preview=True
            )
            from bot import delete_message
            await delete_message(update, context, [message.message_id])
        return
    
    # Detect language
    detected_lang = resume_detector.detect_language(text)
    
    # Show processing message
    processing_msg = await update.message.reply_text(
        "🔄 Анализирую ваше резюме... Это займет 15-30 секунд."
    )
    
    # Get resume analysis using modified prompt
    analysis = await get_resume_analysis(text, detected_lang, convo_id)
    
    # Create ai photos button
    photo_button = create_ai_photos_button(update.effective_user.id, detected_lang)
    
    # Send analysis with photo CTA
    await processing_msg.edit_text(
        escape(analysis, italic=False),
        parse_mode='MarkdownV2',
        reply_markup=photo_button
    )
    
    # Track analytics
    await track_resume_analysis(update.effective_user.id, detected_lang)
    
    # Schedule follow-up message
    from follow_up import schedule_followup_task
    schedule_followup_task(update.effective_user.id, detected_lang, context, chatid)