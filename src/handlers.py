from requests import get
from dotenv import load_dotenv
import os

from telebot import types, TeleBot
from telebot.types import BotCommand, Message, InlineKeyboardButton, InlineKeyboardMarkup
from telebot.util import quick_markup

from src.messages_eng import MESSAGES_ENG
from src.messages_ukr import MESSAGES_UKR
from src.messages_rus import MESSAGES_RUS
from src.inline_buttons import lvl_buttons
from src.helpers import transform_challenge_string

from src.codewars_api_get import Codewars_Challenges
from src.database import Database

from src.keyboardButtons import keyboard_buttons

# с кнопками есть баги, клава иногда не появляется, по фикшу на уроке

class BotHandlers():
    def __init__(self, bot):
        load_dotenv()
        self.admin_ids = os.getenv("ADMIN_IDS") 
        self.admin_ids = self.admin_ids.split(",")

        self.bot: TeleBot = bot

        self.parse_mode = "Markdown"
        self.language = MESSAGES_ENG

        self.database = Database()
        self.codewars_api = Codewars_Challenges()

        self.keyboard_buttons = keyboard_buttons
        
        self.markup = None
    
    
    def start_handlers(self):
        self.start_command()
        # self.check_stats_command() 
        # self.get_username_command()
        # self.random_task_command()
        # self.find_task_command()
        # self.load_challenges_command()
        self.handle_random_text() 
        
    def create_keyboard(self):
        # * КОГДА ДОБАВЛЯЕТЕ НОВУЮ КОММАНДУ В KEYBOARDBUTTON СТАРАЙТЕСЬ РАВНОМЕРНО ДЕЛАТЬ (ОДНА СТРОЧКА С MARKUP.ADD ЭТО ОДНА ГОРИЗОНТАЛЬНАЯ ГРУПА)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True) 
        
        markup.add(self.keyboard_buttons["get_username"], self.keyboard_buttons["check_stats"], self.keyboard_buttons["random_task"])
        markup.add(self.keyboard_buttons["find_task"], self.keyboard_buttons["load_task"], self.keyboard_buttons["random_lvltask"])
        markup.add(self.keyboard_buttons["help"])
        
        return markup
    
    def command_use_log(self, command, tg_user, chat_id):
        for value in self.admin_ids: 
            if str(chat_id) == str(value):
                pass
            else:
                self.bot.send_message(value, f"Пользователь @{tg_user} перешёл в раздел {command}")

    # def lang_check(self, message):
        

    def start(self, message):
            markup = self.create_keyboard()

            #? Предлагаю на /start сразу просить человека создать / привязать аккаунт из Codewars и ввести свой user_name из Codewars в бот. 
            #? Так у нас сразу на руках будет юзернейм и команда для её привязки не будет нужна (ведь, по сути, весь наш функционал завязан именно на привязке к аккаунту Кодварс)
            
            username = message.from_user.username
            self.database.new_user(username, "None")

            text = self.language["start_bot"].format(username)
            
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
            bot_message = self.bot.send_message(
                chat_id=message.chat.id, 
                text=self.language["ask_codewars_username"], 
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
            self.bot.reply_to(message, self.language["check_stats_error"])

# ! иногда есть ошибка Bad requsest, message is too long
    def random_task_command(self, message):
        markup = quick_markup(values=lvl_buttons, row_width=2)
        self.bot.send_message(message.chat.id, self.language["random_task_level_pick"], reply_markup=markup)
        username = message.from_user.username
        self.command_use_log("/random_task", username, message.chat.id)


        """случайная задача из коллекции"""
        @self.bot.callback_query_handler(func=lambda call: True)
        def random_task(call):
            chat_id = call.message.chat.id

            level = call.data.replace('_', ' ')

            text = self.language["random_task_on_screen_answer"].format(level)
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
                text = self.language["random_task_found"].format(level, bot_reply)

                self.bot.send_message(chat_id, text, parse_mode=self.parse_mode)
            else:
                self.bot.send_message(chat_id, self.language["random_task_not_found"])


    def find_task_command(self, message):
        """Поиск задачи из кодварса по названию"""
        bot_message = self.bot.send_message(
            chat_id=message.chat.id, 
            text=self.language["find_task_ask_name"], 
            parse_mode=self.parse_mode
        )
        username = message.from_user.username
        self.command_use_log("/find_task", username, message.chat.id)
        self.bot.register_next_step_handler(message=bot_message, callback=self.find_task_response)
 

    def find_task_response(self, message):
        result = transform_challenge_string(message)
        challenge = self.codewars_api.get_challenge_info_by_slug(result)  
        if challenge == 404:
            self.bot.reply_to(message, self.language["find_task_not_found"])
        else:
            text = self.language["find_task_found"].format(challenge["Challenge name"], challenge["Description"], list(challenge["Rank"].values())[1], challenge["Codewars link"])
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
        bot_message = self.bot.send_message(
            chat_id=message.chat.id, 
            text=self.language["load_challenges_intro"], 
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
            
            bot_reply_text = self.language["load_challenges_count"].format(challenges_count,username)
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
                        
                        
            bot_final_message_text = self.language["load_challenges_final"].format(challenges_count) 
                    
            self.bot.send_message(
                chat_id=message.chat.id, 
                text=bot_final_message_text, 
                parse_mode=self.parse_mode
            )
        except:
            self.bot.send_message(
                chat_id=message.chat.id, 
                text=self.language["load_tasks_error"], 
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
                self.bot.send_message(message.chat.id, "Not in service yet)))")
        
            elif message.text == "Help ❔":
                self.bot.send_message(message.chat.id, "No help, ur alone in this world)))")
             
            else:
                self.bot.send_message(message.chat.id, self.language["random_text_reply"])     
    # сделать так, чтобы при отправке абракадабры от пользователя - он получал рандомную цитату из массива, чтобы читал побольше и не писал хуйню боту