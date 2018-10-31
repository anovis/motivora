from chalicelib import app
from models import Messages,Users

@app.route('/messages', methods=['GET'], cors=True)
def list_messages():
    # TODO only one message set
    messages = Messages.query("EBNHC", Messages.id >= 0)
    message_list = [message.to_dict() for message in messages]
    return {"data":message_list}

@app.route('/users', methods=['GET'], cors=True)
def list_users():
    users = Users.scan(Users.message_set == "EBNHC")
    user_list = [user.to_dict() for user in users]
    return {"data":user_list}

