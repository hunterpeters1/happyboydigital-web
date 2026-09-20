(function () {
  // Reads inventory.json (published by the shop tools) and reflects it on the page.
  //   [data-item-title]     gets the "Sold" badge when that painting is sold out or on hold
  //   [data-hide-if-sold]   is hidden when the painting named in it is sold out (price, buy box)
  //   [data-show-if-sold]   is revealed when the painting named in it is sold out ("This original has sold")
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
      var byTitle = {};
      items.forEach(function (item) { byTitle[item.title] = item.in_stock; });

      function isSoldOut(title) {
        return Object.prototype.hasOwnProperty.call(byTitle, title) && byTitle[title] === false;
      }

      document.querySelectorAll('[data-item-title]').forEach(function (el) {
        if (isSoldOut(el.getAttribute('data-item-title'))) markSoldOut(el);
      });
      document.querySelectorAll('[data-hide-if-sold]').forEach(function (el) {
        // Inline style rather than the hidden attribute, so it wins over any display rule in the CSS.
        if (isSoldOut(el.getAttribute('data-hide-if-sold'))) el.style.display = 'none';
      });
      document.querySelectorAll('[data-show-if-sold]').forEach(function (el) {
        if (isSoldOut(el.getAttribute('data-show-if-sold'))) el.hidden = false;
      });
    })
    .catch(function (err) {
      // Fail silently on the live site (don't break the page if inventory.json
      // is missing/stale) but leave a console trace for debugging.
      console.warn('Inventory sync skipped:', err);
    });
})();
