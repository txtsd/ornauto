import logging

import toml
from account import OrnaAccount
from grind_at_home import GrindAtHome

# Setup logs
logger = logging.getLogger('ornauto')
logger.setLevel(logging.DEBUG)
fileHandler = logging.FileHandler('debug.log')
fileHandler.setLevel(logging.WARNING)
consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(logging.INFO)
logFormat = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fileHandler.setFormatter(logFormat)
consoleHandler.setFormatter(logFormat)
logger.addHandler(fileHandler)
logger.addHandler(consoleHandler)

# Read config
logger.debug('Reading config.toml')
with open('config.toml') as f:
    config_file = f.read()
    logger.debug('Finished reading config.toml')
    try:
        logger.debug('Parsing config.toml')
        configs = toml.loads(config_file)
        logger.debug('Finished parsing config.toml')
    except Exception as e:
        logger.error('Failed to parse config.toml!')

# Pick the first account
config = configs['account'][0]

# Login to the first account
account = OrnaAccount(config)
logger.debug('Logging in')
grind = GrindAtHome(account)
grind.firstRequests()
grind.idle()
# grind.arena_battle()
