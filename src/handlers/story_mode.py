from src.helpers.helpers import Helpers
from src.handlers.handlers import BotHandlers
from src.database import Database

from telebot import TeleBot
from telebot.types import Message


class StoryMode:
    def __init__(self, bot: TeleBot):
        self.bot = bot
        self.helpers = Helpers(bot)
        self.database = Database()
        self.user_handlers = BotHandlers(bot)
    
    def soon(self, message: Message):
        self.bot.send_message(message.chat.id, "The feature is coming soon!")
        
    def change_mode(self, message: Message):
        self.user_handlers.change_mode(message)
        
    def check_rank(self, message: Message):
        uid = message.from_user.id
        user = self.database.users_collection.find_one({"user_id": uid})
        user_rank = user.get("rank")
        rank_message = self.helpers.lang("check_rank", message)
        formatted_message = rank_message.format(user_rank)
        self.bot.send_message(message.chat.id, formatted_message)
    
    def handle_text(self):
        print("SM HANDLER")
        @self.bot.message_handler(func=lambda message: message.text == "Change Mode 🔄")
        def normal_mode(message):
            self.change_mode(message)
            
        @self.bot.message_handler(func=lambda message: message.text == "Receive Mission")
        def receive_task(message):
            self.soon(message)
            
        @self.bot.message_handler(func=lambda message: message.text == "Check Rank")
        def check_level(message):
            self.check_rank(message)