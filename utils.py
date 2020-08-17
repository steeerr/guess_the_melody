import shelve


def start_game(chat_id):
    with shelve.open("game.db") as storage:
        storage[str(chat_id)] = 0
        storage[str(chat_id) + "_cnt"] = 0


def set_new_answer(chat_id):
    with shelve.open("game.db") as storage:
        try:
            cnt = storage[str(chat_id) + "_cnt"]
            cnt += 1
            storage[str(chat_id) + "_cnt"] = cnt
            return cnt
        except KeyError:
            return None


def get_answers_cnt(chat_id):
    with shelve.open("game.db") as storage:
        try:
            cnt = storage[str(chat_id) + "_cnt"]
            return cnt
        except KeyError:
            return None


def good_answer(chat_id):
    with shelve.open("game.db") as storage:
        try:
            score = storage[str(chat_id)]
            score += 1
            storage[str(chat_id)] = score
            return score
        except KeyError:
            return None


def finish_user_game(chat_id):
    with shelve.open("game.db") as storage:
        score = storage[str(chat_id)]
        del storage[str(chat_id)]
        return score
