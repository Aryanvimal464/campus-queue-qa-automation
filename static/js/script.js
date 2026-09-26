/* =========================================================
   Campus Queue - script.js
   - Renders flashed server messages as toast notifications
   - Adds confirmation dialogs on destructive actions
   - Auto-submits the department filter on Generate Token page
   ========================================================= */

document.addEventListener("DOMContentLoaded", function () {
  renderFlashToasts();
  attachConfirmDialogs();
  attachDepartmentAutoFilter();
});

/* ---- Toasts built from the #flash-data script tag (see base.html) ---- */
function renderFlashToasts() {
  var dataEl = document.getElementById("flash-data");
  if (!dataEl) return;

  var messages;
  try {
    messages = JSON.parse(dataEl.textContent);
  } catch (e) {
    return;
  }
  if (!messages || messages.length === 0) return;

  var stack = document.createElement("div");
  stack.className = "cq-toast-stack";
  stack.id = "toast-stack";
  document.body.appendChild(stack);

  messages.forEach(function (item, index) {
    var toast = document.createElement("div");
    toast.className = "cq-toast " + (item.category || "info");
    toast.setAttribute("id", "toast-" + index);
    toast.setAttribute("role", "alert");
    toast.textContent = item.message;
    stack.appendChild(toast);

    setTimeout(function () {
      toast.style.opacity = "0";
      toast.style.transition = "opacity 0.3s";
      setTimeout(function () {
        toast.remove();
      }, 300);
    }, 4500);
  });
}

/* ---- Confirmation dialogs for elements with [data-confirm] ---- */
function attachConfirmDialogs() {
  document.querySelectorAll("[data-confirm]").forEach(function (el) {
    el.addEventListener("submit", function (e) {
      var message = el.getAttribute("data-confirm") || "Are you sure?";
      if (!window.confirm(message)) {
        e.preventDefault();
      }
    });
  });
}

/* ---- Generate Token page: reload with ?department_id= when changed ---- */
function attachDepartmentAutoFilter() {
  var select = document.getElementById("department-select");
  var form = document.getElementById("department-filter-form");
  if (select && form) {
    select.addEventListener("change", function () {
      form.submit();
    });
  }
}
