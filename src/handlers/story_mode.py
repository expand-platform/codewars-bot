from src.keyboardButtons import story_mode_buttons

from telebot import types, TeleBot
from telebot.types import Message
from telebot.states.sync.context import StateContext

from src.helpers.filters import StoryModeState

class StoryMode:
    def __init__(self, bot: TeleBot):
        self.bot = bot
        self.story_mode_buttons = story_mode_buttons
        
    def create_keyboard(self):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True) 
        markup.add(self.story_mode_buttons["receive_task"], self.story_mode_buttons["check_level"], self.story_mode_buttons["normal_mode"])
        return markup
    
    def change_mode(self, message):
        self.bot.reply_to(message, "Hello World!")
    
    def handle_text(self):
        print("SM HANDLER")
        @self.bot.message_handler(state=StoryModeState.active)
        def handle_text(message: Message):
            if message.text == "Normal Mode":
                self.bot.delete_state(message.from_user.id)
                self.change_mode(message)
                print("Normal Mode")
                