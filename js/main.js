// HBD main.js — scroll-away header + slide-out side nav

(function() {
  var bar = document.getElementById('site-header');
  var lastScroll = 0;

  if (!bar) return;

  // Throttle scroll handler for performance
  var ticking = false;
  window.addEventListener('scroll', function() {
    if (!ticking) {
      window.requestAnimationFrame(function() {
        var scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        var hiddenClass = bar.classList.contains('hidden');
        var delta = scrollTop - lastScroll;

        // Mobile Safari's address bar collapsing/expanding mid-scroll makes
        // scrollTop jitter by a few px even during a single steady swipe --
        // ignoring small deltas keeps that noise from flipping the class
        // back and forth so the header never finishes hiding.
        if (Math.abs(delta) > 5) {
          if (delta > 0 && scrollTop > 100 && !hiddenClass) {
            bar.classList.add('hidden');
          } else if (delta < 0 && hiddenClass) {
            bar.classList.remove('hidden');
          }
          lastScroll = scrollTop <= 0 ? 0 : scrollTop;
        }

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

  // Announcement bar close button -- remembers the dismissal by the bar's
  // data-announcement-id, so a *different* announcement (a new id, set in
  // site.json for the next drop) shows again even if the last one was closed.
  var announcementBar = document.getElementById('announcement-bar');
  var announcementClose = document.getElementById('announcement-close');
  if (announcementBar && announcementClose) {
    announcementClose.addEventListener('click', function() {
      document.documentElement.setAttribute('data-announcement-dismissed', '');
      try { localStorage.setItem('hbd-announcement-dismissed', announcementBar.getAttribute('data-announcement-id') || ''); } catch (e) {}
    });
  }

  // Slide-out side nav (same panel at every viewport width)
  var toggle = document.getElementById('nav-toggle');
  var panel = document.getElementById('side-nav');
  var overlay = document.getElementById('nav-overlay');
  var panelClose = document.getElementById('side-nav-close');
  var links = document.getElementById('nav-links');
  if (toggle && panel && overlay && links) {
    var openNav = function() {
      panel.classList.add('open');
      overlay.classList.add('open');
      toggle.setAttribute('aria-expanded', 'true');
      document.body.style.overflow = 'hidden';
      if (panelClose) panelClose.focus();
    };
    var closeNav = function() {
      panel.classList.remove('open');
      overlay.classList.remove('open');
      toggle.setAttribute('aria-expanded', 'false');
      document.body.style.overflow = '';
      toggle.focus();
    };
    toggle.addEventListener('click', function() {
      if (panel.classList.contains('open')) closeNav(); else openNav();
    });
    if (panelClose) panelClose.addEventListener('click', closeNav);
    overlay.addEventListener('click', closeNav);
    // Tapping a link should close the panel, not leave it open underneath
    // the page it just navigated to (or over the same page, for #anchors).
    links.querySelectorAll('a').forEach(function(a) {
      a.addEventListener('click', closeNav);
    });
    document.addEventListener('keydown', function(e) {
      if (!panel.classList.contains('open')) return;
      if (e.key === 'Escape') { closeNav(); return; }
      if (e.key === 'Tab') {
        var focusable = panel.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
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
    var lightboxImg = document.getElementById('lightbox-img');
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
