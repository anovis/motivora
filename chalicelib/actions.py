import os
from twilio.rest import Client
from chalicelib.models import Messages, Users, DecisionTrees, Invocations
from collections import defaultdict
from datetime import datetime, timedelta
import random
from heapq import nlargest
import pdb
import re

import string
#import nltk
#from nltk.corpus import stopwords

import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration

sentry_sdk.init(dsn='https://dc96193451634aeca124f20398991f16@sentry.io/1446994',
                integrations=[AwsLambdaIntegration()])

class MessageActions:
    def __init__(self):
        self.init = True

    def get_stats(self, message, users=None):
        if users is None:
            users = Users.scan(Users.message_set == message.message_set)
        total_sent = 0
        total_rated = 0
        total_rating = 0
        ratings = {
            'rating_0': 0,
            'rating_1': 0,
            'rating_2': 0,
            'rating_3': 0,
            'rating_4': 0,
            'rating_5': 0,
            'rating_6': 0,
            'rating_7': 0,
            'rating_8': 0,
            'rating_9': 0,
            'rating_10': 0,
        }
        for user in users:
            if user.message_set != message.message_set:
                continue
            if (message.id in user.messages_sent):
                total_sent += 1
                for k, v in user.message_response.items():
                    if v['message_sent'] == message.id and 'message' in v:
                        total_rated += 1
                        total_rating += int(v['message'])
                        rating_key = "rating_%s"%(v['message'])
                        ratings[rating_key] += 1
                        break
        avg_rating = 0
        if total_rated >= 1:
            avg_rating = total_rating * 1.0 / total_rated

        message.update(actions=[
            Messages.total_sent.set(total_sent),
            Messages.total_rated.set(total_rated),
            Messages.average_rating.set(round(avg_rating, 1)),
            Messages.rating_0.set(ratings['rating_0']),
            Messages.rating_1.set(ratings['rating_1']),
            Messages.rating_2.set(ratings['rating_2']),
            Messages.rating_3.set(ratings['rating_3']),
            Messages.rating_4.set(ratings['rating_4']),
            Messages.rating_5.set(ratings['rating_5']),
            Messages.rating_6.set(ratings['rating_6']),
            Messages.rating_7.set(ratings['rating_7']),
            Messages.rating_8.set(ratings['rating_8']),
            Messages.rating_9.set(ratings['rating_9']),
            Messages.rating_10.set(ratings['rating_10'])
        ])
        return {
            'total_sent': total_sent,
            'total_rated': total_rated,
            'average_rating': round(avg_rating, 1),
            **ratings
        }

    def get_all_messages_with_stats(self, message_set):
        users = []
        for user in Users.scan(Users.message_set == message_set):
            if user.is_real_user:
                users.append(user)
        messages = []
        for message in Messages.query(message_set, Messages.id >= 0):
            stats = self.get_stats(message, users)
            print("[%s] %s"%(message.id, stats))
            messages.append({**message.to_frontend(), **stats})
        return messages

class UserActions:
    def __init__(self, phone, **kwargs):
        # Twilio phone numbers
        self.motivational_phone_number   = os.environ.get('MOTIVATIONAL_PHONE')
        self.goal_setting_phone_number   = os.environ.get('GOAL_SETTING_PHONE')
        self.direct_message_phone_number = os.environ.get('DIRECT_MESSAGE_PHONE')

        # Reminder message config
        self.reminder_message_text = "Hi! Rating messages is one way we know which ones are most helpful. Please rate the messages you receive, as this will help us send you the most useful messages we can!"
        self.decision_tree_mistake_text = "I'm sorry. I didn't understand that. Can you re-send your response to the last question with a whole number? If you want to start over, please respond with 99."
        self.welcome_message = "Welcome to the Text4Health program! We will send you a message each day to help you feel positive, be physically active, and make healthy food choices. Please rate as many messages as you can, so we know which ones you like the best!"
        self.days_before_rating_reminder = 3

        self.phone = int(phone)
        self.message_received = kwargs.get('Body','').lower()

        # Total program days (including first day with no motivational message)
        self.total_days = 72
        self.initial_static_msg_days = 16
        self.last_message_sent = 0
        self.anti_spam_phone_numbers = [19782108436]
        
        # Tuning params for message selection
        self.total_attr_count = 6
        self.historical_message_discount_factor = 0.1 # Determines how quickly older ratings are down-weighted
        self.unranked_attr_boost = 0.1 # Additional score boost for messages with attrs that have not yet been ranked
        self.prob_of_selection_on_iteration = 0.1 # Minimal boost for top messages
        self.preferred_attr_boost = 0.5 # Constant score boost for preferred categories

    def is_user(self):
        try:
            Users.get(self.phone)
            return True
        except Exception as e:
            return False

    def program_is_complete(self):
        u = Users.get(self.phone)
        if u.message_set == "MASTERY":
            return self.sent_messages_length() >= 14
        else:
            return self.sent_messages_length() >= 72

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

    # Retrieves the next message to be sent, formats it appropriately, and triggers the SMS sending
    def send_next_sms(self, is_test=False):
        user = Users.get(self.phone)
        rating_request = '\n\nHow helpful was this message? [Scale of 0-10, with 0=not helpful at all and 10=very helpful]'
        next_message_id = self.get_next_message()
        message = Messages.get(user.message_set, next_message_id)
        self.last_message_sent = next_message_id;
        body = self.get_message_body(message)
        if is_test:
            print("Would send messge: %s"%(body + rating_request + self.get_anti_spam_message()))
        else:
            self.send_welcome_sms_if_needed()
            self.send_motivational_sms(message, body + rating_request + self.get_anti_spam_message())
            self.send_reminder_sms_if_needed(self.days_before_rating_reminder)
        return True

    def send_welcome_sms_if_needed(self):
        user = Users.get(self.phone)
        if user.welcome_message_received or user.message_set != "Text4Health":
            return False
        try:
            self.send_motivational_sms(None, self.welcome_message)
            print("Sending welcome message: " + self.welcome_message)
            user.update(
                actions=[
                    Users.welcome_message_received.set(True)
                ]
            )
            user.save()
            return True
        except Exception as e:
            sentry_sdk.capture_exception(e)
            return False

    def send_reminder_sms_if_needed(self, num_non_ratings):
        user = Users.get(self.phone)
        if not (self.has_consecutive_non_ratings(user, num_non_ratings)):
            return False
        try:
            self.send_motivational_sms(None, self.reminder_message_text)
            return True
        except Exception as e:
            sentry_sdk.capture_exception(e)
            return False

    def get_message_body(self, message):
        user = Users.get(self.phone)
        if (user.lang_code == "en"):
            body = message.body_en
        elif (user.lang_code == "es"):
            body = message.body_es
        if body is None:
            body = message.body
        return body

    def has_consecutive_non_ratings(self, user, num_non_ratings):
        # Get created_at_date
        created_date = user.created_time.date() - timedelta(days=1)
        # Get date of last rating
        max_timestamp = str(created_date)
        for k in user.message_response.keys():
            if 'message' not in user.message_response[k]:
                continue
            timestamp = user.message_response[k]['timestamp'][0:10]
            if timestamp > max_timestamp:
                max_timestamp = timestamp
        last_rated_day = max_timestamp
        last_seen_date = datetime.strptime(last_rated_day, '%Y-%m-%d').date()
        today = datetime.now().date()
        days_since_rating = max((today - last_seen_date).days - 1, 0)
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

    def send_motivational_sms(self, message, content):
        self.send_sms(content, self.motivational_phone_number)
        if message is not None:
            self.save_motivational_message(message)

    def send_direct_message_sms(self, message):
        self.send_sms(message, self.direct_message_phone_number)
        self.save_direct_message('outgoing', message)

    def send_goal_setting_sms(self, message):
        self.send_sms(message, self.goal_setting_phone_number)

    def send_sms(self, message, sender_phone_number):
        account_sid = os.environ.get('SID')
        auth_token = os.environ.get('TOKEN')
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=message,
            from_=sender_phone_number,
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
        if u.message_set == "MASTERY":
            next_message = self.get_next_sequential_message()
        else:
            next_message = self.get_recommended_message()
        message = Messages.get(u.message_set, next_message)
        log_message = message.to_json()
        log_message['attr_list'] = message.to_json()['attr_list']
        self.log("Chosen next message: " + str(log_message))
        return next_message

    def sent_messages_length(self):
        user = Users.get(self.phone)
        return len(user.messages_sent) if user.messages_sent != None else 0

    def get_next_sequential_message(self):
        user = Users.get(self.phone)
        if not user.messages_sent:
            return 1
        else:
            return max(user.messages_sent) + 1

    def get_recommended_message(self):
        user = Users.get(self.phone)
        user_obj = UserActions(**user.to_dict())
        scored_attributes = user_obj.get_scored_attributes(user_obj, user)
        print("\n%s\n"%(scored_attributes))

        scored_potential_messages = user_obj.get_scored_potential_messages(user_obj, scored_attributes, user)
        print("\n%s\n"%(scored_potential_messages))

        new_message = user_obj.choose_new_recommended_message(user_obj, scored_potential_messages, user)
        print("\n%s\n"%(new_message))

        return new_message


    # Sort scored_potential_messages hash by score
    # Iterate over the hash, and select each new entry with a prob_of_selection_on_iteration probability
    def choose_new_recommended_message(self, user_obj, scored_potential_messages, user):
        # Randomize key ordering
        scored_potential_messages_keys = [ idx for idx in scored_potential_messages.keys() ]
        random.shuffle(scored_potential_messages_keys)
        new_scored_potential_messages = { idx : scored_potential_messages[idx] for idx in scored_potential_messages_keys }
        # Sort hash by score value
        sorted_messages = {k: v for k, v in sorted(new_scored_potential_messages.items(), key=lambda item: item[1],reverse= True)}
        # Iterate over each message, and consider each key in sequence with a likelihood of prob_of_selection_on_iteration
        selected_id = None
        for id, score in sorted_messages.items():
            r = random.random() 
            if r < self.prob_of_selection_on_iteration:
                selected_id = id
                break
        # If we get to the end of our hash without choosing anything, default to the first key
        if selected_id is None:
            for id, score in sorted_messages.items():
                selected_id = id
                break
        return selected_id

    # Retrive all messages from DynamoDB
    # Sum average ratings for each attribute of that message:
    #   > If we have seen a message's attr before, use the average score of rated messages with that attr
    #   > If we have not seen a message's attr before, use the average score of all rated messages, plus delta (optimize to see all attrs)
    #   > If a message does not have a particular attr, use the average score of all rated messages
    #
    # Return a hash of message_id => score
    def get_scored_potential_messages(self, user_obj, scored_attributes, user):
        messages_scored = defaultdict(int)
        all_msgs_og = Messages.query(user.message_set, Messages.id > 0)
        all_msgs = [message.to_frontend() for message in all_msgs_og]
        all_msgs_filtered = filter(lambda msg: msg['id'] not in user.messages_sent and msg['is_active'], all_msgs)
        # Iterate through each potential message
        for msg in all_msgs_filtered:
            message = Messages.get(user.message_set, msg['id'])
            attributes = message.attr_list.as_dict()
            #debug_string = ""
            total_attrs = 0
            # Iterate through all attributes for a given message
            for attr, boolean in attributes.items():
                # Make sure that the attribute is marked at TRUE
                if not boolean: continue
                total_attrs += 1
                if attr in scored_attributes: # An attribute we've seen before, in a scored message
                    messages_scored[msg['id']] += scored_attributes[attr]
                    #debug_string += attr + ": " + str(scored_attributes[attr]) + ", "
                else: # An attribute that has never been scored
                    messages_scored[msg['id']] += scored_attributes['MESSAGE'] + self.unranked_attr_boost
                    #debug_string += attr + ": " + str((scored_attributes['MESSAGE'] + self.unranked_attr_boost)) + ", "
            # Sum scores for all attributes that were not seen in this message
            messages_scored[msg['id']] /= total_attrs
            # Round all scores to the nearest tenth
            messages_scored[msg['id']] = round(messages_scored[msg['id']], 1)
            #print("~%s~ %s %s"%(msg['id'], round(messages_scored[msg['id']], 1), debug_string))
        return messages_scored


    def get_word_rareness():
        all_msgs_og = Messages.query(user.message_set, Messages.id > 0)
        all_msgs = [message.to_frontend() for message in all_msgs_og]
        all_msgs_filtered = filter(lambda msg: msg['id'] not in user.messages_sent, all_msgs)
        token_scores = {}
        for msg in all_msgs_filtered:
            message = Messages.get(user.message_set, msg['id'])
            user_rating = user_obj.get_message_score_for_idx(user.message_response, msg_idx)
            if user_rating is None:
                continue
            print("%s;%s;%s"%(msg['id'], message.body, user_rating))
            clean_tokens = get_clean_tokens_from_message(message.body)
            for clean_token in clean_tokens:
                if clean_token not in token_scores:
                    token_scores[clean_token] = {
                        'absolute_count': 0
                    }
                token_scores[clean_token]['absolute_count'] += 1
        normalized_token_scores = {}
        for token, score_hash in token_scores.items():
            normalized_token_scores[token] = {
                'rareness': token_scores[token]['absolute_count'] / len(all_msgs)
            }
        return normalized_token_scores


    def get_clean_tokens_from_message(message):
        tokens = nltk.word_tokenize(message)
        clean_tokens = []
        for token in tokens:
            # Remove punctuation from tokens
            clean_token = token.translate(str.maketrans('', '', string.punctuation))
            clean_token = clean_token.lower()
            # Exclude tokens that are in our stopwords set, or have 1 or fewer characters
            if (clean_token in stopwords) or len(clean_token) <= 1:
                continue
            # Ensure each token is only counted once per message
            if clean_token not in clean_tokens:
                clean_tokens.append(clean_token)
        return clean_tokens


    def get_scored_words(message, message_score, weight, token_scores, dict_rareness, rareness_scores):
        clean_tokens = get_clean_tokens_from_message(message)
        rareness = 0
        rareness_count = 0
        for clean_token in clean_tokens:
            if clean_token not in token_scores:
                token_scores[clean_token] = {
                    'absolute_count': 0,
                    'absolute_score': 0
                }
            token_scores[clean_token]['absolute_count'] += 1
            token_scores[clean_token]['absolute_score'] += message_score
            if clean_token in dict_rareness:
                rareness += dict_rareness[clean_token]['rareness']
                rareness_count += 1
        overall_rareness = rareness / rareness_count
        rareness_scores[overall_rareness] = message_score
        return token_scores, rareness_scores


    # Returns a dictionary of attributes with weighted scores based on the user's
    # rating of messages with these attributes and the number of times each attribute
    # has been attached to a message that was shown to a user.
    def get_scored_attributes(self, user_obj, user):
        # Compute an average score per category the message has associated with it
        attribute_scores = {}
        #token_scores = {}
        #rareness_scores = {}
        rated_responses = [*user.message_response.keys()]
        rating_total = 0
        for msg_sent_idx in rated_responses:
            weight = max(self.historical_message_discount_factor**(len(rated_responses) - 1), 0.001) - int(msg_sent_idx)
            msg_idx = int(user.message_response[msg_sent_idx]['message_sent'])
            message = Messages.get(user.message_set, msg_idx)
            message_score = user_obj.get_message_score_for_idx(user.message_response, msg_idx)
            if message_score is None:
                continue
            #token_scores, rareness_scores = get_scored_words(message.body, message_score, weight, token_scores, dict_rareness, rareness_scores)
            rating_total += message_score
            attributes = message.attr_list.as_dict()
            attributes["WEIGHTED MESSAGE"] = True
            # Iterate through all attributes for a given message
            for attr, boolean in attributes.items():
                # Make sure that the attribute is marked as True
                if not boolean: continue
                if attr not in attribute_scores:
                    attribute_scores[attr] = {
                        'weighted_score': message_score*weight,
                        'weighted_count': weight,
                        'absolute_score': message_score,
                        'absolute_count': 1
                    }
                else:
                    attribute_scores[attr]['weighted_score'] += message_score*weight
                    attribute_scores[attr]['weighted_count'] += weight
                    attribute_scores[attr]['absolute_score'] += message_score
                    attribute_scores[attr]['absolute_count'] += 1
                #print("Added: %s, %s (%s) to %s = %s"%(message_score, weight, message_score*weight, attr, attribute_scores[attr]['weighted_score']))
        # Compute normalized scores for each attribute (taking into account the weighted_count for each)
        normalized_attribute_scores = {'MESSAGE': (rating_total + 0.01) / (len(rated_responses) + 0.01)}
        for attr, score_hash in attribute_scores.items():
            weighted_score = attribute_scores[attr]['weighted_score'] / attribute_scores[attr]['weighted_count']
            normalized_attribute_scores[attr] = weighted_score
        # Give a boost to preferred_attributes
        for attr, score_hash in attribute_scores.items():
            if attr in user.preferred_attrs:
                normalized_attribute_scores[attr] += self.preferred_attr_boost
        # Compute overall word scores for each word
        #normalized_token_scores = {}
        #for token, score_hash in token_scores.items():
        #    normalized_token_scores[token] = {}
        #    normalized_token_scores[token]['average_score'] = token_scores[token]['absolute_score'] / token_scores[token]['absolute_count']
        #    normalized_token_scores[token]['rareness']      = token_scores[token]['absolute_count'] / len(rated_responses)
        return normalized_attribute_scores#, normalized_token_scores, rareness_scores

    # Returns a dictionary of attributes with unweighted scores for the frontend
    def get_scored_attributes_for_frontend(self, user_obj, user):
        # Compute an average score per category the message has associated with it
        attribute_scores = {}
        #token_scores = {}
        #rareness_scores = {}
        rated_responses = [*user.message_response.keys()]
        rating_total = 0
        for msg_sent_idx in rated_responses:
            msg_idx = int(user.message_response[msg_sent_idx]['message_sent'])
            message = Messages.get(user.message_set, msg_idx)
            message_score = user_obj.get_message_score_for_idx(user.message_response, msg_idx)
            if message_score is None:
                continue
            rating_total += message_score
            attributes = message.attr_list.as_dict()
            top_ten_idx = max([int(x) for x in user.message_response.keys()]) - 10
            if (int(msg_sent_idx) > top_ten_idx):
                attributes["RECENT MESSAGE"] = True
            for attr, boolean in attributes.items():
                if not boolean: continue
                if attr not in attribute_scores:
                    attribute_scores[attr] = {
                        'absolute_score': message_score,
                        'absolute_count': 1
                    }
                else:
                    attribute_scores[attr]['absolute_score'] += message_score
                    attribute_scores[attr]['absolute_count'] += 1
        #print(attribute_scores)
        # Compute final scores for each attribute
        filtered_attrs = ['MESSAGE', 'RECENT MESSAGE', 'Activity', 'Directive', 'Diet', 'Self-care', 'Social', 'Positive Psychology',
            'Positive psychology', 'Overall diet', 'Diet: Fruit/Veg', 'Fat/Chol', 'Physical Activity', 'Activity', 'Sedentary Time']
        final_attr_scores = {}
        for attr, score_hash in attribute_scores.items():
            if attr not in filtered_attrs:
                continue
            final_score = round(attribute_scores[attr]['absolute_score'] / attribute_scores[attr]['absolute_count'], 1)
            final_attr_scores[attr] = final_score
        final_attr_scores['MESSAGE'] = round(rating_total / len(rated_responses), 1)

        return final_attr_scores


    def get_message_score_for_idx(self, message_response, msg_idx):
        for key in message_response.keys():
            if message_response[key]["message_sent"] == msg_idx:
                if 'message' in message_response[key]:
                    return int(message_response[key]['message'])
                else:
                    return None
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

    def save_direct_message(self, direction, message):
        u = Users.get(self.phone)
        next_key = '0'
        print(u.direct_message_response.keys())
        if (len(u.direct_message_response.keys()) > 0):
            next_key = int(sorted(u.direct_message_response.keys(), key=lambda x: int(x))[-1]) + 1
        u.direct_message_response[next_key] = {
            'direction': direction,
            'message'  : message,
            'timestamp': str(datetime.now())
        }
        u.save()

    def save_motivational_message(self, message):
        u = Users.get(self.phone)
        u.message_response[str(message.id)] = {
            'message_sent'  : message.id,
            'timestamp': str(datetime.now())
        }
        u.save()


    def handle_direct_message(self):
        if self.message_received.strip().lower() in ['stop','end']:
            u = Users.get(self.phone)
            u.update(
                actions=[
                    Users.send_message.set(False)
                ]
            )
            u.save()
        self.save_direct_message('incoming', self.message_received)

    def initiate_goal_setting_message(self, u):
        past_key = None
        new_key = 0
        prev_goal_hash = {
            'goal_type': None,
            'goal_subtype': None,
            'goal_amount': None,
        }
        if (len(u.weekly_goals_message_response.keys()) > 0):
            past_key = str(sorted(u.weekly_goals_message_response.keys(), key=lambda x: int(x))[-1])
            new_key = int(past_key) + 1
            prev_goal_hash = u.weekly_goals_message_response[past_key]
        decision_tree = self.get_first_decision_tree("goals", prev_goal_hash)
        u.weekly_goals_message_response[new_key] = {
            'goal_type': prev_goal_hash['goal_type'],
            'goal_subtype': prev_goal_hash['goal_subtype'],
            'goal_amount': prev_goal_hash['goal_amount'],
            'goal_recommendation': None,
            'status': 'ongoing',
            'responses': []
        }
        message = decision_tree.message
        if prev_goal_hash['goal_amount'] is not None:
            message = decision_tree.message.replace("[GOAL AMOUNT]", str(prev_goal_hash['goal_amount']), 1)
        u.weekly_goals_message_response[new_key]['responses'].append({
            'direction': 'outgoing',
            'message': message,
            'timestamp': str(datetime.now()),
            'decision_tree_id': decision_tree.id
        })
        u.save()
        print(message)
        self.send_goal_setting_sms(message)


    def initiate_progress_message(self, u, category="progress"):
        new_key = 0
        prev_goal_hash = {
            'goal_type': None,
            'goal_subtype': None,
            'goal_amount': None,
        }
        if (len(u.weekly_goals_message_response.keys()) > 0):
            new_key = str(sorted(u.weekly_goals_message_response.keys(), key=lambda x: int(x))[-1])
            prev_goal_hash = u.weekly_goals_message_response[new_key]
        decision_tree = self.get_first_decision_tree(category, prev_goal_hash)
        u.weekly_progress_message_response[new_key] = {
            'goal_type': prev_goal_hash['goal_type'],
            'goal_subtype': prev_goal_hash['goal_subtype'],
            'goal_amount': prev_goal_hash['goal_amount'],
            'enabler': None,
            'barrier': None,
            'status': 'ongoing',
            'decision_tree_ids': [],
            'responses': []
        }
        message = decision_tree.message
        if prev_goal_hash['goal_amount'] is not None and prev_goal_hash['goal_subtype'] is not None:
            goal_description = str(prev_goal_hash['goal_amount']) + " " + prev_goal_hash['goal_subtype']
            message = decision_tree.message.replace("[ENTER GOAL]", goal_description, 1)
        u.weekly_progress_message_response[new_key]['responses'].append({
            'direction': 'outgoing',
            'message': message,
            'timestamp': str(datetime.now()),
            'decision_tree_id': decision_tree.id,
        })
        u.save()
        print(message)
        self.send_goal_setting_sms(message)


    def get_first_decision_tree(self, type, prev_goal_hash):
        default_decision_tree = None
        matched_type_decision_tree = None
        matched_subtype_decision_tree = None
        for decision_tree in DecisionTrees.query(type, DecisionTrees.is_root == True):
            if (decision_tree.goal_type == prev_goal_hash['goal_type']):
                matched_type_decision_tree = decision_tree
            if (decision_tree.goal_subtype == prev_goal_hash['goal_subtype']):
                matched_subtype_decision_tree = decision_tree
            if (decision_tree.goal_type is None and decision_tree.goal_subtype is None):
                default_decision_tree = decision_tree

        if matched_subtype_decision_tree is not None:
            return matched_subtype_decision_tree
        elif matched_type_decision_tree is not None:
            return matched_type_decision_tree
        else:
            return default_decision_tree


    def handle_weekly_message(self):
        u = Users.get(self.phone)
        if self.message_received.strip().lower() in ['stop','end']:
            u.update(
                actions=[
                    Users.send_message.set(False)
                ]
            )
            u.save()

        if (len(u.weekly_goals_message_response.keys()) == 0):
            self.initiate_goal_setting_message(u)
            return

        # Exclude non-numeric responses
        response_val = self.message_received
        try:
            response_val = int(response_val.strip())
        except ValueError:
            self.send_goal_setting_sms(self.decision_tree_mistake_text)
            print(self.decision_tree_mistake_text)
            return

        # Identify what type of message we should be sending
        cur_key = sorted(u.weekly_goals_message_response.keys(), key=lambda x: int(x))[-1]
        cur_progress_key = -1
        if (len(u.weekly_progress_message_response.keys()) > 0):
            cur_progress_key = sorted(u.weekly_progress_message_response.keys(), key=lambda x: int(x))[-1]
        latest_goal_message = u.weekly_goals_message_response[cur_key]
        type = "goals"
        last_decision_tree_id = None
        if (cur_key == cur_progress_key):
            latest_progress_message = u.weekly_progress_message_response[cur_key]
            if (latest_progress_message['status'] == 'complete'):
                if u.message_set == "MASTERY":
                    type = "mastery"
                else:
                    self.initiate_goal_setting_message(u)
                    return
            else:
                outgoing_messages = [x for x in latest_progress_message['responses'] if x['direction'] == 'outgoing']
                last_decision_tree_id = outgoing_messages[-1]['decision_tree_id']
                if u.message_set == "MASTERY":
                    type = "mastery"
                else:
                    type = "progress"
        else:
            if (latest_goal_message['status'] == 'complete'):
                if u.message_set == "MASTERY":
                    type = "mastery"
                else:
                    self.initiate_progress_message(u)
                    return
            else:
                outgoing_messages = [x for x in latest_progress_message['responses'] if x['direction'] == 'outgoing']
                last_decision_tree_id = outgoing_messages[-1]['decision_tree_id']
                type = "goals"

        # Reset trees if response value is equal to the special reset value indicated to the user
        if response_val == 99:
            if type == "goals":
                u.weekly_goals_message_response.pop(cur_key, None)
                self.initiate_goal_setting_message(u)
            elif type == "progress":
                u.weekly_progress_message_response.pop(cur_progress_key, None)
                self.initiate_progress_message(u)
            u.save()
            return

        # Iterate over all decision trees to find the right match
        last_decision_tree = DecisionTrees.get(type, last_decision_tree_id)
        decision_trees = DecisionTrees.query(type, DecisionTrees.id > 0)
        criteria_met = 0
        matched_trees = {}
        for decision_tree in decision_trees:
            if decision_tree.parent_ids is not None:
                criteria_met += 1
                if last_decision_tree.id not in decision_tree.parent_ids:
                    continue

            if decision_tree.min_response_val is not None:
                criteria_met += 1
                if response_val < decision_tree.min_response_val or response_val > decision_tree.max_response_val:
                    continue

            if decision_tree.goal_type is not None:
                criteria_met += 1
                if latest_goal_message['goal_type'] != decision_tree.goal_type:
                    continue

            if decision_tree.goal_subtype is not None:
                criteria_met += 1
                if latest_goal_message['goal_subtype'] != decision_tree.goal_subtype:
                    continue  

            if decision_tree.min_goal_amount is not None:
                criteria_met += 1
                if latest_goal_message['goal_amount'] < decision_tree.min_goal_amount or response_val > decision_tree.max_goal_amount:
                    continue

            matched_trees[str(criteria_met)] = decision_tree

        # If no trees were matched, this was an invalid input
        if len(matched_trees) == 0:
            self.send_goal_setting_sms(self.decision_tree_mistake_text)
            print(self.decision_tree_mistake_text)
            return

        # Otherwise, we can move forward
        decision_tree_criteria_met = sorted(matched_trees.keys(), key=lambda x: int(x))[-1]
        decision_tree = matched_trees[decision_tree_criteria_met]

        # First, record the incoming message
        incoming_message = {
            'direction': 'incoming',
            'message': response_val,
            'timestamp': str(datetime.now()),
        }
        if (type == "goals"):
            u.weekly_goals_message_response[cur_key]['responses'].append(incoming_message)
        else:
            u.weekly_progress_message_response[cur_key]['responses'].append(incoming_message)

        # Then compute the outgoing message
        message = decision_tree.message
        if latest_goal_message['goal_amount'] is not None and "GOAL AMOUNT PLUS" in message:
            m = re.search("\[GOAL AMOUNT PLUS (.*)\]", message)
            recommended_goal_amount = int(m.group(1)) + latest_goal_message['goal_amount']
            message = message[:m.start()] + str(recommended_goal_amount) + message[m.end():]
            u.weekly_goals_message_response[cur_key]['goal_recommendation'] = recommended_goal_amount

        if latest_goal_message['goal_amount'] is not None and "GOAL AMOUNT MINUS" in message:
            m = re.search("\[GOAL AMOUNT MINUS (.*)\]", message)
            recommended_goal_amount = latest_goal_message['goal_amount'] - int(m.group(1))
            message = message[:m.start()] + str(recommended_goal_amount) + message[m.end():]
            u.weekly_goals_message_response[cur_key]['goal_recommendation'] = recommended_goal_amount

        # Save the outgoing message to the responses hash
        update_hash = u.weekly_goals_message_response[cur_key]
        if type == 'progress' or type == 'mastery':
            update_hash = u.weekly_progress_message_response[cur_key]
        update_hash['responses'].append({
            'direction': 'outgoing',
            'message': message,
            'timestamp': str(datetime.now()),
            'decision_tree_id': decision_tree.id,
        })

        # Record additional properties, based on the decision tree
        if decision_tree.is_terminal:
            update_hash['status'] = 'complete'
        if decision_tree.set_goal_type is not None:
            update_hash['goal_type'] = decision_tree.set_goal_type
        if decision_tree.set_goal_subtype is not None:
            update_hash['goal_subtype'] = decision_tree.set_goal_subtype
        if decision_tree.set_goal_amount is not None: # Only happens in the goals type
            if decision_tree.set_goal_amount == "RECOMMENDATION":
                update_hash['goal_amount'] = u.weekly_goals_message_response[cur_key]['goal_recommendation']
            else:
                update_hash['goal_amount'] = response_val
        if decision_tree.set_enabler is not None:  # Only happens in the progress type
            update_hash['enabler'] = decision_tree.set_enabler
            update_hash['responses'][-1]['enabler'] = decision_tree.set_enabler 
        if decision_tree.set_barrier is not None: # Only happens in the progress type
            update_hash['barrier'] = decision_tree.set_barrier
            update_hash['responses'][-1]['barrier'] = decision_tree.set_barrier

        u.save()
        print(message)
        self.send_goal_setting_sms(message)
        

    # The handle_message function specifically handles daily motivational text messages
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
            self.send_motivational_sms(None, 'Please reply with a rating for the previous message between 0 and 10. [0=not helpful at all and 10=very helpful]')
        else:
            u = Users.get(self.phone)
            # Make sure that we don't already have a rating for this message
            for k in u.message_response.keys():
                if u.message_response[k]["message_sent"] == u.prev_message and 'message' in u.message_response[k]:
                    self.send_motivational_sms(None, "You've already rated the previous message. Please wait for the next message to send another rating.")
                    return False
            # Create a new response entry
            new_dict = u.message_response
            new_dict[str(u.prev_message)]= {
                'message': self.message_received,
                'timestamp': str(datetime.now()),
                'message_sent': u.prev_message
            }
            u.update(actions=[
               Users.message_response.set(new_dict)
            ])
            u.save()
            self.log("Rated message index: " + str(u.prev_message) + " - Rating: " + str(self.message_received))
        return True


    # update_message_ratings takes an array of hashes in the following format:
    # [{
    #   'sent_at': timestamp (timestamp that starts with YYYY-MM-DD HH:MM:SS)
    #   'msg_id': message_being_rated,
    #   'rating': rating (int between 0 and 10)
    #  }, ... ]
    def update_message_ratings(self, update_arr):
        user_phones = set(int(row['phone']) for row in update_arr)
        users = []
        for user in Users.batch_get(list(user_phones)):
            users.append(user)
        for row in update_arr:
            user = [u for u in users if u.phone ==int(row['phone'])][0]
            sent_at = row['sent_at'][0:19]
            if len(sent_at) < 10:
                print("Could not process sent_at value in row: %s"%(row))
                continue
            new_message_responses = {}
            found = False
            # Test if we should be appending or replacing this rating
            action ="APPEND"
            sent_at_update_val = sent_at
            for j in sorted(user.message_response.keys(), key=lambda x: int(x)):
                rating_data = user.message_response[j]
                if rating_data['message_sent'] == row['msg_id']:
                    action = "REPLACE"
                    found = True
                    if 'timestamp' in rating_data:
                        sent_at_update_val = rating_data['timestamp']
            # Find the correct position to insert the rating
            for j in sorted(user.message_response.keys(), key=lambda x: int(x)):
                rating_data = user.message_response[j]
                if ((action == "APPEND" and sent_at_update_val <= rating_data['timestamp']) or
                    (action == "REPLACE" and rating_data['message_sent'] == row['msg_id'])):            
                    insert_id = j
                    for k in sorted(user.message_response.keys(), key=lambda x: int(x)):
                        if k < insert_id:
                            new_message_responses[k] = user.message_response[k]
                        elif k == insert_id:
                            # Insert current message
                            new_message_responses[k] = {
                                'message': str(row['rating']),
                                'message_sent': int(row['msg_id']),
                                'timestamp': sent_at_update_val
                            }
                            # Move previous message to new slot
                            if action == "APPEND":
                                new_id = str(int(k) + 1)
                                new_message_responses[new_id] = user.message_response[k]
                        elif k > insert_id:
                            new_id = k
                            if action == "APPEND":
                                new_id = str(int(k) + 1)
                            new_message_responses[new_id] = user.message_response[k]
                    found = True
                    break
            # If we didn't find the correct position, append to the end
            if not found:
                action = "APPEND"
                insert_id = '0'
                if (len(user.message_response.keys()) > 0):
                    insert_id = str(int(sorted(user.message_response.keys(), key=lambda x: int(x))[-1]) + 1)
                print("About to APPEND to end for %s"%(insert_id))
                new_message_responses = user.message_response
                new_message_responses[insert_id] = {
                                'message': str(row['rating']),
                                'timestamp': sent_at,
                                'message_sent': int(row['msg_id'])
                            }
        
            # Make the user update
            user.update(
                    actions=[
                        Users.message_response.set(new_message_responses), 
                        Users.messages_sent.add(int(row['msg_id'])),
                    ]
            )

            # Summarize changes
            print("sent_at: %s, eval: %s | id = %s, action=%s"%(sent_at, sent_at_update_val, insert_id, action))
            print(new_message_responses)
            print(user.messages_sent)

    def log(self, msg):
      print()
      print(msg)
      print()
