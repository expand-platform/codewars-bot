import re

"""обрабатываем сообщение пользователя и формирует slug"""
def transform_challenge_string(message):
    user_input = message.text
    remove_unnesecary_symbols = re.sub(r"[!?,.:;\-_`'\"/|\\]", " ", user_input)
    slug_transform = remove_unnesecary_symbols.split()
    result = "-".join(slug_transform)
    lowercase_result = result.lower()
    return lowercase_result