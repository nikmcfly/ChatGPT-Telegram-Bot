# Resumebek - AI Resume Analysis Bot

This is a customized version of the ChatGPT-Telegram-Bot specifically designed for analyzing and improving resumes for students in Kazakhstan.

## Features

- **Multi-language Support**: Analyzes resumes in Kazakh, Russian, and English
- **Smart Resume Detection**: Automatically detects if uploaded document is a resume
- **Comprehensive Analysis**: Provides strengths, weaknesses, and specific recommendations
- **Professional Photo Integration**: Promotes AI Photos student package (990₸)
- **Analytics Tracking**: Tracks user interactions and resume analyses
- **Follow-up Messages**: Sends helpful reminders 24 hours after analysis

## Installation

1. Clone this repository:
```bash
git clone https://github.com/nikmcfly/ChatGPT-Telegram-Bot.git
cd ChatGPT-Telegram-Bot
git checkout resumebek-customization
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.resumebek .env
# Edit .env file with your actual values:
# - BOT_TOKEN: Your Telegram bot token from @BotFather
# - API: Your OpenAI API key
# - ADMIN_CHAT_ID: Your Telegram ID for receiving analytics
```

4. Run the bot:
```bash
python bot.py
```

## Customization Details

### New Files Added:
- `resume_detector.py` - Detects if document is a resume and its language
- `resume_handler.py` - Handles resume document processing
- `analytics.py` - Tracks user interactions and events
- `follow_up.py` - Manages follow-up messages

### Modified Files:
- `config.py` - Added resume-specific prompts and settings
- `bot.py` - Integrated resume handler and customized start message

### Resume Analysis Format

The bot analyzes resumes and provides feedback in this format:

```
📋 **RESUME ANALYSIS**

✅ **STRENGTHS:**
- [3-5 specific strengths]

🔧 **AREAS FOR IMPROVEMENT:**
- [3-5 specific recommendations]

📝 **TEXT SUGGESTIONS:**
- [Specific text corrections]

📊 **OVERALL SCORE:** X/10

📸 **Add a professional photo to your resume!**
Student Package: 990₸ (80% discount)
👆 Click the button below to order
```

## Analytics

Analytics are stored in `analytics/resumebek_analytics.json` with the following events:
- `user_started` - When user starts the bot
- `resume_analyzed` - When resume is analyzed
- `photo_cta_clicked` - When user clicks photo button
- `followup_sent` - When follow-up message is sent

## Testing

1. Start the bot with `/start` command
2. Upload a resume in PDF or Word format
3. Check that analysis is provided with photo CTA button
4. Verify analytics are being tracked
5. Wait 24 hours to confirm follow-up message

## Deployment

For production deployment:
1. Set `WEB_HOOK` in .env for webhook mode
2. Use a process manager like systemd or supervisor
3. Set up SSL certificate for webhook
4. Monitor analytics regularly

## Support

For issues or questions about this customization:
- Original repo: https://github.com/nikmcfly/ChatGPT-Telegram-Bot
- AI Photos integration: https://aiphotos.kz