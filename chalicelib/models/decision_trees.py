from pynamodb.models import Model
from pynamodb.attributes import BooleanAttribute, UnicodeAttribute, JSONAttribute, BooleanAttribute, NumberSetAttribute, NumberAttribute, UTCDateTimeAttribute, UnicodeSetAttribute
from pynamodb.indexes import GlobalSecondaryIndex, AllProjection
from datetime import datetime

class ParentIdIndex(GlobalSecondaryIndex):
    """
    This class represents a global secondary index
    """
    class Meta:
        index_name = 'parent_id-index'
        read_capacity_units = 1
        write_capacity_units = 1
        projection = AllProjection()
    parent_id = NumberAttribute(hash_key=True)

class DecisionTrees(Model):
    class Meta:
        table_name = 'motivora-decision-trees'

    # Fields
    id                = NumberAttribute(hash_key=True)
    message           = UnicodeAttribute()
    parent_id         = NumberAttribute(null=True)
    min_response_val  = NumberAttribute(null=True)
    max_response_val  = NumberAttribute(null=True)
    goal              = UnicodeAttribute(null=True)
    is_terminal       = BooleanAttribute()

    # Indices
    parent_id_index   = ParentIdIndex()

    def to_json(self):
        return self.to_dict()

    def to_dict(self):
        return {
            'id': self.id,
            'message': self.message,
            'min_response_val': self.min_response_val,
            'max_response_val': self.max_response_val,
            'goal': self.goal
        }

    def to_frontend(self):
        return {
            'id': self.id,
            'message': self.message,
            'min_response_val': self.min_response_val,
            'max_response_val': self.max_response_val,
            'goal': self.goal
        }
