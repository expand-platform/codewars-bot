from src.helpers.helpers import Helpers
from src.handlers.handlers import BotHandlers

from telebot import TeleBot
from telebot.types import Message


class StoryMode:
    def __init__(self, bot: TeleBot):
        self.bot = bot
        self.helpers = Helpers(bot)
        self.user_handlers = BotHandlers(bot)
    
    def change_mode(self, message: Message):
        self.user_handlers.change_mode(message)
        
    def soon(self, message: Message):
        self.bot.send_message(message.chat.id, "The feature is coming soon!")
    
    def handle_text(self):
        print("SM HANDLER")
        @self.bot.message_handler(func=lambda message: message.text == "Change Mode 🔄")
        def normal_mode(message):
            self.change_mode(message)
            
        @self.bot.message_handler(func=lambda message: message.text == "Receive Mission")
        def receive_task(message):
            self.soon(message)
            
        @self.bot.message_handler(func=lambda message: message.text == "Check Level")
        def check_level(message):
            self.soon(message)