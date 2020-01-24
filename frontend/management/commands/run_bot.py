from django.conf import settings
from django.core.management.base import BaseCommand
from server.challenge.interface import Challenge
from server.submission.interface import Submission
from server.user.interface import User
from server.context import Context
from django.db.transaction import atomic

import time
import logging
import requests

interval = 10


def retry(func):
    def new_func(*args, **kwargs):
        while True:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logging.exception(e)
                time.sleep(interval)

    return new_func


@retry
def send(msg):
    logging.info("Sending '%s'", msg)
    url = "https://api.telegram.org/bot" + settings.BOT_TOKEN + "/sendMessage"
    data = {"chat_id": settings.BOT_CHAT_ID, "text": msg}
    requests.post(url, data=data, timeout=30).raise_for_status()
    logging.info("Sent")


def submission_to_str(submission):
    context = Context(elevated=True)
    user_nickname = User.get(context, submission["user"]).nickname
    challenge_name = Challenge.get(context, submission["challenge"]).name
    time = submission["time"].astimezone()
    time = time.isoformat(sep=" ", timespec="seconds")
    return f"{time}: [{user_nickname}] solved [{challenge_name}]"


@retry
def get_events_after(pk):
    logging.info("Getting events after %s", pk)
    with atomic():
        context = Context(elevated=True)
        submissions = Submission.get_log(context, match=True, before=pk)
        submissions.sort(key=lambda x: x["pk"])
        for submission in submissions:
            submission["text"] = submission_to_str(submission)
    return submissions


class Command(BaseCommand):
    help = "Run telegram bot"

    def handle(self, *args, **options):
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
        )

        events = get_events_after(None)
        send("Bot started, last event: " + events[-1]["text"])
        if events:
            last_pk = events[-1]["pk"]
        else:
            last_pk = None
        while True:
            events = get_events_after(last_pk)
            logging.info("Count: %s", len(events))
            if events:
                for event in events:
                    send(event["text"])
                last_pk = events[-1]["pk"]
            time.sleep(interval)
