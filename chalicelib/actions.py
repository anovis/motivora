import os
from twilio.rest import Client
import datetime
from chalicelib.models import Messages,Users
from collections import defaultdict
import operator
from datetime import datetime
import random
from heapq import nlargest
# TODO remove v
import pdb


class UserActions:
    def __init__(self, phone, **kwargs):
        self.phone = int(phone)
        self.message_received = kwargs.get('Body','').lower()
        self.message_set = kwargs.get('message_set')
        self.total_days = 28
        self.initial_static_msg_days = 14

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
        if(u.next_message < self.initial_static_msg_days):
          print()
          print("Chosen next message: " + str(u.next_message + 1))
          print()
          return u.next_message + 1

        next_message = self.get_recommended_message()
        print()
        print("Chosen next message: " + str(next_message))
        print()
        return next_message


    def get_recommended_message(self):
        user = Users.get(self.phone)
        scored_attributes = self.get_scored_attributes(user)
        scored_potential_messages = self.get_scored_potential_messages(scored_attributes, user)
        new_message = self.choose_new_recommended_message(scored_potential_messages, user)
        return new_message


    def choose_new_recommended_message(self, scored_potential_messages, user):
        # Determine what day of the program we're on
        created_time_diff = datetime.now() - user.created_time.replace(tzinfo=None)
        # Determine the top # of messages to choose from based on the day of the
        # program we're on. As the program progresses, this window gets smaller
        # and smaller until at the end of the program we're just choosing the highest
        # scoring message.
        top_number_of_msgs_to_choose_from = self.total_days - created_time_diff.days
        # Choose the highest scoring messages
        potential_msg_keys = nlargest(top_number_of_msgs_to_choose_from, scored_potential_messages, key=scored_potential_messages.get)
        # Choose a random message from the top_number_of_msgs_to_choose_from
        return random.choice(potential_msg_keys)


    def get_scored_potential_messages(self, scored_attributes, user):
        messages_scored = defaultdict(int)
        all_msgs_og = Messages.query(self.message_set, Messages.id > 0)
        all_msgs = [message.to_frontend() for message in all_msgs_og]
        all_msgs_filtered = filter(lambda msg: msg['id'] not in user.messages_sent, all_msgs)
        # Iterate through each potential message
        for msg in all_msgs_filtered:
            message = Messages.get(self.message_set, msg['id'])
            attributes = message.attr_list.as_dict()
            # Iterate through all attributes for a given message
            for attr, boolean in attributes.items():
                # Make sure that the attribute is marked at TRUE
                if not boolean: continue
                messages_scored[msg['id']] += scored_attributes[attr]

        return messages_scored


    # Returns a dictionary of attributes with weighted scores based on the user's
    # rating of messages with these attributes and the number of times each attribute
    # has been attached to a message that was shown to a user.
    # 1. Iterate through all messages that a user has been sent
    # 2. For each message that was sent, iterate through all attributes of that message
    # 3. If the message was rated >= 5, add it to a dictionary of properties and scores,
    # if the message was rated < 5 then subtract it from 10 and then subtract that
    # from the dictionary of properties and scores.
    # 4. Multiple the property scores by the number of occurences that each property
    # has across all messages that have been sent to the user.
    def get_scored_attributes(self, user):
        attribute_dict = defaultdict(int)
        attribute_occurrence_dict = defaultdict(int)

        # Iterate through all messages sent
        for msg_idx in user.messages_sent:
            message = Messages.get(self.message_set, msg_idx)
            message_score = int(user.message_response[str(msg_idx)]['message'])
            attributes = message.attr_list.as_dict()
            # Iterate through all attributes for a given message
            for attr, boolean in attributes.items():
                # Make sure that the attribute is marked at TRUE
                if not boolean: continue
                # If the score is >= 5 it is considered positive
                score_is_positive = message_score >= 5
                # Count the occurrences of each attribute
                attribute_occurrence_dict[attr] += 1
                if score_is_positive:
                    attribute_dict[attr] += message_score
                else:
                    # Subtract the negative score from 10 to have an equal
                    # negative effect on the overall score
                    weighted_negative_score = 10 - message_score
                    attribute_dict[attr] -= weighted_negative_score

        # To give some weight to the frequency of each attribute, multiple each
        # attribute's score by the number of times it was rated
        for attr, occurrence in attribute_occurrence_dict.items():
            attribute_dict[attr] *= attribute_occurrence_dict[attr]

        return attribute_dict


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

    def days_between(self, d1, d2):
        d1 = datetime.strptime(d1, "%Y-%m-%d")
        d2 = datetime.strptime(d2, "%Y-%m-%d")
        return abs((d2 - d1).days)

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
            new_dict[len(new_dict)]= {'message':self.message_received,"timestamp":str(datetime.now()),"message_sent":u.prev_message}
            u.update(actions=[
               Users.message_response.set(new_dict)
            ])
            u.save()
        return True
