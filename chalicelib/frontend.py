from chalicelib import app
from chalicelib.models import Messages,Users
from chalice import Response

from chalicelib.actions import UserActions

@app.route('/messages', methods=['GET'], cors=True)
def list_messages():
    # TODO only one message set
    messages = Messages.query("EBNHC", Messages.id >= 0)
    message_list = [message.to_frontend() for message in messages]
    return {"data":message_list}

@app.route('/messages', methods=['POST'], cors=True)
def post_messages():
    payload = app.current_request.json_body
    print(payload)
    # {"data":{"MessageSetName":"t","AttrNum":"2","MessageNum":"1","Attr0":"a","Attr1":"b","Message0":"tt","MessageAttr0":["a","b"]}}
    return Response(body='messages added',
                           status_code=200,
                           headers={'Content-Type': 'text/plain'})


@app.route('/users', methods=['GET'], cors=True)
def list_users():
    users = Users.scan(Users.message_set == "EBNHC")
    user_list = [user.to_frontend() for user in users]
    return {"data": user_list}


@app.route('/test', methods=['GET'], cors=True)
def test():
    user_class = UserActions('17602147229', message_set="EBNHC")
    return user_class.get_next_message()

