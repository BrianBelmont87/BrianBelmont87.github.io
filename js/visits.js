/* Site-wide page views. One small request, no cookies, no animation.
   Shown total = 156 (the old Abacus count) + the tick.rs count.
   If tick.rs does not answer, the line stays at 156. It never shows a dash
   and never goes below that old total. */
(function () {
  var slot = document.querySelector("[data-visits]");
  if (!slot || !window.fetch) {
    return;
  }

  var previousTotal = 156;
  var tick = "https://tick.rs/c/o8w64MeiLWZQ";

  function show(tickCount) {
    var extra = Number(tickCount);
    if (!isFinite(extra) || extra < 0) {
      extra = 0;
    }
    var total = previousTotal + extra;
    if (total < previousTotal) {
      total = previousTotal;
    }
    slot.textContent = total.toLocaleString("en-US");
  }

  function giveUp(ms) {
    return new Promise(function (_, reject) {
      window.setTimeout(function () { reject(new Error("timeout")); }, ms);
    });
  }

  function readTick() {
    var request = fetch(tick, {
      method: "GET",
      credentials: "omit",
      cache: "no-store"
    }).then(function (response) {
      if (!response.ok) {
        throw new Error("status");
      }
      return response.text();
    });
    return Promise.race([request, giveUp(8000)]);
  }

  function refresh() {
    return readTick().then(function (text) {
      show(String(text).trim());
    }).catch(function () {
      show(0);
    });
  }

  fetch(tick, {
    method: "POST",
    credentials: "omit",
    cache: "no-store"
  }).catch(function () {}).then(refresh);

  refresh();
})();
