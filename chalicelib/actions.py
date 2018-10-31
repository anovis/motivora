import os
from twilio.rest import Client
from models import Messages,Users


class UserActions:
    def __init__(self, phone, **kwargs):
        self.phone = phone
        self.message_received = kwargs.get('Body').lower()
        self.message_set = kwargs.get('message_set')

    def is_user(self):
        try:
            Users.get(self.phone)
            return True
        except:
            return False

    @property
    def user(self):
        return self._user()

    def _user(self):
        if not self._user:
            self._user = Users.get(self.phone)
        return self._user

    def send_next_sms(self):
        message = Messages.get(self.message_set,self.user.next_message)
        self.send_sms(message)

    def send_sms(self, message):
        account_sid = os.environ.get('SID')
        auth_token = os.environ.get('TOKEN')
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=message,
            from_=os.environ.get('PHONE'),
            to=self.phone
        )
        return message.sid

    def add_user(self, message_set=None):
        message_set = message_set if message_set is not None else self.message_set
        if not message_set:
            return False

        from models import Users
        #TODO message_set handle better
        new_user = Users(
            phone=self.phone,
            message_set=message_set,
            next_message=1,
            send_message=True,
        )

        new_user.save()

        return True

    def update_post_message(self, message_sent, next_message=None):
        self.user.messages_sent.append(message_sent)
        if next_message:
            self.user.next_message.set(next_message)
        else:
            self.user.next_message.add(1)

        self.user.save()

        return True

    def handle_message(self):
        if self.message_received in ['stop','end']:
            self.user.send_message.set(False)

        else:
            self.user.message_response.set({len(self.user.message_response),self.message_received})

        self.user.save()
        return True
