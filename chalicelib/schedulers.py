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
        print("Hour " + hour, "Users " + len(list(user_list)))
        for user in user_list:
            print(hour, user.to_dict())
            user_obj = UserActions(**user.to_dict())
            # Only send for the first 28 days
            if user_obj.sent_messages_length() >= user_obj.total_days: return 'Program ended (28 days)'
            is_successful = user_obj.send_next_sms()
            if is_successful:
                user_obj.send_sms('How helpful was this message? [Scale of 0-10, with 0=not helpful at all and 10=very helpful]')
                user_obj.set_next_message()
    except Exception as e:
      sentry_sdk.capture_exception(e)
      return {'error': str(e)}

