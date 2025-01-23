from requests import get
from dotenv import load_dotenv
import os 
import html2text

from telebot import types, TeleBot, custom_filters
from telebot.types import BotCommand, Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telebot.util import quick_markup

from src.messages_eng import MESSAGES_ENG
from src.messages_ukr import MESSAGES_UKR
from src.messages_rus import MESSAGES_RUS
from src.inline_buttons import lvl_buttons, lang_buttons
from src.helpers.helpers import Helpers

from src.codewars_api_get import Codewars_Challenges
from src.database import Database

from src.keyboardButtons import keyboard_buttons

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

import time
import random

# с кнопками есть баги, клава иногда не появляется, по фикшу на уроке

class AccessLevel(custom_filters.AdvancedCustomFilter): 
    key='access_level'
    @staticmethod
    def check(message, levels):
        username = message.from_user.username
        access_level = Database().get_user_access(username)
        return access_level in levels

        
class BotHandlers():
    def __init__(self, bot):
        load_dotenv()
        self.admin_ids = os.getenv("ADMIN_IDS") 
        self.admin_ids: list[str] = self.admin_ids.split(",") 

        self.bot: TeleBot = bot

        self.parse_mode = "Markdown"
        self.eng_language = MESSAGES_ENG
        self.rus_language = MESSAGES_RUS
        self.ukr_language = MESSAGES_UKR

        self.database = Database()
        self.codewars_api = Codewars_Challenges()
        self.helpers = Helpers()

        self.keyboard_buttons = keyboard_buttons
        
        self.markup = None
        
    
    
    def start_handlers(self):
        self.start_command()
        self.admin_start()
        self.load_tasks_command()
        self.handle_random_text() 
        
    def create_keyboard(self):
        # * КОГДА ДОБАВЛЯЕТЕ НОВУЮ КОММАНДУ В KEYBOARDBUTTON СТАРАЙТЕСЬ РАВНОМЕРНО ДЕЛАТЬ (ОДНА СТРОЧКА С MARKUP.ADD ЭТО ОДНА ГОРИЗОНТАЛЬНАЯ ГРУПА)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True) 
        
        markup.add(self.keyboard_buttons["random_task"], self.keyboard_buttons["check_stats"])
        markup.add(self.keyboard_buttons["random_lvltask"], self.keyboard_buttons["find_task"], self.keyboard_buttons["story_mode"])
        markup.add(self.keyboard_buttons["authorize"], self.keyboard_buttons["language"], self.keyboard_buttons["help"])
        
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
        ask_lang_message = self.lang("change_language", username)
        sent_message = self.bot.send_message(message.chat.id, ask_lang_message, reply_markup=markup)

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
            
            self.bot.delete_message(call.message.chat.id, sent_message.message_id)
            # Отправляем сообщение о смене языка
            self.bot.send_message(call.message.chat.id, bot_message)
            
            user = self.database.users_collection.find_one({"tg_username": username})
            if user['cw_nickname'] == "None":
                self.authorization(message)
            
       
            
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
        

    def start(self, message):
            markup = self.create_keyboard()
            
            username = message.from_user.username
            self.database.new_user(username, "None")

            self.lang_change(message)

            bot_message = self.lang("start_bot", username)
            text = bot_message.format(username)
            
            print("user chat id:", message.chat.id)

            self.command_use_log("/start", username, message.chat.id)

    def start_command(self):
        """Запускаем бота, а также добавляет пользователя в базу данных, если его там нет"""
        @self.bot.message_handler(commands=["start"], func=lambda message: True) 
        def echo(message):
            self.start(message)
      
    
    def authorization(self, message):
        username = message.from_user.username
        img_path = "src/images/nickname_example.png"
        normalised_img_path = os.path.normpath(img_path)
        self.command_use_log("/authorize", username, message.chat.id)
        
        markup =  InlineKeyboardMarkup()
        cw_signin_page_button = InlineKeyboardButton(self.lang("codewars_signin_button", username), url="https://www.codewars.com/users/sign_in")
        markup.add(cw_signin_page_button)
        
        self.bot.send_photo(message.chat.id, open(normalised_img_path, "rb"), caption=self.lang("nickname_example", username))

        bot_message = self.bot.send_message(
            chat_id=message.chat.id,
            text=self.lang("asking_cwusername", username),
            parse_mode=self.parse_mode,
            reply_markup=markup
        )
        
        self.bot.register_next_step_handler(message=bot_message, callback=self.authorization_ans)
        
    def authorization_ans(self, message):
        markup = self.create_keyboard()
        username = message.from_user.username
        
        filter = {"tg_username": username}
        user = self.database.users_collection.find_one(filter) 
        user_info = self.codewars_api.getuser_function(message.text, username)
        
        if "reason" in user_info:
            print("USER ISN'T FOUND")
            self.authorization(message)
            # self.bot.send_message(message.chat.id, self.lang("authorization_error", username))
        
        else:
            bot_reply = self.lang("successful_authorization", username)
            
            cw_username = user_info["username"]
            honor_lvl = user_info["honor"]
            tasks_done = user_info['codeChallenges']['totalCompleted']
            
            message_text = bot_reply.format(cw_username, honor_lvl, tasks_done)
            
        
            self.database.update_codewars_nickname(username, cw_username)
            self.bot.send_message(message.chat.id, message_text, reply_markup=markup)
            
            if user["totalDone_snum"] == None:
                self.record_first_info(message.text, username, filter)
        
    def record_first_info(self, cw_username, username, filter):
        user = self.codewars_api.getuser_function(cw_username, username) 
        update = {"$set": {"totalDone_snum": user["codeChallenges"]["totalCompleted"]}}
        
        self.database.users_collection.update_one(filter, update, upsert=False)
        
        
    def check_stats_command(self, message): 
            username = message.from_user.username
            
            filter = {"tg_username": username}
            user = self.database.users_collection.find_one(filter)
            
            if user["cw_nickname"] == "None": 
                print("USER DOESN'T HAVE CW ACC")
                message_format = self.lang("ask_codewars_username", username)
                bot_message = self.bot.send_message(
                    chat_id=message.chat.id, 
                    text=message_format, 
                    parse_mode=self.parse_mode
                )
                self.bot.register_next_step_handler(message=bot_message, callback=lambda msg:self.check_stats_response(message, msg.text))
                
            else:
                print("USER HAS CW ACC")
                self.check_stats_response(message, user["cw_nickname"])

            self.command_use_log("/check_stats", username, message.chat.id)

    def check_stats_response(self, message, cw_nickname):
        tg_username = message.from_user.username

        self.database.update_codewars_nickname(tg_username, cw_nickname)
        
        try:
            user_stats = self.codewars_api.check_user_stats(cw_nickname, tg_username)    
            self.bot.reply_to(message, user_stats)
        except:
            bot_message = self.lang("check_stats_error", tg_username)
            self.bot.reply_to(message, bot_message)

    
    
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
    
    def story_mode(self, message):
        username = message.from_user.username
        
        filter = {"tg_username": username}
        user = self.database.users_collection.find_one(filter) 
        
        if user["story_mode"] == False:
            update = {"$set": {"story_mode": True}}
            
        else: 
            update = {"$set": {"story_mode": False}}
            
        self.database.users_collection.update_one(filter, update, upsert=False)
        user = self.database.users_collection.find_one(filter)
        
        return user["story_mode"]
        
        
        

    
     





    def random_level_and_task(self, message):
        
        username = message.from_user.username
        chat_id = message.chat.id
        
        # достать кв никнейм по тг юзеру
        tguser_filter = {"tg_username": username}
        user = self.database.users_collection.find_one(tguser_filter)        
        codewars_name = user["cw_nickname"]

        # статы юзера
        stats = self.codewars_api.getuser_function(codewars_name, username)
        task_difference = stats["codeChallenges"]["totalCompleted"] - user["totalDone_snum"]
         
        if task_difference < 3:
            needs_to_be_done = 3 - task_difference
            
            self.bot.send_message(message.chat.id, self.lang("no_lvl_access", username).format(needs_to_be_done)) 
            
        else:
            # остальной код
            
            self.bot.send_dice(message.chat.id, emoji="🎲")
            self.command_use_log("/random_level_and_task", username, message.chat.id)
            
            challenges = list(self.database.challenges_collection.find({}))
            random_task = random.choice(challenges)
            
            self.challenge_print(random_task, username, chat_id, True)
        

            messages = [
            self.lang("task_name", username).format(random_task["Challenge name"]),
            self.lang("task_description", username).format(random_task['Description']),
            self.lang("task_rank", username).format(random_task['Rank']['name']),
            self.lang("task_url", username).format(random_task['Codewars link']),
            ]

            time.sleep(4)
            
            for i in messages:        
                check = self.helpers.tg_api_try_except(i, username)
                if check == "OK":
                    self.bot.send_message(chat_id, i, parse_mode=self.parse_mode)
                elif check == "TOO_LONG":
                    text = self.lang("message_is_too_long", username)
                    print(text)
                    self.bot.send_message(chat_id, text, parse_mode=self.parse_mode)
        

    def get_ranks(self, message):
        ranks = []
        
        for button in lvl_buttons:
            print("BUTTON: ", button)
            # ranks.append(button)


# ! иногда есть ошибка Bad requsest, message is too long
    def random_task_command(self, message):
        markup = quick_markup(values=lvl_buttons, row_width=2)
        # self.get_ranks(message)
        
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

                print("kata name:", challenge["Challenge name"])
                self.challenge_print(challenge, username, chat_id, False)
                    
                # также разделять описание на куски, если оно слишком длинное (для избежания 400 ошибки) 
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
            check = self.helpers.tg_api_try_except(i, username) 

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
        

    def find_task_response(self, message):
        username = message.from_user.username
        chat_id = message.chat.id
        result = self.helpers.transform_challenge_string(message)
        challenge_api = self.codewars_api.get_challenge_info_by_slug(result)  

        if challenge_api == 404:
            bot_message = self.lang("find_task_not_found", username)
            self.bot.reply_to(message, bot_message)
        else:
            filter = {"Slug": result}
            challenge_database = self.database.challenges_collection.find_one(filter)
            if challenge_database:

                self.challenge_print(challenge_database, username, chat_id, False)
            else:
                self.database.challenges_collection.insert_one(challenge_api)
            
                self.challenge_print(challenge_api, username, chat_id, False)
            # TODO: проверять длину только у описания
                


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
            
    def load_tasks_command(self):
        @self.bot.message_handler(commands=["load_tasks"], access_level=["admin"], func=lambda message: True) 
        def echo(message):
            self.load_challenges_command(message)
                
    def load_challenges_final_step(self, message: Message):
        username = message.from_user.username
        cw_username = message.text
        print("🐍 CD user_name (load_tasks_send_request)", cw_username)
        
        # send request to API
        user_challenges_URL = f"https://www.codewars.com/api/v1/users/{cw_username}/code-challenges/completed" 
        
        try:
            response = get(url=user_challenges_URL)
            data_from_api = response.json()
            total_pages = data_from_api["totalPages"] 
            challenges_count = data_from_api["totalItems"] 

            bot_message = self.lang("load_challenges_count", username)   
            bot_reply_text = bot_message.format(challenges_count,cw_username)
            
            self.bot.send_message(
                chat_id=message.chat.id, 
                text=bot_reply_text, 
                parse_mode=self.parse_mode
            )
            print("total pages:", total_pages)
            for i in range(total_pages):
                print(f'cycle number: {i}')
                
                user_challenges_URL_specific_page = f"https://www.codewars.com/api/v1/users/{cw_username}/code-challenges/completed?page={i}" 
                response = get(url=user_challenges_URL_specific_page)
                data_from_api = response.json()
           
                user_challenges = data_from_api["data"]
            
                for challenge in user_challenges:
                    challenge_slug = challenge["slug"]
                    
                    this_challenge_exists = self.database.is_challenge_in_db(challenge_slug=challenge_slug)
                    # if this_challenge_exists:
                    #     print(f"🐍 challenge {challenge_slug} already exists ❌")
                    # else: 
                    #     print(f"🐍 challenge {challenge_slug} added to the database ✅")
                        
                    
                    if not this_challenge_exists:
                        challenge_info = self.codewars_api.get_challenge_info_by_slug(slug=challenge_slug)
                    
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
    def admin_test(self, message):
        self.bot.reply_to(message, "Only admin can see this message!\n\nHere is a list of admin commands:\n/load_tasks")
        
    def admin_start(self):
        @self.bot.message_handler(commands=["admin"], access_level=["admin"]) 
        def admin(message):
            self.admin_test(message)

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
            
            elif message.text == "Story mode 🏕":
                self.story_mode(message)
                
            elif message.text == "Random task and lvl 🎲":
                self.random_level_and_task(message)
            
            elif message.text == "Language 🌐":
                self.lang_change(message)
        
            elif message.text == "Help ❔":
                username = message.from_user.username
                self.command_use_log("/help", username, message.chat.id)
                bot_message = self.lang("help", username)  
                self.bot.send_message(message.chat.id, bot_message)
                
            elif message.text == "Reauthorize ⚙":
                self.authorization(message)
            
            else:
                username = message.from_user.username
                bot_message = self.lang("random_text_reply", username) 
                self.bot.send_message(message.chat.id, bot_message)      
    # сделать так, чтобы при отправке абракадабры от пользователя - он получал рандомную цитату из массива, чтобы читал побольше и не писал хуйню боту