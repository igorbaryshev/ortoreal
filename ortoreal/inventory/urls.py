from django.urls import path

from inventory import views

app_name = "inventory"

urlpatterns = [
    path("", views.nomenclature, name="nomenclature"),
    path("items/<int:pk>/", views.items, name="items"),
    path("add/", views.AddItemsView.as_view(), name="add_items"),
    path("take/", views.TakeItemsView.as_view(), name="take_items"),
    path("return/", views.ReturnItemsView.as_view(), name="return_items"),
    path("add_part/", views.add_parts, name="add_parts"),
    path("order/", views.OrderView.as_view(), name="order"),
    path("order/<int:pk>/", views.OrderView.as_view(), name="order_by_id"),
    path("order/download/", views.export_orders, name="export_order"),
    path("order/add/", views.FreeOrderItemsView.as_view(), name="free_order"),
    path("logs/", views.InventoryLogsListView.as_view(), name="logs"),
    path(
        "logs/<int:pk>/",
        views.InventoryLogsDetailView.as_view(),
        name="log_items",
    ),
]
