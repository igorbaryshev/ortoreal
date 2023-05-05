let container = document.querySelector("tbody");
let totalForms = document.querySelector("#id_item-TOTAL_FORMS");
let submitButton = document.querySelector("#return-button");
let fullForm = document.querySelector("#form-container");

var form = document.querySelectorAll(".input-row");
var formNum = form.length;

$(document).ready(function () {
  $("#id_job").each(function () {
    $(this).select2({
      theme: "bootstrap-5",
    });
  });
});

function clearFormSet(e) {
  if (totalForms) {
    totalForms.setAttribute("value", "0");
  }
}

if (formNum) {
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
      fullForm.submit();
    }
  });
}

function removeAlert() {
  $(this).closest(".input-row").children("td").removeClass("alert-td");
}
