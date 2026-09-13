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

  // Dark mode toggle. The <head> inline script already applied the saved
  // theme before paint (avoids a flash); the sun/moon icon swap is pure CSS
  // keyed off [data-theme], so this just flips the attribute + saves it.
  var themeToggle = document.getElementById('theme-toggle');
  if (themeToggle) {
    themeToggle.addEventListener('click', function() {
      var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
      if (isDark) {
        document.documentElement.removeAttribute('data-theme');
      } else {
        document.documentElement.setAttribute('data-theme', 'dark');
      }
      try { localStorage.setItem('hbd-theme', isDark ? 'light' : 'dark'); } catch (e) {}
    });
  }

  // Mobile nav toggle
  var toggle = document.getElementById('nav-toggle');
  var links = document.getElementById('nav-links');
  if (toggle && links) {
    var openNav = function() {
      links.classList.add('open');
      document.body.style.overflow = 'hidden';
    };
    var closeNav = function() {
      links.classList.remove('open');
      document.body.style.overflow = '';
    };
    toggle.addEventListener('click', function() {
      if (links.classList.contains('open')) closeNav(); else openNav();
    });
    // Tapping a link should close the menu, not leave it open underneath
    // the page it just navigated to (or over the same page, for #anchors).
    links.querySelectorAll('a').forEach(function(a) {
      a.addEventListener('click', closeNav);
    });
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && links.classList.contains('open')) {
        closeNav();
        toggle.focus();
      }
    });
    document.addEventListener('click', function(e) {
      if (!links.classList.contains('open')) return;
      if (links.contains(e.target) || toggle.contains(e.target)) return;
      closeNav();
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


  // Terminal-style type-on for section kickers (skips the hero kicker, which
  // has its own entrance). JS just sets the character count; CSS does the rest.
  var reduceMotion = window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var kickers = Array.prototype.filter.call(
    document.querySelectorAll('.kicker'),
    function(k) { return !k.closest('.hero-copy'); }
  );
  if (kickers.length && !reduceMotion && 'IntersectionObserver' in window) {
    var kickerObserver = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        if (!entry.isIntersecting) return;
        var k = entry.target;
        var chars = (k.textContent || '').replace(/\s+$/, '').length || 10;
        k.style.setProperty('--kn', String(chars));
        k.classList.add('kicker--type');
        kickerObserver.unobserve(k);
      });
    }, { threshold: 0.9, rootMargin: '0px 0px -6% 0px' });
    kickers.forEach(function(k) { kickerObserver.observe(k); });
  }


  // Click-to-zoom lightbox for painting detail pages. Each such page has one
  // .framed-art[data-large] image and one #lightbox overlay.
  var zoomImg = document.querySelector('.framed-art[data-large]');
  var lightbox = document.getElementById('lightbox');
  if (zoomImg && lightbox) {
    var lightboxImg = lightbox.querySelector('img');
    var lightboxClose = lightbox.querySelector('.lightbox-close');
    var lastFocused = null;

    var openLightbox = function() {
      lightboxImg.src = zoomImg.getAttribute('data-large');
      lightboxImg.alt = zoomImg.alt;
      lightbox.hidden = false;
      document.body.style.overflow = 'hidden';
      lastFocused = document.activeElement;
      if (lightboxClose) lightboxClose.focus();
    };
    var closeLightbox = function() {
      lightbox.hidden = true;
      lightboxImg.src = '';
      document.body.style.overflow = '';
      if (lastFocused && lastFocused.focus) lastFocused.focus();
    };

    zoomImg.setAttribute('tabindex', '0');
    zoomImg.setAttribute('role', 'button');
    zoomImg.setAttribute('aria-label', 'Zoom in on this painting');
    zoomImg.addEventListener('click', openLightbox);
    zoomImg.addEventListener('keydown', function(e) {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openLightbox(); }
    });

    lightbox.addEventListener('click', function(e) {
      if (e.target === lightbox) closeLightbox();
    });
    if (lightboxClose) lightboxClose.addEventListener('click', closeLightbox);
    document.addEventListener('keydown', function(e) {
      if (lightbox.hidden) return;
      if (e.key === 'Escape') { closeLightbox(); return; }
      // Trap focus inside the lightbox while it's open (there's just the
      // close button today, but this keeps working if more get added).
      if (e.key === 'Tab') {
        var focusable = lightbox.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
        if (!focusable.length) return;
        var first = focusable[0];
        var last = focusable[focusable.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault(); last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault(); first.focus();
        }
      }
    });
  }
})();
