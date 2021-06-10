import logging
import math
import random
import secrets
import time
from threading import Timer

import httpx
from colorama import Back, Fore, Style


class RepeatedTimer(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer = None
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.daemon = True
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False


class GrindAtHome:

    def __init__(self, account):
        self.account = account
        self.monsters = {}
        self.shops = {}
        self.area = {}
        # self.area_c = secrets.token_hex(6)
        self.area_c = self.account.config['area_c']
        self.notifications = {}
        self.friends = {}
        self.me = {}
        self.location = {'x': None, 'y': None}
        self.stashed_time = {}
        self.stashed_geo = {}
        self.inventory = {}
        self.hp_total = 0
        self.hp_current = 0
        self.mana_total = 0
        self.mana_current = 0
        self.gold = 0
        self.orns = 0
        self.light_bonus = False
        self.level = 0
        self.arena_do = False
        self.arena_time = time.time()
        self.clan_uuid = None
        self.clan = {}
        self.kingdom_raids_time = time.time()
        self.kingdom_raids_do = False

    # @staticmethod
    def nextLocation(self, distance):
        home_x = float(self.account.config['home_x'])
        home_y = float(self.account.config['home_y'])

        if distance == 'small':
            radius = 0.00001
        elif distance == 'medium':
            radius = 0.0001
        elif distance == 'big':
            radius = 0.0005
        else:
            radius = 0.000001

        random_alpha = 2 * math.pi * random.random()
        random_radius = radius * math.sqrt(random.random())
        new_x = random_radius * math.cos(random_alpha) + home_x
        new_y = random_radius * math.sin(random_alpha) + home_y

        new_x = round(new_x, 7)
        new_y = round(new_y, 7)

        return (new_x, new_y)

    # FirstRequests
    def firstRequests(self):
        logger = logging.getLogger('autorna.GrindAtHome.firstRequests')
        self.get_me()
        self.get_inventory(initial=True)
        self.account.get('/codex/completed/')
        logger.debug('/codex/completed/')
        self.get_friends(initial=True)
        self.get_area(initial=True)
        self.get_monsters(initial=True)
        self.get_shops(initial=True)
        self.account.get('/quests/daily/')
        logger.debug('/quests/daily/')
        self.get_notifications(initial=True)
        self.get_clan()

    def idle(self):
        logger = logging.getLogger('autorna.GrindAtHome.idle')
        exit = False
        rt_mon = RepeatedTimer(30, self.get_monsters)
        rt_shop = RepeatedTimer(30, self.get_shops)
        rt_notif = RepeatedTimer(60, self.get_notifications)
        rt_frnd = RepeatedTimer(120, self.get_friends)
        # rt_area = RepeatedTimer(60, self.get_area, 'small')
        rt_area = RepeatedTimer(60, self.get_area, 'small')
        rt_arena = RepeatedTimer(600, self.arena_check)
        rt_kingdom_raids = RepeatedTimer(600, self.kingdom_raids_check)
        while not exit:
            # pass
            time.sleep(random.uniform(1000, 4000) / 1000)
            if (random.uniform(0, 1000) > 975):
                sleep_time = random.uniform(30, 300)
                log_string = Fore.WHITE + Style.BRIGHT + 'Taking a break for {} minutes' + Style.RESET_ALL
                logger.info(log_string.format(round(sleep_time / 60, 2)))
                time.sleep(sleep_time)
            self.fight()
            self.grab_chests()
            if self.arena_do:
                self.arena_battle()
            if self.kingdom_raids_do:
                self.kingdom_raids_battle()

    def get_monsters(self, initial=False):
        logger = logging.getLogger('autorna.GrindAtHome.get_monsters')
        result_monsters = None
        if initial:
            logger_initial = logging.getLogger('autorna.GrindAtHome.firstRequests')
            logger_initial.debug('/monsters/')
            try:
                result_monsters = self.account.get('/monsters/', params={'i': 1}).json()
            except (httpx.UnsupportedProtocol, httpx.ReadError, httpx.RemoteProtocolError) as e:
                pass
        else:
            logger.debug('/monsters/')
            try:
                result_monsters = self.account.get('/monsters/').json()
            except (httpx.UnsupportedProtocol, httpx.ReadError, httpx.RemoteProtocolError) as e:
                pass
        if result_monsters is not None:
            if not result_monsters['success'] and result_monsters['throttled']:
                logger.debug('throttled')
            elif result_monsters['success'] and 'throttled' not in result_monsters:
                self.monsters = result_monsters

    def get_area(self, distance='small', initial=False):
        logger = logging.getLogger('autorna.GrindAtHome.get_area')
        loc_x, loc_y = self.nextLocation(distance)
        if initial:
            logger_initial = logging.getLogger('autorna.GrindAtHome.firstRequests')
            logger_initial.debug('/area/')
            try:
                result_area = self.account.get(
                    '/area/',
                    params={
                        'i': 1,
                        'latitude': loc_x,
                        'longitude': loc_y,
                        'm': 'false',
                        'c': self.area_c,
                    }
                ).json()
            except (httpx.UnsupportedProtocol, httpx.ReadError, httpx.RemoteProtocolError) as e:
                pass
        else:
            logger.debug('/area/')
            try:
                result_area = self.account.get(
                    '/area/',
                    params={
                        'latitude': loc_x,
                        'longitude': loc_y,
                        'm': 'false',
                        'c': self.area_c,
                    }
                ).json()
            except (httpx.UnsupportedProtocol, httpx.ReadError, httpx.RemoteProtocolError) as e:
                pass
        self.area = result_area

    def get_shops(self, initial=False):
        logger = logging.getLogger('autorna.GrindAtHome.get_shops')
        if initial:
            logger_initial = logging.getLogger('autorna.GrindAtHome.firstRequests')
            logger_initial.debug('/shops/')
            try:
                result_shops = self.account.get('/shops/', params={'i': 1}).json()
            except (httpx.UnsupportedProtocol, httpx.ReadError, httpx.RemoteProtocolError) as e:
                pass
        else:
            logger.debug('/shops/')
            try:
                result_shops = self.account.get('/shops/').json()
            except (httpx.UnsupportedProtocol, httpx.ReadError, httpx.RemoteProtocolError) as e:
                pass
        self.shops = result_shops

    def get_notifications(self, initial=False):
        logger = logging.getLogger('autorna.GrindAtHome.get_notifications')
        if initial:
            logger_initial = logging.getLogger('autorna.GrindAtHome.firstRequests')
            logger_initial.debug('/notifications/')
        else:
            logger.debug('/notifications/')
        try:
            result_notifications = self.account.get('/notifications/', params={'v': 2}).json()
        except (httpx.UnsupportedProtocol, httpx.ReadError, httpx.RemoteProtocolError) as e:
            pass
        if result_notifications and result_notifications['success']:
            if result_notifications['result'] != []:
                logger.info(Fore.YELLOW + result_notifications['result'][0]['items'][0]['title'] + Style.RESET_ALL)
                if 'subtitle' in result_notifications['result'][0]['items'][0]:
                    logger.info(Fore.YELLOW + result_notifications['result'][0]['items'][0]['subtitle'] + Style.RESET_ALL)
                if 'description' in result_notifications['result'][0]['items'][0]:
                    logger.info(Fore.YELLOW + result_notifications['result'][0]['items'][0]['description'] + Style.RESET_ALL)
                self.get_me()
                self.get_inventory()
        self.notifications = result_notifications

    def get_friends(self, initial=False):
        logger = logging.getLogger('autorna.GrindAtHome.get_friends')
        if initial:
            logger_initial = logging.getLogger('autorna.GrindAtHome.firstRequests')
            logger_initial.debug('/friends/')
        else:
            logger.debug('/friends/')
        try:
            result_friends = self.account.get('/friends/').json()
        except (httpx.UnsupportedProtocol, httpx.ReadError, httpx.RemoteProtocolError) as e:
            pass
        self.friends = result_friends

    def get_me(self):
        logger = logging.getLogger('autorna.GrindAtHome.get_me')
        logger.debug('/me/')
        result_me = None
        try:
            result_me = self.account.get('/me/', params={'w': 515, 'v': self.account.config['x-orna-version']}).json()
        except (httpx.UnsupportedProtocol, httpx.ReadError, httpx.RemoteProtocolError) as e:
            pass
        if result_me is None or result_me['success'] is False:
            logger.critical('Failure')
            exit(1)
        else:
            self.hp_total = result_me['user']['hp']
            self.hp_current = result_me['user']['current_hp']
            self.mana_total = result_me['user']['mana']
            self.mana_current = result_me['user']['current_mana']
            self.gold = result_me['user']['gold']
            self.orns = result_me['user']['orns']
            self.light_bonus = result_me['user']['light_bonus']
            self.level = result_me['user']['level']
            self.clan_uuid = result_me['user']['clan']['uuid']
        self.me = result_me

    def fight(self):
        logger = logging.getLogger('autorna.GrindAtHome.fight')
        # mon = max(self.monsters, key=lambda d: d["level"])

        # Check if monster can be removed from time stash
        mon = None
        result = []
        for monster in self.monsters['result']:
            result.append(monster)
        for monster in self.area['result']:
            result.append(monster)
        for monster in result:
            color_i = Fore.WHITE + Style.BRIGHT
            if monster['uuid'] in self.stashed_time:
                if (time.time() - self.stashed_time[monster['uuid']]['time'] > 300):
                    name = ''
                    level = ''
                    arisen = ''
                    berserk = ''
                    boss = ''
                    color_b = ''
                    space_1 = ''
                    space_2 = ''
                    space_3 = ''
                    tier = ''
                    color_i = Fore.WHITE + Style.BRIGHT
                    if 'name' in self.stashed_time[monster['uuid']]:
                        name = self.stashed_time[monster['uuid']]['name']
                    if 'level' in self.stashed_time[monster['uuid']]:
                        level = self.stashed_time[monster['uuid']]['level']
                    if 'berserk' in self.stashed_time[monster['uuid']]:
                        if self.stashed_time[monster['uuid']]['berserk']:
                            berserk = 'Berserk'
                            space_1 = ' '
                            color_b = Fore.RED + Style.BRIGHT
                    if 'boss' in self.stashed_time[monster['uuid']]:
                        if self.stashed_time[monster['uuid']]['boss']:
                            boss = 'Boss'
                            space_2 = ' '
                            color_b = Fore.RED + Style.BRIGHT
                    if 'arisen' in self.stashed_time[monster['uuid']]:
                        if self.stashed_time[monster['uuid']]['arisen']:
                            arisen = 'Arisen'
                            space_3 = ' '
                            color_b = Fore.RED + Style.BRIGHT
                    if 'tier' in self.stashed_time[monster['uuid']]:
                        tier = self.stashed_time[monster['uuid']]['tier']
                    logger_string = Fore.WHITE + Style.BRIGHT + 'Removing ({tier}★) {color_b}{boss}{space_2}{berserk}{space_1}{arisen}{space_3}{color_i}{name} ({level}) from time stash' + Style.RESET_ALL
                    logger.info(logger_string.format(name=name, level=level, tier=tier, berserk=berserk, boss=boss, arisen=arisen, space_1=space_1, space_2=space_2, space_3=space_3, color_b=color_b, color_i=color_i, color_e=Style.RESET_ALL))
                    del(self.stashed_time[monster['uuid']])

        # Check for bosses
        for monster in self.area['result']:
            if monster['uuid'] not in self.stashed_time and monster['uuid'] not in self.stashed_geo:
                if mon is None:
                    mon = monster
                elif monster['level'] > mon['level']:
                    mon = monster

        # If no bosses check through quest mobs
        if mon is None:
            for monster in self.monsters['result']:
                if monster['uuid'] not in self.stashed_time and monster['uuid'] not in self.stashed_geo:
                    if monster['is_quest']:
                        if mon is None:
                            mon = monster
                        elif monster['level'] > mon['level']:
                            mon = monster

        # If no bosses check through regular mobs
        if mon is None:
            for monster in self.monsters['result']:
                if monster['uuid'] not in self.stashed_time and monster['uuid'] not in self.stashed_geo:
                    if mon is None:
                        mon = monster
                    elif monster['level'] > mon['level']:
                        mon = monster

        # If no monsters on map
        if mon is None:
            logger.info(Fore.WHITE + Style.BRIGHT + 'No monsters to fight. Sleeping for 5 seconds.' + Style.RESET_ALL)
            # self.get_monsters()
            time.sleep(5)
            return

        for item in self.inventory['result']:
            need_hp = False
            need_mp = False
            if item['name'] == 'Small Health Potion':
                if item['count'] < 50:
                    need_hp = True
            if item['name'] == 'Small Mana Potion':
                if item['count'] < 50:
                    need_mp = True
            if need_hp or need_mp:
                self.shop_for_potions(hp=need_hp, mp=need_mp)

        if (self.hp_current / self.hp_total < 0.50) or (self.mana_current / self.mana_total < 0.50) or mon['is_berserk'] or mon['level'] >= self.level or mon['is_boss']:
            self.autoheal()

        # Check if we need to use a Torch
        use_torch = True
        for active_item in self.me['user']['active_items']:
            if active_item['name'] == 'Torch':
                use_torch = False

        if use_torch:
            self.use_torch()

        uuid_mon = mon['uuid']
        time.sleep(random.uniform(500, 1000) / 1000)
        logger.debug('/battles/monster/')
        try:
            result = self.account.post('/battles/monster/', data={'uuid': uuid_mon})
        except (httpx.UnsupportedProtocol, httpx.ReadError, httpx.RemoteProtocolError) as e:
            pass

        name = mon['name']
        level = mon['level']
        berserk = mon['is_berserk']
        boss = mon['is_boss']
        arisen = mon['is_arisen']
        tier = mon['tier']
        berserk_text = ''
        berserk_color = ''
        boss_text = ''
        arisen_text = ''
        space_1 = ''
        space_2 = ''
        space_3 = ''

        if berserk:
            berserk_text = 'Berserk'
            berserk_color = Fore.RED + Style.BRIGHT
            space_1 = ' '
        if boss:
            boss_text = 'Boss'
            berserk_color = Fore.RED + Style.BRIGHT
            space_2 = ' '
        if arisen:
            arisen_text = 'Arisen'
            berserk_color = Fore.RED + Style.BRIGHT
            space_3 = ' '

        if result and not result.json()['success']:
            if result.json()['message'] == 'You must wait before you can challenge this monster again':
                self.stashed_time[uuid_mon] = {'time': time.time(), 'name': mon['name'], 'level': mon['level'], 'tier': mon['tier'], 'berserk': mon['is_berserk'], 'boss': mon['is_boss'], 'arisen': mon['is_arisen']}
                logger_str = Fore.WHITE + Style.BRIGHT + 'Moving ({tier}★) {color_b}{boss}{space_2}{berserk}{space_1}{arisen}{space_3}{color_i}{} ({}) to time stash' + Style.RESET_ALL
                logger.info(logger_str.format(mon['name'], mon['level'], tier=tier, berserk=berserk_text, boss=boss_text, arisen=arisen_text, space_1=space_1, space_2=space_2, space_3=space_3, color_b=berserk_color, color_i=color_i, color_e=Style.RESET_ALL))
                return
            if result.json()['message'] == 'Move closer to challenge this monster':
                self.stashed_geo[uuid_mon] = mon['location']
                logger_str = Fore.WHITE + Style.BRIGHT + 'Moving ({tier}★) {color_b}{boss}{space_2}{berserk}{space_1}{arisen}{space_3}{color_i}{} ({}) to geo stash' + Style.RESET_ALL
                logger.info(logger_str.format(mon['name'], mon['level'], tier=tier, berserk=berserk_text, boss=boss_text, arisen=arisen_text, space_1=space_1, space_2=space_2, space_3=space_3, color_b=berserk_color, color_i=color_i, color_e=Style.RESET_ALL))
                return

        logger.info('Fighting ({tier}★) {color_b}{boss}{space_2}{berserk}{space_1}{arisen}{space_3}{color_e}{} ({})'.format(name, level, tier=tier, berserk=berserk_text, boss=boss_text, arisen=arisen_text, space_1=space_1, space_2=space_2, space_3=space_3, color_b=berserk_color, color_e=Style.RESET_ALL))

        if result and result.json()['success']:
            uuid = result.json()['result']['uuid']

            # time.sleep(random.uniform(500, 1500) / 1000)
            logger.debug('/battles/monster/')
            try:
                result = self.account.get('/battles/monster/', params={'uuid': uuid})
            except (httpx.UnsupportedProtocol, httpx.ReadError, httpx.RemoteProtocolError) as e:
                pass

            if result and result.json()['success']:
                uuid_new = result.json()['result']['uuid']
                state_id = ''

                has_won = False
                has_lost = False
                while(not has_won and not has_lost):
                    if 'state_id' in result.json():
                        state_id = result.json()['state_id']

                    time.sleep(random.uniform(150, 500) / 1000)
                    logger.debug('/battles/monster/turn/')

                    need_mp = False
                    if 'player_mana' in result.json():
                        if result.json()['player_mana'] < 35:
                            need_mp = True
                    if 'result' in result.json():
                        if 'player_mana' in result.json()['result']:
                            if result.json()['result']['player_mana'] < 35:
                                need_mp = True
                    if need_mp:
                        ssmp_uuid = None
                        ssmp_id = None
                        lmp_uuid = None
                        lmp_id = None
                        gmp_uuid = None
                        gmp_id = None
                        smp_uuid = None
                        smp_id = None
                        xmp_uuid = None
                        xmp_id = None

                        data_uuid = None
                        data_id = None
                        # Drink MP
                        for item in self.inventory['result']:
                            if item['name'] == 'Small Mana Potion':
                                ssmp_uuid = item['uuid']
                                ssmp_id = item['id']
                            if item['name'] == 'Large Mana Potion':
                                lmp_uuid = item['uuid']
                                lmp_id = item['id']
                            if item['name'] == 'Greater Mana Potion':
                                gmp_uuid = item['uuid']
                                gmp_id = item['id']
                            if item['name'] == 'Super Mana Potion':
                                smp_uuid = item['uuid']
                                smp_id = item['id']
                            if item['name'] == 'X Mana Potion':
                                xmp_uuid = item['uuid']
                                xmp_id = item['id']

                        if ssmp_uuid is None and ssmp_id is None:
                            # No small potions so exit
                            logger.critical('No more potions in inventory. Quit.')
                            exit(1)

                        if ssmp_uuid is not None and ssmp_id is not None:
                            data_uuid = ssmp_uuid
                            data_id = ssmp_id

                        if mon['is_boss'] or mon['is_berserk']:
                            if lmp_uuid is not None and lmp_id is not None:
                                data_uuid = lmp_uuid
                                data_id = lmp_id

                        try:
                            result = self.account.post(
                                '/battles/monster/turn/',
                                data={
                                    'uuid': uuid_new,
                                    'type': 'item',
                                    'item_uuid': data_uuid,
                                    'item_id': data_id,
                                    'grouped': True,
                                    'state_id': state_id
                                }
                            )
                        except (httpx.UnsupportedProtocol, httpx.ReadError, httpx.RemoteProtocolError) as e:
                            pass
                        logging.info('Used 1 ' + Fore.BLUE + 'Small Mana Potion' + Style.RESET_ALL)
                    elif mon['name'] in [
                        'Ghost',
                        'Gheist',
                        'Undead Golem',
                        'Demon Knight',
                        'Greater Demon',
                        'Lesser Sluagh',
                        'Skeleton Rogue',
                        'Skeleton Warrior',
                        'Vampire',
                        'Greater Vampire',
                        'Darkest Demon',
                        'Dark Slime',
                        'Odok',
                        'Odok Brute',
                        'Reaper',
                        'Vampire Lord',
                        'Dokkalfar Knight',
                        'Dokkalfar Lord',
                        'Gorgon',
                        'Racul',
                        'Kraken',
                        'Demon',  # temporary while weapon is dark
                    ]:
                        # Attack with Holy
                        try:
                            result = self.account.post(
                                '/battles/monster/turn/',
                                data={
                                    'uuid': uuid_new,
                                    'type': 'spell',
                                    'spell_id': 'Holystrike',
                                    'state_id': state_id
                                }
                            )
                        except (httpx.UnsupportedProtocol, httpx.ReadError, httpx.RemoteProtocolError) as e:
                            pass
                    elif mon['name'] in [
                        'Blue Slime',
                        'Living Armor',
                        'Blue Flame',
                        'Golem',
                        'Mythril Armor',
                        'Wisp',
                        'Magma Golem',
                        'Great Gazer',
                        "Will-O'-The-Wisp",
                        # 'Twilight Wisp', # resists all
                        'Arisen Undead Golem',
                        'Sandstone Golem',
                        # 'Arisen Mimic King', # resits all
                        'Orichalcum Golem',
                        'Arisen Great Gazer',
                        'Jelly',
                        'Lizarr Warrior',
                        'Lizarr Knight',
                        'Lizarr Lord',
                        'Lizarr Noble',
                        'Earth Core',
                        'Castor',
                        'Frost Mage',
                        'Sea Demon',
                        'Great Lizarr Knight',
                        'Great Lizarr Noble',
                        'Great Lizarr Warrior',
                        'Sea Wyvern',
                        'Hydra',
                        'Coral Beast',
                        'Coral Serpent',
                        'Coral Varmint',
                        'Pollux',
                        'Fallen Demeter, the Earth Magus',
                        'Arisen Hydra',
                        'Camazotz',  # temporary while weapon is dark
                        'Lost Pharaoh',  # temporary while weapon is dark
                    ]:
                        # Attack with Lightning
                        try:
                            result = self.account.post(
                                '/battles/monster/turn/',
                                data={
                                    'uuid': uuid_new,
                                    'type': 'spell',
                                    'spell_id': 'Lightningstrike',
                                    'state_id': state_id
                                }
                            )
                        except (httpx.UnsupportedProtocol, httpx.ReadError, httpx.RemoteProtocolError) as e:
                            pass
                    elif mon['name'] in [
                        'Flame',
                        'Gazer',
                        'Colossus',
                        'Balor Flame',
                        'Firefly',
                        'Flame Core',
                        'Pyre',
                        'Scorcher',
                        'Infernal Bear',
                        'Fallen Vulcan, the Red Knight',
                        'Arisen Vulcan, the Red Knight',
                    ]:
                        # Attack with Water
                        try:
                            result = self.account.post(
                                '/battles/monster/turn/',
                                data={
                                    'uuid': uuid_new,
                                    'type': 'spell',
                                    'spell_id': 'Icestrike',
                                    'state_id': state_id
                                }
                            )
                        except (httpx.UnsupportedProtocol, httpx.ReadError, httpx.RemoteProtocolError) as e:
                            pass
                    elif mon['name'] in [
                        'Great Mimic',
                        'Ancient Mimic',
                        'Mighty Mimic',
                        'Ancient Gazer',
                        'Great Wyvern',
                        'Sea Wyvern',
                        'Dark Dragon',
                        'Drake',
                        'Mimic King',
                        'Small Dragon',
                        'Arcane Dragon',
                        'Tiamat',
                        'Typhon',
                        'Fafnir',
                    ]:
                        # Attack with none of these:
                        # physical, dark, earthern, fire, holy, lightning, water
                        # Most likely DRAGON or arcane
                        # drop from special lists to just hit with physical
                        try:
                            result = self.account.post(
                                '/battles/monster/turn/',
                                data={
                                    'uuid': uuid_new,
                                    'type': 'spell',
                                    'spell_id': 'Dragonstrike',
                                    'state_id': state_id
                                }
                            )
                        except (httpx.UnsupportedProtocol, httpx.ReadError, httpx.RemoteProtocolError) as e:
                            pass
                    elif mon['name'] in [
                        'Legionnaire',
                        'Frost Troll',
                        'Crimson Wood',
                        'Fallen Ithra, the White Knight',
                        'Arisen Ithra, the White Knight',
                        'Fey Cactus',
                        'Scruug',
                        'Frost Core',
                        'Walking Wood',
                        'Great Sprout',
                        'Sprout',
                    ]:
                        # Attack with Fire
                        try:
                            result = self.account.post(
                                '/battles/monster/turn/',
                                data={
                                    'uuid': uuid_new,
                                    'type': 'spell',
                                    'spell_id': 'Firestrike',
                                    'state_id': state_id
                                }
                            )
                        except (httpx.UnsupportedProtocol, httpx.ReadError, httpx.RemoteProtocolError) as e:
                            pass
                    elif mon['name'] in [
                        'Arcane Flame',
                        'Ancient Gazer',
                        'Gargoyle',
                        'Heimdall',
                        'Nidhogg',
                        'Draugr',
                        'Draugr Mage',
                        'Ancient Draugr',
                        'Ancient Draugr Mage',
                        'Draugr Lord',
                        'Ancient Draugr Lord',
                    ]:
                        # Attack with Earthern
                        try:
                            result = self.account.post(
                                '/battles/monster/turn/',
                                data={
                                    'uuid': uuid_new,
                                    'type': 'spell',
                                    'spell_id': 'Earthstrike',
                                    'state_id': state_id
                                }
                            )
                        except (httpx.UnsupportedProtocol, httpx.ReadError, httpx.RemoteProtocolError) as e:
                            pass
                    # elif mon['name'] in [
                    #     'Camazotz',
                    # ]:
                    #     # Attack with Physical or weapon type
                    #     try:
                    #         result = self.account.post(
                    #             '/battles/monster/turn/',
                    #             data={
                    #                 'uuid': uuid_new,
                    #                 'type': 'spell',
                    #                 'spell_id': 'TripleCut',
                    #                 'state_id': state_id
                    #             }
                    #         )
                    #     except (httpx.UnsupportedProtocol, httpx.ReadError, httpx.RemoteProtocolError) as e:
                    #         pass
                    else:
                        # Volley II from offhand arrows
                        try:
                            result = self.account.post(
                                '/battles/monster/turn/',
                                data={
                                    'uuid': uuid_new,
                                    'type': 'ability',
                                    'state_id': state_id
                                }
                            )
                        except (httpx.UnsupportedProtocol, httpx.ReadError, httpx.RemoteProtocolError) as e:
                            pass
                    if result and result.json()['success']:
                        has_won = result.json()['result']['won']
                        has_lost = result.json()['result']['lost']
                    if has_won:
                        for i in range(len(self.area['result'])):
                            if self.area['result'][i]['uuid'] == uuid_mon:
                                del(self.area['result'][i])
                                break
                        for i in range(len(self.monsters['result'])):
                            if self.monsters['result'][i]['uuid'] == uuid_mon:
                                del(self.monsters['result'][i])
                                break
                    elif has_lost:
                        # self.stashed_time[uuid_mon] = time.time()
                        self.stashed_time[uuid_mon] = {'time': time.time(), 'name': mon['name'], 'level': mon['level'], 'tier': mon['tier'], 'berserk': mon['is_berserk'], 'boss': mon['is_boss']}
                        logger_str = Fore.WHITE + Style.BRIGHT + 'Lost battle. Moving ({tier}★) {color_b}{boss}{space_2}{berserk}{space_1}{arisen}{space_3}{color_i}{} ({}) to time stash.' + Style.RESET_ALL
                        logger.info(logger_str.format(mon['name'], mon['level'], tier=tier, berserk=berserk_text, boss=boss_text, arisen=arisen_text, space_1=space_1, space_2=space_2, space_3=space_3, color_b=berserk_color, color_i=color_i, color_e=Style.RESET_ALL))
        self.get_me()

    def autoheal(self):
        logger = logging.getLogger('autorna.GrindAtHome.autoheal')
        time.sleep(random.uniform(500, 1000) / 1000)
        logger.debug('/me/')
        try:
            result = self.account.post('/me/', data={'action': 'autoheal'})
        except (httpx.UnsupportedProtocol, httpx.ReadError, httpx.RemoteProtocolError) as e:
            pass
        if result and result.json()['success']:
            for item in result.json()['result']:
                color = ''
                if 'Health Potion' in item:
                    color = Fore.RED
                elif 'Mana Potion' in item:
                    color = Fore.BLUE
                logger.info('Used {} {color_b}{}{color_e}'.format(result.json()['result'][item], item, color_b=color, color_e=Style.RESET_ALL))
            for item in result.json()['used_items']:
                for thing in self.inventory['result']:
                    if item == thing['id']:
                        thing['count'] -= result.json()['used_items'][item]
        self.hp_current = result.json()['current_hp']
        self.mana_current = result.json()['current_mana']

    def grab_chests(self):
        logger = logging.getLogger('autorna.GrindAtHome.grab_chests')
        assert self.area
        if 'location' in self.area and self.area['success']:
            for chest in self.area['chests']:
                chest_name = chest['sprite'].split('/')[-1].split('.')[0]
                chest_loc = (chest['location'][0], chest['location'][1])
                chest_uuid = chest['uuid']

                time.sleep(random.uniform(500, 1000) / 1000)
                logger.debug('/chest/')
                logger.info('Opening Chest')
                try:
                    result = self.account.post('/chest/', data={'uuid': chest_uuid})
                except (httpx.UnsupportedProtocol, httpx.ReadError, httpx.RemoteProtocolError) as e:
                    pass
                if result and result.json()['success']:
                    count = ''
                    count_space = ''
                    if 'count' in result.json()['result']:
                        count = result.json()['result']['count']
                        count_space = ' '
                    logger.info('Received {count}{count_space}{}'.format(result.json()['result']['name'], count=count, count_space=count_space))
                if 'needs_inventory_refresh' in result.json():
                    if result.json()['needs_inventory_refresh']:
                        self.get_inventory()
                        self.get_area()
                        self.get_monsters()
                        self.get_shops()

    def get_inventory(self, initial=False):
        logger = logging.getLogger('autorna.GrindAtHome.get_inventory')
        if initial:
            logger_initial = logging.getLogger('autorna.GrindAtHome.firstRequests')
            logger_initial.debug('/inventory/')
        else:
            logger.debug('/inventory/')
        try:
            result_inventory = self.account.get('/inventory/').json()
        except (httpx.UnsupportedProtocol, httpx.ReadError, httpx.RemoteProtocolError) as e:
            pass
        self.inventory = result_inventory

    def use_torch(self):
        logger = logging.getLogger('autorna.GrindAtHome.use_torch')
        time.sleep(random.uniform(500, 1500) / 1000)
        logger.debug('/me/')
        try:
            result = self.account.post(
                '/me/',
                data={
                    'type_id': '0217c711-ffac-4447-a356-bd2dc2778b53',  # torch id
                    'action': 'item'
                }
            )
            logger.info('Used ' + Fore.YELLOW + 'torch!' + Style.RESET_ALL)
        except (httpx.UnsupportedProtocol, httpx.ReadError, httpx.RemoteProtocolError) as e:
            pass
        self.get_me()
        self.get_inventory()

    def shop_for_potions(self, hp=False, mp=False):
        logger = logging.getLogger('autorna.GrindAtHome.shop_for_potions')

        shop_use = None
        for shop in self.shops['result']:
            if shop['name'] == "pseudoscope's Shop":
                shop_use = shop
                break
            elif ' Shop' in shop['name']:
                shop_use = shop

        assert shop_use

        time.sleep(random.uniform(500, 1500) / 1000)
        logger.debug('/shopkeeper/')
        try:
            result = self.account.get('/shopkeeper/', params={'uuid': shop_use['uuid']})
        except (httpx.UnsupportedProtocol, httpx.ReadError, httpx.RemoteProtocolError) as e:
            pass

        if result and result.json()['success']:
            for item in result.json()['result']['inventory']:
                if item['name'] == 'Small Health Potion':
                    uuid_hp = item['id']
                if item['name'] == 'Small Mana Potion':
                    uuid_mp = item['id']

            if hp:
                try:
                    result = self.account.post(
                        '/shopkeeper/',
                        data={
                            'item_id': uuid_hp,
                            'action': 'buy',
                            'quantity': 100,
                            'uuid': shop_use['uuid']
                        }
                    )
                    logger.info('Bought 100 ' + Fore.RED + 'Small Health Potions' + Style.RESET_ALL)
                except (httpx.UnsupportedProtocol, httpx.ReadError, httpx.RemoteProtocolError) as e:
                    pass
            if mp:
                try:
                    result = self.account.post(
                        '/shopkeeper/',
                        data={
                            'item_id': uuid_mp,
                            'action': 'buy',
                            'quantity': 100,
                            'uuid': shop_use['uuid']
                        }
                    )
                    logger.info('Bought 100 ' + Fore.BLUE + 'Small Mana Potions' + Style.RESET_ALL)
                except (httpx.UnsupportedProtocol, httpx.ReadError, httpx.RemoteProtocolError) as e:
                    pass

        self.get_me()
        self.get_inventory()

    def arena_check(self):
        logger = logging.getLogger('autorna.GrindAtHome.arena_check')
        if (time.time() - self.arena_time > random.uniform(480, 720)):
            self.arena_do = True

    def arena_battle(self):
        logger = logging.getLogger('autorna.GrindAtHome.arena_battle')
        # rt_mon = RepeatedTimer(30, self.get_monsters)
        # rt_shop = RepeatedTimer(30, self.get_shops)
        # rt_notif = RepeatedTimer(60, self.get_notifications)
        # rt_frnd = RepeatedTimer(120, self.get_friends)
        # rt_area = RepeatedTimer(60, self.get_area, 'small')

        logger.debug('/battles/arena/')
        result = None
        try:
            result = self.account.post('/battles/arena/', data={'state': 1}).json()
        except (httpx.UnsupportedProtocol, httpx.ReadError, httpx.RemoteProtocolError) as e:
            pass

        tokens = None
        if result:
            if result['success']:
                tokens = result['result']['tokens']

        rematch = False

        while tokens > 25:

            time.sleep(random.uniform(1000, 3000) / 1000)

            logger.debug('/battles/arena/')
            try:
                result = self.account.post('/battles/arena/', data={'ranked': True}).json()
            except (httpx.UnsupportedProtocol, httpx.ReadError, httpx.RemoteProtocolError) as e:
                pass

            if result:
                if result['success']:
                    uuid_ranked = result['result']['uuid']

            result_get = None
            logger.debug('/battles/arena/')
            try:
                result_get = self.account.get('/battles/arena/', params={'uuid': uuid_ranked}).json()
            except (httpx.UnsupportedProtocol, httpx.ReadError, httpx.RemoteProtocolError) as e:
                pass

            if not rematch:
                logger.debug('/battles/arena/')
                try:
                    result = self.account.post('/battles/arena/', data={'state': 1}).json()
                except (httpx.UnsupportedProtocol, httpx.ReadError, httpx.RemoteProtocolError) as e:
                    pass

            if result:
                if result['success']:

                    time.sleep(random.uniform(100, 3000) / 1000)

                    logger.info('Arena fight against {}'.format(result_get['result']['opponent']['name']))
                    state_id = ''
                    has_won = False
                    has_lost = False
                    while (not has_won and not has_lost):
                        time.sleep(random.uniform(1000, 3000) / 1000)
                        if 'state_id' in result:
                            state_id = result['state_id']

                        logger.debug('/battles/arena/turn/')
                        try:
                            result = self.account.post(
                                '/battles/arena/turn/',
                                data={
                                    'uuid': uuid_ranked,
                                    'type': 'ability',
                                    'state_id': state_id
                                }
                            ).json()
                        except (httpx.UnsupportedProtocol, httpx.ReadError, httpx.RemoteProtocolError) as e:
                            pass

                        if result and result['success']:
                            has_won = result['result']['won']
                            has_lost = result['result']['lost']
                        if has_won:
                            logger.info('{}Won{} arena battle!'.format(Fore.GREEN, Style.RESET_ALL))
                            rematch = True
                            tokens -= 1
                        if has_lost:
                            logger.info('{}Lost{} arena battle.'.format(Fore.RED, Style.RESET_ALL))
                            rematch = True
                            tokens -= 1

            self.arena_time = time.time()
            self.arena_do = False

    def get_clan(self):
        logger = logging.getLogger('autorna.GrindAtHome.get_clan')
        logger.debug('/clans/')
        try:
            result = self.account.get('/clans/', params={'uuid': self.clan_uuid}).json()
        except (httpx.UnsupportedProtocol, httpx.ReadError, httpx.RemoteProtocolError) as e:
            pass

        if result and 'success' in result and result['success']:
            self.clan = result

    def kingdom_raids_battle(self):
        logger = logging.getLogger('autorna.GrindAtHome.kingdom_raids_battle')

        self.get_clan()
        time.sleep(random.uniform(100, 3000) / 1000)

        uuid_raid = None
        for raid in self.clan['result']['raids']:
            if raid['raid']['active'] and raid['raid']['battleable'] and (raid['raid']['time_left'] <= 1):
                uuid_raid = raid['raid']['uuid']

            assert uuid_raid

            logger.debug('/battles/raid/')
            try:
                result_1 = self.account.post('/battles/raid/', data={'uuid': uuid_raid}).json()
            except (httpx.UnsupportedProtocol, httpx.ReadError, httpx.RemoteProtocolError) as e:
                pass

            uuid_raid_new = None
            if result_1:
                if 'success' in result_1 and result_1['success']:
                    uuid_raid_new = result_1['result']['uuid']

            assert uuid_raid_new

            logger.debug('/battles/raid/')
            try:
                result = self.account.get('/battles/raid/', data={'uuid': uuid_raid_new}).json()
            except (httpx.UnsupportedProtocol, httpx.ReadError, httpx.RemoteProtocolError) as e:
                pass

            if result and 'success' in result and result['success']:
                name = result['result']['opponent']['name']
                level = result['result']['opponent']['level']
                berserk = result['result']['opponent']['berserk']
                berserk_color = Fore.RED + Style.BRIGHT
                color_e = Style.RESET_ALL
                space_1 = ''
                if berserk:
                    berserk_text = 'Berserk'
                    berserk_color = Fore.RED + Style.BRIGHT
                    space_1 = ' '

                logger.info('Fighting Kingdom Raid - {color_b}{berserk}{color_e}{space_1}{} ({})'.format(name, level, berserk=berserk_text, space_1=space_1, color_b=berserk_color, color_e=Style.RESET_ALL))

                has_won = False
                has_lost = False
                state_id = ''

                while (not has_won and not has_lost):
                    time.sleep(random.uniform(1000, 3000) / 1000)
                    if 'state_id' in result:
                        state_id = result['state_id']

                    logger.debug('/battles/raid/turn/')
                    try:
                        result = self.account.post(
                            '/battles/raid/',
                            data={
                                'uuid': uuid_raid,
                                'type': 'ability',
                                'state_id': state_id,
                            }
                        ).json()
                    except (httpx.UnsupportedProtocol, httpx.ReadError, httpx.RemoteProtocolError) as e:
                        pass

                    if result and result['success']:
                        has_won = result['result']['won']
                        has_lost = result['result']['lost']
                    if has_won:
                        logger.info('{}Won{} Kingdom Raid battle!'.format(Fore.GREEN, Style.RESET_ALL))
                    if has_lost:
                        logger.info('{}Lost{} Kingdom Raid battle.'.format(Fore.RED, Style.RESET_ALL))
                    if has_won or has_lost:
                        self.get_me()
                        self.get_clan()

    def kingdom_raids_check(self):
        logger = logging.getLogger('autorna.GrindAtHome.kingdom_raids_check')
        if (time.time() - self.kingdom_raids_time > random.uniform(480, 720)):
            self.kingdom_raids_do = True
