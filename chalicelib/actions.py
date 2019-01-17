import os
from twilio.rest import Client
import datetime
from chalicelib.models import Messages,Users
import pdb


class UserActions:
    def __init__(self, phone, **kwargs):
        self.phone = int(phone)
        self.message_received = kwargs.get('Body','').lower()
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
        user = Users.get(self.phone)
        try:
            message = Messages.get(self.message_set,user.next_message)
            self.send_sms(message.body)
            return True

        except:
            return False

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

        from chalicelib.models import Users
        #TODO message_set handle better
        new_user = Users(
            phone=self.phone,
            message_set=message_set,
            next_message=1,
            send_message=True,
        )

        new_user.save()

        return True

    def get_next_message(self):
        u = Users.get(self.phone)
        # Serve the standard message set until after 14 days
        # if(u.next_message < 14): return u.next_message + 1
        return get_reccomended_message()

    def get_reccomended_message(self):
        # TODO - get the scheduler to run locally on demand so you can trigger this and act like it needs a new message to send
        user = Users.get(self.phone)
        pdb.set_trace()

    def set_next_message(self,):

        u = Users.get(self.phone)
        sent_message = u.next_message
        next_message = self.get_next_message()
        u.update(
            actions=[
                Users.messages_sent.add(sent_message),
                Users.prev_message.set(sent_message),
                Users.next_message.set(next_message)
            ]
        )
        u.save()

        return True

    def should_set_time(self):
        try:
            u = Users.get(self.phone)
            if len(u.messages_sent) == 0:
                time = int(self.message_received)
                if 0 <= time <=24:
                    return True
                return False
        except:
            return False

    def update_time(self):
        time = int(self.message_received)
        u = Users.get(self.phone)
        u.update(
            actions=[
                Users.time.set(time)
            ]
        )
        u.save()

    def handle_message(self):
        if self.message_received in ['stop','end']:
            u = Users.get(self.phone)
            u.update(
                actions=[
                    Users.send_message.set(False)
                ]
            )
            u.save()
        else:
            u = Users.get(self.phone)
            new_dict = u.message_response
            new_dict[len(new_dict)]= {'message':self.message_received,"timestamp":str(datetime.datetime.now()),"message_sent":u.prev_message}
            u.update(actions=[
               Users.message_response.set(new_dict)
            ])
            u.save()
        return True
