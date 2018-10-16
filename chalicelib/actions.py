import os
from twilio.rest import Client
from models import Messages,Users


class UserActions:
    def __init__(self, phone, **kwargs):
        self.phone = phone
        self.message = kwargs.get('Body')
        self.message_set = kwargs.get('message_set')

    def send_sms(self, message=None):
        message = message if message is not None else self.message
        if not message:
            return False

        account_sid = os.environ.get('SID')
        auth_token = os.environ.get('TOKEN')
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=message,
            from_="+16172022992",
            to=self.phone
        )
        return message.sid

    def add_user(self, message_set):
        message = message_set if message_set is not None else self.message_set
        if not message:
            return False

        from models import Users
        user = Users(
            phone=self.phone,
            message_set=message_set,
            next_message=1,
            send_message=True,
        )

        user.save()

        return user

    def update_post_message(self, message_sent, next_message=None):
        user = Users(self.phone)
        user.messages_sent.append(message_sent)
        if next_message:
            user.next_message.set(next_message)
        else:
            user.next_message.add(1)

        user.save()

        return user

