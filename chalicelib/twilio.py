from chalicelib import app
from models import Messages,Users
from chalicelib.actions import UserActions


@app.route('/twilio/handle', methods=['GET'], cors=True)
def handle_twilio():
    query = app.current_request.query_params
    phone = query.get('From')

    # TODO only EBNHC for now
    message_set = "EBNHC"

    user = UserActions(phone, message_set=message_set, **query)

    if not user:
        user.add_user()
        message = Messages(message_set, 0)
        user.send_sms(message.body)
        user.update_post_message(0)
