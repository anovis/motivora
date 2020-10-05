from chalicelib import app
from chalicelib.models import Messages, Users, Invocations, DecisionTrees
from chalice import Response
from chalicelib.actions import UserActions, MessageActions
from collections import defaultdict
from datetime import datetime
import pdb

DEFAULT_MESSAGE_SET = "EBNHC"

# Returns all messages
@app.route('/messages', methods=['GET'], cors=True)
def list_messages():
  # In use in the interface
  message_set = app.current_request.query_params.get('message_set')
  if message_set is None:
    message_set = DEFAULT_MESSAGE_SET
  messages = Messages.query(message_set, Messages.id >= 0)
  message_list = [message.to_frontend() for message in messages]
  return {"data":message_list}

@app.route('/messages/attributes', methods=['GET'], cors=True)
def list_messages():
  payload = app.current_request.json_body
  message_set = DEFAULT_MESSAGE_SET
  if payload is not None and 'data' in payload and 'message_set' in payload['data']:
    message_set = payload['message_set']
  messages = Messages.query(message_set, Messages.id >= 0)
  users    = Users.query(message_set, Messages.id >= 0)
  attributes = {}
  for message in messages:
    for attr_name, attr_val in message.attr_list.as_dict().items():
      if attr_name not in attributes:
        attributes[attr_name] = {'message_ids': []}
      attributes[attr_name]['message_ids'].append(message.id)

  return {"data":attributes}

# Updates a message
@app.route('/messages', methods=['PUT'], cors=True)
def update_message():
  payload = app.current_request.json_body
  message_set = DEFAULT_MESSAGE_SET
  if payload is not None and 'data' in payload and 'message_set' in payload['data']:
    message_set = payload['message_set']
  message_id = int(app.current_request.json_body['data']['id'])
  message_json = app.current_request.json_body['data']
  try:
    message = Messages.get(message_set, message_id)
    if 'body' in message_json:
      message.update(actions=[
        Messages.body.set(message_json['body'])
      ])
    if 'body_en' in message_json:
      message.update(actions=[
        Messages.body_en.set(message_json['body_en'])
      ])
    if 'body_es' in message_json:
      message.update(actions=[
        Messages.body_es.set(message_json['body_es'])
      ])
    if 'is_active' in message_json:
      isActive = (message_json['is_active'] == 'true')
      message.update(actions=[
        Messages.is_active.set(isActive)
      ])
    return Response(
      body='Success',
      status_code=200,
      headers={'Content-Type': 'text/plain'}
    )
  except Exception as e:
    print(e)
    return Response(
      body='Something went wrong while trying to update your message.',
      status_code=500,
      headers={'Content-Type': 'text/plain'}
    )


# Allows for creating a new message in the message set
@app.route('/messages', methods=['POST'], cors=True)
def post_messages():
  payload = app.current_request.json_body
  message_sets = set(elem['message_set'] for elem in payload['messages'])
  messages = []
  for message_set in list(message_sets):
    for m in Messages.query(message_set, Messages.id >= 0):
      messages.append(m)
  # Create each new message
  for m in payload['messages']:
    id = int(m['id'])
    matching_messages = [elem for elem in messages if elem.id == id and elem.message_set == m['message_set']]
    attributes = format_message_attributes_for_model(m['attributes'])
    if len(matching_messages) > 0:
      message = matching_messages[0]
    else:
      message = Messages(
        id=id,
        message_set=message_set,
        attr_list=attributes,
        total_attr=len(m['attributes'])
      )
    # Add appropriate message variables depending on what was provided by the user
    if 'body' in m:
      message.body = m['body']
    if 'body_en' in m:
      message.body_en = m['body_en']
    if 'body_es' in m:
      message.body_es = m['body_es']
    if 'is_active' in m:
      message.is_active = (m['is_active'] == 'true')
    if 'attributes' in m:
      message.attr_list = attributes
    message.save()
  #except Exception as e:
  #  print(e)
  #  return Response(
  #    body=e.print_stack(),
  #    status_code=500,
  #    headers={'Content-Type': 'text/plain'}
  #  )
  return Response(
    body='Success',
    status_code=200,
    headers={'Content-Type': 'text/plain'}
  )

# Allows for creating or updating a user
@app.route('/user', methods=['POST'], cors=True)
def post_user():
  payload = app.current_request.json_body
  phone = int(payload['phone'])
  try:
    user = Users.get(phone)
  except Users.DoesNotExist:
    user = Users(phone)
    user.message_set = DEFAULT_MESSAGE_SET
    user.messages_sent = []
    user.message_response = {}
    user.weekly_goals_message_response = {}
    user.direct_message_response = {}
    user.send_message = False
    user.save()

  try:
    if 'message_set' in payload:
      user.update(actions=[Users.message_set.set(payload['message_set'])]) 
  
    if 'lang_code' in payload:
      user.update(actions=[Users.lang_code.set(payload['lang_code'])]) 
  
    if 'time' in payload:
      user.update(actions=[Users.time.set(int(payload['time']))]) 
  
    if 'preferred_attrs' in payload:
      user.update(actions=[Users.preferred_attrs.set(payload['preferred_attrs'])]) 

    if 'send_message' in payload:
      sendMessage = (payload['send_message'] == 'true');
      user.update(actions=[Users.send_message.set(sendMessage)]) 

    if 'is_real_user' in payload:
      sendMessage = (payload['is_real_user'] == 'true');
      user.update(actions=[Users.is_real_user.set(sendMessage)]) 

  except Exception as e:
    print(e)
    return Response(
      body='Something went wrong while trying to add your messages.',
      status_code=500,
      headers={'Content-Type': 'text/plain'}
    )
  user = Users.get(phone)
  return Response(
    body=user.to_frontend(),
    status_code=200,
    headers={'Content-Type': 'text/plain'}
  )

# Returns all users
@app.route('/users', methods=['GET'], cors=True)
def list_users():
  # In use in the interface
  message_set = app.current_request.query_params.get('message_set')
  if message_set is None:
    message_set = DEFAULT_MESSAGE_SET
  users = Users.scan(Users.message_set == message_set)
  user_list = [user.to_frontend() for user in users]
  return {"data": user_list}

@app.route('/users/message_history', methods=['GET'], cors=True)
def get_message_history():
  # In use in the interface
  payload = app.current_request.json_body
  phone = int(app.current_request.query_params.get('phone'))
  user = Users.get(phone)
  since_timestamp = app.current_request.query_params.get('since')

  user_obj = UserActions(**user.to_dict())
  all_messages = []
  for i, daily_message_data in user.message_response.items():
    if since_timestamp is not None and since_timestamp.replace("T", " ") > daily_message_data["timestamp"].replace("T", " "):
      continue
    message = Messages.get(user.message_set, int(daily_message_data["message_sent"]))
    body = message.get_body(user.lang_code)
    attrs = list(message.attr_list.as_dict().keys())
    message_rating = "-"
    if "message" in daily_message_data:
      message_rating = int(daily_message_data["message"])
    all_messages.append({
      "rating": message_rating,
      "timestamp": daily_message_data["timestamp"],
      "data_type": "message",
      "id": message.id,
      "body": body,
      "attrs": attrs,
      "category": "daily",
      "direction": "outgoing"
    })
  for i, direct_message_data in user.direct_message_response.items():
    if since_timestamp is not None and since_timestamp.replace("T", " ") > direct_message_data["timestamp"].replace("T", " "):
      continue
    direct_message = direct_message_data
    direct_message["category"] = "direct"
    all_messages.append(direct_message)
  for i, weekly_goals_data in user.weekly_goals_message_response.items():
    for message in weekly_goals_data["responses"]:
      if since_timestamp is not None and since_timestamp.replace("T", " ") > message["timestamp"].replace("T", " "):
        continue
      all_messages.append({
        "timestamp": message['timestamp'],
        "data_type": "decision_tree",
        "body": message['message'],
        "attrs": [],
        "category": "weekly_goals",
        "direction": message['direction']
      })
      if 'decision_tree_id' in message:
        all_messages[-1]['id'] = message['decision_tree_id']

  for i, weekly_goals_data in user.weekly_progress_message_response.items():
    for message in weekly_goals_data["responses"]:
      if since_timestamp is not None and since_timestamp.replace("T", " ") > message["timestamp"].replace("T", " "):
        continue
      all_messages.append({
        "timestamp": message['timestamp'],
        "data_type": "decision_tree",
        "body": message['message'],
        "attrs": [],
        "category": "weekly_progress",
        "direction": message['direction']
      })
      if 'decision_tree_id' in message:
        all_messages[-1]['id'] = message['decision_tree_id']
      if 'enabler' in message:
        all_messages[-1]['enabler'] = message['enabler']
      if 'barrier' in message:
        all_messages[-1]['barrier'] = message['barrier']

  m = list(user.messages_sent)
  return Response(
    body={"data": all_messages},
    status_code=200,
    headers={'Content-Type': 'text/plain'}
  )

@app.route('/users/direct_message_history', methods=['GET'], cors=True)
def get_message_history():
  payload = app.current_request.json_body
  user = Users.get(payload['phone'])
  return Response(
    body={"direct_messages": user.direct_message_response},
    status_code=200,
    headers={'Content-Type': 'text/plain'}
  )

@app.route('/messages/get_stats', methods=['GET'], cors=True)
def direct_message_stats():
  # In use in the interface
  message_set = app.current_request.query_params.get('message_set')
  message_id = int(app.current_request.query_params.get('id'))
  message = Messages.get(message_set, message_id)
  stats = MessageActions().get_stats(message)
  stats.update(message.to_frontend())
  return Response(
    body=stats,
    status_code=200,
    headers={'Content-Type': 'text/plain'}
  )

@app.route('/users/attrs', methods=['GET'], cors=True)
def get_ranked_attrs():
  phone = int(app.current_request.query_params.get('phone'))
  user = Users.get(phone)
  user_obj = UserActions(**user.to_dict())
  try:
    ranked_attrs = user_obj.get_scored_attributes_for_frontend(user_obj, user)
  except Exception as e:
    print(e)
    return Response(
      body='Something went wrong while trying to send your message.',
      status_code=500,
      headers={'Content-Type': 'text/plain'}
    )
  return Response(
    body={"data": {"ranked_attrs": ranked_attrs, "preferred_attrs": list(user.preferred_attrs)}},
    status_code=200,
    headers={'Content-Type': 'text/plain'}
  )

# Sends a direct message to a user
@app.route('/users/send_message', methods=['POST'], cors=True)
def send_direct_message_to_user():
  # In use in the interface
  print("send_message")
  payload = app.current_request.json_body
  phone_number = int(payload['phone_number'])
  message      = payload['message']
  user = Users.get(phone_number)
  user_obj = UserActions(**user.to_dict())
  try:
    user_obj.send_direct_message_sms(message)
  except Exception as e:
    print(e)
    return Response(
      body='Something went wrong while trying to send your message.',
      status_code=500,
      headers={'Content-Type': 'text/plain'}
    )
  return Response(
    body='Success',
    status_code=200,
    headers={'Content-Type': 'text/plain'}
  )

@app.route('/users/add_message_rating', methods=['POST'], cors=True)
def add_message_rating():
  # In use in the interface
  print("add_message_rating")
  payload = app.current_request.json_body
  update_arr   = payload['message_ratings']
  phone        = int(payload['message_ratings'][0]['phone'])
  user = Users.get(phone)
  user_obj = UserActions(**user.to_dict())
  try:
    user_obj.update_message_ratings(update_arr)
  except Exception as e:
    print(e)
    return Response(
      body='Something went wrong while trying to send your message.',
      status_code=500,
      headers={'Content-Type': 'text/plain'}
    )
  return Response(
    body='Success',
    status_code=200,
    headers={'Content-Type': 'text/plain'}
  )

# Test endpoint only used locally
@app.route('/test', methods=['GET'], cors=True)
def test():
  hour = 1
  user = Users.get(17818194295)
  user_obj = UserActions(**user.to_dict())
  print("Hour: " + str(hour), "Phone: " + str(user_obj.phone))
  invocation_id = datetime.today().strftime('%Y-%m-%d:%H') + '-' + str(user_obj.phone)
  # Only send for users that haven't recieved a message for this Lambda invocation
  if user_obj.has_processed_for_invocation_id(invocation_id):
      print('Already processed ' + str(user_obj.phone) + ' for Invocation ID: ' + invocation_id)
  # Only send for the first 28 days
  elif user_obj.sent_messages_length() >= user_obj.total_days:
      print('Program ended (28 days) ' + str(user_obj.phone))
  else:
      print('Sending message to ' + str(user_obj.phone))
      is_successful = user_obj.send_next_sms()
      if is_successful:
          user_obj.set_next_message()
          # Keep track of the fact that we processed this user for this
          # Lambda invocation. Could be that we don't get to all of them
          # and so the Lambda function would automatically retry.
          new_invocation = Invocations(
              invocation_id=invocation_id
          )
          new_invocation.save()
      else:
          sentry_sdk.capture_exception('Message sending unsuccessful for ' + str(user_obj.phone))
  return False

#
# Utility functions
#

# Get the largest ID of existing messages
def get_current_largest_message_id(message_set):
  highest_id = 0
  all_messages = Messages.query(message_set)
  for msg in all_messages:
    if msg.id > highest_id:
      highest_id = msg.id
  return highest_id

# Format attributes array so that we can save them the way the model wants them
def format_message_attributes_for_model(attributes):
  formatted_attrs = defaultdict(int)
  for attr in attributes:
    formatted_attrs[attr] = True
  return formatted_attrs

