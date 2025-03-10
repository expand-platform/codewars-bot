from telebot import types

normal_mode_buttons = {
    "authorize": types.KeyboardButton("Reauthorize ⚙"),
    "check_stats": types.KeyboardButton("Check stats 🏅"),
    "random_task": types.KeyboardButton("Random task 🥋"),
    "find_task": types.KeyboardButton("Find task 🔍"),
    "story_mode": types.KeyboardButton("Change mode 🔄"),
    "random_lvltask": types.KeyboardButton("Random task and lvl 🎲"),
    "help": types.KeyboardButton("Help ❔"),
    "language": types.KeyboardButton("Language 🌐")
}

story_mode_buttons = {
    "receive_task": types.KeyboardButton("Receive Mission"),
    "check_level": types.KeyboardButton("Check Rank"),
    "normal_mode": types.KeyboardButton("Change Mode 🔄"),
}