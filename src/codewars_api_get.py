import requests
from src.database import Database
from dotenv import load_dotenv
import os

class Codewars_Challenges:
    """инит (удивительно)"""
    def __init__(self):
        load_dotenv()
        self.bot_token = os.getenv("TOKEN_FOR_TGBOT")
        self.database = Database()

    def getuser_function(self, codewars_username: str, telegram_username: str):
        url = f"https://www.codewars.com/api/v1/users/{codewars_username}"
        response = requests.get(url)
        user = response.json()
        
        return user

    def check_user_stats(self, codewars_username: str, telegram_username: str):
        user = self.getuser_function(codewars_username, telegram_username)
        print("USER: ", user)
        
        if user["skills"] == []:
            skills = "No skills"
        
        else:
            skills = user["skills"]
        
        user_info = {
            "Codewars name": user["username"],
            "Telegram name": telegram_username,
            "Rank": user["ranks"]["overall"]["name"],
            "Honor": user["honor"],
            "Clan": user["clan"],
            "Leaderboard": user["leaderboardPosition"],
            "Skills": user["skills"],
            "Code challenges": user["codeChallenges"]
        }
        
        string_form = f"Codewars name: {user["username"]}\n\nTelegram name: {telegram_username}\n\nRank: {user["ranks"]["overall"]["name"]}\n\nHonor: {user["honor"]}\n\nClan: {user["clan"]}\n\nLeaderboard: {user["leaderboardPosition"]}\n\nSkills: {skills}\n\nCode challenges: {user["codeChallenges"]["totalCompleted"]}\n\nScore: {user["ranks"]["overall"]["score"]}"
        return string_form

    """функция для поиска задачи по уровню и языку"""
    def find_challenge(self):
        challenge = self.database.challenges_collection.aggregate([{"$sample": {"size": 1}}])
        for i in challenge:
            result = f"Here is a random codewars task:\n\nChallenge name: {i["Challenge name"]}\n\nDescription: {i["Description"]}\n\nRank: {list(i["Rank"].values())[1]}\n\nCodewars link: {i["Codewars link"]}"
            return result

    """достать инфу из конкретной задачи"""
    def get_challenge_info_by_slug(self, slug: str, language: str="any"):
        challenge_slug = slug
        url = f"https://www.codewars.com/api/v1/code-challenges/{challenge_slug}"
        response = requests.get(url)
        challenge_language = language

        if response.status_code == 200:
            # Получение данных о задаче
            challenge = response.json()

            # Вывод имени, описания и ссылки на задачу
            if challenge_language != "any":
                url = f"https://www.codewars.com/kata/{challenge['slug']}/train/{challenge_language}"
            else: 
                url = f"https://www.codewars.com/kata/{challenge['slug']}/train"
            
            challenge_info = {
                "Slug": challenge["slug"],
                "Challenge name": challenge['name'],
                "Description": challenge['description'],
                "Rank": challenge["rank"],
                "Codewars link": url
            }
            print("Slug:", challenge_info["Slug"], "\n" "Challenge name:", challenge_info["Challenge name"], "\n", "Description:", challenge_info["Description"], "\n", "Rank:", list(challenge_info["Rank"].values())[1], "\n", "Codewars link:", challenge_info["Codewars link"])
            return challenge_info
        else:
            print(f"Ошибка: {response.status_code}")
            return response.status_code

if __name__ == "__main__":
    cw = Codewars_Challenges()
    cw.get_challenge_info_by_slug("vowel-count")