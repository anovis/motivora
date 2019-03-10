from chalicelib import app
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

        if (not user_class.is_user()) and user_class.message_received.lower() == 'join':
            user_class.add_user()
            message = Messages.get(message_set, 0)
            user_class.send_sms(message.body)

        elif user_class.should_set_time():
            user_class.update_time()
            user_class.send_sms('Thank you for your response. The time has been set.')

        else:
            user_class.handle_message()
            user_class.send_sms('Thank you for your feedback!')

        return {'data':200}
    except Exception as e:
      return {'error': str(e)}


