from config import app
from controller_functions import *

app.add_url_rule("/", view_func=index)
app.add_url_rule("/users/create", methods=["POST"], view_func=register)
app.add_url_rule("/users/login", methods=["POST"], view_func=login)
app.add_url_rule("/logout", view_func=logout)
app.add_url_rule("/products", view_func=products)
app.add_url_rule("/orders", methods=["POST"], view_func=orders)
app.add_url_rule("/orders/confirmation", view_func=confirmation)
app.add_url_rule("/orders/confirm", methods=["POST"], view_func=place_transaction)
app.add_url_rule("/orders/cancel", view_func=cancel_order)
