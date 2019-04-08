from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, NumberAttribute, MapAttribute

class Messages(Model):
    class Meta:
        table_name = 'motivora-messages'

    id = NumberAttribute(range_key=True)
    message_set = UnicodeAttribute(hash_key=True)
    attr_list = MapAttribute()
    body = UnicodeAttribute()
    seq = UnicodeAttribute()
    total_attr = NumberAttribute()
    total_disliked = NumberAttribute(default=0)
    total_liked = NumberAttribute(default=0)
    total_resp = NumberAttribute(default=0)
    total_sent = NumberAttribute(default=0)

    def to_json(self):
        return self.to_dict()

    def to_dict(self):
        return {
            'id': self.id,
            'message_set': self.message_set,
            'attr_list': self.attr_list,
            'body': self.body,
            'seq': self.seq,
            'total_attr': self.total_attr,
            'total_disliked': self.total_disliked,
            'total_liked': self.total_liked,
            'total_resp': self.total_resp,
            'total_sent': self.total_sent
        }

    def to_frontend(self):
        if(self.attr_list is None):
          attr_list = ''
        else:
          attr_list = str(self.attr_list.as_dict())
        return {
            'id': self.id,
            'message_set': self.message_set,
            'body': self.body,
            'attr_list': attr_list,
            'total_disliked': self.total_disliked,
            'total_liked': self.total_liked,
            'total_sent': self.total_sent
        }
