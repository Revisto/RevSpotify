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


def test_start_and_help():
    update_mock = MagicMock()
    context_mock = MagicMock()
    Faker().generate_message_data(update_mock)
    output = start_and_help(update_mock, context_mock)

    # check response
    assert update_mock.message.reply_text.call_args[0][0] == View.welcome()
    assert len(update_mock.message.reply_text.call_args_list) == 1

    # check logs
    assert log_check(update_mock, context_mock)


def test_cancel_without_wait_messages():
    update_mock = MagicMock()
    context_mock = MagicMock()
    Faker().generate_message_data(update_mock)
    output = cancel(update_mock, context_mock)

    # check the output
    assert output == ConversationHandler.END

    # check response
    assert update_mock.message.reply_text.call_args[0][0] == View.cancel()
    assert len(update_mock.message.reply_text.call_args_list) == 1

    assert context_mock.bot.delete_message.call_args_list == list()

    # check logs
    assert log_check(update_mock, context_mock)


def test_cancel_with_wait_messages():
    update_mock = MagicMock()
    context_mock = MagicMock()
    Faker().generate_wait_messages(context_mock)
    wait_messages = context_mock.user_data["wait_messages"].copy()
    Faker().generate_message_data(update_mock)
    output = cancel(update_mock, context_mock)

    # check the output
    assert output == ConversationHandler.END

    # check response
    assert update_mock.message.reply_text.call_args[0][0] == View.cancel()
    assert len(update_mock.message.reply_text.call_args_list) == 1

    assert context_mock.user_data["wait_messages"] == list()

    for index in range(len(wait_messages)):
        assert (
            context_mock.bot.delete_message.call_args_list[index][0][0]
            == update_mock.message.chat_id
        )
        assert (
            context_mock.bot.delete_message.call_args_list[index][0][1]
            == wait_messages[index]
        )
    assert len(context_mock.bot.delete_message.call_args_list) == len(wait_messages)

    # check logs
    assert log_check(update_mock, context_mock)


def test_query_no_link_in_private_chat():
    update_mock = MagicMock()
    context_mock = MagicMock()
    Faker().generate_message_data(
        update_mock, chat_type="private", text=lorem.sentence()
    )
    output = query(update_mock, context_mock)

    # check the output
    assert output == ConversationHandler.END

    # check response
    assert update_mock.message.reply_text.call_args[0][0] == View.link_is_not_valid()
    assert len(update_mock.message.reply_text.call_args_list) == 1


def test_query_no_link_in_group_chat():
    update_mock = MagicMock()
    context_mock = MagicMock()
    Faker().generate_message_data(update_mock, chat_type="group", text=lorem.sentence())
    output = query(update_mock, context_mock)

    # check the output
    assert output == ConversationHandler.END

    # check response
    assert update_mock.message.reply_text.call_args is None


def test_query_invalid_link():
    update_mock = MagicMock()
    context_mock = MagicMock()
    track_link = "https://www.open.spotify.com/track/aAaAaAaAaAaAaAaAaAaAaA"
    Faker().generate_message_data(
        update_mock, text=f"{lorem.sentence()} {track_link} {lorem.sentence()}"
    )
    update_mock.message.reply_text.return_value = Faker().return_message_id_approach()
    output = query(update_mock, context_mock)

    # check the output
    assert output == ConversationHandler.END

    # check response
    assert update_mock.message.reply_text.call_args_list[0][0][0] == View.wait()
    assert (
        update_mock.message.reply_text.call_args_list[1][0][0] == View.not_found_link()
    )
    assert len(update_mock.message.reply_text.call_args_list) == 2

    assert (
        context_mock.bot.delete_message.call_args_list[0][0][0]
        == update_mock.message.chat_id
    )
    assert (
        context_mock.bot.delete_message.call_args_list[0][0][1]
        == update_mock.message.reply_text.return_value.message_id
    )
    assert len(context_mock.bot.delete_message.call_args_list) == 1

    # check logs
    assert log_check(update_mock, context_mock)


def test_query_track_link_which_is_on_deezer():
    update_mock = MagicMock()
    context_mock = MagicMock()
    # pretty cool song btw, and also the name contains slashes (so it's a good thing to test)
    track_link = "https://open.spotify.com/track/0HY1DtNo8toftlRMMy4Ts6"
    Faker().generate_message_data(
        update_mock, text=f"{lorem.sentence()} {track_link} {lorem.sentence()}"
    )
    update_mock.message.reply_text.return_value = Faker().return_message_id_approach()
    Faker().set_user_data_approach(context_mock)
    output = query(update_mock, context_mock)

    # check the output
    assert output == ConversationHandler.END
    # check response
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
        == open(
            "tests/song/deezer/cover/What I’ve Done - Shadow of the Day - Heavy - Numb - In the End.png",
            "rb",
        ).read()
    )
    assert len(update_mock.message.reply_photo.call_args_list) == 1

    assert (
        context_mock.bot.send_audio.call_args_list[0][0][0]
        == update_mock.message.chat_id
    )
    assert audio_equal_in_tests(
        context_mock.bot.send_audio.call_args_list[0][0][1],
        "tests/song/deezer/What I’ve Done - Shadow of the Day - Heavy - Numb - In the End.mp3",
    )
    assert len(context_mock.bot.send_audio.call_args_list) == 1

    # check logs
    assert log_check(update_mock, context_mock)


def test_query_track_link_which_is_on_youtube():
    update_mock = MagicMock()
    context_mock = MagicMock()
    # well, it's hard to find a song which is on youtube but not on deezer,
    # so I'll just use this one, hope it doesn't become available on deezer
    track_link = "https://open.spotify.com/track/5F11BqJt3VHlsWNOV4zO7x"
    Faker().generate_message_data(
        update_mock, text=f"{lorem.sentence()} {track_link} {lorem.sentence()}"
    )
    update_mock.message.reply_text.return_value = Faker().return_message_id_approach()
    Faker().set_user_data_approach(context_mock)
    output = query(update_mock, context_mock)

    # check the output
    assert output == ConversationHandler.END

    # check response
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
        == open(
            "tests/song/youtube/cover/Shaal - The Shawl (Ft.Ehsan Sobhani).png", "rb"
        ).read()
    )
    assert len(update_mock.message.reply_photo.call_args_list) == 1

    assert (
        context_mock.bot.send_audio.call_args_list[0][0][0]
        == update_mock.message.chat_id
    )
    assert audio_equal_in_tests(
        context_mock.bot.send_audio.call_args_list[0][0][1],
        "tests/song/youtube/Shaal - The Shawl (Ft.Ehsan Sobhani).mp3",
    )
    assert len(context_mock.bot.send_audio.call_args_list) == 1

    # check logs
    assert log_check(update_mock, context_mock)


def test_query_album():
    update_mock = MagicMock()
    context_mock = MagicMock()
    album_link = "https://open.spotify.com/album/6rPU1BHqLneslZ1N1EvVdR"
    Faker().generate_message_data(
        update_mock, text=f"{lorem.sentence()} {album_link} {lorem.sentence()}"
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
        == open("tests/album/cover/Are You Alright.png", "rb").read()
    )
    assert len(update_mock.message.reply_photo.call_args_list) == 1

    for index in range(4):
        assert (
            context_mock.bot.send_audio.call_args_list[index][0][0]
            == update_mock.message.chat_id
        )

    assert audio_equal_in_tests(
        context_mock.bot.send_audio.call_args_list[0][0][1], "tests/album/Taunt.mp3"
    )
    assert audio_equal_in_tests(
        context_mock.bot.send_audio.call_args_list[1][0][1], "tests/album/One Day.mp3"
    )
    assert audio_equal_in_tests(
        context_mock.bot.send_audio.call_args_list[2][0][1], "tests/album/Sex Sells.mp3"
    )
    assert audio_equal_in_tests(
        context_mock.bot.send_audio.call_args_list[3][0][1],
        "tests/album/Cause for Concern.mp3",
    )
    assert len(context_mock.bot.send_audio.call_args_list) == 4

    # check logs
    assert log_check(update_mock, context_mock)


def test_query_invalid_album():
    update_mock = MagicMock()
    context_mock = MagicMock()
    album_link = "https://open.spotify.com/album/aAaAaAaAaAaAaAaAaAaAaA"
    Faker().generate_message_data(
        update_mock, text=f"{lorem.sentence()} {album_link} {lorem.sentence()}"
    )
    update_mock.message.reply_text.return_value = Faker().return_message_id_approach()
    Faker().set_user_data_approach(context_mock)
    output = query(update_mock, context_mock)

    # check the output
    assert output == ConversationHandler.END

    # check response
    assert context_mock.user_data["wait_messages"] == []

    assert update_mock.message.reply_text.call_args_list[0][0][0] == View.wait()
    assert (
        update_mock.message.reply_text.call_args_list[1][0][0] == View.not_found_link()
    )
    assert len(update_mock.message.reply_text.call_args_list) == 2

    assert (
        context_mock.bot.delete_message.call_args_list[0][0][0]
        == update_mock.message.chat_id
    )
    assert (
        context_mock.bot.delete_message.call_args_list[0][0][1]
        == update_mock.message.reply_text.return_value.message_id
    )
    assert len(context_mock.bot.delete_message.call_args_list) == 1

    # check logs
    assert log_check(update_mock, context_mock)


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

    assert audio_equal_in_tests(
        context_mock.bot.send_audio.call_args_list[0][0][1],
        "tests/artist/Another One Bites The Dust.mp3",
    )
    assert audio_equal_in_tests(
        context_mock.bot.send_audio.call_args_list[1][0][1],
        "tests/artist/Bohemian Rhapsody.mp3",
    )
    assert audio_equal_in_tests(
        context_mock.bot.send_audio.call_args_list[2][0][1],
        "tests/artist/Don't Stop Me Now.mp3",
    )
    assert audio_equal_in_tests(
        context_mock.bot.send_audio.call_args_list[3][0][1],
        "tests/artist/Under Pressure.mp3",
    )
    assert audio_equal_in_tests(
        context_mock.bot.send_audio.call_args_list[4][0][1],
        "tests/artist/We Will Rock You.mp3",
    )
    assert audio_equal_in_tests(
        context_mock.bot.send_audio.call_args_list[5][0][1],
        "tests/artist/Crazy Little Thing Called Love.mp3",
    )
    assert audio_equal_in_tests(
        context_mock.bot.send_audio.call_args_list[6][0][1],
        "tests/artist/Radio Ga Ga.mp3",
    )
    assert audio_equal_in_tests(
        context_mock.bot.send_audio.call_args_list[7][0][1],
        "tests/artist/We Are The Champions.mp3",
    )
    assert audio_equal_in_tests(
        context_mock.bot.send_audio.call_args_list[8][0][1],
        "tests/artist/I Want To Break Free.mp3",
    )
    assert audio_equal_in_tests(
        context_mock.bot.send_audio.call_args_list[9][0][1],
        "tests/artist/Somebody To Love.mp3",
    )
    assert len(context_mock.bot.send_audio.call_args_list) == 10

    # check logs
    assert log_check(update_mock, context_mock)


def test_query_invalid_artist():
    update_mock = MagicMock()
    context_mock = MagicMock()
    artist_link = "https://open.spotify.com/artist/aAaAaAaAaAaAaAaAaAaAaA"
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
    assert (
        update_mock.message.reply_text.call_args_list[1][0][0] == View.not_found_link()
    )
    assert len(update_mock.message.reply_text.call_args_list) == 2

    assert (
        context_mock.bot.delete_message.call_args_list[0][0][0]
        == update_mock.message.chat_id
    )
    assert (
        context_mock.bot.delete_message.call_args_list[0][0][1]
        == update_mock.message.reply_text.return_value.message_id
    )
    assert len(context_mock.bot.delete_message.call_args_list) == 1

    # check logs
    assert log_check(update_mock, context_mock)


def test_query_valid_playlist_count():
    update_mock = MagicMock()
    context_mock = MagicMock()
    playlist_link = "https://open.spotify.com/playlist/2dQYegk69l9VFO9oF3gkRY"
    Faker().generate_message_data(
        update_mock, text=f"{lorem.sentence()} {playlist_link} {lorem.sentence()}"
    )
    update_mock.message.reply_text.return_value = Faker().return_message_id_approach()
    update_mock.message.reply_photo.return_value = Faker().return_message_id_approach()
    Faker().set_user_data_approach(context_mock)
    output = query(update_mock, context_mock)

    # check the output
    assert output == 1

    # check response
    assert context_mock.user_data["spotify_links"] == [
        "https://open.spotify.com/track/4uvXM1oAW1kmKbT8GqGkxd",
        "https://open.spotify.com/track/17JbvwPoGbrCQfeFbccBAA",
        "https://open.spotify.com/track/4ReoHjamZ3qSfy3GcpCSCI",
        "https://open.spotify.com/track/3RxGw4kMbWNtDFPLVft1nE",
    ]
    assert context_mock.user_data["wait_messages"] == [
        update_mock.message.reply_text.return_value.message_id
    ]
    assert context_mock.user_data["playlist_photo_message"] == {
        "message_id": update_mock.message.reply_photo.return_value.message_id,
        "name": "Revspotify Tests, A Valid Short Playlist",
    }

    assert update_mock.message.reply_text.call_args_list[0][0][0] == View.wait()
    assert len(update_mock.message.reply_text.call_args_list) == 1

    assert (
        update_mock.message.reply_photo.call_args_list[0][0][0].read()
        == open(
            "tests/playlist/cover/Revspotify Tests, A Valid Short Playlist.png", "rb"
        ).read()
    )
    assert update_mock.message.reply_photo.call_args.kwargs[
        "caption"
    ] == View.receive_count_of_playlist_songs_to_send("4")
    assert len(update_mock.message.reply_photo.call_args_list) == 1

    # check logs
    assert log_check(update_mock, context_mock)


def test_query_valid_playlist_with_cover_but_empty():
    update_mock = MagicMock()
    context_mock = MagicMock()
    playlist_link = "https://open.spotify.com/playlist/4uellSv6udX6w27EctPBhl"
    Faker().generate_message_data(
        update_mock, text=f"{lorem.sentence()} {playlist_link} {lorem.sentence()}"
    )
    update_mock.message.reply_text.return_value = Faker().return_message_id_approach()
    update_mock.message.reply_photo.return_value = Faker().return_message_id_approach()
    Faker().set_user_data_approach(context_mock)
    output = query(update_mock, context_mock)

    # check the output
    assert output == ConversationHandler.END

    # check response
    assert update_mock.message.reply_text.call_args_list[0][0][0] == View.wait()
    assert len(update_mock.message.reply_text.call_args_list) == 1

    assert context_mock.user_data["wait_messages"] == []

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
        == open(
            "tests/playlist/cover/Revspotify Tests, An Empty Playlist.png", "rb"
        ).read()
    )
    assert (
        update_mock.message.reply_photo.call_args.kwargs["caption"]
        == View.playlist_is_empty()
    )
    assert len(update_mock.message.reply_photo.call_args_list) == 1

    # check logs
    assert log_check(update_mock, context_mock)


def test_query_valid_playlist_without_cover_and_empty():
    update_mock = MagicMock()
    context_mock = MagicMock()
    playlist_link = "https://open.spotify.com/playlist/2SkXJTNiZzJcep07TnP5az"
    Faker().generate_message_data(
        update_mock, text=f"{lorem.sentence()} {playlist_link} {lorem.sentence()}"
    )
    update_mock.message.reply_text.return_value = Faker().return_message_id_approach()
    update_mock.message.reply_photo.return_value = Faker().return_message_id_approach()
    Faker().set_user_data_approach(context_mock)
    output = query(update_mock, context_mock)

    # check the output
    assert output == ConversationHandler.END

    # check response
    assert context_mock.user_data["wait_messages"] == []

    assert update_mock.message.reply_text.call_args_list[0][0][0] == View.wait()
    assert (
        update_mock.message.reply_text.call_args_list[1][0][0]
        == View.playlist_is_empty()
    )
    assert len(update_mock.message.reply_text.call_args_list) == 2

    assert (
        context_mock.bot.delete_message.call_args_list[0][0][0]
        == update_mock.message.chat_id
    )
    assert (
        context_mock.bot.delete_message.call_args_list[0][0][1]
        == update_mock.message.reply_text.return_value.message_id
    )
    assert len(context_mock.bot.delete_message.call_args_list) == 1

    # check logs
    assert log_check(update_mock, context_mock)


def test_query_invalid_playlist():
    update_mock = MagicMock()
    context_mock = MagicMock()
    playlist_link = "https://open.spotify.com/playlist/aAaAaAaAaAaAaAaAaAaAaA"
    Faker().generate_message_data(
        update_mock, text=f"{lorem.sentence()} {playlist_link} {lorem.sentence()}"
    )
    update_mock.message.reply_text.return_value = Faker().return_message_id_approach()
    update_mock.message.reply_photo.return_value = Faker().return_message_id_approach()
    Faker().set_user_data_approach(context_mock)
    output = query(update_mock, context_mock)

    # check the output
    assert output == ConversationHandler.END

    # check response
    assert context_mock.user_data["wait_messages"] == []

    assert update_mock.message.reply_text.call_args_list[0][0][0] == View.wait()
    assert (
        update_mock.message.reply_text.call_args_list[1][0][0] == View.not_found_link()
    )
    assert len(update_mock.message.reply_text.call_args_list) == 2

    assert (
        context_mock.bot.delete_message.call_args_list[0][0][0]
        == update_mock.message.chat_id
    )
    assert (
        context_mock.bot.delete_message.call_args_list[0][0][1]
        == update_mock.message.reply_text.return_value.message_id
    )
    assert len(context_mock.bot.delete_message.call_args_list) == 1

    # check logs
    assert log_check(update_mock, context_mock)


def test_second_step_of_playlist_conversation_with_correct_spotify_inputs_and_more_count_than_track_counts():
    update_mock = MagicMock()
    context_mock = MagicMock()
    Faker().set_user_data_approach(context_mock)
    Faker().generate_wait_messages(context_mock)
    wait_messages = context_mock.user_data["wait_messages"].copy()
    Faker().generate_message_data(update_mock, text="999")
    context_mock.user_data["spotify_links"] = [
        "https://open.spotify.com/track/6UgmVIVyznBDdkpqkKyc1O",
        "https://open.spotify.com/track/7lQ8MOhq6IN2w8EYcFNSUk",
        "https://open.spotify.com/track/2jiozkiIJZvTYEz58j6UFh",
        "https://open.spotify.com/track/aAaAaAaAaAaAaAaAaAaAaA",
    ]
    context_mock.user_data["playlist_photo_message"] = {
        "message_id": 123456,
        "name": "Revspotify Tests",
    }
    update_mock.message.reply_text.return_value = Faker().return_message_id_approach()
    output = send_playlist(update_mock, context_mock)

    # check the output
    assert output == ConversationHandler.END

    # check response
    assert context_mock.user_data["wait_messages"] == []
    for index in range(len(wait_messages)):
        assert (
            context_mock.bot.delete_message.call_args_list[index][0][0]
            == update_mock.message.chat_id
        )
        assert (
            context_mock.bot.delete_message.call_args_list[index][0][1]
            == wait_messages[index]
        )
    assert len(context_mock.bot.delete_message.call_args_list) == len(wait_messages)

    for index in range(3):
        assert (
            context_mock.bot.send_audio.call_args_list[index][0][0]
            == update_mock.message.chat.id
        )

    assert audio_equal_in_tests(
        context_mock.bot.send_audio.call_args_list[0][0][1],
        "tests/playlist/Between The Bars.mp3",
    )
    assert audio_equal_in_tests(
        context_mock.bot.send_audio.call_args_list[1][0][1],
        "tests/playlist/Without Me.mp3",
    )
    assert audio_equal_in_tests(
        context_mock.bot.send_audio.call_args_list[2][0][1],
        "tests/playlist/Strange Effect.mp3",
    )

    assert len(context_mock.bot.send_audio.call_args_list) == 3

    assert (
        update_mock.message.reply_text.call_args_list[0][0][0] == View.not_found_link()
    )
    assert (
        update_mock.message.reply_text.call_args_list[1][0][0] == View.playlist_done()
    )
    assert len(update_mock.message.reply_text.call_args_list) == 2

    assert context_mock.user_data["playlist_photo_message"] is None

    assert (
        context_mock.bot.edit_message_caption.call_args_list[0][0][0]
        == update_mock.message.chat.id
    )
    assert context_mock.bot.edit_message_caption.call_args_list[0][0][1] == 123456
    assert (
        context_mock.bot.edit_message_caption.call_args.kwargs["caption"]
        == "Revspotify Tests"
    )
    assert len(context_mock.bot.edit_message_caption.call_args_list) == 1


def test_second_step_of_playlist_conversation_with_correct_spotify_inputs_and_exact_track_counts():
    update_mock = MagicMock()
    context_mock = MagicMock()
    Faker().set_user_data_approach(context_mock)
    Faker().generate_wait_messages(context_mock)
    wait_messages = context_mock.user_data["wait_messages"].copy()
    Faker().generate_message_data(update_mock, text="4")
    context_mock.user_data["spotify_links"] = [
        "https://open.spotify.com/track/6UgmVIVyznBDdkpqkKyc1O",
        "https://open.spotify.com/track/7lQ8MOhq6IN2w8EYcFNSUk",
        "https://open.spotify.com/track/2jiozkiIJZvTYEz58j6UFh",
        "https://open.spotify.com/track/aAaAaAaAaAaAaAaAaAaAaA",
    ]
    context_mock.user_data["playlist_photo_message"] = {
        "message_id": 123456,
        "name": "Revspotify Tests",
    }
    update_mock.message.reply_text.return_value = Faker().return_message_id_approach()
    output = send_playlist(update_mock, context_mock)

    # check the output
    assert output == ConversationHandler.END

    # check response
    assert context_mock.user_data["wait_messages"] == []
    for index in range(len(wait_messages)):
        assert (
            context_mock.bot.delete_message.call_args_list[index][0][0]
            == update_mock.message.chat_id
        )
        assert (
            context_mock.bot.delete_message.call_args_list[index][0][1]
            == wait_messages[index]
        )
    assert len(context_mock.bot.delete_message.call_args_list) == len(wait_messages)

    for index in range(3):
        assert (
            context_mock.bot.send_audio.call_args_list[index][0][0]
            == update_mock.message.chat.id
        )

    assert audio_equal_in_tests(
        context_mock.bot.send_audio.call_args_list[0][0][1],
        "tests/playlist/Between The Bars.mp3",
    )
    assert audio_equal_in_tests(
        context_mock.bot.send_audio.call_args_list[1][0][1],
        "tests/playlist/Without Me.mp3",
    )
    assert audio_equal_in_tests(
        context_mock.bot.send_audio.call_args_list[2][0][1],
        "tests/playlist/Strange Effect.mp3",
    )
    assert len(context_mock.bot.send_audio.call_args_list) == 3

    assert (
        update_mock.message.reply_text.call_args_list[0][0][0] == View.not_found_link()
    )
    assert (
        update_mock.message.reply_text.call_args_list[1][0][0] == View.playlist_done()
    )
    assert len(update_mock.message.reply_text.call_args_list) == 2

    assert context_mock.user_data["playlist_photo_message"] is None

    assert (
        context_mock.bot.edit_message_caption.call_args_list[0][0][0]
        == update_mock.message.chat.id
    )
    assert context_mock.bot.edit_message_caption.call_args_list[0][0][1] == 123456
    assert (
        context_mock.bot.edit_message_caption.call_args.kwargs["caption"]
        == "Revspotify Tests"
    )
    assert len(update_mock.message.reply_text.call_args_list) == 1


def test_second_step_of_playlist_conversation_with_correct_spotify_inputs_and_exact_track_counts():
    update_mock = MagicMock()
    context_mock = MagicMock()
    Faker().set_user_data_approach(context_mock)
    Faker().generate_wait_messages(context_mock)
    wait_messages = context_mock.user_data["wait_messages"].copy()
    Faker().generate_message_data(update_mock, text="4")
    context_mock.user_data["spotify_links"] = [
        "https://open.spotify.com/track/6UgmVIVyznBDdkpqkKyc1O",
        "https://open.spotify.com/track/7lQ8MOhq6IN2w8EYcFNSUk",
        "https://open.spotify.com/track/2jiozkiIJZvTYEz58j6UFh",
        "https://open.spotify.com/track/aAaAaAaAaAaAaAaAaAaAaA",
    ]
    context_mock.user_data["playlist_photo_message"] = {
        "message_id": 123456,
        "name": "Revspotify Tests",
    }
    update_mock.message.reply_text.return_value = Faker().return_message_id_approach()
    output = send_playlist(update_mock, context_mock)

    # check the output
    assert output == ConversationHandler.END

    # check response
    assert context_mock.user_data["wait_messages"] == []
    for index in range(len(wait_messages)):
        assert (
            context_mock.bot.delete_message.call_args_list[index][0][0]
            == update_mock.message.chat_id
        )
        assert (
            context_mock.bot.delete_message.call_args_list[index][0][1]
            == wait_messages[index]
        )
    assert len(context_mock.bot.delete_message.call_args_list) == len(wait_messages)

    for index in range(3):
        assert (
            context_mock.bot.send_audio.call_args_list[index][0][0]
            == update_mock.message.chat.id
        )

    assert (
        context_mock.bot.send_audio.call_args_list[0][0][1].read()
        == open("tests/playlist/Between The Bars.mp3", "rb").read()
    )
    assert (
        context_mock.bot.send_audio.call_args_list[1][0][1].read()
        == open("tests/playlist/Without Me.mp3", "rb").read()
    )
    assert (
        context_mock.bot.send_audio.call_args_list[2][0][1].read()
        == open("tests/playlist/Strange Effect.mp3", "rb").read()
    )
    assert len(context_mock.bot.send_audio.call_args_list) == 3

    assert (
        update_mock.message.reply_text.call_args_list[0][0][0] == View.not_found_link()
    )
    assert (
        update_mock.message.reply_text.call_args_list[1][0][0] == View.playlist_done()
    )
    assert len(update_mock.message.reply_text.call_args_list) == 2

    assert context_mock.user_data["playlist_photo_message"] is None

    assert (
        context_mock.bot.edit_message_caption.call_args_list[0][0][0]
        == update_mock.message.chat.id
    )
    assert context_mock.bot.edit_message_caption.call_args_list[0][0][1] == 123456
    assert (
        context_mock.bot.edit_message_caption.call_args.kwargs["caption"]
        == "Revspotify Tests"
    )
    assert len(context_mock.bot.edit_message_caption.call_args_list) == 1


def test_second_step_of_playlist_conversation_with_correct_spotify_inputs_and_less_track_counts():
    update_mock = MagicMock()
    context_mock = MagicMock()
    Faker().set_user_data_approach(context_mock)
    Faker().generate_wait_messages(context_mock)
    wait_messages = context_mock.user_data["wait_messages"].copy()
    Faker().generate_message_data(update_mock, text="2")
    context_mock.user_data["spotify_links"] = [
        "https://open.spotify.com/track/6UgmVIVyznBDdkpqkKyc1O",
        "https://open.spotify.com/track/7lQ8MOhq6IN2w8EYcFNSUk",
        "https://open.spotify.com/track/2jiozkiIJZvTYEz58j6UFh",
        "https://open.spotify.com/track/aAaAaAaAaAaAaAaAaAaAaA",
    ]
    context_mock.user_data["playlist_photo_message"] = {
        "message_id": 123456,
        "name": "Revspotify Tests",
    }
    update_mock.message.reply_text.return_value = Faker().return_message_id_approach()
    output = send_playlist(update_mock, context_mock)

    # check the output
    assert output == ConversationHandler.END

    # check response
    assert context_mock.user_data["wait_messages"] == []
    for index in range(len(wait_messages)):
        assert (
            context_mock.bot.delete_message.call_args_list[index][0][0]
            == update_mock.message.chat_id
        )
        assert (
            context_mock.bot.delete_message.call_args_list[index][0][1]
            == wait_messages[index]
        )
    assert len(context_mock.bot.delete_message.call_args_list) == len(wait_messages)

    for index in range(2):
        assert (
            context_mock.bot.send_audio.call_args_list[index][0][0]
            == update_mock.message.chat.id
        )

    assert (
        context_mock.bot.send_audio.call_args_list[0][0][1].read()
        == open("tests/playlist/Between The Bars.mp3", "rb").read()
    )
    assert (
        context_mock.bot.send_audio.call_args_list[1][0][1].read()
        == open("tests/playlist/Without Me.mp3", "rb").read()
    )
    assert len(context_mock.bot.send_audio.call_args_list) == 2

    assert (
        update_mock.message.reply_text.call_args_list[0][0][0] == View.playlist_done()
    )
    assert len(update_mock.message.reply_text.call_args_list) == 1

    assert context_mock.user_data["playlist_photo_message"] is None

    assert (
        context_mock.bot.edit_message_caption.call_args_list[0][0][0]
        == update_mock.message.chat.id
    )
    assert context_mock.bot.edit_message_caption.call_args_list[0][0][1] == 123456
    assert (
        context_mock.bot.edit_message_caption.call_args.kwargs["caption"]
        == "Revspotify Tests"
    )
    assert len(update_mock.message.reply_text.call_args_list) == 1


def test_second_step_of_playlist_conversation_with_correct_spotify_inputs_and_zero_as_track_counts():
    update_mock = MagicMock()
    context_mock = MagicMock()
    Faker().set_user_data_approach(context_mock)
    Faker().generate_wait_messages(context_mock)
    wait_messages = context_mock.user_data["wait_messages"].copy()
    Faker().generate_message_data(update_mock, text="0")
    context_mock.user_data["spotify_links"] = [
        "https://open.spotify.com/track/6UgmVIVyznBDdkpqkKyc1O",
        "https://open.spotify.com/track/7lQ8MOhq6IN2w8EYcFNSUk",
        "https://open.spotify.com/track/2jiozkiIJZvTYEz58j6UFh",
        "https://open.spotify.com/track/aAaAaAaAaAaAaAaAaAaAaA",
    ]
    context_mock.user_data["playlist_photo_message"] = {
        "message_id": 123456,
        "name": "Revspotify Tests",
    }
    update_mock.message.reply_text.return_value = Faker().return_message_id_approach()
    output = send_playlist(update_mock, context_mock)

    # check the output
    assert output == ConversationHandler.END

    # check response
    assert context_mock.user_data["wait_messages"] == []
    for index in range(len(wait_messages)):
        assert (
            context_mock.bot.delete_message.call_args_list[index][0][0]
            == update_mock.message.chat_id
        )
        assert (
            context_mock.bot.delete_message.call_args_list[index][0][1]
            == wait_messages[index]
        )
    assert len(context_mock.bot.delete_message.call_args_list) == len(wait_messages)

    assert len(context_mock.bot.send_audio.call_args_list) == 0

    assert (
        update_mock.message.reply_text.call_args_list[0][0][0]
        == View.not_valid_number()
    )
    assert len(update_mock.message.reply_text.call_args_list) == 1

    assert context_mock.user_data["playlist_photo_message"] is None

    assert (
        context_mock.bot.edit_message_caption.call_args_list[0][0][0]
        == update_mock.message.chat.id
    )
    assert context_mock.bot.edit_message_caption.call_args_list[0][0][1] == 123456
    assert (
        context_mock.bot.edit_message_caption.call_args.kwargs["caption"]
        == "Revspotify Tests"
    )
    assert len(update_mock.message.reply_text.call_args_list) == 1


def test_second_step_of_playlist_conversation_with_correct_spotify_inputs_and_text_as_track_counts():
    update_mock = MagicMock()
    context_mock = MagicMock()
    Faker().set_user_data_approach(context_mock)
    Faker().generate_wait_messages(context_mock)
    wait_messages = context_mock.user_data["wait_messages"].copy()
    Faker().generate_message_data(update_mock, text="blah")
    context_mock.user_data["spotify_links"] = [
        "https://open.spotify.com/track/6UgmVIVyznBDdkpqkKyc1O",
        "https://open.spotify.com/track/7lQ8MOhq6IN2w8EYcFNSUk",
        "https://open.spotify.com/track/2jiozkiIJZvTYEz58j6UFh",
        "https://open.spotify.com/track/aAaAaAaAaAaAaAaAaAaAaA",
    ]
    context_mock.user_data["playlist_photo_message"] = {
        "message_id": 123456,
        "name": "Revspotify Tests",
    }
    update_mock.message.reply_text.return_value = Faker().return_message_id_approach()
    output = send_playlist(update_mock, context_mock)

    # check the output
    assert output == ConversationHandler.END

    # check response
    assert context_mock.user_data["wait_messages"] == []
    for index in range(len(wait_messages)):
        assert (
            context_mock.bot.delete_message.call_args_list[index][0][0]
            == update_mock.message.chat_id
        )
        assert (
            context_mock.bot.delete_message.call_args_list[index][0][1]
            == wait_messages[index]
        )
    assert len(context_mock.bot.delete_message.call_args_list) == len(wait_messages)

    assert len(context_mock.bot.send_audio.call_args_list) == 0

    assert (
        update_mock.message.reply_text.call_args_list[0][0][0]
        == View.not_valid_number()
    )
    assert len(update_mock.message.reply_text.call_args_list) == 1

    assert context_mock.user_data["playlist_photo_message"] is None
    assert context_mock.bot.edit_message_caption(
        update_mock.message.chat.id, 123456, caption="Revspotify Tests"
    )


def test_search_intro():
    update_mock = MagicMock()
    context_mock = MagicMock()
    output = search_intro(update_mock, context_mock)

    # check the output
    assert output == 1

    # check response
    assert update_mock.message.reply_text.call_args_list[0][0][0] == View.search_intro()
    assert len(update_mock.message.reply_text.call_args_list) == 1


def test_search_track_with_invalid_input():
    update_mock = MagicMock()
    context_mock = MagicMock()
    Faker().generate_message_data(
        update_mock,
        text="blahblahblahblahblah@#$blahblahblahblah@#$blahblahblahblahblah",
    )
    update_mock.message.reply_text.return_value = Faker().return_message_id_approach()
    output = search_track(update_mock, context_mock)

    # check the output
    assert output == ConversationHandler.END

    # check response
    assert update_mock.message.reply_text.call_args_list[0][0][0] == View.no_results()
    assert len(update_mock.message.reply_text.call_args_list) == 1

    # check logs
    assert log_check(update_mock, context_mock)


def test_search_track_with_valid_input():
    update_mock = MagicMock()
    context_mock = MagicMock()
    Faker().set_user_data_approach(context_mock)
    Faker().generate_message_data(update_mock, text="Bomrani To Kojayi")
    update_mock.message.reply_text.return_value = Faker().return_message_id_approach()
    output = search_track(update_mock, context_mock)
    expected_tracks = [
        {
            "track_number": 1,
            "id": "619289672",
            "song_name": "To Kojayi?",
            "artist": "Bomrani",
            "duration": "02:33",
        },
        {
            "track_number": 2,
            "id": "900376672",
            "song_name": "To Kojayi? Live (Where Are You?) (Live)",
            "artist": "Bomrani",
            "duration": "02:59",
        },
    ]

    # check the output
    assert output == 2

    # check response
    assert update_mock.message.reply_text.call_args_list[0][0][
        0
    ] == View.choose_from_search_results(expected_tracks)
    assert len(update_mock.message.reply_text.call_args_list) == 1

    assert context_mock.user_data["search_tracks"] == expected_tracks

    # check logs
    assert log_check(update_mock, context_mock)


def test_choose_track_from_search_results_without_results_given():
    update_mock = MagicMock()
    context_mock = MagicMock()
    Faker().generate_message_data(update_mock, text="3")
    update_mock.message.reply_text.return_value = Faker().return_message_id_approach()
    Faker().set_user_data_approach(context_mock)
    output = choose_from_search_results(update_mock, context_mock)

    # check the output
    assert output == ConversationHandler.END

    # check response
    assert (
        update_mock.message.reply_text.call_args_list[0][0][0]
        == View.unexpected_error()
    )
    assert len(update_mock.message.reply_text.call_args_list) == 1


def test_choose_track_from_search_results_valid():
    update_mock = MagicMock()
    context_mock = MagicMock()
    Faker().generate_message_data(update_mock, text="3")
    update_mock.message.reply_text.return_value = Faker().return_message_id_approach()
    Faker().set_user_data_approach(context_mock)
    context_mock.user_data["search_tracks"] = [
        {"id": "12209331"},
        {"id": "9997018"},
        {"id": "74126058"},
    ]
    output = choose_from_search_results(update_mock, context_mock)

    # check the output
    assert output == ConversationHandler.END

    # check response
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
        == open("tests/search/cover/Sweet Dreams (Are Made Of This).png", "rb").read()
    )
    assert len(update_mock.message.reply_photo.call_args_list) == 1

    assert (
        context_mock.bot.send_audio.call_args_list[0][0][0]
        == update_mock.message.chat_id
    )
    assert (
        context_mock.bot.send_audio.call_args_list[0][0][1].read()
        == open("tests/search/Sweet Dreams (Are Made Of This).mp3", "rb").read()
    )
    assert len(context_mock.bot.send_audio.call_args_list) == 1


def test_choose_track_from_search_results_invalid_string_input():
    update_mock = MagicMock()
    context_mock = MagicMock()
    Faker().generate_message_data(update_mock, text="blahblah")
    update_mock.message.reply_text.return_value = Faker().return_message_id_approach()
    Faker().set_user_data_approach(context_mock)
    context_mock.user_data["search_tracks"] = [
        {"id": "12209331"},
        {"id": "9997018"},
        {"id": "74126058"},
    ]
    output = choose_from_search_results(update_mock, context_mock)

    # check the output
    assert output == ConversationHandler.END

    # check response
    assert (
        update_mock.message.reply_text.call_args_list[0][0][0]
        == View.not_valid_number()
    )
    assert len(update_mock.message.reply_text.call_args_list) == 1


def test_choose_track_from_search_results_invalid_int_input():
    update_mock = MagicMock()
    context_mock = MagicMock()
    Faker().generate_message_data(update_mock, text="999")
    update_mock.message.reply_text.return_value = Faker().return_message_id_approach()
    Faker().set_user_data_approach(context_mock)
    context_mock.user_data["search_tracks"] = [
        {"id": "12209331"},
        {"id": "9997018"},
        {"id": "74126058"},
    ]
    output = choose_from_search_results(update_mock, context_mock)

    # check the output
    assert output == ConversationHandler.END

    # check response
    assert (
        update_mock.message.reply_text.call_args_list[0][0][0]
        == View.not_valid_number()
    )
    assert len(update_mock.message.reply_text.call_args_list) == 1


def test_choose_track_from_search_results_invalid_song_id():
    update_mock = MagicMock()
    context_mock = MagicMock()
    Faker().generate_message_data(update_mock, text="1")
    update_mock.message.reply_text.return_value = Faker().return_message_id_approach()
    Faker().set_user_data_approach(context_mock)
    context_mock.user_data["search_tracks"] = [
        {"id": "99999999999999999999"},
        {"id": "9997018"},
        {"id": "74126058"},
    ]
    output = choose_from_search_results(update_mock, context_mock)

    # check the output
    assert output == ConversationHandler.END

    # check response
    assert update_mock.message.reply_text.call_args_list[0][0][0] == View.wait()
    assert (
        update_mock.message.reply_text.call_args_list[1][0][0]
        == View.error_downloading_track()
    )
    assert len(update_mock.message.reply_text.call_args_list) == 2
