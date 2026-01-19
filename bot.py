import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Простая база продуктов
FOOD_DB = {
    'яблоко': {'cal': 52, 'p': 0.3, 'f': 0.2, 'c': 14},
    'банан': {'cal': 89, 'p': 1.1, 'f': 0.3, 'c': 23},
    'пицца': {'cal': 266, 'p': 11, 'f': 10, 'c': 33},
    'бургер': {'cal': 295, 'p': 17, 'f': 14, 'c': 24},
    'салат': {'cal': 15, 'p': 1, 'f': 0.2, 'c': 3},
    'курица': {'cal': 239, 'p': 27, 'f': 14, 'c': 0},
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """
🍎 *Food Calorie Bot* 🍔

Отправь название продукта:
• яблоко
• банан
• пицца
• бургер
• салат
• курица

Или /list - все продукты
"""
    await update.message.reply_text(text, parse_mode="Markdown")

async def list_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    foods = "\n".join([f"• {food}" for food in FOOD_DB.keys()])
    await update.message.reply_text(f"🍽 *Продукты:*\n{foods}", parse_mode="Markdown")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    
    if text in FOOD_DB:
        info = FOOD_DB[text]
        response = f"""
📊 *{text.capitalize()}*
🔥 {info['cal']} ккал
🥚 {info['p']}г белков
🥑 {info['f']}г жиров
🍞 {info['c']}г углеводов
"""
    else:
        response = f"❌ Не знаю '{text}'. Напиши /list"
    
    await update.message.reply_text(response, parse_mode="Markdown")

def main():
    # Токен берется из настроек Render
    TOKEN = os.getenv("TELEGRAM_TOKEN", "")
    
    if not TOKEN:
        print("❌ Нет токена! Добавь TELEGRAM_TOKEN в Render")
        return
    
    # Создаем бота
    app = Application.builder().token(TOKEN).build()
    
    # Команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("list", list_cmd))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # Запуск
    print("🤖 Бот запущен!")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
