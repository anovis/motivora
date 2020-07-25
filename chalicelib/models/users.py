from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, JSONAttribute, BooleanAttribute, NumberSetAttribute, NumberAttribute, UTCDateTimeAttribute, UnicodeSetAttribute
from pynamodb.indexes import GlobalSecondaryIndex, AllProjection
from datetime import datetime


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

    # Metadata Fields
    phone             = NumberAttribute(hash_key=True)
    message_set       = UnicodeAttribute(default='EBNHC')
    lang_code         = UnicodeAttribute(default='en')
    prev_message      = NumberAttribute(default=0)
    send_message      = BooleanAttribute(default=True)
    time              = NumberAttribute(default=9)
    messages_sent     = NumberSetAttribute(default=[0])
    attr_scores       = JSONAttribute(null=True)
    preferred_attrs   = UnicodeSetAttribute(default=[])
    created_time      = UTCDateTimeAttribute(default=datetime.now(), null=False)

    # Message response fields
    message_response  = JSONAttribute(default={}, null=True)
    weekly_goals_message_response  = JSONAttribute(default={}, null=True)
    direct_message_response  = JSONAttribute(default={}, null=True)

    # Indices
    time_index        = TimeIndex()

    def to_json(self):
        return self.to_dict()

    def to_dict(self):
        return {
            'phone': self.phone,
            'message_set': self.message_set,
            'lang_code': self.lang_code,
            'time': self.time,
            'prev_message': self.prev_message,
            'send_message': self.send_message,
            'messages_sent': self.messages_sent,
            'attr_scores': self.attr_scores,
            'preferred_attrs': self.preferred_attrs,
            'weekly_goals_message_response': self.weekly_goals_message_response,
            'direct_message_response': self.direct_message_response,
        }

    def to_frontend(self):
        return {
            'phone': self.phone,
            'time': self.time,
            'message_set': self.message_set,
            'send_message': self.send_message,
            'lang_code': self.lang_code,
        }
