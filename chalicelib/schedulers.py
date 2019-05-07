from chalicelib import app
from chalice import Rate
from datetime import datetime
from chalicelib.models import Users
from chalicelib.actions import UserActions

import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration

sentry_sdk.init(dsn='https://dc96193451634aeca124f20398991f16@sentry.io/1446994',
                integrations=[AwsLambdaIntegration()])

@app.schedule(Rate(1, unit=Rate.HOURS))
def every_hour(event):
    try:
        hour = datetime.now().hour
        user_list = Users.time_index.query(hour, Users.send_message == True)
        print("Fetching users with hour: " + str(hour))
        for user in user_list:
            user_obj = UserActions(**user.to_dict())
            print("Hour: " + str(hour), "Phone: " + str(user_obj.phone))
            # Only send for the first 28 days
            if user_obj.sent_messages_length() >= user_obj.total_days:
                print('Program ended (28 days) ' + str(user_obj.phone))
            else:
                print('Sending message to ' + str(user_obj.phone))
                is_successful = user_obj.send_next_sms()
                if is_successful:
                    user_obj.set_next_message()
                else:
                    sentry_sdk.capture_exception('Message sending unsuccessful for ' + str(user_obj.phone))
    except Exception as e:
      sentry_sdk.capture_exception(e)
      return {'error': str(e)}

