from chalicelib.models.messages import Messages
from chalicelib.models.users import Users
from chalicelib.models.invocations import Invocations
from chalicelib.models.decision_trees import DecisionTrees

if not Messages.exists():
    Messages.create_table(read_capacity_units=20, write_capacity_units=5, wait=True)

if not Users.exists():
    Users.create_table(read_capacity_units=5, write_capacity_units=5, wait=True)

if not Invocations.exists():
    Invocations.create_table(read_capacity_units=5, write_capacity_units=5, wait=True)

if not DecisionTrees.exists():
    DecisionTrees.create_table(read_capacity_units=10, write_capacity_units=5, wait=True)
