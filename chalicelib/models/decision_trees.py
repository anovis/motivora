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
    id                = NumberAttribute(range_key=True)
    type              = UnicodeAttribute(hash_key=True)
    message           = UnicodeAttribute()
    parent_ids        = NumberSetAttribute(default=[])
    min_response_val  = NumberAttribute(null=True)
    max_response_val  = NumberAttribute(null=True)
    goal_type         = UnicodeAttribute(null=True)
    goal_subtype      = UnicodeAttribute(null=True)
    min_goal_amount   = NumberAttribute(null=True)
    max_goal_amount   = NumberAttribute(null=True)
    is_root           = BooleanAttribute()
    is_terminal       = BooleanAttribute()
    set_goal_type     = UnicodeAttribute(null=True)
    set_goal_subtype  = UnicodeAttribute(null=True)
    set_goal_amount   = UnicodeAttribute(null=True)
    set_enabler       = UnicodeAttribute(null=True)
    set_barrier       = UnicodeAttribute(null=True)

    # Indices
    parent_id_index   = ParentIdIndex()

    def to_json(self):
        return self.to_dict()

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'message': self.message,
            'min_response_val': self.min_response_val,
            'max_response_val': self.max_response_val,
            'goal_type': self.goal_type,
            'goal_subtype': self.goal_subtype,
            'min_goal_amount': self.min_goal_amount,
            'max_goal_amount': self.max_goal_amount,
            'is_root': self.is_root,
            'is_terminal': self.is_terminal,
            'set_goal_type': self.set_goal_type,
            'set_goal_subtype': self.set_goal_subtype,
            'set_goal_amount': self.set_goal_amount,
            'set_enabler': self.set_enabler,
            'set_barrier': self.set_barrier,
        }

    def to_frontend(self):
        return {
            'id': self.id,
            'type': self.type,
            'message': self.message,
            'min_response_val': self.min_response_val,
            'max_response_val': self.max_response_val,
            'goal_type': self.goal_type,
            'goal_subtype': self.goal_subtype,
            'min_goal_amount': self.min_goal_amount,
            'max_goal_amount': self.max_goal_amount,
            'is_root': self.is_root,
            'is_terminal': self.is_terminal,
            'set_goal_type': self.set_goal_type,
            'set_goal_subtype': self.set_goal_subtype,
            'set_goal_amount': self.set_goal_amount,
            'set_enabler': self.set_enabler,
            'set_barrier': self.set_barrier,
        }

