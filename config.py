import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Telegram
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

    # Roboflow
    ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY")
    ROBOFLOW_PROJECT = os.getenv("ROBOFLOW_PROJECT", "food-detection-6")
    ROBOFLOW_VERSION = os.getenv("ROBOFLOW_VERSION", "1")

    # Open Food Facts
    OPEN_FOOD_FACTS_URL = "https://world.openfoodfacts.org/api/v0/product/"

    # Локальная база (если API не сработает)
    FOOD_DATABASE = {
        "apple": {"name": "Яблоко", "calories": 52, "protein": 0.3, "fat": 0.2, "carbs": 14},
        "banana": {"name": "Банан", "calories": 89, "protein": 1.1, "fat": 0.3, "carbs": 23},
        "pizza": {"name": "Пицца", "calories": 266, "protein": 11, "fat": 10, "carbs": 33},
        "hamburger": {"name": "Гамбургер", "calories": 295, "protein": 17, "fat": 14, "carbs": 24},
        "sandwich": {"name": "Сэндвич", "calories": 250, "protein": 10, "fat": 8, "carbs": 30},
        "salad": {"name": "Салат", "calories": 15, "protein": 1, "fat": 0.2, "carbs": 3},
        "chicken": {"name": "Курица", "calories": 239, "protein": 27, "fat": 14, "carbs": 0},
        "rice": {"name": "Рис", "calories": 130, "protein": 2.7, "fat": 0.3, "carbs": 28},
        "bread": {"name": "Хлеб", "calories": 265, "protein": 9, "fat": 3.2, "carbs": 49},
        "egg": {"name": "Яйцо", "calories": 155, "protein": 13, "fat": 11, "carbs": 1},
        "milk": {"name": "Молоко", "calories": 42, "protein": 3.4, "fat": 1, "carbs": 5},
        "cheese": {"name": "Сыр", "calories": 402, "protein": 25, "fat": 33, "carbs": 1},
        "pasta": {"name": "Паста", "calories": 131, "protein": 5, "fat": 1, "carbs": 25},
        "fish": {"name": "Рыба", "calories": 206, "protein": 22, "fat": 12, "carbs": 0},
        "orange": {"name": "Апельсин", "calories": 47, "protein": 0.9, "fat": 0.1, "carbs": 12},
        "carrot": {"name": "Морковь", "calories": 41, "protein": 0.9, "fat": 0.2, "carbs": 10},
    }
    