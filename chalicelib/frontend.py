from chalicelib import app
from chalicelib.models import Messages, Users, Invocations
from chalice import Response
from chalicelib.actions import UserActions
from collections import defaultdict
from datetime import datetime
import pdb

# TODO only works for one message set currently
message_set = "EBNHC"

# Returns all messages
@app.route('/messages', methods=['GET'], cors=True)
def list_messages():
  messages = Messages.query(message_set, Messages.id >= 0)
  message_list = [message.to_frontend() for message in messages]
  return {"data":message_list}

# Updates a message
@app.route('/messages', methods=['PUT'], cors=True)
def update_message():
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


