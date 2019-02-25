from chalicelib import app
from chalicelib.models import Messages, Users
from chalice import Response
from chalicelib.actions import UserActions
from collections import defaultdict
# TODO remove v
import pdb

# TODO only works for one message set currently
message_set = "EBNHC"

# Returns all messages
@app.route('/messages', methods=['GET'], cors=True)
def list_messages():
  messages = Messages.query(message_set, Messages.id >= 0)
  message_list = [message.to_frontend() for message in messages]
  return {"data":message_list}

# Allows for creating a new message in the message set
@app.route('/messages', methods=['POST'], cors=True)
def post_messages():
  payload = app.current_request.json_body
  print(payload)
  try:
    # Create each new message
    current_largest_id = get_current_largest_message_id()
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
  users = Users.scan(Users.message_set == message_set)
  user_list = [user.to_frontend() for user in users]
  return {"data": user_list}

#
# Utility functions
#

# Get the largest ID of existing messages
def get_current_largest_message_id():
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


