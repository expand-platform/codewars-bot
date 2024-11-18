import telebot
from telebot import types

keyboard_buttons = {
    "get_username": types.KeyboardButton("Get your username"),
    "check_stats": types.KeyboardButton("Check stats"),
    "random_task": types.KeyboardButton("Random task"),
    "find_task": types.KeyboardButton("Find task"),
    "load_task": types.KeyboardButton("Load task"),
    "random_lvltask": types.KeyboardButton("Random task and lvl"),
    "help": types.KeyboardButton("Help")
    # ! help doesn't work for now
}