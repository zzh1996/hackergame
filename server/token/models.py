import base64
import OpenSSL

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()
private_key = OpenSSL.crypto.load_privatekey(OpenSSL.crypto.FILETYPE_PEM,
                                             settings.PRIVATE_KEY)


class Token(models.Model):
    user = models.OneToOneField(User, models.CASCADE, primary_key=True)
    token = models.TextField(db_index=True)

    def __str__(self):
        return self.token

    @classmethod
    def get(cls, user):
        try:
            return user.token
        except cls.DoesNotExist:
            id = str(user.pk)
            sig = OpenSSL.crypto.sign(private_key, id.encode(), 'sha256')
            token = id + ':' + base64.b64encode(sig).decode()
            return Token.objects.create(user=user, token=token)