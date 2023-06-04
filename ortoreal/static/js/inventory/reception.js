$(document).ready(function () {
  function cleanForm(form) {
    form.querySelectorAll("td").forEach((field) => {
      field.classList.remove("alert-td");
    });
    form.querySelector('[name$="-part"]').value = "";
    form.querySelector('[name$="-vendor2"]').checked = false;
    form.querySelector('[name$="-quantity"]').setAttribute("value", 0);
    form.querySelectorAll("label").forEach((label) => {
      label.remove();
    });
  }

  function resetInputs() {
    let columns = $(this).closest(".input-row");
    columns.find('[id$="-vendor2"]').prop({"checked": false});
    columns.find('[id$="-quantity"]').prop({"value": 0});
    columns.find('[id$="-price"]').prop({"value": "0.00"});
  }

  // подготавливаем переменные и события в форме
  let totalForms = document.querySelector("#id_form-TOTAL_FORMS");
  let forms = document.querySelectorAll(".input-row");
  let formNum = forms.length;
  if (formNum == 1) {
    $("#remove-form").hide();
  }
  $(".form-group.col:first-child").each(function () {
    $(this).addClass("w-50");
  });
  let firstForm = forms[0].cloneNode(true);
  cleanForm(firstForm);
  let partSelect = $('[id$="-part"]');
  partSelect.each(function () {
    $(this).select2({});
  });
  partSelect.on("change", resetInputs)
  partSelect.on("change", removeAlert);
  ////////////////////////////////////////////////////

  function addForm() {
    let form = firstForm.cloneNode(true);
    let formRegex = RegExp(`form-(\\d){1,3}-`, "g");

    alerts = form.querySelectorAll(".alert");
    alerts.forEach((alert) => {
      alert.remove();
    });

    form.innerHTML = form.innerHTML.replace(formRegex, `form-${formNum}-`);
    document.querySelector("#form-container tbody").append(form);
    part = $(`[name="form-${formNum}-part"]`);
    part.select2();
    part.on("change", resetInputs);
    formNum++;
    totalForms.setAttribute("value", `${formNum}`);
    $("#remove-form").show();
  }

  function removeForm() {
    let lastForm = $(".input-row").last();
    formNum--;
    nextSib = lastForm.next();
    if (nextSib && nextSib.children(".alert-row")) {
      nextSib.remove();
    }
    lastForm.remove();
    totalForms.setAttribute("value", `${formNum}`);
    if (formNum == 1) {
      $("#remove-form").hide();
    }
  }

  function removeLastEmpty(e) {
    e.preventDefault();
    if (formNum > 1) {
      let form = document.querySelectorAll(".input-row");
      let lastForm = form[formNum - 1];
      let select = lastForm.querySelector("select").value;
      let quantity = lastForm.querySelector("input").value;
      if (!select && quantity == "0") {
        removeForm(e);
      }
    }
    let form_container = document.querySelector("#form-container");
    if (form_container.checkValidity()) {
      form_container.submit();
    } else {
      form_container.reportValidity();
    }
  }

  function removeAlert() {
    $(this)
      .closest(".row.item-form")
      .children(".form-group.col")
      .has('[id$="-quantity"]')
      .children(".alert")
      .remove();
  }

  function addMore(e) {
    if ($(this).val()) {
      addForm(e);
    }
  }

  $("#form-container").on("change", '[id$="-part"]:last', addMore);

  let addButton = document.querySelector("#add-form");
  let removeButton = document.querySelector("#remove-form");
  let submitButton = document.querySelector("#submit-form");

  addButton.addEventListener("click", addForm);
  removeButton.addEventListener("click", removeForm);
  submitButton.addEventListener("click", removeLastEmpty);
});
