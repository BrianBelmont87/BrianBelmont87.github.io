/* Site-wide page-view count. One small request, no cookies, no animation. */
(function () {
  var slot = document.querySelector("[data-visits]");
  if (!slot || !window.fetch) {
    return;
  }

  fetch("https://abacus.jasoncameron.dev/hit/brianbelmont87.github.io/visits", {
    credentials: "omit",
    cache: "no-store",
    referrerPolicy: "no-referrer"
  })
    .then(function (response) {
      if (!response.ok) {
        throw new Error("counter");
      }
      return response.json();
    })
    .then(function (data) {
      var value = Number(data && data.value);
      if (!isFinite(value)) {
        return;
      }
      slot.textContent = value.toLocaleString("en-US");
    })
    .catch(function () {
      slot.textContent = "—";
    });
})();
