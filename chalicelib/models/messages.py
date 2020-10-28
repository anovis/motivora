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
    total_sent = NumberAttribute(default=0)
    total_rated = NumberAttribute(default=0)
    average_rating = NumberAttribute(default=0)
    is_active  = BooleanAttribute(default=True)

    # TO BE DEPRECATED
    total_disliked = NumberAttribute(default=0)
    total_liked = NumberAttribute(default=0)
    total_resp = NumberAttribute(default=0)

    rating_0 = NumberAttribute(default=0)
    rating_1 = NumberAttribute(default=0)
    rating_2 = NumberAttribute(default=0)
    rating_3 = NumberAttribute(default=0)
    rating_4 = NumberAttribute(default=0)
    rating_5 = NumberAttribute(default=0)
    rating_6 = NumberAttribute(default=0)
    rating_7 = NumberAttribute(default=0)
    rating_8 = NumberAttribute(default=0)
    rating_9 = NumberAttribute(default=0)
    rating_10 = NumberAttribute(default=0)

    def to_json(self):
        json = self.to_dict()
        json['attr_list'] = list(json['attr_list'])
        return json

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
            'is_active': self.is_active,
            'total_sent': self.total_sent,
            'total_rated': self.total_rated,
            'average_rating': self.average_rating,
            'rating_0': self.rating_0,
            'rating_1': self.rating_1,
            'rating_2': self.rating_2,
            'rating_3': self.rating_3,
            'rating_4': self.rating_4,
            'rating_5': self.rating_5,
            'rating_6': self.rating_6,
            'rating_7': self.rating_7,
            'rating_8': self.rating_8,
            'rating_9': self.rating_9,
            'rating_10': self.rating_10,
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
            'is_active': self.is_active,
            'total_sent': self.total_sent,
            'total_rated': self.total_rated,
            'average_rating': self.average_rating,
            'rating_0': self.rating_0,
            'rating_1': self.rating_1,
            'rating_2': self.rating_2,
            'rating_3': self.rating_3,
            'rating_4': self.rating_4,
            'rating_5': self.rating_5,
            'rating_6': self.rating_6,
            'rating_7': self.rating_7,
            'rating_8': self.rating_8,
            'rating_9': self.rating_9,
            'rating_10': self.rating_10,
        }

    def get_body(self, lang_code):
        body_content = self.body
        if lang_code == "es":
            body_content = self.body_es
        if lang_code == "en":
            body_content = self.body_en
        return body_content