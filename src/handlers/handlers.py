import os 
import html2text
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.memory import MemoryJobStore

from telebot import types, TeleBot
from telebot.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telebot.util import quick_markup

from src.messages.en import MESSAGES_ENG
from src.messages.ukr import MESSAGES_UKR
from src.messages.ru import MESSAGES_RUS
from src.inline_buttons import lvl_buttons, lang_buttons, mode_buttons
from src.helpers.helpers import Helpers
from src.helpers.Dotenv import Dotenv
from src.helpers.keyboards import normal_mode_keyboard, story_mode_keyboard

from src.codewars_api_get import Codewars_Challenges
from src.database import Database
from src.handlers.admin_handlers import Admin

# from src.keyboardButtons import keyboard_buttons

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

import random

from requests import get
 
class BotHandlers():
    def __init__(self, bot):
        self.admin_ids = Dotenv().admin_ids

        self.bot: TeleBot = bot

        self.parse_mode = "Markdown"
        self.eng_language = MESSAGES_ENG
        self.rus_language = MESSAGES_RUS
        self.ukr_language = MESSAGES_UKR

        self.database = Database()
        self.codewars_api = Codewars_Challenges()
        self.helpers = Helpers(self.bot)
        self.admin_handlers = Admin(self.bot)
        
        self.scheduler = BackgroundScheduler(
            jobstores = {
                'default': MemoryJobStore()
            }
        )

        # self.keyboard_buttons = keyboard_buttons
        
        self.markup = None
        
    def start_handlers(self):
        self.start_command()
        self.handle_random_text() 
        
    def lang_change(self, message: Message):

        username = message.from_user.username
        # self.helpers.command_use_log("/language_change", username, message.chat.id)
        markup = quick_markup(values=lang_buttons, row_width=1)
        ask_lang_message = self.helpers.lang("change_language", message)
        sent_message = self.bot.send_message(message.chat.id, ask_lang_message, reply_markup=markup)

        @self.bot.callback_query_handler(func=lambda call: call.message.message_id == sent_message.message_id)
        def lang_change_callback(call: CallbackQuery):
            lang = call.data
            username = call.from_user.username

            self.database.update_user_language(message, lang)

            bot_message = self.helpers.lang("language_changed", message)
            self.bot.edit_message_reply_markup(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=None
            )
            
            self.bot.delete_message(call.message.chat.id, sent_message.message_id)
            self.bot.send_message(call.message.chat.id, bot_message)
            
            user = self.database.users_collection.find_one({"tg_username": username})
            
            if user['cw_nickname'] == "None":
                self.authorization(message)

    def start(self, message: Message):
            markup = normal_mode_keyboard()
            
            username = message.from_user.username

            self.database.new_user(username, "None", message)

            self.lang_change(message)

            bot_message = self.helpers.lang("start_bot", message)
            text = bot_message.format(username)
            self.bot.send_message(message.chat.id, text, reply_markup=markup)
            
            print("user chat id:", message.chat.id)

            self.helpers.command_use_log("/start", username, message.chat.id)

    def start_command(self):
        """Запускаем бота, а также добавляет пользователя в базу данных, если его там нет"""
        @self.bot.message_handler(commands=["start"], func=lambda message: True) 
        def echo(message):
            self.start(message)
      
    
    def authorization(self, message: Message):
        username = message.from_user.username
        img_path = "src/images/nickname_example.png"
        normalised_img_path = os.path.normpath(img_path)
        # self.helpers.command_use_log("/authorize", username, message.chat.id)
        
        markup =  InlineKeyboardMarkup()
        cw_signin_page_button = InlineKeyboardButton(self.helpers.lang("codewars_signin_button", message), url="https://www.codewars.com/users/sign_in")
        markup.add(cw_signin_page_button)
        
        self.bot.send_photo(message.chat.id, open(normalised_img_path, "rb"), caption=self.helpers.lang("nickname_example", message))

        bot_message = self.bot.send_message(
            chat_id=message.chat.id,
            text=self.helpers.lang("asking_cwusername", message),
            parse_mode=self.parse_mode,
            reply_markup=markup
        )
        
        self.bot.register_next_step_handler(message=bot_message, callback=self.authorization_ans)
        
    def authorization_ans(self, message: Message):
        markup = self.create_keyboard()
        username = message.from_user.username
        
        filter = {"tg_username": username}
        user = self.database.users_collection.find_one(filter) 
        user_info = self.codewars_api.getuser_function(message.text)
        
        if "reason" in user_info:
            print("USER ISN'T FOUND")
            self.authorization(message)
            # self.bot.send_message(message.chat.id, self.lang("authorization_error", username))
        
        else:
            bot_reply = self.helpers.lang("successful_authorization", message)
            
            cw_username = user_info["username"]
            honor_lvl = user_info["honor"]
            tasks_done = user_info['codeChallenges']['totalCompleted']
            
            message_text = bot_reply.format(cw_username, honor_lvl, tasks_done)
            
        
            self.database.update_codewars_nickname(message, cw_username)
            self.bot.send_message(message.chat.id, message_text, reply_markup=markup)
            
            if user["totalDone_snum"] == None:
                self.record_first_info(message.text, username, filter)
        
    def record_first_info(self, cw_username, username, filter):
        user = self.codewars_api.getuser_function(cw_username) 
        update = {"$set": {"totalDone_snum": user["codeChallenges"]["totalCompleted"]}}
        
        self.database.users_collection.update_one(filter, update, upsert=False)
        
        
    def check_stats_command(self, message: Message): 
            username = message.from_user.username
            self.helpers.command_use_log("/check_stats", username, message.chat.id)
            
            filter = {"tg_username": username}
            user = self.database.users_collection.find_one(filter)
            
            self.check_stats_response(message, user["cw_nickname"])


    def check_stats_response(self, message: Message, cw_nickname: str):
        tg_username = message.from_user.username
        
        try:
            user_stats = self.codewars_api.check_user_stats(cw_nickname, tg_username)    
            self.bot.reply_to(message, user_stats)
        except:
            bot_message = self.helpers.lang("check_stats_error", message)
            self.bot.reply_to(message, bot_message)

    def change_mode(self, message: Message):
        username = message.from_user.username
        
        filter = {"tg_username": username}
        user = self.database.users_collection.find_one(filter)
        markup = quick_markup(values=mode_buttons, row_width=1)
        ask_mode = self.helpers.lang("mode_selection", message)
        sent_message = self.bot.send_message(message.chat.id, ask_mode, reply_markup=markup)
        
        @self.bot.callback_query_handler(func=lambda call: call.message.message_id == sent_message.message_id)
        def mode_choice_callback(call: CallbackQuery):
            mode = call.data
            markup_buttons = None
            
            if mode == "STORY":
                markup_buttons = story_mode_keyboard()
                update = {"$set": {"story_mode": True}}
                bot_message = self.helpers.lang("story_mode_selected", message)
                
            else:
                update = {"$set": {"story_mode": False}}
                markup_buttons = normal_mode_keyboard()
                bot_message = self.helpers.lang("normal_mode_selected", message)
                
            self.database.users_collection.update_one(filter, update, upsert=False)
            self.bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
            
            self.bot.delete_message(call.message.chat.id, sent_message.message_id)
            self.bot.send_message(call.message.chat.id, bot_message, reply_markup=markup_buttons)
        
        return user["story_mode"]
        
    def random_level_and_task(self, message: Message):
        
        username = message.from_user.username
        chat_id = message.chat.id
        
        # достать кв никнейм по тг юзеру
        tguser_filter = {"tg_username": username}
        user = self.database.users_collection.find_one(tguser_filter)        
        codewars_name = user["cw_nickname"]

        # статы юзера
        stats = self.codewars_api.getuser_function(codewars_name)
        task_difference = stats["codeChallenges"]["totalCompleted"] - user["totalDone_snum"]
         
        if task_difference < 3:
            needs_to_be_done = 3 - task_difference
            
            self.bot.send_message(message.chat.id, self.helpers.lang("no_lvl_access", message).format(needs_to_be_done)) 
            
        else:
            # остальной код
            
            self.bot.send_dice(message.chat.id, emoji="🎲")
            # self.helpers.command_use_log("/random_level_and_task", username, message.chat.id)
            
            challenges = list(self.database.challenges_collection.find({}))
            random_task = random.choice(challenges)
            
            self.helpers.challenge_print(random_task, message, chat_id, True)

    def random_task_command(self, message: Message):
        markup = quick_markup(values=lvl_buttons, row_width=2)
        
        username = message.from_user.username
        bot_message = self.helpers.lang("random_task_level_pick", message)

        # Отправляем сообщение с кнопками
        sent_message = self.bot.send_message(message.chat.id, bot_message, reply_markup=markup)
        # self.helpers.command_use_log("/random_task", username, message.chat.id)

        """Случайная задача из коллекции"""
        @self.bot.callback_query_handler(func=lambda call: call.message.message_id == sent_message.message_id)
        def random_task(call):
            chat_id = call.message.chat.id

            # Получаем уровень из данных кнопки
            level = call.data.replace('_', ' ')
            bot_callback = self.helpers.lang("random_task_on_screen_answer", message)
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

                print("kata name:", challenge["Challenge name"])
                self.helpers.challenge_print(challenge, message, chat_id, False)
                    
            else:
                bot_message = self.helpers.lang("random_task_not_found", message)
                self.bot.send_message(chat_id, bot_message)
            self.bot.delete_message(chat_id, sent_message.message_id)

    def find_task_command(self, message: Message):
        """Поиск задачи из кодварса по названию"""
        username = message.from_user.username
        message_format = self.helpers.lang("find_task_ask_name", message)
        bot_message = self.bot.send_message(
            chat_id=message.chat.id, 
            text=message_format, 
            parse_mode=self.parse_mode
        )
        # self.helpers.command_use_log("/find_task", username, message.chat.id) 
        self.bot.register_next_step_handler(message=bot_message, callback=self.find_task_response)
        
    def find_task_response(self, message: Message):
        username = message.from_user.username
        chat_id = message.chat.id
        result = self.helpers.transform_challenge_string(message)
        challenge_api = self.codewars_api.get_challenge_info_by_slug(result)  

        if challenge_api == 404:
            bot_message = self.helpers.lang("find_task_not_found", message)
            self.bot.reply_to(message, bot_message)
        else:
            filter = {"Slug": result}
            challenge_database = self.database.challenges_collection.find_one(filter)
            if challenge_database:

                self.helpers.challenge_print(challenge_database, message, chat_id, False)
            else:
                self.database.challenges_collection.insert_one(challenge_api)
            
                self.helpers.challenge_print(challenge_api, message, chat_id, False)
            # TODO: проверять длину только у описания
    
    def send_reminder(self, chat_id, message: Message):
        reminders = self.helpers.lang("reminders", message)
        reminder = random.choice(reminders)
        self.bot.send_message(chat_id, reminder)

    def setup_reminder(self, message: Message):
        try:
            user_id = message.from_user.id
            chat_id = message.chat.id
            username = message.from_user.username
            job_id = f"reminder_{user_id}"  # Create a unique job ID for the user
            
            # Check if a job with this ID already exists
            if not self.scheduler.get_job(job_id):
                self.scheduler.add_job(self.send_reminder, 'interval', days=3, args=[chat_id, username], id=job_id, replace_existing=True)
                
            if not self.scheduler.running:
                self.scheduler.start()
                
            print("setup_reminder: ", self.scheduler.get_jobs())
        except Exception as e:
            print("Error: ", e)

    def shutdown_reminder(self, message: Message):
        user_id = message.from_user.id
        job_id = f"reminder_{user_id}"  # Create a unique job ID for the user
        
        # Remove the specific user's reminder job if it exists
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
            # self.scheduler.shutdown()
            
        print("shutdown_reminder: ", self.scheduler.get_jobs())

    def handle_random_text(self):
        """This function handles random text from the user."""

        @self.bot.message_handler(func=lambda message: message.text == "Check stats 🏅")
        def check_stats(message):
            self.check_stats_command(message)
            self.helpers.command_use_log("/check_stats", message.from_user.username, message.from_user.id)

        @self.bot.message_handler(func=lambda message: message.text == "Random task 🥋")
        def random_task(message):
            self.random_task_command(message)
            self.helpers.command_use_log("/random_task", message.from_user.username, message.from_user.id)

        @self.bot.message_handler(func=lambda message: message.text == "Find task 🔍")
        def find_task(message):
            self.find_task_command(message)
            self.helpers.command_use_log("/find_task", message.from_user.username, message.from_user.id)

        @self.bot.message_handler(func=lambda message: message.text == "Change mode 🔄")
        def story_mode(message):
            self.change_mode(message)
            self.helpers.command_use_log("/story_mode", message.from_user.username, message.from_user.id)

        @self.bot.message_handler(func=lambda message: message.text == "Random task and lvl 🎲")
        def random_task_and_lvl(message):
            self.random_level_and_task(message)
            self.helpers.command_use_log("/random_task_and_level", message.from_user.username, message.from_user.id)

        @self.bot.message_handler(func=lambda message: message.text == "Language 🌐")
        def change_language(message):
            self.lang_change(message)
            self.helpers.command_use_log("/language", message.from_user.username, message.from_user.id)

        @self.bot.message_handler(func=lambda message: message.text == "Help ❔")
        def help_command(message):
            bot_message = self.helpers.lang("help", message)
            self.bot.send_message(message.chat.id, bot_message)
            self.helpers.command_use_log("/help", message.from_user.username, message.from_user.id)

        @self.bot.message_handler(func=lambda message: message.text == "Reauthorize ⚙")
        def reauthorize(message):
            self.authorization(message)
            self.helpers.command_use_log("/reauthorize", message.from_user.username, message.from_user.id)
            
        # Start a new reminder job after handling the user's message
        # self.setup_reminder(message)
               
        
    # сделать так, чтобы при отправке абракадабры от пользователя - он получал рандомную цитату из массива, чтобы читал побольше и не писал хуйню боту





     # def send_sticker_list(self, message):
    #     sticker_pack_name = "Astolfobydanveliar_by_fStikBot"  # Replace with the sticker pack name
    #     sticker_set = self.bot.get_sticker_set(name=sticker_pack_name)
    #     stickers_id = []
    #     for sticker in sticker_set.stickers:
    #         stickers_id.append(sticker.file_id)
    #         print("STICKER: ", stickers_id)
    #         print("STICKER: ", sticker)
        
    #     # print("STICKERS: ", stickers)  #! теперь бот отправляет Астольфо)))
    #     self.bot.send_sticker(message.chat.id, )
    