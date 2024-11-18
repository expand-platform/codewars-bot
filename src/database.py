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

        self.users_db = self.client['bot-users']
        self.users_collection: Collection = self.users_db['users']
        
        self.challenges_db = self.client['codewars-challenges']
        self.challenges_collection: Collection = self.challenges_db['challenges']

    def new_user(self, username: str, userlvl: int):
        """Функция создаёт нового юзера, сюда кидаем юзернейм и его уровень (скорее всего уровень будет 0, так как пользователь новый)"""
        filter = {"name": username}
        user = self.users_collection.find_one(filter)
        if user:
            print(f"Пользователь с юзернеймом {username} уже существует.")
        else:
            document = {"name": username, "lvl": userlvl}
            self.users_collection.insert_one(document)
            print(f"Создан пользователь с юзернеймом {username} и {userlvl} уровнем.")

    def update_user(self, username: str, userlvl: int):
        """Функция меняет пользователю уровень, сюда кидаем юзернейм и новый уровень для пользователя"""
        filter = {"name": username}
        update = {"$set": {"lvl": userlvl}}
        self.users_collection.update_one(filter, update, upsert=False)
        print(f"Пользователю {username} выдан {userlvl} уровень.")

    def pull_user(self, username: str):
        """Эта функция находит данные пользователя (например уровень), имея только юзернейм, в эту функцию нужно кидать только юзернейм"""
        filter = {"name": username}
        user = self.users_collection.find_one(filter)

        # Проверка, найден ли пользователь
        if user:
            lvl = user.get("lvl")
            print(f"Уровень пользователя {username} - {lvl}")
            return lvl
        else:
            print(f"Пользователь с именем '{username}' не найден в базе данных.")
            return
    
    def is_challenge_in_db(self, challenge_slug) -> Union[dict, None]:
        """ return None if no challenge exists """
        return self.challenges_collection.find_one(filter={"Slug": challenge_slug})

    def save_challenge(self, new_challenge):
        self.challenges_collection.insert_one(new_challenge)
        print("challenge added to db!")
