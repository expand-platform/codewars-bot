import re
import os
import time
import html2text

from telebot import TeleBot
from telebot.types import Message

from src.messages.en import MESSAGES_ENG
from src.messages.ukr import MESSAGES_UKR
from src.messages.ru import MESSAGES_RUS

from src.database import Database
from src.helpers.Dotenv import Dotenv

"""обрабатываем сообщение пользователя и формирует slug"""
class Helpers():
    def __init__(self, bot):
        self.database = Database()

        self.eng_language = MESSAGES_ENG
        self.rus_language = MESSAGES_RUS
        self.ukr_language = MESSAGES_UKR

        self.parse_mode = "Markdown"

        self.admin_ids = Dotenv().admin_ids
        
        self.bot: TeleBot = bot

    def command_use_log(self, command, tg_user, chat_id):
        # test comment
        env = Dotenv().environment
        # if chat_id not in self.admin_ids:
        self.database.stat_update(command)

        if env == "PRODUCTION":

            for value in self.admin_ids: 
                print("value:", value)
                if str(chat_id) != str(value):
                    self.bot.send_message(value, f"Пользователь @{tg_user} перешёл в раздел {command}")
               
    
    def lang(self, text: str, message: Message):
        lang = self.database.pull_user_lang(message)
        if lang == "ENG":
            reply = self.eng_language[text]
        elif lang == "RUS":
            reply = self.rus_language[text] 
        elif lang == "UKR":
            reply = self.ukr_language[text]
        return reply

    def transform_challenge_string(self, message: Message):
        user_input = message.text
        remove_unnesecary_symbols = re.sub(r"[!?,.:;\-_`'\"/|\\]", " ", user_input)
        slug_transform = remove_unnesecary_symbols.split()
        result = "-".join(slug_transform)
        lowercase_result = result.lower()
        return lowercase_result

    def challenge_print(self, challenge_source, message, chat_id, sleep):
        messages = [
            self.lang("task_name", message).format(challenge_source["Challenge name"]),
            self.lang("task_rank", message).format(challenge_source['Rank']['name']),
            self.lang("task_description", message).format(challenge_source['Description']),
            self.lang("task_url", message).format(challenge_source['Codewars link']),
        ]

        if sleep == True:
            time.sleep(4)

        for index, i in enumerate(messages, start=1):
            if index == 1: 
                bold_kata_name = f"*{challenge_source["Challenge name"]}*"
                reply = f"{self.lang("task_name", message).format(bold_kata_name)}"
                self.bot.send_message(chat_id, bold_kata_name, self.parse_mode) 
            elif index == 2:
                self.bot.send_message(chat_id, i, self.parse_mode) 
            elif index == 3:
                try:
                    converter = html2text.HTML2Text()
                    converter.ignore_links = True
                    task_in_markdown = converter.handle(challenge_source['Description'])

                    self.bot.send_message(chat_id, task_in_markdown, self.parse_mode) 
                except:
                    text = self.lang("message_is_too_long", message)
                    self.bot.send_message(chat_id, text, parse_mode=self.parse_mode)
            elif index == 4:
                link = f"[Link]({challenge_source['Codewars link']})"
                reply = self.lang("task_url", message).format(link)
                self.bot.send_message(chat_id, reply, parse_mode=self.parse_mode)
