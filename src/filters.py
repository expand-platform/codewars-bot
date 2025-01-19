import telebot
from telebot.types import Message
from src.database import Database

class ExceptionHandler(telebot.ExceptionHandler):
    def handle(self, exception):
        print("Exception occured: ", exception)

class AccessLevel(telebot.custom_filters.AdvancedCustomFilter): 
    key='access_level'
    print("check1")
    @staticmethod
    def check(message: Message, levels):
        print("check2")
        username = message.from_user.username
        access_level = Database().get_user_access(username) 
        print(access_level)
        return access_level in levels
