import os
from dotenv import load_dotenv

from telebot import TeleBot, ExceptionHandler
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from src.helpers.Dotenv import Dotenv
from src.helpers.Admin import Admins  

from src.bot_commands import commands
from src.handlers import BotHandlers, AccessLevel



class ExceptionHandler(ExceptionHandler):
    def handle(self, exception):
        print("❌ Exception occured: ", exception)

class Bot: 
    def __init__(self) -> None:
        load_dotenv()
        self.parse_mode = "Markdown"
        
        self.bot_token = Dotenv().bot_token
        self.bot = TeleBot(self.bot_token, exception_handler=ExceptionHandler())
        
        self.commands = commands
        
        self.handlers = BotHandlers(self.bot)

        #? helpers
        self.admins = Admins(self.bot)
        
        self.startBot()
    
    def setup_command_menu(self):
        self.bot.set_my_commands(self.commands)
        keyboard = InlineKeyboardMarkup()
        button = InlineKeyboardButton("Start", callback_data='start')
        keyboard.add(button)
        self.bot.add_custom_filter(AccessLevel())

    def startBot(self):
        """ set up hanlders, starts bot polling """
        print("Bot started")
        self.admins.notify_admins(selected_admins=["Дамир"], message="Начинаю работу... /start")
        
        self.setup_command_menu()
        self.handlers.start_handlers()

        #? Теперь есть класс Dotenv для работы с Dotenv 
        env = os.getenv("ENVIRONMENT")   
        if env == "DEVELOPMENT":
            print("development")
            self.bot.infinity_polling(restart_on_change=True)
        else:
            print("production")
            self.bot.infinity_polling()
