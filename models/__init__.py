from models.messages import Messages
from models.users import Users


if not Messages.exists():
    Messages.create_table(read_capacity_units=5, write_capacity_units=5, wait=True)

if not Users.exists():
    Users.create_table(read_capacity_units=5, write_capacity_units=5, wait=True)
