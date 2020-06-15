import os
from twilio.rest import Client
from chalicelib.models import Messages, Users, Invocations
from collections import defaultdict
from datetime import datetime, timedelta
import random
from heapq import nlargest
import pdb

import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration

sentry_sdk.init(dsn='https://dc96193451634aeca124f20398991f16@sentry.io/1446994',
                integrations=[AwsLambdaIntegration()])

class UserActions:
    def __init__(self, phone, **kwargs):
        self.phone = int(phone)
        self.message_received = kwargs.get('Body','').lower()
        self.message_set = kwargs.get('message_set')
        # Total program days (including first day with no motivational message)
        self.total_days = 29
        self.prelim_rated_messages = 16
        self.initial_static_msg_days = 14
        self.last_message_sent = 0
        self.anti_spam_phone_numbers = [19782108436]
        self.reminder_message_text = "Hi! Rating messages is one way we know which ones are most helpful. Please rate the messages you receive, as this will help us send you the most useful messages we can!"
        self.days_before_rating_reminder = 5

    def is_user(self):
        try:
            Users.get(self.phone)
            return True
        except Exception as e:
            return False

    def has_processed_for_invocation_id(self, invocation_id):
        try:
            found = Invocations.query(invocation_id)
            found_arr = [f for f in found]
            if len(found_arr) == 0: return False
            return True
        except Exception as e:
            return False

    def is_int(self, string):
        try:
            return isinstance(int(string), int)
        except Exception as e:
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
            rating_request = '\n\nHow helpful was this message? [Scale of 0-10, with 0=not helpful at all and 10=very helpful]'
            next_message_id = self.get_next_message()
            message = Messages.get(self.message_set, next_message_id)
            self.last_message_sent = next_message_id;
            self.send_sms(message.body + rating_request + self.get_anti_spam_message())
            self.send_reminder_sms_if_needed(self.days_before_rating_reminder)
            return True
        except Exception as e:
            sentry_sdk.capture_exception(e)
            return False

    def send_reminder_sms_if_needed(self, num_non_ratings):
        user = Users.get(self.phone)
        if not (self.has_consecutive_non_ratings(user, num_non_ratings)):
            return False
        try:
            self.send_sms(self.reminder_message_text)
            return True
        except Exception as e:
            sentry_sdk.capture_exception(e)
            return False


    def has_consecutive_non_ratings(self, user, num_non_ratings):
        # Get created_at_date
        created_date = user.created_time.date() - timedelta(days=1)
        # Get date of last rating
        last_rated_index = str(len(user.message_response) - 1)
        last_rated_day = user.message_response[last_rated_index]['timestamp'][0:10]
        last_rated_date = datetime.strptime(last_rated_day, '%Y-%m-%d').date()
        # Use created_at + last_rated to create a last_seen date
        last_seen_date = max(created_date, last_rated_date)
        today = datetime.now().date()
        days_since_rating = (today - last_seen_date).days - 1
        print("%s days since rating for %s"%(days_since_rating, user.phone))
        # Return True only if this the day we should be sending the message
        if days_since_rating > 0 and ((days_since_rating % num_non_ratings) == 0):
            return True
        else:
            return False


    def get_anti_spam_message(self):
        if self.phone in self.anti_spam_phone_numbers:
            return '\n\nText STOP to stop receiving messages'
        else:
            return ''

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

        new_user = Users(
            phone=self.phone,
            message_set=message_set,
            send_message=True
        )
        new_user.save()
        return True

    def get_next_message(self):
        u = Users.get(self.phone)
        # Serve the standard message set until after 14 days
        # Total program is 28 days
        last_message_sent_id = u.prev_message
        if(last_message_sent_id < self.initial_static_msg_days):
          message = Messages.get(self.message_set, last_message_sent_id + 1)
          log_message = message.to_json()
          log_message['attr_list'] = message.to_json()['attr_list'].as_dict()
          self.log("Chosen next message: " + str(log_message))
          return last_message_sent_id + 1

        next_message = self.get_recommended_message()
        message = Messages.get(self.message_set, next_message)
        log_message = message.to_json()
        log_message['attr_list'] = message.to_json()['attr_list'].as_dict()
        self.log("Chosen next message: " + str(log_message))
        return next_message

    def sent_messages_length(self):
        user = Users.get(self.phone)
        return len(user.messages_sent) - self.prelim_rated_messages if user.messages_sent != None else 0

    def get_recommended_message(self):
        user = Users.get(self.phone)
        scored_attributes = self.get_scored_attributes(user)
        print()
        print(scored_attributes)
        print()
        scored_potential_messages = self.get_scored_potential_messages(scored_attributes, user)
        print()
        print(scored_potential_messages)
        print()
        new_message = self.choose_new_recommended_message(scored_potential_messages, user)
        print()
        print(new_message)
        print()
        return new_message


    def choose_new_recommended_message(self, scored_potential_messages, user):
        # Create a new dictionary with a random ordering of keys so that the
        # nlargest function doesn't pick the top scored messages after they're sorted
        scored_potential_messages_keys = [ idx for idx in scored_potential_messages.keys() ]
        random.shuffle(scored_potential_messages_keys)
        new_scored_potential_messages = { idx : scored_potential_messages[idx] for idx in scored_potential_messages_keys }
        # Determine the top # of messages to choose from based on the number of messages
        # we've sent already. As the program progresses, this window gets smaller
        # and smaller until at the end of the program we're just choosing the highest
        # scoring message.
        diff = self.total_days - len(user.messages_sent)
        top_number_of_msgs_to_choose_from = diff if diff > 0 else 1
        # Choose the highest scoring messages
        potential_msg_keys = nlargest(top_number_of_msgs_to_choose_from, new_scored_potential_messages, key=new_scored_potential_messages.get)
        # Create a collection of potential messages that is partially reccomended and
        # partially random.
        potential_msg_keys_with_rand = self.get_potential_msg_keys_with_rand(potential_msg_keys, new_scored_potential_messages, top_number_of_msgs_to_choose_from)
        # Choose a random message from the top_number_of_msgs_to_choose_from
        print()
        print(diff, top_number_of_msgs_to_choose_from, potential_msg_keys_with_rand)
        print()
        return random.choice(potential_msg_keys_with_rand)

    def get_potential_msg_keys_with_rand(self, recommended_msg_keys, scored_potential_msg_keys, window_size):
        # Return an array of message keys comprising 70% reccomended and 30%
        # random messages.
        rand_pool = [el for el in scored_potential_msg_keys if el not in recommended_msg_keys]
        random_msgs_percentage = 0.3
        number_of_random_messages = round(random_msgs_percentage * window_size)
        rand = rand_pool[0:number_of_random_messages]
        reccomended = recommended_msg_keys[0:window_size-number_of_random_messages]
        return rand + reccomended


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
        slow_down_constant = 2
        total_possible_rating = 10
        attribute_dict = defaultdict(int)
        attribute_occurrence_dict = defaultdict(int)

        # Iterate through all messages that have been rated
        rated_responses = [*user.message_response.keys()]
        rated_responses.remove('0')
        for msg_sent_idx in rated_responses:
            msg_idx = int(user.message_response[msg_sent_idx]['message_sent'])
            message = Messages.get(self.message_set, msg_idx)
            message_score = self.get_message_score_for_idx(user.message_response, msg_idx)
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
                    # Divide message score by a constant to slow down algorithm learning
                    attribute_dict[attr] += (message_score / slow_down_constant)
                else:
                    # Subtract the negative score from total possible rating to have an equal
                    # negative effect on the overall score
                    # Divide message score by a constant to slow down algorithm learning
                    weighted_negative_score = (total_possible_rating - message_score) / slow_down_constant
                    attribute_dict[attr] -= weighted_negative_score

        return attribute_dict


    def get_message_score_for_idx(self, message_response, msg_idx):
        for key in message_response.keys():
            if message_response[key]["message_sent"] == msg_idx:
                return int(message_response[key]['message'])
        print(message_response)
        sentry_sdk.capture_exception(Exception('Msg Idx not found in messages sent - ' + str(msg_idx)))
        return 0


    def set_next_message(self):
        try:
            u = Users.get(self.phone)
            u.update(
                actions=[
                    Users.messages_sent.add(self.last_message_sent),
                    Users.prev_message.set(self.last_message_sent),
                ]
            )
            u.save()
            return True
        except Exception as e:
            print(e)
            sentry_sdk.capture_exception(e)
            return False

    def should_set_time(self):
        try:
            u = Users.get(self.phone)
            if u.prev_message == 0:
                return True
        except Exception as e:
            sentry_sdk.capture_exception(e)
            return False

    def update_time(self):
        # Since we ask for the time in ET, add 4 hours to it to get it into GMT
        # which is the timezone that we store the time in.
        time = int(self.message_received) + 4
        if(time > 23):
            time = abs(24 - time)
        u = Users.get(self.phone)
        u.update(
            actions=[
                Users.time.set(time)
            ]
        )
        u.save()

    def handle_message(self):
        if self.message_received.strip().lower() in ['stop','end']:
            u = Users.get(self.phone)
            u.update(
                actions=[
                    Users.send_message.set(False)
                ]
            )
            u.save()
        elif self.message_received.strip().lower() in ['start']:
            u = Users.get(self.phone)
            u.update(
                actions=[
                    Users.send_message.set(True)
                ]
            )
            u.save()
        elif not self.is_int(self.message_received) or int(self.message_received) < 0 or int(self.message_received) > 10:
            self.send_sms('Please reply with a rating for the previous message between 0 and 10. [0=not helpful at all and 10=very helpful]')
        else:
            u = Users.get(self.phone)
            # Make sure that we don't already have a rating for this message
            for k in u.message_response.keys():
                if u.message_response[k]["message_sent"] == u.prev_message:
                    self.send_sms("You've already rated the previous message. Please wait for the next message to send another rating.")
                    return False
            # Create a new response entry
            new_dict = u.message_response
            new_dict[len(new_dict)]= {'message': self.message_received, "timestamp": str(datetime.now()), "message_sent": u.prev_message}
            u.update(actions=[
               Users.message_response.set(new_dict)
            ])
            u.save()
            self.log("Rated message index: " + str(u.prev_message) + " - Rating: " + str(self.message_received))
        return True

    def log(self, msg):
      print()
      print(msg)
      print()
