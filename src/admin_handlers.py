from telebot import TeleBot
from telebot.types import Message
from requests import get

from src.codewars_api_get import Codewars_Challenges
from src.database import Database
from src.helpers.helpers import Helpers

class Admin():
    def __init__(self, bot: TeleBot):
        self.bot = bot

        self.database = Database()
        self.codewars_api = Codewars_Challenges()
        self.helpers = Helpers(self.bot)

        self.parse_mode = "Markdown"
    
    def start_admin_handlers(self):
        self.admin_commands_start()
        self.load_tasks_command()


    def admin_commands_start(self):
        @self.bot.message_handler(commands=["admin"], access_level=["admin"]) 
        def admin(message):
            self.bot.send_message(message.chat.id, "Only admin can see this message!\n\nHere is a list of admin commands:\n/load_tasks", parse_mode=self.parse_mode)

    def load_tasks_command(self):
        @self.bot.message_handler(commands=["load_tasks"], access_level=["admin"], func=lambda message: True) 
        def echo(message):
            """ load tasks from another user, saves them to db """  

            username = message.from_user.username
            self.command_use_log("/load_tasks", username, message.chat.id)
            message_format = self.helpers.lang("load_challenges_intro", username)     

            bot_message = self.bot.send_message(
                chat_id=message.chat.id, 
                text=message_format, 
                parse_mode=self.parse_mode
            )

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
            total_pages = data_from_api["totalPages"] 
            challenges_count = data_from_api["totalItems"] 

            bot_message = self.helpers.lang("load_challenges_count", username)   
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
                            
                    if not this_challenge_exists:
                        challenge_info = self.codewars_api.get_challenge_info_by_slug(slug=challenge_slug)
                    
                        if challenge:
                            self.database.save_challenge(new_challenge=challenge_info)
                            
            bot_message = self.helpers.lang("load_challenges_final", username)   
            bot_final_message_text = bot_message.format(challenges_count) 
                    
            self.bot.send_message(
                chat_id=message.chat.id, 
                text=bot_final_message_text, 
                parse_mode=self.parse_mode
            )
        except:
            bot_message = self.helpers.lang("load_tasks_error", username) 
            self.bot.send_message(
                chat_id=message.chat.id, 
                text=bot_message, 
                parse_mode=self.parse_mode
            )