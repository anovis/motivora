from chalicelib import app
from chalice import Rate
import datetime
from chalicelib.models import Users

from chalicelib.actions import UserActions


@app.schedule(Rate(1, unit=Rate.HOURS))
def every_hour(event):
    hour = datetime.datetime.now().hour
    user_list = Users.time_index.query(hash_key=hour)
    for user in user_list:
        user_obj = UserActions(**user.to_dict())
        is_successful = user_obj.send_next_sms()
        if is_successful:
            user_obj.send_sms('How helpful was this message?”  [Scale of 0-10, with 0=not helpful at all and 10=very helpful]')
            user_obj.set_next_message()

