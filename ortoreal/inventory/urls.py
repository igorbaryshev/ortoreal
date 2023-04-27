from django.urls import path

from inventory import views

app_name = "inventory"

urlpatterns = [
    path("", views.nomenclature, name="nomenclature"),
    path("items/<int:pk>/", views.items, name="items"),
    path("add/", views.add_items, name="add_items"),
    path("take/", views.take_items, name="take_items"),
    path("add_part/", views.add_parts, name="add_parts"),
    path("order/", views.OrderView.as_view(), name="order"),
    path("order/<int:pk>/", views.OrderView.as_view(), name="order_by_id"),
    path("order/download/", views.export_orders, name="export_order"),
]
