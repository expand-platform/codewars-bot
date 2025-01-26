import re
from src.messages_eng import MESSAGES_ENG
from src.messages_ukr import MESSAGES_UKR
from src.messages_rus import MESSAGES_RUS
from src.database import Database
import time
import html2text
from telebot import TeleBot


"""обрабатываем сообщение пользователя и формирует slug"""
class Helpers():
    def __init__(self, bot):
        self.database = Database()

        self.eng_language = MESSAGES_ENG
        self.rus_language = MESSAGES_RUS
        self.ukr_language = MESSAGES_UKR
        
        self.bot: TeleBot = bot
    
    def lang(self, message, username):
        lang = self.database.pull_user_lang(username)
        if lang == "ENG":
            message = self.eng_language[message]
            return message
        elif lang == "RUS":
            message = self.rus_language[message]
            return message
        elif lang == "UKR":
            message = self.ukr_language[message]
            return message

    def transform_challenge_string(self, message):
        user_input = message.text
        remove_unnesecary_symbols = re.sub(r"[!?,.:;\-_`'\"/|\\]", " ", user_input)
        slug_transform = remove_unnesecary_symbols.split()
        result = "-".join(slug_transform)
        lowercase_result = result.lower()
        return lowercase_result

    def tg_api_try_except(self, text: str, username: str, max_length=4095):
        if len(text) <= max_length: 
            return "OK"
        elif len(text) > max_length:
            return "TOO_LONG"

    def challenge_print(self, challenge_source, username, chat_id, sleep):
        messages = [
            self.lang("task_name", username).format(challenge_source["Challenge name"]),
            self.lang("task_description", username).format(challenge_source['Description']),
            self.lang("task_rank", username).format(challenge_source['Rank']['name']),
            self.lang("task_url", username).format(challenge_source['Codewars link']),
        ]

        if sleep == True:
            time.sleep(4)

        for i in messages:        
            check = self.tg_api_try_except(i, username) 

            if check == "OK":
                try:
                    # конвертация html в markdown
                    converter = html2text.HTML2Text()
                    converter.ignore_links = False
                    task_in_markdown = converter.handle(i)

                    self.bot.send_message(chat_id, task_in_markdown, self.parse_mode) 
                except:
                    self.bot.send_message(chat_id, i)
            elif check == "TOO_LONG":
                text = self.lang("message_is_too_long", username)
                self.bot.send_message(chat_id, text, parse_mode=self.parse_mode)
