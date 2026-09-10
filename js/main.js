// HBD main.js — scroll-away yellow header + mobile nav toggle

(function() {
  var bar = document.getElementById('yellow-bar');
  var lastScroll = 0;
  var scrollThreshold = 80;

  if (!bar) return;

  // Throttle scroll handler for performance
  var ticking = false;
  window.addEventListener('scroll', function() {
    if (!ticking) {
      window.requestAnimationFrame(function() {
        var scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        var scrolledClass = bar.classList.contains('scrolled');
        var hiddenClass = bar.classList.contains('hidden');

        // Add 'scrolled' class for subtle shrink effect
        if (scrollTop > scrollThreshold) {
          if (!scrolledClass) bar.classList.add('scrolled');
        } else {
          if (scrolledClass) bar.classList.remove('scrolled');
        }

        // Hide on scroll down, show on scroll up
        if (scrollTop > lastScroll && scrollTop > 100 && !hiddenClass) {
          bar.classList.add('hidden');
        } else if (scrollTop < lastScroll && hiddenClass) {
          bar.classList.remove('hidden');
        }

        lastScroll = scrollTop <= 0 ? 0 : scrollTop;
        ticking = false;
      });
      ticking = true;
    }
  });

  // Mobile nav toggle
  var toggle = document.getElementById('nav-toggle');
  var links = document.getElementById('nav-links');
  if (toggle && links) {
    toggle.addEventListener('click', function() {
      links.classList.toggle('open');
    });
  }

  // Highlight the nav link matching the current page
  var navAnchors = document.querySelectorAll('#nav-links a');
  var currentPath = window.location.pathname.replace(/\/index\.html$/, '/');
  navAnchors.forEach(function(anchor) {
    var anchorPath = anchor.getAttribute('href').replace(/\/index\.html$/, '/');
    if (anchorPath === currentPath) {
      anchor.setAttribute('aria-current', 'page');
    }
  });


  // Click-to-copy email chip (footer "Copy" button)
  var copyButtons = document.querySelectorAll('.copy-email-btn');
  copyButtons.forEach(function(btn) {
    if (!navigator.clipboard || !navigator.clipboard.writeText) {
      btn.style.display = 'none';
      return;
    }
    btn.addEventListener('click', function() {
      var email = btn.getAttribute('data-email');
      navigator.clipboard.writeText(email).then(function() {
        btn.textContent = 'Copied!';
        btn.classList.add('copied');
        setTimeout(function() {
          btn.textContent = 'Copy';
          btn.classList.remove('copied');
        }, 1500);
      });
    });
  });


  // Scroll-reveal: elements marked [data-reveal] fade up as they enter view.
  // data-reveal="info" animates the element's .project-info child (so the
  // painting stays visible); any other value animates the element itself.
  var revealItems = document.querySelectorAll('[data-reveal]');
  if (revealItems.length) {
    document.body.classList.add('reveal-on');

    var prefersReducedMotion = window.matchMedia &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (prefersReducedMotion || !('IntersectionObserver' in window)) {
      revealItems.forEach(function(el) { el.classList.add('is-revealed'); });
    } else {
      // Stagger each item by its column so every row cascades left-to-right,
      // regardless of how many rows the grid has.
      revealItems.forEach(function(el) {
        var parent = el.parentElement;
        var siblings = parent ? parent.children : [el];
        var index = Array.prototype.indexOf.call(siblings, el);
        var cols = 1;
        if (parent) {
          var tpl = getComputedStyle(parent).gridTemplateColumns;
          if (tpl && tpl !== 'none') cols = tpl.split(' ').length;
        }
        var col = cols > 0 ? index % cols : Math.max(index, 0);
        var target = el.getAttribute('data-reveal') === 'info'
          ? el.querySelector('.project-info')
          : el;
        if (target) target.style.transitionDelay = (col * 0.08) + 's';
      });

      var revealObserver = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-revealed');
            revealObserver.unobserve(entry.target);
          }
        });
      }, { threshold: 0.15, rootMargin: '0px 0px -12% 0px' });

      revealItems.forEach(function(el) { revealObserver.observe(el); });
    }
  }
})();
