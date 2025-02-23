from telebot import types

from src.keyboardButtons import normal_mode_buttons, story_mode_buttons

def normal_mode_keyboard():
    """ Кнопки для обычного режима """
    # * КОГДА ДОБАВЛЯЕТЕ НОВУЮ КОММАНДУ В KEYBOARDBUTTON СТАРАЙТЕСЬ РАВНОМЕРНО ДЕЛАТЬ (ОДНА СТРОЧКА С MARKUP.ADD ЭТО ОДНА ГОРИЗОНТАЛЬНАЯ ГРУПА)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True) 
    
    markup.add(normal_mode_buttons["random_task"], normal_mode_buttons["check_stats"])
    markup.add(normal_mode_buttons["random_lvltask"], normal_mode_buttons["find_task"], normal_mode_buttons["story_mode"])
    markup.add(normal_mode_buttons["authorize"], normal_mode_buttons["language"], normal_mode_buttons["help"])
    
    return markup

def story_mode_keyboard():
    """ Кнопки для стори мода """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True) 
    markup.add(story_mode_buttons["receive_task"], story_mode_buttons["check_level"], story_mode_buttons["normal_mode"])
    return markup