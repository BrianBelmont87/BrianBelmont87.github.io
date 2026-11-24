/* Site-wide page views. One small request, no cookies, no animation.
   The previous Abacus counter often never answered from a browser, so the
   footer stayed on the dash. This uses tick.rs instead. The old total could
   not be copied, so the number starts again. */
(function () {
  var slot = document.querySelector("[data-visits]");
  if (!slot || !window.fetch) {
    return;
  }

  var controller = typeof AbortController === "function" ? new AbortController() : null;
  var timer = controller ? window.setTimeout(function () { controller.abort(); }, 6000) : 0;

  fetch("https://tick.rs/c/o8w64MeiLWZQ", {
    method: "POST",
    credentials: "omit",
    cache: "no-store",
    referrerPolicy: "no-referrer",
    signal: controller ? controller.signal : undefined
  })
    .then(function (response) {
      if (!response.ok) {
        throw new Error("counter");
      }
      return response.text();
    })
    .then(function (text) {
      var value = Number(String(text).trim());
      if (!isFinite(value)) {
        return;
      }
      slot.textContent = value.toLocaleString("en-US");
    })
    .catch(function () {
      slot.textContent = "—";
    })
    .then(function () {
      if (timer) {
        window.clearTimeout(timer);
      }
    });
})();
