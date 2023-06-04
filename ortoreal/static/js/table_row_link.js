$(document).ready(function ($) {
  $("tbody tr").click(function () {
    if (!window.getSelection().toString()) {
      window.location = $(this).data("href");
    }
  });
});
