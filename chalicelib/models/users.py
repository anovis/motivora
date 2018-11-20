from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, JSONAttribute, BooleanAttribute, NumberSetAttribute, NumberAttribute


from pynamodb.indexes import GlobalSecondaryIndex, AllProjection


class TimeIndex(GlobalSecondaryIndex):
    """
    This class represents a global secondary index
    """
    class Meta:
        index_name = 'time-index'
        read_capacity_units = 1
        write_capacity_units = 1
        projection = AllProjection()
    time = NumberAttribute(default=9, hash_key=True)



class Users(Model):
    class Meta:
        table_name = 'motivora-users'

    phone = NumberAttribute(hash_key=True)
    message_set = UnicodeAttribute()
    # next_message_body = UnicodeAttribute()
    next_message = NumberAttribute(default=1)
    prev_message = NumberAttribute(default=1)
    send_message = BooleanAttribute(default=True)
    time = NumberAttribute(default=9)
    time_index = TimeIndex()
    messages_sent = NumberSetAttribute(null=True)
    attr_scores = JSONAttribute(null=True)
    message_response = JSONAttribute(default={}, null=True)

    def to_json(self):
        return self.to_dict()

    def to_dict(self):
        return {
            'phone': self.phone,
            'message_set': self.message_set,
            'time': self.time,
            'next_message': self.next_message,
            'prev_message': self.prev_message,
            'send_message': self.send_message,
            'messages_sent': self.messages_sent,
            'attr_scores': self.attr_scores,
            'message_response': self.message_response,
        }

    def to_frontend(self):
        return {
            'phone': self.phone,
            'time': self.time,
            'message_set': self.message_set,
            'next_message': self.next_message,
            'send_message': self.send_message,
            }
