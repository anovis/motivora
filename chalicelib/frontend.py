from chalicelib import app
from chalicelib.models import Messages, Users, Invocations, DecisionTrees
from chalice import Response
from chalicelib.actions import UserActions
from collections import defaultdict
from datetime import datetime
import pdb

# TODO only works for one message set currently
DEFAULT_MESSAGE_SET = "EBNHC"

# Returns all messages
@app.route('/messages', methods=['GET'], cors=True)
def list_messages():
  payload = app.current_request.json_body
  message_set = DEFAULT_MESSAGE_SET
  if payload is not None and 'data' in payload and 'message_set' in payload['data']:
    message_set = payload['message_set']
  messages = Messages.query(message_set, Messages.id >= 0)
  message_list = [message.to_frontend() for message in messages]
  return {"data":message_list}

# Updates a message
@app.route('/messages', methods=['PUT'], cors=True)
def update_message():
  payload = app.current_request.json_body
  message_set = DEFAULT_MESSAGE_SET
  if payload is not None and 'data' in payload and 'message_set' in payload['data']:
    message_set = payload['message_set']
  message_id = int(app.current_request.json_body['data']['id'])
  new_message = app.current_request.json_body['data']['message']
  try:
    message = Messages.get(message_set, message_id)
    message.update(actions=[
      Messages.body.set(new_message)
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
  print(payload)
  try:
    # Create each new message
    current_largest_id = get_current_largest_message_id(payload['data']['messageSetName'])
    for message in payload['data']['messages']:
      current_largest_id += 1
      new_message = Messages(
        id=current_largest_id,
        message_set=payload['data']['messageSetName'],
        attr_list=format_message_attributes_for_model(message['attributes']),
        body=message['message'],
        total_attr=len(message['attributes']),
        seq=str(current_largest_id)
      )
      new_message.save()
  except Exception as e:
    print(e)
    return Response(
      body='Something went wrong while trying to add your messages.',
      status_code=500,
      headers={'Content-Type': 'text/plain'}
    )
  return Response(
    body='Success',
    status_code=200,
    headers={'Content-Type': 'text/plain'}
  )

# Returns all users
@app.route('/users', methods=['GET'], cors=True)
def list_users():
  payload = app.current_request.json_body
  message_set = DEFAULT_MESSAGE_SET
  if payload is not None and 'data' in payload and 'message_set' in payload['data']:
    message_set = payload['message_set']
  users = Users.scan(Users.message_set == message_set)
  user_list = [user.to_frontend() for user in users]
  return {"data": user_list}

# Sends a direct message to a user
@app.route('/users/send_message', methods=['POST'], cors=True)
def send_direct_message_to_user():
  print("send_message")
  payload = app.current_request.json_body
  phone_number = payload['phone_number']
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

# Params must be a hash with two keys:
#   phone_number: Must be an 11-digit int, starting with 1
#   message_ratings: Must be an array of JSON hashes that follows the format described by update_message_ratings
@app.route('/users/add_message_rating', methods=['POST'], cors=True)
def send_direct_message_to_user():
  print("add_message_rating")
  payload = app.current_request.json_body
  update_arr   = payload['message_ratings']
  phone        = payload['phone_number']
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

