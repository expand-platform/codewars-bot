import re

"""обрабатываем сообщение пользователя и формирует slug"""
class Helpers():
    def __init__(self):
        pass

    def transform_challenge_string(self, message):
        user_input = message.text
        remove_unnesecary_symbols = re.sub(r"[!?,.:;\-_`'\"/|\\]", " ", user_input)
        slug_transform = remove_unnesecary_symbols.split()
        result = "-".join(slug_transform)
        lowercase_result = result.lower()
        return lowercase_result

    def split_message(self, text: str, max_length=4096):
        parts = []
        new_text = text
        if len(text) > max_length:
            split_index = text[:max_length].rfind('\n') 
            if split_index == -1:
                split_index = max_length
            parts.append(text[:split_index])
            new_text = text[split_index:].lstrip()
        parts.append(new_text)  
        print(parts)
        return parts
        # ! плохо сделано, потом перепишу, пока не трогать
        # попробовать метод split()