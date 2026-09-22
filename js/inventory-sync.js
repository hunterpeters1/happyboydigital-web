(function () {
  // Reads inventory.json (published by the shop tools) and reflects it on the page.
  // Each painting is 'available', 'held' (an open invoice is holding it) or 'sold'.
  //   [data-item-title]           gets the Sold seal when that painting is sold (a hold doesn't get one)
  //   [data-hide-if-unavailable]  is hidden unless the painting named in it is available (price, buy box)
  //   [data-show-if-sold]         is revealed when the painting is sold ("This original has sold")
  //   [data-show-if-held]         is revealed when the painting is on hold ("This original is on hold")
  // If inventory.json can't be read the page just shows everything as available.
  var INVENTORY_URL = '/inventory.json';
  var SOLD_GRAPHIC_URL = '/assets/sold-seal.svg';

  function markSoldOut(el) {
    if (el.querySelector('.status-badge')) return; // already marked (manual or otherwise)
    var img = document.createElement('img');
    img.src = SOLD_GRAPHIC_URL;
    img.alt = 'Sold';
    img.width = 56;
    img.height = 56;
    img.loading = 'lazy';
    img.className = 'status-badge';
    el.insertBefore(img, el.firstChild);
  }

  fetch(INVENTORY_URL, { cache: 'no-store' })
    .then(function (res) {
      if (!res.ok) throw new Error('inventory.json fetch failed: ' + res.status);
      return res.json();
    })
    .then(function (data) {
      var items = (data && data.items) || [];
      var statusByTitle = {};
      items.forEach(function (item) {
        // Older files only have in_stock: false, which meant sold.
        statusByTitle[item.title] = item.status || (item.in_stock === false ? 'sold' : 'available');
      });

      function statusOf(title) {
        return Object.prototype.hasOwnProperty.call(statusByTitle, title) ? statusByTitle[title] : 'available';
      }

      document.querySelectorAll('[data-item-title]').forEach(function (el) {
        if (statusOf(el.getAttribute('data-item-title')) === 'sold') markSoldOut(el);
      });
      document.querySelectorAll('[data-hide-if-unavailable]').forEach(function (el) {
        // Inline style rather than the hidden attribute, so it wins over any display rule in the CSS.
        if (statusOf(el.getAttribute('data-hide-if-unavailable')) !== 'available') el.style.display = 'none';
      });
      document.querySelectorAll('[data-show-if-sold]').forEach(function (el) {
        if (statusOf(el.getAttribute('data-show-if-sold')) === 'sold') el.hidden = false;
      });
      document.querySelectorAll('[data-show-if-held]').forEach(function (el) {
        if (statusOf(el.getAttribute('data-show-if-held')) === 'held') el.hidden = false;
      });
    })
    .catch(function (err) {
      // Fail silently on the live site (don't break the page if inventory.json
      // is missing/stale) but leave a console trace for debugging.
      console.warn('Inventory sync skipped:', err);
    });
})();
