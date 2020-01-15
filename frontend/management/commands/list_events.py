from django.core.management.base import BaseCommand
from server.challenge.interface import Challenge
from server.submission.interface import Submission
from server.user.interface import User
from server.context import Context
from django.db.transaction import atomic
from datetime import timezone


class Command(BaseCommand):
    help = "List events"

    @atomic
    def handle(self, *args, **options):
        context = Context(elevated=True)
        submissions = Submission.get_log(context, match=True)
        submissions.sort(key=lambda x: x["time"])
        for submission in submissions:
            user_nickname = User.get(context, submission["user"]).nickname
            challenge_name = Challenge.get(context, submission["challenge"]).name
            time = submission["time"].astimezone()
            time = time.isoformat(sep=" ", timespec="seconds")
            print(f"{time}: [{user_nickname}] solved [{challenge_name}]")
