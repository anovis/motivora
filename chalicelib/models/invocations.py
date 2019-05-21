from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, NumberAttribute

class Invocations(Model):
    class Meta:
        table_name = 'motivora-invocations'

    invocation_id = UnicodeAttribute(hash_key=True)
    phone = NumberAttribute()
