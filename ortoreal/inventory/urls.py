from django.urls import path

from inventory import views

app_name = "inventory"

urlpatterns = [
    path("", views.NomenclatureListView.as_view(), name="nomenclature"),
    path("items/<int:pk>/", views.PartItemsListView.as_view(), name="items"),
    path("reception/", views.ReceptionView.as_view(), name="reception"),
    path("take/", views.TakeItemsView.as_view(), name="take_items"),
    path("return/", views.ReturnItemsView.as_view(), name="return_items"),
    path("add_parts/", views.AddPartsView.as_view(), name="add_parts"),
    path("orders/", views.OrdersView.as_view(), name="orders"),
    path("orders/current/", views.OrderView.as_view(), name="order"),
    path(
        "orders/current/edit/",
        views.FreeOrderEditView.as_view(),
        name="free_order_edit",
    ),
    path("orders/<int:pk>/", views.OrderView.as_view(), name="order_by_id"),
    path("orders/download/", views.export_orders, name="export_order"),
    path("orders/add/", views.FreeOrderAddView.as_view(), name="free_order"),
    path("logs/", views.InventoryLogsListView.as_view(), name="logs"),
    path(
        "logs/<int:pk>/",
        views.InventoryLogsDetailView.as_view(),
        name="log_items",
    ),
    path("pick_parts/", views.PickPartsView.as_view(), name="pick_parts"),
    path("sets/", views.JobSetsView.as_view(), name="job_sets"),
    path("sets/<int:pk>/", views.JobSetView.as_view(), name="job_set"),
    path("sets/all/", views.AllJobSetsView.as_view(), name="all_job_sets"),
    path("margins/", views.MarginView.as_view(), name="margins"),
]
