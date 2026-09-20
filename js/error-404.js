// The 404 page's 'corrupted page' effect: the first scroll, key press or click glitches the facade
// and reveals the real site behind it. Respects prefers-reduced-motion.
(function () {
  var stage = document.getElementById('errorStage');
  var facade = document.getElementById('errorFacade');
  var revealed = document.getElementById('errorRevealed');
  var hintBtn = document.getElementById('errorHint');
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var triggered = false;

  function swapAria() {
    facade.setAttribute('aria-hidden', 'true');
    revealed.removeAttribute('aria-hidden');
  }

  function trigger() {
    if (triggered) return;
    triggered = true;

    if (reduce) {
      stage.classList.add('is-revealed');
      swapAria();
      return;
    }

    stage.classList.add('is-glitching');
    setTimeout(function () {
      stage.classList.add('is-revealed');
      swapAria();
    }, 640);
  }

  window.addEventListener('scroll', trigger, { passive: true, once: true });
  window.addEventListener('wheel', trigger, { passive: true, once: true });
  window.addEventListener('touchmove', trigger, { passive: true, once: true });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'ArrowDown' || e.key === 'PageDown' || e.key === ' ') trigger();
  });
  document.addEventListener('click', function () {
    if (stage.classList.contains('is-revealed')) return;
    trigger();
  });
})();
