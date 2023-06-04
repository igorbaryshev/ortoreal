var totalForms = document.querySelector("#id_form-TOTAL_FORMS");
function clearFormSet() {
  if (totalForms) {
    totalForms.setAttribute("value", "0");
  }
}

$(document).ready(function () {
  let totalForms = document.querySelector("#id_form-TOTAL_FORMS");
  let addButton = document.querySelector("#add-form");
  let removeButton = document.querySelector("#remove-form");
  let submitButton = document.querySelector("#take-button");
  let fullForm = $("#form-container");

  var forms = document.querySelectorAll(".input-row");
  var formNum = forms.length;

  function changeAvailable() {
    let index = $(this).prop("selectedIndex");
    let select = $(this)
      .closest(".input-row")
      .children("td")
      .has('[id$="-total"]')
      .find("select");
    select.prop("selectedIndex", index);
    let value = select.find("option:selected").text();
    let input = $(this)
      .closest(".input-row")
      .children("td")
      .has('[id$="-quantity"]')
      .find("input");
    input.attr("max", value);
    $(this).closest(".input-row").children("td").find("#p-total").text(value);
  }

  function resetQuantity() {
    let input = $(this)
      .closest(".input-row")
      .children("td")
      .has('[id$="-quantity"]')
      .find("input");
    input.val(0);
  }

  function cleanForm(form) {
    form.querySelectorAll("td").forEach((field) => {
      field.classList.remove("alert-td");
    });
    form.querySelector('[name$="-available"]').value = "";
    form.querySelector('[name$="-part"]').value = "";
    form.querySelector('[name$="-quantity"]').value = "0";
  }

  if (formNum == 1) {
    $("#remove-form").hide();
  }
  $("#id_job").each(function () {
    $(this).select2({
      theme: "bootstrap-5",
    });
  });
  $('[id$="-part"').each(function () {
    $(this).select2();
  });
  $('[id$="-part"]').each(changeAvailable);

  function removeLastEmpty() {
    if (formNum > 0) {
      let form = document.querySelectorAll(".input-row");
      let lastForm = form[formNum - 1];
      let select = lastForm.querySelector("select").value;
      let quantity = lastForm.querySelector("input").value;
      if (!select && Number(quantity) == 0) {
        removeForm();
      }
    }
  }

  function addForm(e) {
    e.preventDefault();
    let form = firstForm.cloneNode(true);
    let formRegex = RegExp(`form-(\\d){1,3}-`, "g");

    alerts = form.querySelectorAll(".alert");
    alerts.forEach((alert) => {
      alert.remove();
    });

    form.innerHTML = form.innerHTML.replace(formRegex, `form-${formNum}-`);
    document.querySelector("#form-container tbody").append(form);
    cleanForm(form);
    $(`[name="form-${formNum}-part"]`).select2();
    formNum++;
    totalForms.setAttribute("value", `${formNum}`);
    $("#remove-form").show();
    $('[id$="-part"]').on("change", function () {
      changeAvailable.call($(this));
      resetQuantity.call($(this));
    });
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

  function removeAlert() {
    $(this).closest(".input-row").children("td").removeClass("alert-td");
  }

  fullForm.on("change", '[id$="-part"]:last', addMore);

  function addMore(e) {
    if ($(this).val()) {
      addForm(e);
    }
  }

  /* Если в формсете есть формы, то... */
  if (formNum) {
    var firstForm = forms[0].cloneNode(true);

    addButton.addEventListener("click", addForm);
    removeButton.addEventListener("click", removeForm);
    /*submitButton.addEventListener('click', removeLastEmpty);*/
    const input = document.querySelector(".table-responsive");
    /* Исправляем и сообщаем о неверном вводе числа в таблицу */
    input.addEventListener("change", (e) => {
      if (e.target.type == "number") {
        value = Number(e.target.value);
        max = Number(e.target.max);
        min = Number(e.target.min);
        e.target.setCustomValidity(`Не больше ${max}`);
        if (value > max && !e.target.reportValidity()) {
          e.target.value = max;
        } else if (value < min) {
          e.target.value = min;
        }
      }
    });

    submitButton.addEventListener("click", function (e) {
      e.preventDefault();
      if (confirm("Подтвердить.")) {
        removeLastEmpty();
        fullForm.submit();
      }
    });

    let partSelect = $('[id$="-part"]');

    partSelect.on("change", function () {
      changeAvailable.call($(this));
      resetQuantity.call($(this));
    });
    partSelect.on("change", removeAlert);
  }
});
