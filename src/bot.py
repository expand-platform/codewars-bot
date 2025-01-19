import os
from dotenv import load_dotenv

import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.bot_commands import commands

from src.handlers import BotHandlers
from src.admin_handlers import Admin
from src.filters import AccessLevel, ExceptionHandler

class Bot: 
    def __init__(self) -> None:
        load_dotenv()
        
        self.bot_token = os.getenv("TOKEN_FOR_TGBOT")
        self.bot = telebot.TeleBot(self.bot_token, exception_handler=ExceptionHandler())
        
        self.commands = commands
        
        self.handlers = BotHandlers(self.bot)
        self.admin_handlers = Admin(self.bot)
        
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
        
        self.setup_command_menu()
        self.handlers.start_handlers()
        self.admin_handlers.start_admin_handlers()
         
        env = os.getenv("ENVIRONMENT")   
        if env == "DEVELOPMENT":
            print("development")
            self.bot.infinity_polling(restart_on_change=True)
        else:
            print("production")
            self.bot.infinity_polling()