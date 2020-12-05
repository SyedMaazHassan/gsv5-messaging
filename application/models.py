from django.db import models
from datetime import datetime
from django.contrib.auth.models import User, auth
import random
import hashlib as hl
import six, base64

# Create your models here.

class allMsg(models.Model):
    sender = models.ForeignKey(User, on_delete = models.CASCADE, related_name = "sender_user")
    receiver = models.ForeignKey(User, on_delete = models.CASCADE, related_name = "receiver_user")
    message = models.TextField()
    moment = models.DateTimeField(default = datetime.now())

    def generate_code(self):
        strs = self.sender.username + self.receiver.username
        print(strs)
        code_hash = hl.md5(strs.encode())
        return code_hash.hexdigest()

    def encode(self, key, string):
        encoded_chars = []
        for i in range(len(string)):
            key_c = key[i % len(key)]
            encoded_c = chr(ord(string[i]) + ord(key_c) % 256)
            encoded_chars.append(encoded_c)
        encoded_string = ''.join(encoded_chars)
        encoded_string = encoded_string.encode('latin') if six.PY3 else encoded_string
        return base64.urlsafe_b64encode(encoded_string).rstrip(b'=')

    def save(self, *args, **kwargs):
        if not self.pk:
            our_key = self.generate_code()
            self.message = self.encode(our_key, self.message)
            
        super(allMsg, self).save(*args, **kwargs)
