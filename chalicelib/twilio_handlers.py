from chalicelib import app
from chalice import Response
from chalicelib.models import Messages
from chalicelib.actions import UserActions
from urllib.parse import parse_qs
import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration

sentry_sdk.init(dsn='https://dc96193451634aeca124f20398991f16@sentry.io/1446994',
                integrations=[AwsLambdaIntegration()])

@app.route('/twilio/handle', methods=['GET','POST'], content_types=['application/x-www-form-urlencoded', 'application/json'], cors=True)
def handle_twilio():
    try:
        raw_request = app.current_request.raw_body
        print(raw_request)

        parsed_request = {key.decode(): val[0].decode().strip() for key, val in parse_qs(raw_request).items()}
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
            if time_is_valid(user_class):
                user_class.update_time()
                user_class.send_sms('Thank you for your response. The time has been set.')
            else:
                user_class.send_sms('Please respond with the time that you would like to receive messages (a number between 0 and 23 - Eastern Timezone).')
        # User responding to each message with a rating
        else:
            user_class.handle_message()

        return Response(
          body='',
          status_code=200,
          headers={'Content-Type': 'text/plain'}
        )
    except Exception as e:
          print(e)
          sentry_sdk.capture_exception(e)
          return {'error': str(e)}

def time_is_valid(user_class):
    if user_class.is_int(user_class.message_received):
        return 0 <= int(user_class.message_received) <= 24
    else:
        return False

