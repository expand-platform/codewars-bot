from requests import get
from dotenv import load_dotenv
import os 

from telebot import types, TeleBot
from telebot.types import BotCommand, Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telebot.util import quick_markup

from src.messages_eng import MESSAGES_ENG
from src.messages_ukr import MESSAGES_UKR
from src.messages_rus import MESSAGES_RUS
from src.inline_buttons import lvl_buttons, lang_buttons
from src.helpers import transform_challenge_string

from src.codewars_api_get import Codewars_Challenges
from src.database import Database

from src.keyboardButtons import keyboard_buttons

import time
import random

# с кнопками есть баги, клава иногда не появляется, по фикшу на уроке

class BotHandlers():
    def __init__(self, bot):
        load_dotenv()
        self.admin_ids = os.getenv("ADMIN_IDS") 
        self.admin_ids = self.admin_ids.split(",") 

        self.bot: TeleBot = bot

        self.parse_mode = "Markdown"
        self.eng_language = MESSAGES_ENG
        self.rus_language = MESSAGES_RUS
        self.ukr_language = MESSAGES_UKR

        self.database = Database()
        self.codewars_api = Codewars_Challenges()

        self.keyboard_buttons = keyboard_buttons
        
        self.markup = None
        
    
    
    def start_handlers(self):
        self.start_command()
        self.handle_random_text() 
        
    def create_keyboard(self):
        # * КОГДА ДОБАВЛЯЕТЕ НОВУЮ КОММАНДУ В KEYBOARDBUTTON СТАРАЙТЕСЬ РАВНОМЕРНО ДЕЛАТЬ (ОДНА СТРОЧКА С MARKUP.ADD ЭТО ОДНА ГОРИЗОНТАЛЬНАЯ ГРУПА)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True) 
        
        markup.add(self.keyboard_buttons["get_username"], self.keyboard_buttons["check_stats"], self.keyboard_buttons["random_task"])
        markup.add(self.keyboard_buttons["find_task"], self.keyboard_buttons["load_task"], self.keyboard_buttons["random_lvltask"])
        markup.add(self.keyboard_buttons["language"], self.keyboard_buttons["help"])
        
        return markup
    
    def command_use_log(self, command, tg_user, chat_id):
        env = os.getenv("ENVIRONMENT") 
        if env == "PRODUCTION":
            for value in self.admin_ids: 
                if str(chat_id) == str(value):
                    pass
                else:
                    self.bot.send_message(value, f"Пользователь @{tg_user} перешёл в раздел {command}")

    def lang_change(self, message: Message):
        username = message.from_user.username
        self.command_use_log("/language_change", username, message.chat.id)
        markup = quick_markup(values=lang_buttons, row_width=1)
        bot_message = self.lang("change_language", username)
        sent_message = self.bot.send_message(message.chat.id, bot_message, reply_markup=markup)

        @self.bot.callback_query_handler(func=lambda call: call.message.message_id == sent_message.message_id)
        def lang_change_callback(call: CallbackQuery):
            lang = call.data
            username = call.from_user.username

            # Обновляем язык в базе данных
            self.database.update_user_language(username, lang)
            bot_message = self.lang("language_changed", username)

            # Удаляем кнопки, заменяя их пустой разметкой
            self.bot.edit_message_reply_markup(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=None
            )

            # Отправляем сообщение о смене языка
            self.bot.send_message(call.message.chat.id, bot_message)
            

    def lang(self, message, username):
        lang = self.database.pull_user_lang(username)
        print(lang)
        if lang == "ENG":
            message = self.eng_language[message]
            return message
        elif lang == "RUS":
            message = self.rus_language[message]
            return message
        elif lang == "UKR":
            message = self.ukr_language[message]
            return message
        

    def start(self, message):
            markup = self.create_keyboard()

            
            #? Предлагаю на /start сразу просить человека создать / привязать аккаунт из Codewars и ввести свой user_name из Codewars в бот. 
            #? Так у нас сразу на руках будет юзернейм и команда для её привязки не будет нужна (ведь, по сути, весь наш функционал завязан именно на привязке к аккаунту Кодварс)
            
            username = message.from_user.username
            self.database.new_user(username, "None")

            bot_message = self.lang("start_bot", username)
            text = bot_message.format(username)
            
            print("user chat id:", message.chat.id)
            self.bot.send_message(message.chat.id, text, reply_markup=markup) 
                
            self.command_use_log("/start", username, message.chat.id)
            #? Ещё на старте бота предлагаю добавить отправку сообщения админам, мол,
            #? "бот запущен и ждёт команд, нажми /start"

    def start_command(self):
        """Запускаем бота, а также добавляет пользователя в базу данных, если его там нет"""
        @self.bot.message_handler(commands=["start"], func=lambda message: True) 
        def echo(message):
            self.start(message)
            
            
    def check_stats_command(self, message): 
            username = message.from_user.username
            message_format = self.lang("ask_codewars_username", username)
            bot_message = self.bot.send_message(
                chat_id=message.chat.id, 
                text=message_format, 
                parse_mode=self.parse_mode
            )
            self.command_use_log("/check_stats", username, message.chat.id)
            self.bot.register_next_step_handler(message=bot_message, callback=self.check_stats_response)


    def check_stats_response(self, message):
        tg_username = message.from_user.username
        try:
            user_stats = self.codewars_api.check_user_stats(message.text, tg_username)
            self.bot.reply_to(message, user_stats)
        except:
            bot_message = self.lang("check_stats_error", tg_username)
            self.bot.reply_to(message, bot_message)

    def random_level_and_task(self, message):
        self.bot.send_dice(message.chat.id, emoji="🎲")
        username = message.from_user.username
        self.command_use_log("/random_level_and_task", username, message.chat.id)
        
        challanges = list(self.database.challenges_collection.find({}))
        random_task = random.choice(challanges)
        
        bot_reply = (
                    f"Challenge name: {random_task['Challenge name']}\n\n"
                    f"Description: {random_task['Description']}\n\n"
                    f"Rank: {random_task['Rank']['name']}\n\n"
                    f"Codewars link: {random_task['Codewars link']}"
                )
        
        bot_message = self.lang("random_task_n_lvl", username) 
        text = bot_message.format(bot_reply)
        
        time.sleep(4)
        
        self.bot.send_message(message.chat.id, text, parse_mode=self.parse_mode)
        
        
        
        
        
        # self.bot.send_message(message.chat.id, "hehehehe...")




# ! иногда есть ошибка Bad requsest, message is too long
    def random_task_command(self, message):
        markup = quick_markup(values=lvl_buttons, row_width=2)
        username = message.from_user.username
        bot_message = self.lang("random_task_level_pick", username)

        # Отправляем сообщение с кнопками
        sent_message = self.bot.send_message(message.chat.id, bot_message, reply_markup=markup)
        self.command_use_log("/random_task", username, message.chat.id)

        """Случайная задача из коллекции"""
        @self.bot.callback_query_handler(func=lambda call: call.message.message_id == sent_message.message_id)
        def random_task(call):
            chat_id = call.message.chat.id

            # Получаем уровень из данных кнопки
            level = call.data.replace('_', ' ')
            bot_callback = self.lang("random_task_on_screen_answer", username)
            callback_text = bot_callback.format(level)
            self.bot.answer_callback_query(call.id, callback_text)

            # Удаляем кнопки после нажатия
            self.bot.edit_message_reply_markup(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=None
            )

            # Создаём фильтр для случайной задачи
            filter = [
                {"$match": {"Rank.name": level}},
                {"$sample": {"size": 1}}
            ]

            # Получаем случайную задачу из базы данных
            result = list(self.database.challenges_collection.aggregate(filter))

            if result:
                challenge = result[0]

                bot_reply = (
                    f"Challenge name: {challenge['Challenge name']}\n\n"
                    f"Description: {challenge['Description']}\n\n"
                    f"Rank: {challenge['Rank']['name']}\n\n"
                    f"Codewars link: {challenge['Codewars link']}"
                )
                bot_message = self.lang("random_task_found", username)
                text = bot_message.format(level, bot_reply)

                # Отправляем задачу пользователю
                self.bot.send_message(chat_id, text, parse_mode=self.parse_mode)
            else:
                bot_message = self.lang("random_task_not_found", username)
                self.bot.send_message(chat_id, bot_message)

    def find_task_command(self, message):
        """Поиск задачи из кодварса по названию"""
        username = message.from_user.username
        message_format = self.lang("find_task_ask_name", username)
        bot_message = self.bot.send_message(
            chat_id=message.chat.id, 
            text=message_format, 
            parse_mode=self.parse_mode
        )
        self.command_use_log("/find_task", username, message.chat.id) 
        self.bot.register_next_step_handler(message=bot_message, callback=self.find_task_response)
 

    def find_task_response(self, message):
        username = message.from_user.username
        result = transform_challenge_string(message)
        challenge = self.codewars_api.get_challenge_info_by_slug(result)  
        if challenge == 404:
            bot_message = self.lang("find_task_not_found", username)
            self.bot.reply_to(message, bot_message)
        else:
            bot_message = self.lang("find_task_found", username)
            text = bot_message.format(challenge["Challenge name"], challenge["Description"], list(challenge["Rank"].values())[1], challenge["Codewars link"])
            filter = {"Slug": result}
            challenge_check = self.database.challenges_collection.find_one(filter)
            print(challenge_check)
            if challenge_check:
                print("Такая задача уже есть в базе данных, поэтому она не была добавлена в базу.")
            else:
                self.database.challenges_collection.insert_one(challenge)
            self.bot.reply_to(message, text)

           
    def load_challenges_command(self, message):
        """ load tasks from another user, saves them to db """  
        username = message.from_user.username
        message_format = self.lang("load_challenges_intro", username)        
        bot_message = self.bot.send_message(
            chat_id=message.chat.id, 
            text=message_format, 
            parse_mode=self.parse_mode
        )
        self.command_use_log("/load_tasks", username, message.chat.id)
        self.bot.register_next_step_handler(message=bot_message, callback=self.load_challenges_final_step)
                
                
    def load_challenges_final_step(self, message: Message):
        username = message.from_user.username
        cw_username = message.text
        print("🐍 CD user_name (load_tasks_send_request)", cw_username)
        
        # send request to API
        user_challenges_URL = f"https://www.codewars.com/api/v1/users/{cw_username}/code-challenges/completed" 
        
        try:
            response = get(url=user_challenges_URL)
            data_from_api = response.json()
            # try:
            challenges_count = data_from_api["totalItems"] 
            # except:
            #     self.bot.send_message(message.chat.id, )
            bot_message = self.lang("load_challenges_count", username)   
            bot_reply_text = bot_message.format(challenges_count,cw_username)
            print(bot_reply_text)
            
            self.bot.send_message(
                chat_id=message.chat.id, 
                text=bot_reply_text, 
                parse_mode=self.parse_mode
            )
            
            user_challenges = data_from_api["data"]
            
            for challenge in user_challenges:
                challenge_slug = challenge["slug"]
                print("🐍 challenge_slug (load_challenges_final_step) ",challenge_slug)
                
                this_challenge_exists = self.database.is_challenge_in_db(challenge_slug=challenge_slug)
                print("🐍 this_challenge_exists (load_challenges_final_step) ",this_challenge_exists)
                
                if not this_challenge_exists:
                    challenge_info = self.codewars_api.get_challenge_info_by_slug(slug=challenge_slug)
                    print("🐍challenge info (load_challenges_final_step)", challenge_info)
                
                    if challenge:
                        self.database.save_challenge(new_challenge=challenge_info)
                        
            bot_message = self.lang("load_challenges_final", username)   
            bot_final_message_text = bot_message.format(challenges_count) 
                    
            self.bot.send_message(
                chat_id=message.chat.id, 
                text=bot_final_message_text, 
                parse_mode=self.parse_mode
            )
        except:
            bot_message = self.lang("load_tasks_error", username) 
            self.bot.send_message(
                chat_id=message.chat.id, 
                text=bot_message, 
                parse_mode=self.parse_mode
            )


    def handle_random_text(self):
        """эта функция принимает текст от пользователя, формирует slug, и находит такую задачу в кодварсе"""
        @self.bot.message_handler(func=lambda message: True)
        def handle_text(message):
            if message.text == "Start ✅":
                self.start(message)
            
            elif message.text == "Check stats 🏅":
                self.check_stats_command(message)
                
            elif message.text == "Random task 🥋":
                self.random_task_command(message)
            
            elif message.text == "Find task 🔍":
                self.find_task_command(message)
            
            elif message.text == "Load task 🔃":
                self.load_challenges_command(message)
                
            elif message.text == "Random task and lvl 🎲":
                self.random_level_and_task(message)
            
            elif message.text == "Language 🌐":
                self.lang_change(message)
        
            elif message.text == "Help ❔":
                username = message.from_user.username
                self.command_use_log("/help", username, message.chat.id)
                bot_message = self.lang("help", username)  
                self.bot.send_message(message.chat.id, bot_message)
            else:
                username = message.from_user.username
                bot_message = self.lang("random_text_reply", username) 
                self.bot.send_message(message.chat.id, bot_message)      
    # сделать так, чтобы при отправке абракадабры от пользователя - он получал рандомную цитату из массива, чтобы читал побольше и не писал хуйню боту