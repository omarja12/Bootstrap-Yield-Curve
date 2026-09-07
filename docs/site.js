/* Mobile navigation toggle, shared by every page. */
(function () {
  var btn = document.getElementById('menuBtn');
  var bar = document.getElementById('sidebar');
  if (!btn || !bar) { return; }
  btn.addEventListener('click', function () {
    var open = bar.classList.toggle('open');
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    btn.textContent = open ? 'CLOSE' : 'MENU';
  });
})();
