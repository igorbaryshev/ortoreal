from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from inventory.forms import InventoryLogForm, ItemAddFormSet, ItemTakeFormSet
from inventory.models import Item, InventoryLog


@login_required
def add_items(request):
    entry_form = InventoryLogForm(request.POST or None, prefix="entry")
    item_formset = ItemAddFormSet(request.POST or None, prefix="item")

    if (
        request.method == "POST"
        and entry_form.is_valid()
        and item_formset.is_valid()
    ):
        date = entry_form.cleaned_data.get("date")
        operation = entry_form.cleaned_data.get("operation")
        comment = entry_form.cleaned_data.get("comment")
        batch_items = []
        batch_logs = []
        for form in item_formset:
            quantity = form.cleaned_data.get("quantity")
            part = form.cleaned_data.get("part")
            warehouse = form.cleaned_data.get("warehouse")
            batch_items += [
                Item(part=part, warehouse=warehouse, date_added=date)
                for _ in range(quantity)
            ]
            log = InventoryLog(
                operation=operation,
                comment=comment,
                part=part,
                added_by=request.user,
                date=date,
                quantity=quantity,
            )
            batch_logs.append(log)
        InventoryLog.objects.bulk_create(batch_logs)
        Item.objects.bulk_create(batch_items)

        return redirect("/admin/inventory/inventorylog/")

    context = {
        "form": entry_form,
        "formset": item_formset,
    }

    return render(request, "inventory/add_items.html", context)


@login_required
def take_items(request):
    entry_form = InventoryLogForm(request.POST or None, prefix="entry")
    item_formset = ItemTakeFormSet(request.POST or None, prefix="item")

    if item_formset.is_valid():
        for form in item_formset:
            total = form.cleaned_data
            print(total)
    # if (
    #     request.method == "POST"
    #     and entry_form.is_valid()
    #     and item_formset.is_valid()
    # ):
    #     date = entry_form.cleaned_data.get("date")
    #     operation = entry_form.cleaned_data.get("operation")
    #     comment = entry_form.cleaned_data.get("comment")
    #     for form in item_formset:
    #         quantity = form.cleaned_data.get("quantity")
    #         part = form.cleaned_data.get("part")
    #         warehouse = form.cleaned_data.get("warehouse")
    #         batch_items += [
    #             Item(part=part, warehouse=warehouse, date_added=date)
    #             for _ in range(quantity)
    #         ]
    #         log = InventoryLog(
    #             operation=operation,
    #             comment=comment,
    #             part=part,
    #             added_by=request.user,
    #             date=date,
    #             quantity=quantity,
    #         )
    #         batch_logs.append(log)
    #     InventoryLog.objects.bulk_create(batch_logs)
    #     Item.objects.bulk_create(batch_items)
# 
    #     return redirect("/admin/inventory/inventorylog/")

    context = {
        "form": entry_form,
        "formset": item_formset,
    }

    return render(request, "inventory/add_items.html", context)
