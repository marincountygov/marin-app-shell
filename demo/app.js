(() => {
  "use strict";

  function updateVersion() {
    document.querySelectorAll("[data-shell-version]").forEach((element) => {
      element.textContent = window.MarinAppShell?.version || "unknown";
    });
  }

  document.addEventListener("marinos:shell-ready", updateVersion);
  updateVersion();

  const code = document.querySelector("#integration-example");
  const copyButton = document.querySelector("[data-demo-copy]");
  if (code && copyButton) {
    copyButton.dataset.copyValue = code.textContent.trim();
  }
})();
