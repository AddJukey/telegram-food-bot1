import os
import logging
import asyncio
import tempfile
import json
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from io import BytesIO
import base64
# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== НАСТРОЙКИ API ==========
ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY", "pxdm5gsSa9zxNzhvq4oX")
WORKSPACE_NAME = "kalori-lsshy"
WORKFLOW_ID = "detect-count-and-visualize"

# Workflow API endpoint
WORKFLOW_URL = f"https://serverless.roboflow.com/workflow/{WORKFLOW_ID}"


# ========== БАЗА ПРОДУКТОВ ==========
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
    """Распознает еду на фото через Roboflow Workflow API"""
    try:
        # Кодируем фото в base64
        img_base64 = base64.b64encode(photo_bytes).decode('utf-8')
        
        # Формируем запрос к Workflow API
        params = {
            "access_key": ROBOFLOW_API_KEY,
            "workspace": WORKSPACE_NAME
        }
        
        # Тело запроса в формате base64
        payload = {
            "image": {
                "type": "base64",
                "value": img_base64
            }
        }
        
        # Отправляем запрос (синхронно, оборачиваем в thread)
        def run_workflow_request():
            response = requests.post(
                WORKFLOW_URL,
                params=params,
                json=payload,
                timeout=30
            )
            return response
        
        # Запускаем в отдельном потоке
        response = await asyncio.to_thread(run_workflow_request)
        
        if response.status_code == 200:
            result = response.json()
            
            # Workflow возвращает список результатов, берем первый
            if isinstance(result, list) and len(result) > 0:
                result_data = result[0]
            else:
                result_data = result
            
            # Извлекаем предсказания
            predictions = result_data.get('predictions', [])
            visualization = result_data.get('visualization', None)
            
            # Обрабатываем предсказания
            detected_foods = []
            if predictions:
                for pred in predictions:
                    food_name = pred.get('class', '').lower()
                    confidence = pred.get('confidence', 0) * 100  # в процентах
                    
                    # Фильтруем только продукты с достаточной уверенностью
                    if confidence > 40:  # Порог 40%
                        detected_foods.append({
                            "name": food_name,
                            "confidence": round(confidence, 1),
                            "russian_name": FOOD_DATABASE.get(food_name, {}).get("ru", food_name),
                            "raw_prediction": pred
                        })
            
            # Убираем дубликаты (берем продукт с наибольшей уверенностью)
            unique_foods = {}
            for food in detected_foods:
                name = food["name"]
                if name not in unique_foods or food["confidence"] > unique_foods[name]["confidence"]:
                    unique_foods[name] = food
            
            # Возвращаем результат с визуализацией
            return {
                "foods": list(unique_foods.values())[:5],  # Возвращаем топ-5
                "visualization": visualization  # base64 изображение с разметкой
            }
        else:
            logger.error(f"Workflow API ошибка: {response.status_code}, {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Ошибка распознавания: {e}")
        return None

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
🖼 *Визуализация* - покажу разметку на фото

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
        
        result = await detect_food_in_photo(photo_bytes)
        
        if not result or not result.get("foods"):
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
        
        detected_foods = result["foods"]
        visualization = result.get("visualization")
        
        # Формируем текстовый отчет
        await message.edit_text("📊 *Определяю калорийность...*", parse_mode="Markdown")
        
        response_text = "🍽 *Результаты анализа:*\n\n"
        
        # Считаем количество каждого типа еды
        from collections import Counter
        food_counter = Counter()
        for food in detected_foods:
            food_counter[food['name']] += 1
        
        total_calories = 0
        for i, (food_name, count) in enumerate(food_counter.items(), 1):
            # Получаем информацию о продукте
            food_info = FOOD_DATABASE.get(food_name, {"ru": food_name, "calories": 200})
            ru_name = food_info.get("ru", food_name)
            
            # Находим максимальную уверенность для этого типа
            max_conf = max([f['confidence'] for f in detected_foods if f['name'] == food_name])
            
            response_text += f"*{i}. {ru_name.capitalize()}* ({count} шт.)\n"
            response_text += f"   🔍 Уверенность: {max_conf}%\n"
            response_text += f"   🔥 Калории: *{food_info.get('calories', 200)}* ккал/100г\n\n"
            
            total_calories += food_info.get('calories', 200) * count
        
        # Добавляем общий подсчет
        total_items = sum(food_counter.values())
        if total_items > 0:
            response_text += f"📊 *Общая статистика:*\n"
            response_text += f"• Всего объектов: {total_items}\n"
            response_text += f"• Уникальных типов: {len(food_counter)}\n"
            response_text += f"• Примерная калорийность: *{total_calories} ккал*\n\n"
        
        # Добавляем примечания
        response_text += (
            "⚠️ *Важно:*\n"
            "• Данные приблизительные\n"
            "• Указано на 100г продукта\n"
            "• Фактическая калорийность зависит от рецепта\n"
            "• Для точности используйте кухонные весы"
        )
        
        # Если есть визуализация, отправляем фото с результатами
        if visualization:
            try:
                # Извлекаем base64 данные
                if ',' in visualization:
                    img_data = visualization.split(',')[1]
                else:
                    img_data = visualization
                
                # Декодируем base64
                img_bytes = base64.b64decode(img_data)
                
                # Удаляем сообщение "Определяю калорийность"
                await message.delete()
                
                # Отправляем визуализацию с подписью
                await update.message.reply_photo(
                    photo=BytesIO(img_bytes),
                    caption=response_text,
                    parse_mode="Markdown"
                )
                return
                
            except Exception as e:
                logger.error(f"Ошибка обработки визуализации: {e}")
                # Если не удалось отправить фото, отправляем текст
                await message.edit_text(response_text, parse_mode="Markdown")
        else:
            # Если нет визуализации, отправляем только текст
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
                if food in FOOD_DATABASE:
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
        
    elif text in ['/start', 'старт']:
        await start(update, context)
        
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
    logger.info("🤖 Бот запущен с распознаванием фото через Workflow API!")
    print("=" * 50)
    print("🎯 Бот поддерживает:")
    print("• 📸 Распознавание еды по фото (Workflow API)")
    print("• 🖼 Визуализация результатов (bounding boxes)")
    print("• 📊 Подсчет калорий")
    print("• 🔍 Текстовый поиск")
    print("=" * 50)
    print(f"🌐 Workspace: {WORKSPACE_NAME}")
    print(f"⚙️ Workflow: {WORKFLOW_ID}")
    print("=" * 50)
    
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
    
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
