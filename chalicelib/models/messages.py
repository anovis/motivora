from pynamodb.models import Model
from pynamodb.attributes import BooleanAttribute, UnicodeAttribute, NumberAttribute, MapAttribute

class Messages(Model):
    class Meta:
        table_name = 'motivora-messages'

    id = NumberAttribute(range_key=True)
    message_set = UnicodeAttribute(default='EBNHC',hash_key=True)
    attr_list = MapAttribute()
    body = UnicodeAttribute(null=True)
    body_en = UnicodeAttribute(null=True)
    body_es = UnicodeAttribute(null=True)
    seq = UnicodeAttribute(null=True)
    total_attr = NumberAttribute()
    total_disliked = NumberAttribute(default=0)
    total_liked = NumberAttribute(default=0)
    total_resp = NumberAttribute(default=0)
    total_sent = NumberAttribute(default=0)
    is_active  = BooleanAttribute(default=True)

    def to_json(self):
        return self.to_dict()

    def to_dict(self):
        return {
            'id': self.id,
            'message_set': self.message_set,
            'attr_list': self.attr_list,
            'body': self.body,
            'body_en': self.body_en,
            'body_es': self.body_es,
            'seq': self.seq,
            'total_attr': self.total_attr,
            'total_disliked': self.total_disliked,
            'total_liked': self.total_liked,
            'total_resp': self.total_resp,
            'total_sent': self.total_sent,
            'is_active': self.is_active
        }

    def to_frontend(self):
        if(self.attr_list is None):
          attr_list = ''
        else:
          attr_list = str(self.attr_list.as_dict())
        return {
            'id': self.id,
            'message_set': self.message_set,
            'attr_list': attr_list,
            'body': self.body,
            'body_en': self.body_en,
            'body_es': self.body_es,
            'is_active': self.is_active
        }
