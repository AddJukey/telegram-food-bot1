import os
import logging
import requests
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from io import BytesIO
import base64

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== НАСТРОЙКИ API ==========
# Получите ключ на roboflow.com
ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY", "SdDPMkh7re1XETDPXd49")
ROBOFLOW_MODEL = "food-detection-6"
ROBOFLOW_VERSION = "1"

# ========== БАЗА ПРОДУКТОВ ==========
# Расширенная база с переводом и калориями
FOOD_DATABASE = {
    "apple": {"ru": "яблоко", "calories": 52, "protein": 0.3, "fat": 0.2, "carbs": 14},
    "banana": {"ru": "банан", "calories": 89, "protein": 1.1, "fat": 0.3, "carbs": 23},
    "orange": {"ru": "апельсин", "calories": 47, "protein": 0.9, "fat": 0.1, "carbs": 12},
    "pizza": {"ru": "пицца", "calories": 266, "protein": 11, "fat": 10, "carbs": 33},
    "hamburger": {"ru": "гамбургер", "calories": 295, "protein": 17, "fat": 14, "carbs": 24},
    "sandwich": {"ru": "сэндвич", "calories": 250, "protein": 10, "fat": 8, "carbs": 30},
    "salad": {"ru": "салат", "calories": 15, "protein": 1, "fat": 0.2, "carbs": 3},
    "chicken": {"ru": "курица", "calories": 239, "protein": 27, "fat": 14, "carbs": 0},
    "rice": {"ru": "рис", "calories": 130, "protein": 2.7, "fat": 0.3, "carbs": 28},
    "bread": {"ru": "хлеб", "calories": 265, "protein": 9, "fat": 3.2, "carbs": 49},
    "egg": {"ru": "яйцо", "calories": 155, "protein": 13, "fat": 11, "carbs": 1},
    "milk": {"ru": "молоко", "calories": 42, "protein": 3.4, "fat": 1, "carbs": 5},
    "cheese": {"ru": "сыр", "calories": 402, "protein": 25, "fat": 33, "carbs": 1},
    "pasta": {"ru": "паста", "calories": 131, "protein": 5, "fat": 1, "carbs": 25},
    "fish": {"ru": "рыба", "calories": 206, "protein": 22, "fat": 12, "carbs": 0},
    "carrot": {"ru": "морковь", "calories": 41, "protein": 0.9, "fat": 0.2, "carbs": 10},
    "tomato": {"ru": "помидор", "calories": 18, "protein": 0.9, "fat": 0.2, "carbs": 3.9},
    "potato": {"ru": "картофель", "calories": 77, "protein": 2, "fat": 0.1, "carbs": 17},
    "cake": {"ru": "торт", "calories": 350, "protein": 4, "fat": 15, "carbs": 50},
    "ice cream": {"ru": "мороженое", "calories": 207, "protein": 3.5, "fat": 11, "carbs": 24},
    "chocolate": {"ru": "шоколад", "calories": 546, "protein": 4.9, "fat": 31, "carbs": 61},
    "coffee": {"ru": "кофе", "calories": 2, "protein": 0.1, "fat": 0, "carbs": 0},
    "tea": {"ru": "чай", "calories": 1, "protein": 0, "fat": 0, "carbs": 0},
    "soup": {"ru": "суп", "calories": 50, "protein": 3, "fat": 2, "carbs": 6},
    "fries": {"ru": "картофель фри", "calories": 312, "protein": 3.4, "fat": 15, "carbs": 41},
    "steak": {"ru": "стейк", "calories": 271, "protein": 26, "fat": 19, "carbs": 0},
    "pork": {"ru": "свинина", "calories": 242, "protein": 25, "fat": 14, "carbs": 0},
    "beef": {"ru": "говядина", "calories": 250, "protein": 26, "fat": 15, "carbs": 0},
    "shrimp": {"ru": "креветки", "calories": 85, "protein": 18, "fat": 0.9, "carbs": 0.2},
    "sushi": {"ru": "суши", "calories": 150, "protein": 5, "fat": 0.5, "carbs": 30},
    "donut": {"ru": "пончик", "calories": 452, "protein": 5, "fat": 25, "carbs": 51},
    "cookie": {"ru": "печенье", "calories": 502, "protein": 5, "fat": 24, "carbs": 65},
    "pancake": {"ru": "блин", "calories": 227, "protein": 6, "fat": 10, "carbs": 28},
    "waffle": {"ru": "вафля", "calories": 291, "protein": 8, "fat": 14, "carbs": 35},
}

# ========== ФУНКЦИЯ РАСПОЗНАВАНИЯ ЕДЫ ==========
async def detect_food_in_photo(photo_bytes):
    """Распознает еду на фото через Roboflow API"""
    try:
        # Кодируем фото в base64
        img_base64 = base64.b64encode(photo_bytes).decode("utf-8")
        
        # URL API Roboflow
        url = f"https://detect.roboflow.com/{ROBOFLOW_MODEL}/{ROBOFLOW_VERSION}"
        
        # Параметры запроса
        params = {
            "api_key": ROBOFLOW_API_KEY,
            "confidence": 40,  # Порог уверенности (40%)
            "overlap": 30,
            "format": "json"
        }
        
        # Заголовки
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        # Отправляем запрос к Roboflow
        response = requests.post(
            url, 
            params=params, 
            headers=headers, 
            data={"image": img_base64},
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Извлекаем найденные продукты
            detected_foods = []
            if "predictions" in result:
                for pred in result["predictions"]:
                    food_name = pred["class"].lower()
                    confidence = pred["confidence"] * 100  # В процентах
                    
                    # Фильтруем только продукты с достаточной уверенностью
                    if confidence > 40:  # Порог 40%
                        detected_foods.append({
                            "name": food_name,
                            "confidence": round(confidence, 1),
                            "russian_name": FOOD_DATABASE.get(food_name, {}).get("ru", food_name)
                        })
            
            # Убираем дубликаты (берем продукт с наибольшей уверенностью)
            unique_foods = {}
            for food in detected_foods:
                name = food["name"]
                if name not in unique_foods or food["confidence"] > unique_foods[name]["confidence"]:
                    unique_foods[name] = food
            
            return list(unique_foods.values())[:3]  # Возвращаем топ-3
            
        else:
            logger.error(f"Roboflow API error: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Ошибка распознавания: {e}")
        return None

# ========== ПОИСК КАЛОРИЙ ==========
def get_calories_info(food_name):
    """Ищет информацию о калориях для продукта"""
    # Сначала ищем в локальной базе
    if food_name in FOOD_DATABASE:
        return FOOD_DATABASE[food_name]
    
    # Если нет в базе, ищем в Open Food Facts
    try:
        search_url = "https://world.openfoodfacts.org/cgi/search.pl"
        params = {
            'search_terms': food_name,
            'search_simple': 1,
            'json': 1,
            'page_size': 1
        }
        
        response = requests.get(search_url, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('products') and len(data['products']) > 0:
                product = data['products'][0]
                nutriments = product.get('nutriments', {})
                
                return {
                    "ru": food_name,
                    "calories": nutriments.get('energy-kcal_100g', 200),
                    "protein": round(nutriments.get('proteins_100g', 10), 1),
                    "fat": round(nutriments.get('fat_100g', 10), 1),
                    "carbs": round(nutriments.get('carbohydrates_100g', 20), 1),
                    "source": "Open Food Facts"
                }
    except:
        pass
    
    # Если ничего не нашли, возвращаем примерные значения
    return {
        "ru": food_name,
        "calories": 200,
        "protein": 10,
        "fat": 10,
        "carbs": 20,
        "source": "примерные значения"
    }

# ========== ОБРАБОТЧИКИ TELEGRAM ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    welcome_text = """
🍕 *Food Scanner Bot* 🤖

Я умею распознавать еду на фото и определять калорийность!

*Что я могу:*
📸 *Анализ фото* - отправьте фото еды
📊 *Определение калорий* - для 35+ видов еды
🔍 *Текстовый поиск* - отправьте название продукта

*Примеры распознаваемой еды:*
• Фрукты: яблоко, банан, апельсин
• Овощи: морковь, помидор, картофель
• Готовые блюда: пицца, бургер, суши
• Десерты: торт, мороженое, шоколад
• И многое другое!

*Отправьте мне фото еды для анализа!*
"""
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка фото"""
    try:
        # Отправляем сообщение о начале обработки
        message = await update.message.reply_text("🔄 *Анализирую фото...*\n\nПодождите 10-20 секунд...", parse_mode="Markdown")
        
        # Получаем фото (самое большое качество)
        photo_file = await update.message.photo[-1].get_file()
        
        # Скачиваем фото как bytes
        photo_bytes = await photo_file.download_as_bytearray()
        
        # Распознаем еду на фото
        await message.edit_text("🤖 *Распознаю еду на фото...*", parse_mode="Markdown")
        
        detected_foods = await detect_food_in_photo(photo_bytes)
        
        if not detected_foods or len(detected_foods) == 0:
            await message.edit_text(
                "❌ *Не удалось распознать еду*\n\n"
                "*Возможные причины:*\n"
                "• Еда плохо видна на фото\n"
                "• Продукт не входит в базу\n"
                "• Слишком темное/размытое фото\n\n"
                "*Попробуйте:*\n"
                "1. Сделать более четкое фото\n"
                "2. Убедиться, что еда занимает большую часть кадра\n"
                "3. Отправить название продукта текстом",
                parse_mode="Markdown"
            )
            return
        
        # Получаем информацию о калориях
        await message.edit_text("📊 *Определяю калорийность...*", parse_mode="Markdown")
        
        response_text = "🍽 *Результаты анализа:*\n\n"
        
        total_calories = 0
        total_protein = 0
        total_fat = 0
        total_carbs = 0
        
        for i, food in enumerate(detected_foods, 1):
            # Получаем информацию о продукте
            food_info = get_calories_info(food["name"])
            
            response_text += f"*{i}. {food_info['ru'].capitalize()}*\n"
            response_text += f"   🔍 Уверенность: {food['confidence']}%\n"
            response_text += f"   🔥 Калории: *{food_info['calories']}* ккал/100г\n"
            response_text += f"   🥚 Белки: {food_info['protein']}г\n"
            response_text += f"   🥑 Жиры: {food_info['fat']}г\n"
            response_text += f"   🍞 Углеводы: {food_info['carbs']}г\n"
            
            if "source" in food_info:
                source_icon = "🌐" if food_info["source"] == "Open Food Facts" else "📱"
                response_text += f"   {source_icon} Источник: {food_info['source']}\n"
            
            response_text += "\n"
            
            # Суммируем для общего подсчета
            total_calories += food_info['calories']
            total_protein += food_info['protein']
            total_fat += food_info['fat']
            total_carbs += food_info['carbs']
        
        # Добавляем общий подсчет (если распознано несколько продуктов)
        if len(detected_foods) > 1:
            response_text += "📈 *Примерный итог (на 100г каждого продукта):*\n"
            response_text += f"🔥 *{total_calories} ккал*\n"
            response_text += f"🥚 {round(total_protein, 1)}г белков\n"
            response_text += f"🥑 {round(total_fat, 1)}г жиров\n"
            response_text += f"🍞 {round(total_carbs, 1)}г углеводов\n\n"
        
        # Добавляем примечания
        response_text += (
            "⚠️ *Важно:*\n"
            "• Данные приблизительные\n"
            "• Указано на 100г продукта\n"
            "• Фактическая калорийность зависит от рецепта\n"
            "• Для точности используйте кухонные весы\n\n"
            "📝 *Совет:* Для точного подсчета взвесьте продукт и умножьте на коэффициент."
        )
        
        await message.edit_text(response_text, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка обработки фото: {e}")
        await update.message.reply_text(
            "❌ *Произошла ошибка при обработке фото*\n\n"
            "Попробуйте:\n"
            "1. Отправить фото еще раз\n"
            "2. Проверить интернет-соединение\n"
            "3. Отправить название продукта текстом",
            parse_mode="Markdown"
        )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений"""
    text = update.message.text.lower().strip()
    
    if text in ['/list', 'список', 'продукты']:
        # Показываем список продуктов
        categories = {
            "🍎 Фрукты": ["apple", "banana", "orange"],
            "🥦 Овощи": ["carrot", "tomato", "potato"],
            "🍕 Готовые блюда": ["pizza", "hamburger", "sandwich", "sushi"],
            "🍗 Мясо и рыба": ["chicken", "fish", "steak", "pork", "beef", "shrimp"],
            "🥛 Молочные продукты": ["milk", "cheese", "egg"],
            "🍞 Основное": ["bread", "rice", "pasta"],
            "🍰 Десерты": ["cake", "ice cream", "chocolate", "donut", "cookie", "pancake", "waffle"],
            "🍵 Напитки": ["coffee", "tea", "soup"]
        }
        
        response = "📋 *Список распознаваемых продуктов:*\n\n"
        for category, foods in categories.items():
            response += f"*{category}:*\n"
            for food in foods:
                ru_name = FOOD_DATABASE[food]["ru"]
                response += f"• {ru_name}\n"
            response += "\n"
        
        response += "Всего: 35+ продуктов\n\n*Отправьте фото или название продукта!*"
        
        await update.message.reply_text(response, parse_mode="Markdown")
        
    elif text in ['/help', 'помощь']:
        await update.message.reply_text(
            "📖 *Помощь*\n\n"
            "• Отправьте *фото еды* для анализа\n"
            "• Отправьте *название продукта* текстом\n"
            "• /list - список всех продуктов\n"
            "• /start - начать заново\n\n"
            "Бот использует AI для распознавания еды! 🤖",
            parse_mode="Markdown"
        )
        
    else:
        # Ищем продукт в базе
        found = False
        for eng_name, food_info in FOOD_DATABASE.items():
            if text in food_info["ru"] or text == eng_name:
                response = f"""
📊 *{food_info['ru'].capitalize()}*

*Пищевая ценность на 100г:*
🔥 Калории: *{food_info['calories']} ккал*
🥚 Белки: {food_info['protein']}г
🥑 Жиры: {food_info['fat']}г
🍞 Углеводы: {food_info['carbs']}г

*Расчет для вашей порции:*
1. Взвесьте продукт в граммах
2. Формула: (вес / 100) × {food_info['calories']}
3. Пример: 250г = {food_info['calories'] * 2.5:.0f} ккал
"""
                await update.message.reply_text(response, parse_mode="Markdown")
                found = True
                break
        
        if not found:
            # Показываем похожие продукты
            similar = []
            for eng_name, food_info in FOOD_DATABASE.items():
                if text in food_info["ru"] or any(word in food_info["ru"] for word in text.split()):
                    similar.append(food_info["ru"])
            
            if similar:
                suggestions = "\n".join([f"• {s}" for s in similar[:5]])
                await update.message.reply_text(
                    f"🤔 *'{text}' не найден*\n\n"
                    f"*Похожие продукты:*\n{suggestions}\n\n"
                    "Используйте /list для полного списка",
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text(
                    f"❌ Продукт '{text}' не найден\n\n"
                    "Попробуйте:\n"
                    "• Отправить фото еды\n"
                    "• Использовать /list\n"
                    "• Проверить написание",
                    parse_mode="Markdown"
                )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Ошибка: {context.error}")
    try:
        await update.message.reply_text(
            "❌ *Произошла ошибка*\n\n"
            "Попробуйте отправить команду /start",
            parse_mode="Markdown"
        )
    except:
        pass

# ========== ЗАПУСК БОТА ==========
def main():
    """Основная функция"""
    TOKEN = os.getenv("TELEGRAM_TOKEN", "")
    
    if not TOKEN:
        logger.error("❌ TELEGRAM_TOKEN не установлен")
        print("❌ Добавьте TELEGRAM_TOKEN в переменные окружения")
        return
    
    if not ROBOFLOW_API_KEY:
        logger.warning("⚠️ ROBOFLOW_API_KEY не установлен. Распознавание фото не будет работать.")
        print("⚠️ Для распознавания фото добавьте ROBOFLOW_API_KEY")
    
    # Создаем приложение
    app = Application.builder().token(TOKEN).build()
    
    # Регистрируем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("list", handle_text))
    app.add_handler(CommandHandler("help", handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_error_handler(error_handler)
    
    # Запускаем бота
    logger.info("🤖 Бот запущен с распознаванием фото!")
    print("=" * 50)
    print("🎯 Бот поддерживает:")
    print("• 📸 Распознавание 35+ видов еды по фото")
    print("• 📊 База калорийности")
    print("• 🔍 Текстовый поиск")
    print("=" * 50)
    
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
