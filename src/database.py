from typing import Union
from pymongo import MongoClient
from pymongo.collection import Collection
import os
import dotenv

class Database:
    def __init__(self):
        # Коннект к базе
        dotenv.load_dotenv()
        connect = os.getenv("MONGO_CONNECT")
        self.client = MongoClient(connect)

        database_name = "codewars_bot"
        
        self.database = self.client[database_name]
        
        self.users_collection: Collection = self.database['users']
        self.challenges_collection: Collection = self.database['challenges']

    def new_user(self, username: str, cw_login: str):
        """Функция создаёт нового юзера, сюда кидаем юзернейм и его уровень (скорее всего уровень будет 0, так как пользователь новый)
        cw = code wars
        """
        
        tguser_filter = {"tg_username": username}
        user = self.users_collection.find_one(tguser_filter)
        if user:
            print(f"Пользователь с юзернеймом {username} уже существует.")
        else:
            document = {"tg_username": username, "cw_nickname": cw_login, "desired_language": "ENG", "access_level": "user", "totalDone_snum": None}
            self.users_collection.insert_one(document)
            print(f"Создан пользователь с юзернеймом {username}.")

    def update_codewars_nickname(self, username: str, cw_login: str):
        filter = {"tg_username": username}
        update = {"$set": {"cw_nickname": cw_login}}
        self.users_collection.update_one(filter, update, upsert=False)
        print(f"Пользователю {username} привязан никнейм {cw_login} на кодварс.")

    def update_user_language(self, username: str, lang: str):
        filter = {"tg_username": username}
        update = {"$set": {"desired_language": lang}}
        self.users_collection.update_one(filter, update, upsert=False)
        print(f"Пользователю {username} привязан {lang} язык")

    def pull_user_lang(self, username: str):
        """Эта функция находит данные пользователя (например уровень), имея только юзернейм, в эту функцию нужно кидать только юзернейм"""
        filter = {"tg_username": username}
        user = self.users_collection.find_one(filter) 

        # Проверка, найден ли пользователь
        if user:
            lang = user.get("desired_language")
            return lang
        else:
            print(f"Пользователь с именем '{username}' не найден в базе данных.")
            return
    
    def is_challenge_in_db(self, challenge_slug) -> Union[dict, None]:
        """ return None if no challenge exists """
        return self.challenges_collection.find_one(filter={"Slug": challenge_slug})

    def save_challenge(self, new_challenge):
        self.challenges_collection.insert_one(new_challenge)
        print("challenge added to db!")
        
    def get_user_access(self, username: str):
        tguser_filter = {"tg_username": username}
        user = self.users_collection.find_one(tguser_filter)
        
        if user:
            access_level = user.get("access_level")
            print("Уровень доступа пользователя: ", access_level)
            return access_level
        else:
            print(f"Пользователь с именем '{username}' не найден в базе данных.")
            return f"Пользователь с именем '{username}' не найден в базе данных."