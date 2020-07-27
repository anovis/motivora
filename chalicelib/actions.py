import os
from twilio.rest import Client
from chalicelib.models import Messages, Users, DecisionTrees, Invocations
from collections import defaultdict
from datetime import datetime, timedelta
import random
from heapq import nlargest
import pdb

import string
#import nltk
#from nltk.corpus import stopwords
#from chalicelib.actions import UserActions

import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration

sentry_sdk.init(dsn='https://dc96193451634aeca124f20398991f16@sentry.io/1446994',
                integrations=[AwsLambdaIntegration()])

class MessageActions:
    def __init__(self, message_id, message_set):
        self.id = message_id
        self.message_set = message_set

    def get_stats(self):
        total_sent = 0
        total_rated = 0
        total_rating = 0
        for user in Users.scan(Users.message_set == self.message_set):
            if user.message_set != self.message_set:
                continue
            if (self.id in user.messages_sent):
                total_sent += 1
                for k, v in user.message_response.items():
                    if v['message_sent'] == self.id:
                        total_rated += 1
                        total_rating += int(v['message'])
                        break
        avg_rating = 0
        if total_rated > 1:
            avg_rating = total_rating * 1.0 / total_rated
        return {
            'total_sent': total_sent,
            'total_rated': total_rated,
            'average_rating': round(avg_rating, 1)
        }

class UserActions:
    def __init__(self, phone, **kwargs):
        # Twilio phone numbers
        self.motivational_phone_number   = os.environ.get('MOTIVATIONAL_PHONE')
        self.goal_setting_phone_number   = os.environ.get('GOAL_SETTING_PHONE')
        self.direct_message_phone_number = os.environ.get('DIRECT_MESSAGE_PHONE')

        # Reminder message config
        self.reminder_message_text = "Hi! Rating messages is one way we know which ones are most helpful. Please rate the messages you receive, as this will help us send you the most useful messages we can!"
        self.decision_tree_mistake_text = " is not a valid answer. Please try again."
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
        self.prob_of_selection_on_iteration = 0. # Minimal boost for top messages

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

    # Retrieves the next message to be sent, formats it appropriately, and triggers the SMS sending
    def send_next_sms(self, is_test=False):
        user = Users.get(self.phone)
        try:
            rating_request = '\n\nHow helpful was this message? [Scale of 0-10, with 0=not helpful at all and 10=very helpful]'
            next_message_id = self.get_next_message()
            message = Messages.get(user.message_set, next_message_id)
            self.last_message_sent = next_message_id;
            body = self.get_message_body(message)
            if is_test:
                print("Would send messge: %s"%(body + rating_request + self.get_anti_spam_message()))
            else:
                self.send_motivational_sms(body + rating_request + self.get_anti_spam_message())
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
            self.send_motivational_sms(self.reminder_message_text)
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

    def send_motivational_sms(self, message):
        self.send_sms(message, self.motivational_phone_number)

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
        next_message = self.get_recommended_message()
        message = Messages.get(u.message_set, next_message)
        log_message = message.to_json()
        log_message['attr_list'] = message.to_json()['attr_list'].as_dict()
        self.log("Chosen next message: " + str(log_message))
        return next_message

    def sent_messages_length(self):
        user = Users.get(self.phone)
        return len(user.messages_sent) if user.messages_sent != None else 0

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
        all_msgs_filtered = filter(lambda msg: msg['id'] not in user.messages_sent, all_msgs)
        # Iterate through each potential message
        for msg in all_msgs_filtered:
            message = Messages.get(user.message_set, msg['id'])
            attributes = message.attr_list.as_dict()
            # Iterate through all attributes for a given message
            for attr, boolean in attributes.items():
                # Make sure that the attribute is marked at TRUE
                if not boolean: continue
                if attr in scored_attributes: # An attribute we've seen before, in a scored message
                    messages_scored[msg['id']] += scored_attributes[attr]
                else: # An attribute that has never been scored
                    messages_scored[msg['id']] += scored_attributes['MESSAGE'] + self.unranked_attr_boost
            # Sum scores for all attributes that were not seen in this message
            messages_scored[msg['id']] /= self.total_attr_count
            # Round all scores to the nearest tenth
            messages_scored[msg['id']] = round(messages_scored[msg['id']], 1)
        return messages_scored


    def get_word_rareness():
        all_msgs_og = Messages.query(user.message_set, Messages.id > 0)
        all_msgs = [message.to_frontend() for message in all_msgs_og]
        all_msgs_filtered = filter(lambda msg: msg['id'] not in user.messages_sent, all_msgs)
        token_scores = {}
        for msg in all_msgs_filtered:
            message = Messages.get(user.message_set, msg['id'])
            user_rating = user_obj.get_message_score_for_idx(user.message_response, msg_idx)
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
            weight = (self.historical_message_discount_factor)**((len(rated_responses) - 1) - int(msg_sent_idx))
            msg_idx = int(user.message_response[msg_sent_idx]['message_sent'])
            message = Messages.get(user.message_set, msg_idx)
            message_score = user_obj.get_message_score_for_idx(user.message_response, msg_idx)
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
        normalized_attribute_scores = {'MESSAGE': rating_total / len(rated_responses)}
        for attr, score_hash in attribute_scores.items():
            weighted_score = attribute_scores[attr]['weighted_score'] / attribute_scores[attr]['weighted_count']
            normalized_attribute_scores[attr] = weighted_score
        # Give a boost to preferred_attributes
        for attr, score_hash in attribute_scores.items():
            if attr in user.preferred_attrs:
                normalized_attribute_scores[attr] += normalized_attribute_scores["WEIGHTED MESSAGE"]
        # Compute overall word scores for each word
        #normalized_token_scores = {}
        #for token, score_hash in token_scores.items():
        #    normalized_token_scores[token] = {}
        #    normalized_token_scores[token]['average_score'] = token_scores[token]['absolute_score'] / token_scores[token]['absolute_count']
        #    normalized_token_scores[token]['rareness']      = token_scores[token]['absolute_count'] / len(rated_responses)
        return normalized_attribute_scores#, normalized_token_scores, rareness_scores


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


    def handle_direct_message(self):
        self.save_direct_message('incoming', self.message_received)

    def handle_goal_setting_message(self):
        u = Users.get(self.phone)
        cur_key = '-1'
        print(u.weekly_goals_message_response.keys())
        if (len(u.weekly_goals_message_response.keys()) > 0):
            cur_key = sorted(u.weekly_goals_message_response.keys(), key=lambda x: int(x))[-1]
        if cur_key not in u.weekly_goals_message_response.keys() or u.weekly_goals_message_response[cur_key]['status'] == 'complete':
            cur_key = str(int(cur_key) + 1)
            decision_tree = DecisionTrees.get(200000)
            u.weekly_goals_message_response[cur_key] = {
                'goal': self.message_received,
                'status': 'ongoing',
                'decision_tree_ids': []
            }
            message = decision_tree.message.replace("[ENTER GOAL]", u.weekly_goals_message_response[cur_key]['goal'], 1)
        else:
            last_decision_tree_id = u.weekly_goals_message_response[cur_key]['decision_tree_ids'][-1]
            decision_trees = DecisionTrees.parent_id_index.query(last_decision_tree_id)
            try:
                next_choice = int(self.message_received)
            except ValueError:
                self.send_goal_setting_sms("'%s'%s"%(self.message_received,self.decision_tree_mistake_text))
                return
            decision_tree = None
            for d in decision_trees:
                print("%s, %s, %s"%(d.min_response_val, d.max_response_val, next_choice))
                if (d.min_response_val <= next_choice and d.max_response_val >= next_choice):
                    print("%s, %s"%(d.goal, u.weekly_goals_message_response[cur_key]['goal']))
                    if (d.goal is None or d.goal.lower() == u.weekly_goals_message_response[cur_key]['goal']):
                        decision_tree = d
                        break
            if decision_tree is None:
                self.send_goal_setting_sms("'%s'%s"%(self.message_received,self.decision_tree_mistake_text))
                return
            message = decision_tree.message
        u.weekly_goals_message_response[cur_key]['decision_tree_ids'].append(decision_tree.id)
        if decision_tree.is_terminal:
            u.weekly_goals_message_response[cur_key]['status'] = 'complete'
        u.save()
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
            self.send_motivational_sms('Please reply with a rating for the previous message between 0 and 10. [0=not helpful at all and 10=very helpful]')
        else:
            u = Users.get(self.phone)
            # Make sure that we don't already have a rating for this message
            for k in u.message_response.keys():
                if u.message_response[k]["message_sent"] == u.prev_message:
                    self.send_motivational_sms("You've already rated the previous message. Please wait for the next message to send another rating.")
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


    # update_message_ratings takes an array of hashes in the following format:
    # [{
    #   'sent_at': timestamp (timestamp that starts with YYYY-MM-DD HH:MM:SS)
    #   'msg_id': message_being_rated,
    #   'rating': rating (int between 0 and 10)
    #  }, ... ]
    #
    # Note that only 1 rated message can be considered per calendar day.
    def update_message_ratings(self, update_arr):
        user = Users.get(self.phone)
        for row in update_arr:
            sent_at = row['sent_at'][0:19]
            if len(sent_at) < 10:
                print("Could not process sent_at value in row: %s"%(row))
                continue
            new_message_responses = {}
            found = False
            for j in sorted(user.message_response.keys(), key=lambda x: int(x)):
                rating_data = user.message_response[j]
                if sent_at[0:10] <= rating_data['timestamp'][0:10]:
                    action = "APPEND"
                    if (sent_at[0:10] == rating_data['timestamp'][0:10]):
                        action = "REPLACE"
                    
                    insert_id = j
                    for k in sorted(user.message_response.keys(), key=lambda x: int(x)):
                        if k < insert_id:
                            new_message_responses[k] = user.message_response[k]
                        elif k == insert_id:
                            # Insert current message
                            new_message_responses[k] = {
                                'message': str(row['rating']),
                                'timestamp': sent_at,
                                'message_sent': int(row['msg_id'])
                            }
                            # Move previous message to new slot
                            new_id = str(int(k) + 1)
                            new_message_responses[new_id] = user.message_response[k]
                        elif k > insert_id:
                            new_id = k
                            if action == "APPEND":
                                new_id = str(int(k) + 1)
                            new_message_responses[new_id] = user.message_response[k]
                    found = True
                    break
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
        
            # Summarize changes
            print("sent_at: %s, eval: %s | id = %s, action=%s"%(sent_at, rating_data['timestamp'], insert_id, action))
            print(new_message_responses)
        
            # Make the user update
            user.update(
                    actions=[
                        Users.message_response.set(new_message_responses), 
                        Users.messages_sent.add(int(row['msg_id'])),
                    ]
            )

    def log(self, msg):
      print()
      print(msg)
      print()
