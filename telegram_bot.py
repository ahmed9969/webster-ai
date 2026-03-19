from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler
from assistant import get_answer, get_course_recommendations, detect_language
import os

TOKEN = os.environ.get("WEBSTER_BOT_TOKEN")

MENU, ASKING, RECOMMENDING = range(3)

menu_buttons = [
    ["💬 Ask a Question"],
    ["📚 Course Recommendations"],
    ["🌐 Change Language", "ℹ️ About"]
]

WELCOME = {
    "en": """👋 Welcome to *WebsterBot*!

I'm your AI academic assistant for Webster University Tashkent.

I can help you with:
📖 Course information
🎓 Graduation requirements  
📋 Academic policies
📅 Important dates
🗺️ Course recommendations

Choose an option below or just ask me anything!""",

    "uz": """👋 *WebsterBot*ga xush kelibsiz!

Men Webster University Toshkent uchun AI akademik yordamchiman.

Sizga yordam bera olaman:
📖 Kurslar haqida ma'lumot
🎓 Bitirish talablari
📋 Akademik siyosatlar
📅 Muhim sanalar
🗺️ Kurs tavsiyalari

Quyidagi variantdan birini tanlang yoki savol bering!""",

    "ru": """👋 Добро пожаловать в *WebsterBot*!

Я ваш AI-помощник для Webster University Ташкент.

Я могу помочь вам с:
📖 Информацией о курсах
🎓 Требованиями к выпуску
📋 Академической политикой
📅 Важными датами
🗺️ Рекомендациями по курсам

Выберите опцию ниже или просто задайте вопрос!"""
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "en")
    reply_markup = ReplyKeyboardMarkup(menu_buttons, resize_keyboard=True)
    await update.message.reply_text(
        WELCOME[lang],
        parse_mode="Markdown",
        reply_markup=reply_markup
    )
    return MENU

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    lang = context.user_data.get("lang", "en")

    if "Ask" in text or "Savol" in text or "Вопрос" in text:
        prompts = {
            "en": "What would you like to know about Webster University Tashkent? Ask me anything! 💬",
            "uz": "Webster University Toshkent haqida nima bilmoqchisiz? Istalgan savolni bering! 💬",
            "ru": "Что вы хотите узнать о Webster University Ташкент? Задайте любой вопрос! 💬"
        }
        await update.message.reply_text(prompts[lang])
        return ASKING

    elif "Recommendation" in text or "Tavsiya" in text or "Рекомендац" in text:
        keyboard = [
            [InlineKeyboardButton("BS Computer Science", callback_data="major_CS")],
            [InlineKeyboardButton("BS Business Administration", callback_data="major_BA")],
            [InlineKeyboardButton("BS Management Information Systems", callback_data="major_MIS")],
            [InlineKeyboardButton("BA International Relations", callback_data="major_IR")],
            [InlineKeyboardButton("BA Economics", callback_data="major_ECON")],
            [InlineKeyboardButton("BA Psychology", callback_data="major_PSY")],
            [InlineKeyboardButton("Other", callback_data="major_OTHER")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        prompts = {
            "en": "Select your major to get course recommendations:",
            "uz": "Kurs tavsiyalarini olish uchun mutaxassisligingizni tanlang:",
            "ru": "Выберите вашу специальность для получения рекомендаций по курсам:"
        }
        await update.message.reply_text(prompts[lang], reply_markup=reply_markup)
        return RECOMMENDING

    elif "Language" in text or "Til" in text or "Язык" in text:
        keyboard = [
            [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
            [InlineKeyboardButton("🇺🇿 O'zbek", callback_data="lang_uz")],
            [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Choose your language / Tilni tanlang / Выберите язык:", reply_markup=reply_markup)
        return MENU

    elif "About" in text or "Haqida" in text or "О боте" in text:
        about = {
            "en": """ℹ️ *About WebsterBot*

WebsterBot is an AI-powered academic assistant built specifically for Webster University Tashkent students.

🤖 Powered by Claude AI
📚 Based on official Webster documents
🌐 Supports English, Uzbek and Russian
🎓 Helps with courses, policies and more

Built by a Webster CS student as a research project.""",
            "uz": """ℹ️ *WebsterBot haqida*

WebsterBot — Webster University Toshkent talabalari uchun maxsus yaratilgan AI akademik yordamchi.

🤖 Claude AI bilan ishlaydi
📚 Rasmiy Webster hujjatlariga asoslanadi  
🌐 Ingliz, O'zbek va Rus tillarini qo'llab-quvvatlaydi
🎓 Kurslar, siyosatlar va boshqalar bilan yordam beradi""",
            "ru": """ℹ️ *О WebsterBot*

WebsterBot — AI-помощник, созданный специально для студентов Webster University Ташкент.

🤖 Работает на Claude AI
📚 Основан на официальных документах Webster
🌐 Поддерживает английский, узбекский и русский
🎓 Помогает с курсами, политиками и многим другим"""
        }
        await update.message.reply_text(about[lang], parse_mode="Markdown")
        return MENU

    else:
        # Treat as a direct question
        lang_detected = detect_language(text)
        context.user_data["lang"] = lang_detected
        
        await update.message.reply_text("⏳ Searching Webster documents...")
        answer, sources = get_answer(text, lang_detected)
        
        if sources:
            answer += f"\n\n📄 *Sources:* {', '.join(sources)}"
        
        await update.message.reply_text(answer, parse_mode="Markdown")
        return MENU

async def handle_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = update.message.text
    lang = detect_language(question)
    context.user_data["lang"] = lang
    
    await update.message.reply_text("⏳ Searching Webster documents...")
    
    answer, sources = get_answer(question, lang)
    
    if sources:
        answer += f"\n\n📄 *Sources:* {', '.join(sources)}"
    
    await update.message.reply_text(answer, parse_mode="Markdown")
    
    follow_up = {
        "en": "Do you have another question? 💬",
        "uz": "Yana savolingiz bormi? 💬",
        "ru": "Есть ещё вопросы? 💬"
    }
    await update.message.reply_text(follow_up[lang])
    return ASKING

async def handle_major_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    major_map = {
        "major_CS": "Computer Science",
        "major_BA": "Business Administration",
        "major_MIS": "Management Information Systems",
        "major_IR": "International Relations",
        "major_ECON": "Economics",
        "major_PSY": "Psychology",
        "major_OTHER": "General"
    }
    
    lang_map = {
        "lang_en": "en",
        "lang_uz": "uz",
        "lang_ru": "ru"
    }
    
    data = query.data
    
    if data in lang_map:
        context.user_data["lang"] = lang_map[data]
        lang = lang_map[data]
        confirmed = {
            "en": "✅ Language set to English!",
            "uz": "✅ Til O'zbek tiliga o'rnatildi!",
            "ru": "✅ Язык установлен на русский!"
        }
        await query.message.reply_text(confirmed[lang])
        return MENU
    
    if data in major_map:
        major = major_map[data]
        context.user_data["pending_major"] = major
        lang = context.user_data.get("lang", "en")
        
        prompts = {
            "en": f"Great! You selected *{major}*.\n\nWhat are your interests or career goals? (e.g. AI, web dev, finance, data science)",
            "uz": f"Ajoyib! Siz *{major}* tanladingiz.\n\nQiziqishlaringiz yoki martaba maqsadlaringiz nima?",
            "ru": f"Отлично! Вы выбрали *{major}*.\n\nКаковы ваши интересы или карьерные цели?"
        }
        await query.message.reply_text(prompts[lang], parse_mode="Markdown")
        return RECOMMENDING

async def handle_recommendation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    interests = update.message.text
    major = context.user_data.get("pending_major", "Computer Science")
    lang = context.user_data.get("lang", "en")
    
    await update.message.reply_text("⏳ Generating your personalized recommendations...")
    
    recommendations = get_course_recommendations(major, interests)
    
    await update.message.reply_text(recommendations, parse_mode="Markdown")
    
    reply_markup = ReplyKeyboardMarkup(menu_buttons, resize_keyboard=True)
    back = {
        "en": "Back to main menu:",
        "uz": "Asosiy menyuga qaytish:",
        "ru": "Вернуться в главное меню:"
    }
    await update.message.reply_text(back[lang], reply_markup=reply_markup)
    return MENU

def main():
    app = Application.builder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(filters.TEXT & ~filters.COMMAND, start)
        ],
        states={
            MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, menu),
                CallbackQueryHandler(handle_major_callback)
            ],
            ASKING: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_question),
                CallbackQueryHandler(handle_major_callback)
            ],
            RECOMMENDING: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_recommendation),
                CallbackQueryHandler(handle_major_callback)
            ]
        },
        fallbacks=[CommandHandler("start", start)]
    )
    
    app.add_handler(conv_handler)
    
    print("Webster AI Telegram Bot is running! 🎓")
    app.run_polling()

if __name__ == "__main__":
    main()
