from chalicelib import app
from chalice import Response
from chalicelib.models import Messages
from chalicelib.actions import UserActions
from urllib.parse import parse_qs

@app.route('/twilio/handle', methods=['GET','POST'], content_types=['application/x-www-form-urlencoded', 'application/json'], cors=True)
def handle_twilio():
    try:
        raw_request = app.current_request.raw_body
        parsed_request = {key.decode(): val[0].decode() for key, val in parse_qs(raw_request).items()}
        phone = parsed_request.get('From')
        # TODO only EBNHC for now
        message_set = "EBNHC"
        user_class = UserActions(phone, message_set=message_set, **parsed_request)

        # New user send "join"
        if (not user_class.is_user()) and user_class.message_received.lower() == 'join':
            user_class.add_user()
            message = Messages.get(message_set, 0)
            user_class.send_sms(message.body)
        # New user responding with time that they'd like to be messaged
        elif user_class.should_set_time():
            if 0 <= int(user_class.message_received) <= 24:
                user_class.update_time()
                user_class.send_sms('Thank you for your response. The time has been set.')
            else:
                user_class.send_sms('Please respond with the time that you would like to receive messages (a number between 0 and 24 - Eastern Timezone).')
        # User responding to each message with a rating
        else:
            user_class.handle_message()

        return Response(
          body='',
          status_code=200,
          headers={'Content-Type': 'text/plain'}
        )
    except Exception as e:
      return {'error': str(e)}


