(() => {
  const toggle = document.getElementById("menuToggle");
  const sidebar = document.querySelector(".sidebar");
  if (toggle && sidebar) toggle.addEventListener("click", () => sidebar.classList.toggle("open"));
  if ("serviceWorker" in navigator && window.location.protocol === "https:") {
    window.addEventListener("load", () => navigator.serviceWorker.register("/sw.js").catch(() => {}));
  }
  document.querySelectorAll("form").forEach(form => {
    form.querySelectorAll("input:not([type=checkbox]):not([type=hidden]),select,textarea").forEach(field => {
      if (!field.classList.contains("form-control") && field.tagName !== "TEXTAREA") field.classList.add("form-control");
      if (field.tagName === "SELECT") field.classList.add("form-select");
    });
  });
})();