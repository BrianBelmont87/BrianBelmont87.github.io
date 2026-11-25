/* Site-wide page views. One small request, no cookies, no animation.
   tick.rs counts the visit with POST, but that answer is a redirect and the
   old script gave up after 6 seconds, which left the dash on screen.
   A plain GET shows the number, and the previous Abacus total is only used
   if tick.rs does not answer. */
(function () {
  var slot = document.querySelector("[data-visits]");
  if (!slot || !window.fetch) {
    return;
  }

  var tick = "https://tick.rs/c/o8w64MeiLWZQ";
  var abacus = "https://abacus.jasoncameron.dev/get/brianbelmont87.github.io/visits";
  var shown = false;

  function show(value) {
    var number = Number(String(value).trim());
    if (!isFinite(number)) {
      return false;
    }
    slot.textContent = number.toLocaleString("en-US");
    shown = true;
    return true;
  }

  function giveUp(ms) {
    return new Promise(function (_, reject) {
      window.setTimeout(function () { reject(new Error("timeout")); }, ms);
    });
  }

  function read(url) {
    var request = fetch(url, {
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

  function showTickOrPrevious() {
    return read(tick).then(function (text) {
      if (!show(text)) {
        throw new Error("bad");
      }
    }).catch(function () {
      return read(abacus).then(function (text) {
        var data = JSON.parse(text);
        if (!show(data && data.value)) {
          throw new Error("bad");
        }
      });
    }).catch(function () {
      if (!shown) {
        slot.textContent = "—";
      }
    });
  }

  fetch(tick, {
    method: "POST",
    credentials: "omit",
    cache: "no-store"
  }).catch(function () {}).then(showTickOrPrevious);

  showTickOrPrevious();
})();
