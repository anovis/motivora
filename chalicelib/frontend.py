from chalicelib import app
from chalicelib.models import Messages, Users
from chalice import Response
from chalicelib.actions import UserActions
from collections import defaultdict

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

@app.route('/test', methods=['GET'], cors=True)
def test():
  user = Users.get(17602147229)
  user_obj = UserActions(**user.to_dict())
  # Only send for the first 28 days
  if user_obj.sent_messages_length() >= user_obj.total_days: return 'Program ended (28 days)'
  is_successful = user_obj.send_next_sms()
  if is_successful:
      user_obj.send_sms('How helpful was this message? [Scale of 0-10, with 0=not helpful at all and 10=very helpful]')
      user_obj.set_next_message()
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


