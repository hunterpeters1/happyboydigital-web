(function () {
  // Reads inventory.json (pushed by the Receipt Generator tool's "Sync to
  // Website" button) and marks any [data-item-title] element whose title is
  // sold out with the same sold-seal badge already used for one-off sold
  // paintings on work.html.
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

      document.querySelectorAll('[data-item-title]').forEach(function (el) {
        var title = el.getAttribute('data-item-title');
        if (Object.prototype.hasOwnProperty.call(byTitle, title) && byTitle[title] === false) {
          markSoldOut(el);
        }
      });
    })
    .catch(function (err) {
      // Fail silently on the live site (don't break the page if inventory.json
      // is missing/stale) but leave a console trace for debugging.
      console.warn('Inventory sync skipped:', err);
    });
})();
