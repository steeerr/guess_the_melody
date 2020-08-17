import json
import logging
import random
import sqlite3

import requests
from telethon import TelegramClient, events, Button
import utils
from constants import API_HASH, API_ID, CLIENT_ID, CLIENT_SECRET

main_genre = 'trap'
device_model = "spotify_bot"
version = "1.5"
system_version, app_version = version, version
client = TelegramClient('anon3', API_ID, API_HASH, device_model=device_model,
                        system_version=system_version, app_version=app_version)
logging.basicConfig(level=logging.ERROR, filename='log.log',
                    format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s')
logger = logging.getLogger(__name__)
conn = sqlite3.connect("quiz_bot.db")
cursor = conn.cursor()


class Database:
    def __init__(self):
        try:
            self.db = json.load(open("./database.json"))
        except FileNotFoundError:
            print("You need to run generate.py first, please read the Readme.")

    def save_token(self, token):
        self.db["access_token"] = token
        self.save()

    def save_refresh(self, token):
        self.db["refresh_token"] = token
        self.save()

    def save_bio(self, bio):
        self.db["bio"] = bio
        self.save()

    def save_spam(self, which, what):
        self.db[which + "_spam"] = what

    def return_token(self):
        return self.db["access_token"]

    def return_refresh(self):
        return self.db["refresh_token"]

    def return_bio(self):
        return self.db["bio"]

    def return_spam(self, which):
        return self.db[which + "_spam"]

    def save(self):
        with open('./database.json', 'w') as outfile:
            json.dump(self.db, outfile, indent=4, sort_keys=True)


database = Database()


def response_to_spotify():
    # Make a request for the Search API with pattern and random index
    oauth = {
        "Authorization": "Bearer " + database.return_token()}
    # Cap the max number of requests until getting RICK ASTLEYED
    r = requests.get(
        '{}/search?q={}&type=track&limit=40&offset={}'.format(
            'https://api.spotify.com/v1',
            "%20genre:%22{}%22".format(get_genre().replace(" ", "%20")),
            random.randint(0, 200)
        ),
        headers=oauth
    )
    if r.status_code == 200:
        return r
    elif r.status_code == 401:
        data = {"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET,
                "grant_type": "refresh_token",
                "refresh_token": database.return_refresh()}
        r = requests.post("https://accounts.spotify.com/api/token", data=data)
        received = r.json()
        # if a new refresh is token as well, we save it here
        try:
            database.save_refresh(received["refresh_token"])
        except KeyError:
            pass
        database.save_token(received["access_token"])
        # since we didnt actually update our status yet, lets do this without the 30 seconds wait
        skip = True
        return None
    elif r.status_code == 204:
        return None
    else:
        return None


@client.on(events.CallbackQuery(data=b'1'))
async def correct_handler(event):
    utils.good_answer(event.chat_id)
    utils.set_new_answer(event.chat_id)
    await event.answer('Correct answer!')
    await client.delete_messages(event.chat, event.message_id)
    await get_quiz(event.chat_id)


@client.on(events.CallbackQuery(data=b'2'))
async def wrong_handler(event):
    utils.set_new_answer(event.chat_id)
    await event.answer('Wrong answer!')
    await client.delete_messages(event.chat, event.message_id)
    await get_quiz(event.chat_id)


class Track:

    def __init__(self, ind, artist, song, track_url):
        self.ind = ind % 10
        self.artis = artist
        self.song = song
        self.track_url = track_url
        self.full_name = '{} - {}'.format(artist, song)


class PoolToBot:

    def __init__(self, track, answer):
        self.track = track
        self.answer = answer


def get_genre():
    random_wildcards = ["emo rap", "russian trap", "trap", "russian hip hop"]
    return random.choice(random_wildcards)


async def get_quiz(user_id):
    games = utils.get_answers_cnt(user_id)
    if games is not None and games < 10:
        try:
            artist = None
            song = None
            poll_opts = []
            url_song = None
            track = 0
            r = response_to_spotify()
            if r is not None:
                track_list = r.json()
                for track in range(39):
                    artist = track_list['tracks']['items'][track]['artists'][0]['name']
                    song = track_list['tracks']['items'][track]['name']
                    url_song = track_list['tracks']['items'][track]['preview_url']
                    poll_opts.append(Track(track, artist, song, url_song))

            poll = []
            track_url_ga = None
            ind_ga = None
            fl = True
            if len(poll_opts) > 4:
                for opt in poll_opts:
                    # if len(opt.full_name) < 64:
                    # have link? podhodit k ok answer
                    if opt.track_url is not None and fl:
                        poll.append(PoolToBot(opt.full_name, b'1'))
                        track_url_ga = opt.track_url
                        fl = False
                    else:
                        poll.append(PoolToBot(opt.full_name, b'2'))
                    if len(poll) == 4:
                        break
                random.shuffle(poll)
                await client.send_message(user_id, 'Чо за песня нахой?', file=track_url_ga, buttons=[
                    [Button.inline(poll[0].track, poll[0].answer)],
                    [Button.inline(poll[1].track, poll[1].answer)],
                    [Button.inline(poll[2].track, poll[2].answer)],
                    [Button.inline(poll[3].track, poll[3].answer)]

                ])
            else:
                await get_quiz(user_id)
        except:
            await get_quiz(user_id)
    else:
        score = utils.finish_user_game(user_id)
        cursor.execute('INSERT INTO games VALUES (?, ?, ?)', [None, score, user_id])
        conn.commit()
        await client.send_message(user_id, "gg wp score: {}/{}".format(score, games),
                                  buttons=[[Button.text('Start', resize=True, single_use=True)],
                                           [Button.text('Doska Pocheta', resize=True, single_use=True)]])


@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    cursor.execute('SELECT * FROM users WHERE id=?', [event.chat_id])
    have_id = cursor.fetchall()
    if len(have_id) == 0:
        cursor.execute('INSERT INTO users VALUES (?, ?, ?, ?)', [event.chat_id, event.chat.username, None,
                                                                 '{} {}'.format(event.chat.first_name,
                                                                                event.chat.last_name)])
        conn.commit()
    await client.send_message(event.chat_id, "Ну привет.\n Хочешь поугадывать хуйню со спотифай НАЖИМАЙ Start!",
                              buttons=[[Button.text('Start', resize=True, single_use=True)],
                                       [Button.text('Doska Pocheta', resize=True, single_use=True)]])


@client.on(events.NewMessage(pattern='Stop'))
async def stop_game(event):
    await client.send_message(event.chat_id, "ну можешь вернуться потом",
                              buttons=[[Button.text('Start', resize=True, single_use=True)],
                                       [Button.text('Doska Pocheta', resize=True, single_use=True)]])


@client.on(events.NewMessage(pattern='Doska Pocheta'))
async def get_board(event):
    cursor.execute(
        'select ((count(games.score)*100)+((4*sum(games.score)))/5), u.login, u.name, count(games.score), sum(games.score) from games left join users u on u.id = games.user_id group by 2 order by 1 desc')
    msg = 'Доска почета \n'
    score_board = cursor.fetchall()
    i = 1
    for score in score_board:
        if i == 1:
            pref = '🥇'
        elif i == 2:
            pref = '🥈'
        elif i == 3:
            pref = '🥉'
        else:
            pref = ' '
        if score[1] is None:
            name = score[2]
        else:
            name = '@' + score[1]
        msg += '{}.{} {} games: {}, score: {}\n'.format(i, pref, name, score[3], score[4])
        i += 1
        if i == 10:
            break
    await client.send_message(event.chat_id, msg)


@client.on(events.NewMessage(pattern='Start'))
async def start_game(event):
    await client.send_message(event.chat_id, "Ииииии мы начинаем",
                              buttons=[[Button.text('Stop', resize=True, single_use=True)],
                                       [Button.text('Doska Pocheta', resize=True, single_use=True)]])
    utils.start_game(event.chat_id)
    await get_quiz(event.chat_id)


client.start()
client.run_until_disconnected()
