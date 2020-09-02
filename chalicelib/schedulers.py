from chalicelib import app
from chalice import Rate
from datetime import datetime
from chalicelib.models import Users, Invocations
from chalicelib.actions import UserActions, MessageActions

import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration

sentry_sdk.init(dsn='https://dc96193451634aeca124f20398991f16@sentry.io/1446994',
                integrations=[AwsLambdaIntegration()])

@app.schedule(Rate(1, unit=Rate.HOURS))
def calculate_stats(event):
    message_sets = ["EBNHC", "Text4Health"]
    for message_set in message_sets:
        print("Computing updated stats for message set: %s"%(message_set))
        MessageActions().get_all_messages_with_stats(message_set)
    print("Completed update")

@app.schedule(Rate(1, unit=Rate.HOURS))
def every_hour(event):
    # Convert the UTC time to the ET time that is stored in the database
    hour = get_et_hour()
    user_list = Users.time_index.query(hour, Users.send_message == True)
    print("Fetching users with send_message True and with hour: " + str(hour))
    # Iterate through users for this time
    for user in user_list:
        process_message(user)

# Use this scheduler to test what will happen if the user was sent a message right away
@app.schedule(Rate(5, unit=Rate.MINUTES))
def every_minute(event):
    # Add phone numbers here that you want to send a make-up message to
    phone_numbers = [14196150311, 17812497320, 18479270519]
    for phone_number in phone_numbers:
        user = Users.get(phone_number)
        process_message(user)

@app.schedule(Rate(1, unit=Rate.HOURS))
def send_weekly_messages(event):
    # Convert the UTC time to the ET time that is stored in the database
    goal_message_sent_day_of_week = 0
    progress_message_sent_day_of_week = 3
    cur_day_of_week = datetime.today().weekday()
    hours = get_weekly_message_hour()
    for hour in hours:
        user_list = Users.time_index.query(hour, Users.send_message == True)
        print("Fetching users with send_message True and with hour: " + str(hour))
        # Iterate through users for this time
        for user in user_list:
            if user.message_set != "Text4Health":
                continue
            user_obj = UserActions(**user.to_dict())
            if cur_day_of_week == goal_message_sent_day_of_week:
                user_obj.initiate_goal_setting_message(user)
            if cur_day_of_week == progress_message_sent_day_of_week:
                user_obj.initiate_progress_message(user)

def get_et_hour():
    hour = datetime.now().hour - 4
    if hour < 0:
        hour += 24
    return hour

def get_weekly_message_hour():
    hour = get_et_hour()
    if hour < 13:
        return [hour - 2]
    elif hour >= 13 and hour <= 18:
        return [hour + 2, hour - 2]
    else:
        return [hour + 2]

def process_message(user):
    user_obj = UserActions(**user.to_dict())
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



