from chalicelib import app
from chalice import Rate
from datetime import datetime
from chalicelib.models import Users, Invocations
from chalicelib.actions import UserActions

import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration

sentry_sdk.init(dsn='https://dc96193451634aeca124f20398991f16@sentry.io/1446994',
                integrations=[AwsLambdaIntegration()])

@app.schedule(Rate(1, unit=Rate.HOURS))
def every_hour(event):
    hour = datetime.now().hour
    user_list = Users.time_index.query(hour, Users.send_message == True)
    print("Fetching users with send_message True and with hour: " + str(hour))
    # Iterate through users for this time
    for user in user_list:
        user_obj = UserActions(**user.to_dict())
        print("Hour: " + str(hour), "Phone: " + str(user_obj.phone))
        # Create invocation ID for today and this hour
        invocation_id = datetime.today().strftime('%Y-%m-%d:%H') + '-' + str(user_obj.phone)
        # Only send for users that haven't recieved a message for this Lambda invocation
        if user_obj.has_processed_for_invocation_id(invocation_id):
            print('Already processed ' + str(user_obj.phone) + ' for Invocation ID: ' + invocation_id)
        # Only send for the first 28 days
        elif user_obj.sent_messages_length() >= user_obj.total_days:
            print('Program ended (28 days) ' + str(user_obj.phone) + '. Setting send_message to False.')
            user.update(
                actions=[
                    Users.send_message.set(False)
                ]
            )
            user.save()
        else:
            print('Sending message to ' + str(user_obj.phone))
            is_successful = user_obj.send_next_sms()
            if is_successful:
                print('Setting next message')
                user_obj.set_next_message()
                # Keep track of the fact that we processed this user for this
                # Lambda invocation. Could be that we don't get to all of them
                # and so the Lambda function would automatically retry.
                print('Setting invocation ID')
                new_invocation = Invocations(
                    invocation_id=invocation_id
                )
                new_invocation.save()
            else:
                print('Message sending unsuccessful for ' + str(user_obj.phone))
                sentry_sdk.capture_exception('Message sending unsuccessful for ' + str(user_obj.phone))

