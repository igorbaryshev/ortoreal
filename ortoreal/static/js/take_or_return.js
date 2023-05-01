let container = document.querySelector("tbody");
let addButton = document.querySelector("#add-form");
let removeButton = document.querySelector("#remove-form");
let totalForms = document.querySelector("#id_item-TOTAL_FORMS");
let buttonRow = document.querySelector(".button-row");
let takeButton = document.querySelector("#take-button");

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
    /*$("#id_entry-prosthetist").select2({
        theme: 'bootstrap-5'
    });
    $("#id_entry-client").select2({
        theme: 'bootstrap-5'
    });*/

    $('[id$="-part"').each(function() {
        $(this).select2({
        });
    });
    $('[id$="-part"]').each(changeTotal);
});

addButton.addEventListener('click', addForm);
removeButton.addEventListener('click', removeForm);    
takeButton.addEventListener('click', removeLastEmpty);
const input = document.querySelector('.table-responsive');

/* Исправляем и сообщаем о неверном вводе числа в таблицу */
input.addEventListener('input', (e) => {
    if (e.target.type == "number"){
        value = Number(e.target.value);
        max = Number(e.target.max);
        min = Number(e.target.min);
        console.log(value);
        if (value > max){
            e.target.setCustomValidity(`Не больше ${max}`)
            e.target.reportValidity();
            e.target.value = max;
        }
        else if (value < min){
            e.target.setCustomValidity(`Не меньше ${min}`)
            e.target.reportValidity();
            e.target.value = min;
        }
    }
});

function removeLastEmpty(e) {
    e.preventDefault();
    if (formNum > 0) {
        let form = document.querySelectorAll(".input-row");
        let lastForm = form[formNum - 1];
        let select = lastForm.querySelector("select").value;
        let quantity = lastForm.querySelector("input").value;
        if (!select && quantity == "0") {
            removeForm(e);
        }
    }
    let form_container = document.querySelector("#form-container");
    form_container.submit();
    
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

let partSelect = $('[id$="-part"]');

partSelect.on('change', changeTotal);
partSelect.on('change', removeAlert);

function changeTotal() {
    let index = $(this).prop("selectedIndex");
    let select = $(this).closest(".input-row").children("td").has('[id$="-total"]').find("select");
    select.prop('selectedIndex', index);
    let value = select.find("option:selected").text();
    console.log(value);
    let input = $(this).closest(".input-row").children("td").has('[id$="-quantity"]').find("input")
    input.attr("max", value);
    input.val(0);
    $(this).closest(".input-row").children("td").find("#p-total").text(value);
}

function removeAlert() {
    $(this).closest(".input-row").children("td").removeClass("alert-td");
}


$('#form-container').on('change', '[id$="-part"]:last', addMore);

function addMore(e) {
    if ($(this).val()) {
        addForm(e);
    }
}