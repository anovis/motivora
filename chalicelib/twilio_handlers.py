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
        try:
          user = Users.get(phone)
          user_class = UserActions(phone, message_set=user.message_set, **parsed_request)
          user_class.handle_message()
        except Users.DoesNotExist:
          print("Received message from unenrolled user!")

        return Response(
          body='',
          status_code=200,
          headers={'Content-Type': 'text/plain'}
        )
    except Exception as e:
          print(e)
          sentry_sdk.capture_exception(e)
          return {'error': str(e)}

@app.route('/twilio/handle_direct_sms_response', methods=['GET','POST'], content_types=['application/x-www-form-urlencoded', 'application/json'], cors=True)
def handle_direct_sms_response():
    try:
        raw_request = app.current_request.raw_body
        print(raw_request)

        parsed_request = {key.decode(): val[0].decode().strip() for key, val in parse_qs(raw_request).items()}
        phone = parsed_request.get('From')
        #phone = "18479270519"
        #parsed_request = {'From': '18479270519', 'Body': 'hello, motivora!'}
        user_class = UserActions(phone, **parsed_request)

        if user_class.is_user():
          user_class.handle_direct_message()

        return Response(
          body='',
          status_code=200,
          headers={'Content-Type': 'text/plain'}
        )
    except Exception as e:
          print(e)
          sentry_sdk.capture_exception(e)
          return {'error': str(e)}

@app.route('/twilio/handle_goal_setting_response', methods=['GET','POST'], content_types=['application/x-www-form-urlencoded', 'application/json'], cors=True)
def handle_goal_setting_response():
    try:
        raw_request = app.current_request.raw_body
        print(raw_request)

        parsed_request = {key.decode(): val[0].decode().strip() for key, val in parse_qs(raw_request).items()}
        phone = parsed_request.get('From')
        # TODO only EBNHC for now
        message_set = "EBNHC"
        user_class = UserActions(phone, message_set=message_set, **parsed_request)

        # New user send "join"
        if not user_class.is_user():
            print("Received message from unenrolled user!")
        # User responding to each message with a rating
        else:
            user_class.send_goal_setting_sms("Message received, thank you!")

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

