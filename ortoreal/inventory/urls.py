from django.urls import path

from inventory import views

app_name = "inventory"

urlpatterns = [
    path("add/", views.add_items, name="add_items"),
    path("take/", views.take_items, name="take_items"),
]
