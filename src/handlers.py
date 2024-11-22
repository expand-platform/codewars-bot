from requests import get
from dotenv import load_dotenv
import os

from telebot import types
from telebot.types import BotCommand, Message, InlineKeyboardButton, InlineKeyboardMarkup
from telebot.util import quick_markup

from src.messages import MESSAGES
from src.inline_buttons import lvl_buttons
from src.helpers import transform_challenge_string

from src.codewars_api_get import Codewars_Challenges
from src.database import Database

from src.keyboardButtons import keyboard_buttons


class BotHandlers():
    def __init__(self, bot):
        load_dotenv()
        self.admin_ids = os.getenv("ADMIN_IDS")
        self.admin_ids = self.admin_ids.split(",")

        self.bot = bot

        self.parse_mode = "Markdown"
        self.messages = MESSAGES

        self.database = Database()
        self.codewars_api = Codewars_Challenges()

        self.keyboard_buttons = keyboard_buttons
    
    
    def start_handlers(self):
        self.start_command()
        self.check_stats_command() 
        self.get_username_command()
        self.random_task_command()
        self.find_task_command()
        self.load_challenges_command()
        self.handle_random_text() 
        self.create_keyboard()
        
    def create_keyboard(self):
        # ! ДОБАВИЛ КНОПКИ ВРОДЕ НО ИХ ЕЩЕ НЕТУ
        # * КОГДА ДОБАВЛЯЕТЕ НОВУЮ КОММАНДУ В KEYBOARDBUTTON СТАРАЙТЕСЬ РАВНОМЕРНО ДЕЛАТЬ (ОДНА СТРОЧКА С MARKUP.ADD ЭТО ОДНА ГОРИЗОНТАЛЬНАЯ ГРУПА)
        self.markup = types.ReplyKeyboardMarkup(resize_keyboard=True) 
        
        self.markup.add(self.keyboard_buttons["get_username"], self.keyboard_buttons["check_stats"], self.keyboard_buttons["random_task"])
        self.markup.add(self.keyboard_buttons["find_task"], self.keyboard_buttons["load_task"], self.keyboard_buttons["random_lvltask"])
        self.markup.add(self.keyboard_buttons["help"])

    def command_use_log(self, command, tg_user, chat_id):
        for value in self.admin_ids: 
            if str(chat_id) == str(value):
                pass
            else:
                self.bot.send_message(value, f"Пользователь {tg_user} перешёл в раздел {command}")

    def start_command(self):
        """Запускаем бота, а также добавляет пользователя в базу данных, если его там нет"""
        @self.bot.message_handler(commands=["start"], func=lambda message: True)
        def echo_all(message):
            #? Предлагаю на /start сразу просить человека создать / привязать аккаунт из Codewars и ввести свой user_name из Codewars в бот. 
            #? Так у нас сразу на руках будет юзернейм и команда для её привязки не будет нужна (ведь, по сути, весь наш функционал завязан именно на привязке к аккаунту Кодварс)
            
            username = message.from_user.username
            text = self.messages["start_bot"].format(username)
            
            print("user chat id:", message.chat.id)
            self.bot.send_message(message.chat.id, text) 
             
            self.command_use_log("/start", username, message.chat.id)
            
            #? Ещё на старте бота предлагаю добавить отправку сообщения админам, мол,
            #? "бот запущен и ждёт команд, нажми /start"
            
            
    def check_stats_command(self): 
        @self.bot.message_handler(commands=["check_stats"])
        def check_stats(message):
            bot_message = self.bot.send_message(
                chat_id=message.chat.id, 
                text=self.messages["ask_codewars_username"], 
                parse_mode=self.parse_mode
            )
            username = message.from_user.username
            self.command_use_log("/check_stats", username, message.chat.id)
            self.bot.register_next_step_handler(message=bot_message, callback=self.check_stats_response)


    def check_stats_response(self, message):
        tg_username = message.from_user.username
        try:
            user_stats = self.codewars_api.check_user_stats(message.text, tg_username)
            self.bot.reply_to(message, user_stats)
        except:
            self.bot.reply_to(message, self.messages["check_stats_error"])
        
        
    def get_username_command(self):
        """Дает возможность взять свой юзернейм"""
        @self.bot.message_handler(commands=["getusername"])
        def get_user_name(message):
            username = message.from_user.username
            text = self.messages["tg_username"].format(username) 
            self.bot.reply_to(message, text) 
            self.command_use_log("/getusername", username, message.chat.id)


    def random_task_command(self):
        @self.bot.message_handler(commands=['random_task'])
        def random_task_level_pick(message: Message):   
            markup = quick_markup(values=lvl_buttons, row_width=2)
            self.bot.send_message(message.chat.id, self.messages["random_task_level_pick"], reply_markup=markup)
            username = message.from_user.username
            self.command_use_log("/random_task", username, message.chat.id)


        """случайная задача из коллекции"""
        @self.bot.callback_query_handler(func=lambda call: True)
        def random_task(call):
            chat_id = call.message.chat.id

            level = call.data.replace('_', ' ')

            text = self.messages["random_task_on_screen_answer"].format(level)
            self.bot.answer_callback_query(call.id, text)

            filter = [
                {"$match": {"Rank.name": level}},
                {"$sample": {"size": 1}}
            ]

            # Random task from database by level
            result = list(self.database.challenges_collection.aggregate(filter))

            if result:
                challenge = result[0]

                bot_reply = (
                    f"Challenge name: {challenge['Challenge name']}\n\n"
                    f"Description: {challenge['Description']}\n\n"
                    f"Rank: {challenge['Rank']['name']}\n\n"
                    f"Codewars link: {challenge['Codewars link']}"
                )
                text = self.messages["random_task_found"].format(level, bot_reply)

                self.bot.send_message(chat_id, text)
            else:
                self.bot.send_message(chat_id, self.messages["random_task_not_found"])


    def find_task_command(self):
        """Поиск задачи из кодварса по названию"""
        @self.bot.message_handler(commands=['find_task'])
        def echo(message):
            bot_message = self.bot.send_message(
                chat_id=message.chat.id, 
                text=self.messages["find_task_ask_name"], 
                parse_mode=self.parse_mode
            )
            username = message.from_user.username
            self.command_use_log("/find_task", username, message.chat.id)
            self.bot.register_next_step_handler(message=bot_message, callback=self.find_task_response)


    def find_task_response(self, message):
        result = transform_challenge_string(message)
        challenge = self.codewars_api.get_challenge_info_by_slug(result)  
        if challenge == 404:
            self.bot.reply_to(message, self.messages["find_task_not_found"])
        else:
            text = self.messages["find_task_found"].format(challenge["Challenge name"], challenge["Description"], list(challenge["Rank"].values())[1], challenge["Codewars link"])
            filter = {"Slug": result}
            challenge_check = self.database.challenges_collection.find_one(filter)
            print(challenge_check)
            if challenge_check:
                print("Такая задача уже есть в базе данных, поэтому она не была добавлена в базу.")
            else:
                self.database.challenges_collection.insert_one(challenge)
            self.bot.reply_to(message, text)

           
    def load_challenges_command(self):
        """ load tasks from another user, saves them to db """
        @self.bot.message_handler(commands=['load_tasks'])
        def load_tasks(message: Message):            
            bot_message = self.bot.send_message(
                chat_id=message.chat.id, 
                text=self.messages["load_challenges_intro"], 
                parse_mode=self.parse_mode
            )
            username = message.from_user.username
            self.command_use_log("/load_tasks", username, message.chat.id)
            self.bot.register_next_step_handler(message=bot_message, callback=self.load_challenges_final_step)
                
                
    def load_challenges_final_step(self, message: Message):
        username = message.text
        print("🐍 CD user_name (load_tasks_send_request)", username)
        
        # send request to API
        user_challenges_URL = f"https://www.codewars.com/api/v1/users/{username}/code-challenges/completed" 
        
        try:
            response = get(url=user_challenges_URL)
            data_from_api = response.json()
            # try:
            challenges_count = data_from_api["totalItems"] 
            # except:
            #     self.bot.send_message(message.chat.id, )
            
            bot_reply_text = self.messages["load_challenges_count"].format(challenges_count,username)
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
                        
                        
            bot_final_message_text = self.messages["load_challenges_final"].format(challenges_count) 
                    
            self.bot.send_message(
                chat_id=message.chat.id, 
                text=bot_final_message_text, 
                parse_mode=self.parse_mode
            )
        except:
            self.bot.send_message(
                chat_id=message.chat.id, 
                text=self.messages["load_tasks_error"], 
                parse_mode=self.parse_mode
            )


    def handle_random_text(self):
        """эта функция принимает текст от пользователя, формирует slug, и находит такую задачу в кодварсе"""
        @self.bot.message_handler(func=lambda message: True)
        def handle_text(message):
            self.bot.send_message(message.chat.id, self.messages["random_text_reply"])     
    # сделать так, чтобы при отправке абракадабры от пользователя - он получал рандомную цитату из массива, чтобы читал побольше и не писал хуйню боту