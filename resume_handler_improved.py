# resume_handler_improved.py
from resume_detector_improved import ImprovedResumeDetector as ResumeDetector
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError, TimedOut, NetworkError
from md2tgmd.src.md2tgmd import escape
from utils.scripts import GetMesageInfo, Document_extract
from config import Users, get_robot, RESUME_PROMPTS, AI_PHOTOS_URL
import utils.decorators as decorators
import logging
import asyncio
from typing import Optional

logger = logging.getLogger(__name__)

resume_detector = ResumeDetector()

# Error messages in multiple languages
ERROR_MESSAGES = {
    'file_read_error': {
        'kk': "❌ Файлды оқу мүмкін болмады. Басқа форматты қолданып көріңіз.",
        'ru': "❌ Не удалось прочитать файл. Попробуйте другой формат.",
        'en': "❌ Failed to read the file. Please try another format."
    },
    'analysis_error': {
        'kk': "😔 Кешіріңіз, резюмені талдау кезінде қате пайда болды. Біраздан кейін қайталап көріңіз.",
        'ru': "😔 Извините, произошла ошибка при анализе резюме. Попробуйте позже.",
        'en': "😔 Sorry, an error occurred while analyzing the resume. Please try again later."
    },
    'network_error': {
        'kk': "🌐 Желі қатесі. Интернет байланысын тексеріп, қайталап көріңіз.",
        'ru': "🌐 Ошибка сети. Проверьте интернет-соединение и попробуйте снова.",
        'en': "🌐 Network error. Please check your connection and try again."
    },
    'timeout_error': {
        'kk': "⏱️ Талдау уақыты өте ұзаққа созылды. Қайталап көріңіз.",
        'ru': "⏱️ Анализ занял слишком много времени. Попробуйте еще раз.",
        'en': "⏱️ Analysis took too long. Please try again."
    },
    'api_error': {
        'kk': "🤖 AI қызметімен байланыс орнату мүмкін болмады. Біраздан кейін қайталап көріңіз.",
        'ru': "🤖 Не удалось связаться с AI сервисом. Попробуйте позже.",
        'en': "🤖 Failed to connect to AI service. Please try later."
    },
    'file_too_large': {
        'kk': "📏 Файл тым үлкен. 10MB-тан кіші файл жүктеңіз.",
        'ru': "📏 Файл слишком большой. Загрузите файл меньше 10MB.",
        'en': "📏 File is too large. Please upload a file smaller than 10MB."
    }
}

async def extract_document_text(document):
    """Extract text from document using existing extraction logic"""
    # This will use the existing Document_extract function
    file_url = await document.get_file()
    file_path = file_url.file_path
    text = await Document_extract(file_path, None, "gpt")
    return text

async def track_resume_analysis(user_id: int, language: str):
    """Track resume analysis event"""
    from analytics_improved import analytics
    await analytics.track_resume_analysis(user_id, language)

async def track_user_start(user_id: int, language: str):
    """Track user start event"""
    from analytics_improved import analytics
    await analytics.track_user_start(user_id, language)

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

async def get_resume_analysis_with_retry(text: str, language: str, convo_id: str, 
                                        max_retries: int = 3) -> Optional[str]:
    """Get GPT analysis with retry logic"""
    prompt = RESUME_PROMPTS.get(language, RESUME_PROMPTS['ru'])
    
    robot, role, api_key, api_url = get_robot(convo_id)
    engine = Users.get_config(convo_id, "engine")
    
    for attempt in range(max_retries):
        try:
            response = await asyncio.wait_for(
                robot.ask_async(
                    prompt.format(resume_text=text[:3000]),  # Limit text length
                    convo_id=convo_id,
                    model=engine,
                    api_url=api_url,
                    api_key=api_key,
                    pass_history=0
                ),
                timeout=60.0  # 60 second timeout
            )
            
            # Add photo CTA to response
            cta_texts = {
                'kk': "\n\n📸 **Резюмеңізге кәсіби сурет қосыңыз!**\nСтудент пакеті: 990₸ (80% жеңілдік)\n👆 Тапсырыс беру үшін төмендегі батырманы басыңыз",
                'ru': "\n\n📸 **Добавьте профессиональное фото к резюме!**\nСтуденческий пакет: 990₸ (скидка 80%)\n👆 Нажмите кнопку ниже для заказа",
                'en': "\n\n📸 **Add a professional photo to your resume!**\nStudent Package: 990₸ (80% discount)\n👆 Click the button below to order"
            }
            
            cta = cta_texts.get(language, cta_texts['ru'])
            return response + cta
            
        except asyncio.TimeoutError:
            logger.warning(f"Timeout on attempt {attempt + 1} for resume analysis")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise
                
        except Exception as e:
            logger.error(f"Error on attempt {attempt + 1} for resume analysis: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise
    
    return None

def get_error_message(error_type: str, language: str) -> str:
    """Get localized error message"""
    return ERROR_MESSAGES.get(error_type, {}).get(language, ERROR_MESSAGES[error_type]['ru'])

@decorators.GroupAuthorization
@decorators.Authorization
async def handle_document_resumebek_improved(update, context):
    """Improved document handler with better error handling"""
    _, _, image_url, chatid, _, _, _, message_thread_id, convo_id, file_url, _, voice_text = await GetMesageInfo(update, context)
    
    # Default language for error messages
    user_language = 'ru'
    
    try:
        # Check file size (Telegram limit is 20MB, but we'll limit to 10MB for processing)
        if update.message.document and update.message.document.file_size > 10 * 1024 * 1024:
            await update.message.reply_text(
                get_error_message('file_too_large', user_language)
            )
            return
        
        # Extract text from document
        if file_url:
            try:
                robot, role, api_key, api_url = get_robot(convo_id)
                engine = Users.get_config(convo_id, "engine")
                from aient.src.aient.core.utils import get_engine
                engine_type, _ = get_engine({"base_url": api_url}, endpoint=None, original_model=engine)
                if robot.__class__.__name__ == "chatgpt":
                    engine_type = "gpt"
                
                text = await asyncio.wait_for(
                    Document_extract(file_url, image_url, engine_type),
                    timeout=30.0  # 30 second timeout for file extraction
                )
                
            except asyncio.TimeoutError:
                await update.message.reply_text(
                    get_error_message('timeout_error', user_language)
                )
                return
                
            except Exception as e:
                logger.error(f"Failed to extract text from document: {e}")
                await update.message.reply_text(
                    get_error_message('file_read_error', user_language)
                )
                return
        else:
            await update.message.reply_text(
                get_error_message('file_read_error', user_language)
            )
            return
        
        if not text or len(text.strip()) < 50:  # Minimum text length check
            await update.message.reply_text(
                get_error_message('file_read_error', user_language)
            )
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
        detected_lang, confidence = resume_detector.detect_language(text)
        user_language = detected_lang  # Update language for error messages
        
        logger.info(f"Resume detected for user {update.effective_user.id}, language: {detected_lang} (confidence: {confidence}%)")
        
        # Show processing message
        processing_messages = {
            'kk': "🔄 Резюмеңізді талдап жатырмын... Бұл 15-30 секунд алады.",
            'ru': "🔄 Анализирую ваше резюме... Это займет 15-30 секунд.",
            'en': "🔄 Analyzing your resume... This will take 15-30 seconds."
        }
        
        processing_msg = await update.message.reply_text(
            processing_messages.get(detected_lang, processing_messages['ru'])
        )
        
        try:
            # Get resume analysis with retry logic
            analysis = await get_resume_analysis_with_retry(text, detected_lang, convo_id)
            
            if not analysis:
                raise Exception("Failed to get analysis after retries")
            
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
            
            # Schedule follow-up message with persistence
            try:
                from follow_up_persistent import schedule_followup_task_persistent
                schedule_followup_task_persistent(update.effective_user.id, detected_lang, context, chatid)
            except Exception as e:
                logger.error(f"Failed to schedule follow-up: {e}")
                # Don't fail the whole process if follow-up scheduling fails
            
        except asyncio.TimeoutError:
            await processing_msg.edit_text(
                get_error_message('timeout_error', user_language)
            )
            logger.error(f"Timeout during resume analysis for user {update.effective_user.id}")
            
        except NetworkError:
            await processing_msg.edit_text(
                get_error_message('network_error', user_language)
            )
            logger.error(f"Network error during resume analysis for user {update.effective_user.id}")
            
        except Exception as e:
            await processing_msg.edit_text(
                get_error_message('api_error', user_language)
            )
            logger.error(f"Failed to analyze resume for user {update.effective_user.id}: {e}")
            
    except TelegramError as e:
        logger.error(f"Telegram error in resume handler: {e}")
        # Can't send error message if Telegram is having issues
        
    except Exception as e:
        logger.error(f"Unexpected error in resume handler: {e}")
        try:
            await update.message.reply_text(
                get_error_message('analysis_error', user_language)
            )
        except:
            pass  # If we can't even send an error message, just log it