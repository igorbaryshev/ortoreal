var form = document.querySelectorAll(".input-row");
var formNum = form.length;
if (formNum == 1) {
  $("#remove-form").hide();
}

var firstForm = form[0].cloneNode(true);

function cleanForm(form) {
    form.querySelectorAll("td").forEach(field => {
        field.classList.remove("alert-td");
    });
    if (form.querySelector('[name$="-warehouse"]')) {
        form.querySelector('[name$="-warehouse"]').value = "";
    } else {
        form.querySelector('[name$="-total"]').value = "";
    }
    form.querySelector('[name$="-part"]').value = "";
    form.querySelector('[name$="-quantity"]').value = 0;
    form.querySelectorAll('label').forEach(label => {
        label.remove();
    });
}

$(document).ready(function() {
    /*$("#id_entry-operation").addClass("form-control");*/
    $("#id_entry-prosthetist").select2({
        theme: 'bootstrap-5'
    });
    $("#id_entry-client").select2({
        theme: 'bootstrap-5'
    });
    $('[id$="-part"').each(function() {
        $(this).select2({
        });
    });
    $(".form-group.col:first-child").each(function() {
      $(this).addClass("w-50");
    });
    $('[id$="-part"]').each(changeTotal);
});

let container = document.querySelector("tbody");
let addButton = document.querySelector("#add-form");
let removeButton = document.querySelector("#remove-form");
let totalForms = document.querySelector("#id_item-TOTAL_FORMS");
let buttonRow = document.querySelector(".button-row");
let submitButton = document.querySelector("#submit-form");

addButton.addEventListener('click', addForm);
removeButton.addEventListener('click', removeForm);    
submitButton.addEventListener('click', removeLastEmpty);

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
    }
    else {
        form_container.reportValidity();
    }
}

function addForm(e) {
    e.preventDefault();
    let form = firstForm.cloneNode(true);
    let formRegex = RegExp(`item-(\\d){1,3}-`,'g');

    
    alerts = form.querySelectorAll(".alert")
    alerts.forEach(alert => {
        alert.remove();
    });

    form.innerHTML = form.innerHTML.replace(formRegex, `item-${formNum}-`);
    console.log(form);
    document.querySelector("#form-container tbody").append(form);
    cleanForm(form);
    $(`[name="item-${formNum}-part"]`).select2();
    /*$(".select2.select2-container").last().addClass("form-control");*/
    formNum++;
    totalForms.setAttribute('value', `${formNum}`);
    $("#remove-form").show();
    $('[id$="-part"]').on('change', changeTotal);
}

function removeForm(e) {
    e.preventDefault();

    let lastForm = $(".input-row").last();
    formNum--;
    nextSib = lastForm.next();
    if (nextSib && nextSib.children(".alert-row")){
        nextSib.remove();
    }
    lastForm.remove();
    totalForms.setAttribute('value', `${formNum}`);
    if (formNum == 1) {
        $("#remove-form").hide();
    }
}

$('[id$="-part"]').on('change', changeTotal);
$('[id$="-part"]').on('change', removeAlert);

function changeTotal() {
    let value = $(this).val();
    $(this).closest(".row.item-form").children(".form-group.col").has('[id$="-total"]').children("select").prop('selectedIndex', value);
}
function removeAlert() {
    if ($('.form-container.taking')) {
        $(this).closest(".row.item-form").children(".form-group.col").has('[id$="-quantity"]').children(".alert").remove();
    }
}


$('#form-container').on('change', '[id$="-part"]:last', addMore);

function addMore(e) {
    if ($(this).val()) {
        addForm(e);
    }
}