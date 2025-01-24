import re


"""обрабатываем сообщение пользователя и формирует slug"""
class Helpers():
    def __init__(self, ):
        pass
    
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

    def transform_challenge_string(self, message):
        user_input = message.text
        remove_unnesecary_symbols = re.sub(r"[!?,.:;\-_`'\"/|\\]", " ", user_input)
        slug_transform = remove_unnesecary_symbols.split()
        result = "-".join(slug_transform)
        lowercase_result = result.lower()
        return lowercase_result

    def tg_api_try_except(self, text: str, username: str, max_length=4095):
        if len(text) <= max_length: 
            return "OK"
        elif len(text) > max_length:
            return "TOO_LONG"

