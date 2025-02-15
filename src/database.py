from typing import Union
from pymongo import MongoClient
from pymongo.collection import Collection
from src.helpers.Dotenv import Dotenv
from telebot.types import Message
from bson import ObjectId
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from threading import Timer

class Database:
    def __init__(self):
        # Коннект к базе
        connect = Dotenv().mongodb_string
        self.client = MongoClient(connect)

        database_name = "codewars_bot"
        
        self.database = self.client[database_name]
        
        self.users_collection: Collection = self.database['users']


        self.challenges_collection: Collection = self.database['challenges']
        self.analytics: Collection = self.database['analytics']
        
    def date_to_date_analystics(self):
        doc_id = "67ae1e0b83699d5a8115cfc0"
        document = self.analytics.find_one({"_id": ObjectId(doc_id)})
        current_date = datetime.now(timezone.utc)
        month_before = current_date - relativedelta(month=1)
        update = {"$set": {"starting_date": month_before}}
        
        self.analytics.update_one({"_id": ObjectId(doc_id)}, update)
        Timer(10, self.date_to_date_analystics).start()


        


        print("CURRENT: ", current_date, " MONTH BEFORE: ", month_before)
        

        


    def stat_update(self, command):
        self.date_to_date_analystics()

        doc_id = "679f4042d631b228c70a5faf" 
        document = self.analytics.find_one({"_id": ObjectId(doc_id)}) # getting analytics document from database


        form = document.get(command) + 1 # finding the used command in the document and adding 1 as user used it
        update1 = {"$set": {command: form}} # variable to update data
        self.analytics.update_one({}, update1, upsert=False) # updating the command in the file

        count_users = self.users_collection.count_documents({}) # counts how many documents there are in an user collection in database
        update2 = {"$set": {"total_users": count_users}} # variable to update the number of users (just rewrites it, doesn't neccessary mean it's gonna add user or smth)
        self.analytics.update_one({}, update2, upsert=False) # updating data in database



    def show_analytics(self):
        document = self.analytics.find_one({})
        # Сообщение прижато к левому краю специально, так нужно
        message = f"""
total_users: {document.get("total_users")}

commands:

start: {document.get("/start")}
check_stats: {document.get("/check_stats")}
find_task: {document.get("/find_task")}
random_task: {document.get("/random_task")}
random_task_and_level: {document.get("/random_task_and_level")}
story_mode: {document.get("/story_mode")}
language: {document.get("/language")}
help: {document.get("/help")}
reauthorize: {document.get("/reauthorize")}
            """

        return message

    def new_user(self, username: str, cw_login: str, message: Message):
        """Функция создаёт нового юзера, сюда кидаем юзернейм и его уровень (скорее всего уровень будет 0, так как пользователь новый)
        cw = code wars
        """
        chat_id = message.chat.id
        user_id = message.from_user.id
        user_id_filter = {"user_id": user_id}

        user = self.users_collection.find_one(user_id_filter)

        if user:
            print(f"Пользователь с чат айди {chat_id} уже существует.")

        else:
            document = {"tg_username": username, 
                        "chat_id": chat_id, 
                        "user_id": user_id, 
                        "cw_nickname": cw_login, 
                        "desired_language": "ENG", 
                        "access_level": "user", 
                        "totalDone_snum": None, 
                        "story_mode": False}
            self.users_collection.insert_one(document)
            print(f"Создан пользователь с юзернеймом {username}.")

    def update_codewars_nickname(self, message: Message, cw_login: str):
        user_id = message.from_user.id
        username = message.from_user.username
        filter = {"user_id": user_id}
        update = {"$set": {"cw_nickname": cw_login}}
        self.users_collection.update_one(filter, update, upsert=False)
        print(f"Пользователю {username} привязан никнейм {cw_login} на кодварс.")

    def update_user_language(self, message: Message, lang: str):
        user_id = message.from_user.id
        username = message.from_user.username
        filter = {"user_id": user_id}
        update = {"$set": {"desired_language": lang}}
        self.users_collection.update_one(filter, update, upsert=False)
        print(f"Пользователю {username} привязан {lang} язык")

    def pull_user_lang(self, message: Message):
        """Эта функция находит данные пользователя (например уровень), имея только юзернейм, в эту функцию нужно кидать только юзернейм"""
        user_id = message.from_user.id
        username = message.from_user.username
        filter = {"user_id": user_id}
        user = self.users_collection.find_one(filter) 


        # Проверка, найден ли пользователь
        if user:
            lang = user.get("desired_language")
            return lang
        else:
            print(f"Пользователь с именем '{username}' не найден в базе данных.")
            return
        
    def pull_user_cw_nickname(self, message: Message):
        """Эта функция находит данные пользователя (например уровень), имея только юзернейм, в эту функцию нужно кидать только юзернейм"""
        user_id = message.from_user.id
        username = message.from_user.username
        filter = {"user_id": user_id}
        user = self.users_collection.find_one(filter) 

        # Проверка, найден ли пользователь
        if user:
            cw_nickname = user.get("cw_nickname")
            return cw_nickname
        else:
            print(f"Пользователь с именем '{username}' не найден в базе данных.")
            return
    
    def is_challenge_in_db(self, challenge_slug) -> Union[dict, None]:
        """ return None if no challenge exists """
        return self.challenges_collection.find_one(filter={"Slug": challenge_slug})

    def save_challenge(self, new_challenge):
        self.challenges_collection.insert_one(new_challenge)
        print("challenge added to db!")
        
    def get_user_access(self, message: Message):
        user_id = message.from_user.id
        username = message.from_user.username
        tg_user_filter = {"user_id": user_id}
        user = self.users_collection.find_one(tg_user_filter)
        
        if user:
            access_level = user.get("access_level")
            print("Уровень доступа пользователя: ", access_level)
            return access_level
        else:
            print(f"Пользователь с именем '{username}' не найден в базе данных.")
            return f"Пользователь с именем '{username}' не найден в базе данных."