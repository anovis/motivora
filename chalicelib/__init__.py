from chalice import Chalice
app = Chalice(app_name='motivora')
app.debug = True

from chalicelib import (
    frontend,
    twilio_handlers
)
