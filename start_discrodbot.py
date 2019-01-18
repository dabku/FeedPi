import logging
from logging.handlers import RotatingFileHandler
import sys
from os import path, makedirs
from libs.discordbot import create_bot

if __name__ == '__main__':
    script_dir = path.dirname(path.realpath(sys.argv[0]))
    logger = logging.getLogger('libs.discordbot')
    logger.setLevel(logging.DEBUG)
    log_dir = path.join(script_dir, 'log')
    if not path.exists(path.join(script_dir, 'log')):
        makedirs(log_dir)

    handler = RotatingFileHandler(filename=path.join(log_dir, 'discord.log'),
                                  encoding='utf-8', maxBytes=1048576, backupCount=5)
    formatter = logging.Formatter(
        '%(asctime)s%(levelname)8s()|%(filename)s:%(lineno)s - %(funcName)s() - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    ch = logging.StreamHandler(sys.stdout)

    ch.setFormatter(formatter)
    logger.addHandler(ch)
    logger.info('run')

    bot = create_bot('discord_config.json')
    bot.start_bot()
