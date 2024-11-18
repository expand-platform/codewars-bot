from telebot.types import BotCommand

commands = [
    BotCommand("start", "start bot"),
    BotCommand("getusername", "get your username"),
    BotCommand("check_stats", "check codewars user stats"),
    BotCommand("random_task", "find a random task"),
    BotCommand("find_task", "find codewars task by its name"),
    BotCommand("load_tasks", "add new tasks at a glance")
]