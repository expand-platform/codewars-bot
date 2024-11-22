import os
from dotenv import load_dotenv

import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.bot_commands import commands

from src.handlers import BotHandlers

class Bot: 
    def __init__(self) -> None:
        load_dotenv()
        
        self.bot_token = os.getenv("TOKEN_FOR_TGBOT")
        self.bot = telebot.TeleBot(self.bot_token)
        
        self.commands = commands
        
        self.handlers = BotHandlers(self.bot)
        
        self.startBot()
    
    def setup_command_menu(self):
        self.bot.set_my_commands(self.commands)
        keyboard = InlineKeyboardMarkup()
        button = InlineKeyboardButton("Start", callback_data='start')
        keyboard.add(button)

    def startBot(self):
        """ set up hanlders, starts bot polling """
        print("Bot started")
        
        self.setup_command_menu()
        self.handlers.start_handlers()
         
        #! Это должно быть только на development, нужно сделать переменную в env
        #! и написать if
        # self.bot.infinity_polling(restart_on_change=True)
        self.bot.infinity_polling()


"""
Вопрос первый: как сделать бота интересным? 
добавить какие нибудь интересные фишки. какие?

Вопрос второй: как сделать бота затягивающим?
первый и третий пункт

Вопрос третий: как сделать так чтобы люди возвращались к боту?
должен быть удобнее, чем просто зайти на кодварс.

"""