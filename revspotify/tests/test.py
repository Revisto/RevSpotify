import os, sys

p = os.path.abspath(".")
sys.path.insert(1, p)

from unittest.mock import MagicMock
from telegram.ext.conversationhandler import ConversationHandler
from random import randint
import lorem
import names
import requests

from handlers.handler import (
    query,
    search_track,
    start_and_help,
    cancel,
    send_playlist,
    search_intro,
    search_track,
    choose_from_search_results,
)
from views.messages import View
from config import Config
from audio_compare.audio_diff import audio_equal


class Faker:
    class multiple_input_handling:
        def __init__(self):
            self.messages = []

    def generate_message_data(
        self,
        update_mock,
        chat_id=randint(100000, 9999999),
        text=lorem.sentence(),
        message_id=randint(10, 999),
        from_user_id=randint(100000, 9999999),
        from_user_first_name=names.get_first_name(),
        from_user_last_name=names.get_last_name(),
        from_user_username=names.get_full_name().replace(" ", "_"),
        chat_type="private",
    ):
        update_mock.message.chat_id = chat_id
        update_mock.message.chat.id = chat_id
        update_mock.message.text = text
        update_mock.message.message_id = message_id
        update_mock.message.from_user.id = from_user_id
        update_mock.message.from_user.first_name = from_user_first_name
        update_mock.message.from_user.last_name = from_user_last_name
        update_mock.message.from_user.username = from_user_username
        update_mock.message.chat.type = chat_type

    def generate_wait_messages(self, context_mock, message_counts=randint(1, 10)):
        context_mock.user_data = dict()
        context_mock.user_data["wait_messages"] = list()
        for i in range(int(message_counts)):
            context_mock.user_data["wait_messages"].append(randint(10, 999))

    def return_message_id_approach(self):
        mock = MagicMock()
        mock.message_id = randint(10, 999)
        return mock

    def set_user_data_approach(self, context_mock):
        context_mock.user_data = dict()
        return


def audio_equal_in_tests(file1, name2):
    """Compares two audio files and returns ``True`` if they have the same
    audio streams.
    Open the second file and save it due to the tests need and remove it after the comparison.
    """
    name1 = file1.name + "-test"
    with open(name1, "wb") as f:
        f.write(file1.read())
    files=[('file',('test.mp3', open(name1, 'rb'), 'audio/mpeg'))]
    url = "http://test.revs.ir/upload/" + name1.split("/")[-1]
    #response = requests.request("POST", url, data={}, files=files)
    result = audio_equal(name1, name2)
    os.remove(name1)
    return result

def log_check(update_mock, context_mock):
    sent_message_check = all(
        parameter in context_mock.bot.send_message.call_args.kwargs["text"]
        for parameter in [
            update_mock.message.text,
            update_mock.message.from_user.first_name,
            update_mock.message.from_user.last_name,
            update_mock.message.from_user.username,
        ]
    )
    forwarded_message_check = all(
        [
            context_mock.bot.forward_message.call_args.kwargs["chat_id"]
            == Config.LOG_CHAT_ID,
            context_mock.bot.forward_message.call_args.kwargs["from_chat_id"]
            == update_mock.message.chat_id,
            context_mock.bot.forward_message.call_args.kwargs["message_id"]
            == update_mock.message.message_id,
        ]
    )

    return sent_message_check and forwarded_message_check


def test_query_artist():
    update_mock = MagicMock()
    context_mock = MagicMock()
    artist_link = "https://open.spotify.com/artist/1dfeR4HaWDbWqFHLkxsg1d"
    Faker().generate_message_data(
        update_mock, text=f"{lorem.sentence()} {artist_link} {lorem.sentence()}"
    )
    update_mock.message.reply_text.return_value = Faker().return_message_id_approach()
    Faker().set_user_data_approach(context_mock)
    output = query(update_mock, context_mock)

    # check the output
    assert output == ConversationHandler.END

    # check response
    assert context_mock.user_data["wait_messages"] == []

    assert update_mock.message.reply_text.call_args_list[0][0][0] == View.wait()
    assert len(update_mock.message.reply_text.call_args_list) == 1

    assert (
        context_mock.bot.delete_message.call_args_list[0][0][0]
        == update_mock.message.chat_id
    )
    assert (
        context_mock.bot.delete_message.call_args_list[0][0][1]
        == update_mock.message.reply_text.return_value.message_id
    )
    assert len(context_mock.bot.delete_message.call_args_list) == 1

    assert (
        update_mock.message.reply_photo.call_args_list[0][0][0].read()
        == open("tests/artist/cover/Queen.png", "rb").read()
    )
    assert (
        update_mock.message.reply_photo.call_args.kwargs["caption"]
        == "Queen\nClassic Rock - Glam Rock - Rock"
    )
    assert len(update_mock.message.reply_photo.call_args_list) == 1

    for index in range(10):
        assert (
            context_mock.bot.send_audio.call_args_list[index][0][0]
            == update_mock.message.chat_id
        )


    print("111111--------------------------------------")
    assert audio_equal_in_tests(

        context_mock.bot.send_audio.call_args_list[0][0][1],
        "tests/artist/Another One Bites The Dust.mp3",
    )
    print("1--------------------------------------")
    assert audio_equal_in_tests(

        context_mock.bot.send_audio.call_args_list[1][0][1],
        "tests/artist/Bohemian Rhapsody.mp3",
    )
    print("2--------------------------------------")
    assert audio_equal_in_tests(

        context_mock.bot.send_audio.call_args_list[2][0][1],
        "tests/artist/Don't Stop Me Now.mp3",
    )
    print("3`--------------------------------------")
    assert audio_equal_in_tests(

        context_mock.bot.send_audio.call_args_list[3][0][1],
        "tests/artist/Under Pressure.mp3",
    )
    print("4--------------------------------------")
    assert audio_equal_in_tests(

        context_mock.bot.send_audio.call_args_list[4][0][1],
        "tests/artist/We Will Rock You.mp3",
    )
    print("5--------------------------------------")
    assert audio_equal_in_tests(

        context_mock.bot.send_audio.call_args_list[5][0][1],
        "tests/artist/Crazy Little Thing Called Love.mp3",
    )
    print("-6-------------------------------------")
    assert audio_equal_in_tests(

        context_mock.bot.send_audio.call_args_list[6][0][1],
        "tests/artist/Radio Ga Ga.mp3",
    )
    print("-7-------------------------------------")
    assert audio_equal_in_tests(

        context_mock.bot.send_audio.call_args_list[7][0][1],
        "tests/artist/We Are The Champions.mp3",
    )
    print("---8-----------------------------------")
    assert audio_equal_in_tests(

        context_mock.bot.send_audio.call_args_list[8][0][1],
        "tests/artist/I Want To Break Free.mp3",
    )
    print("-------99----------999---------------------")
    assert audio_equal_in_tests(

        context_mock.bot.send_audio.call_args_list[9][0][1],
        "tests/artist/Somebody To Love.mp3",
    )
    print("--------00000000000------------------------------")
    assert len(context_mock.bot.send_audio.call_args_list) == 10

    # check logs
    assert log_check(update_mock, context_mock)
