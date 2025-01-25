from .Dotenv import Dotenv
from telebot import TeleBot

class Admins():
    def __init__(self, bot: TeleBot):
        self.parse_mode = "Markdown"

        self.bot = bot

        self.admin_ids = Dotenv().admin_ids

        self.admins = [
            { 
                "name": "Дамир", 
                "id": 331697498 
            },
            { 
                "name": "Даня", 
                "id": 1402095363 
            },
            { 
                "name": "Дима", 
                "id": 1356631201 
            },
        ]

    # ! Пожалуйста, протестируйте, работает ли try-except
    def notify_admins(self, selected_admins: list[str], message: str):
        for admin_name in selected_admins:
            for admin in self.admins:
                # if this is a selected admin
                if admin_name == admin["name"]:
                    try: 
                        self.bot.send_message(admin["id"], message, parse_mode=self.parse_mode)
                    except: 
                        print(f"Для тебя нет уведомлений во время {message}")
                        pass
            

