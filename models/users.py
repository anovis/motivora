from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, JSONAttribute, BooleanAttribute, NumberSetAttribute, NumberAttribute, UnicodeSetAttribute


class Users(Model):
    class Meta:
        table_name = 'motivora-users'

    phone = UnicodeAttribute(hash_key=True)
    message_set = UnicodeAttribute()
    # next_message_body = UnicodeAttribute()
    next_message = NumberAttribute(default=1)
    send_message = BooleanAttribute(default=True)
    time = NumberAttribute(default=9)
    messages_sent = NumberSetAttribute(default={}, null=True)
    attr_scores = JSONAttribute(null=True)
    message_response = JSONAttribute(null=True)

    def to_json(self):
        return self.to_dict()

    def to_dict(self):
        return {
            'phone': self.phone,
            'message_set': self.message_set,
            'time': self.time,
            'next_message_body': self.next_message_body,
            'next_message': self.next_message,
            'send_message': self.send_message,
            'messages_sent': self.messages_sent,
            'attr_scores': self.attr_scores,
            'message_response': self.message_response,
        }
