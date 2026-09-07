/* Interactive curve on the Results page.
   Data is the output of the original notebook run. */
(function () {
  var svg = document.getElementById('chart');
  if (!svg) { return; }

  var tip = document.getElementById('tip');
  var legendEl = document.getElementById('legend');
  var titleEl = document.getElementById('chart-title');
  var NS = 'http://www.w3.org/2000/svg';
  var PAD_L = 50, PAD_R = 62, PAD_T = 16, PAD_B = 30;

  var M = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

  /* Categorical slots validated for CVD separation and >=3:1 contrast
     against the #ffffff card surface. */
  var VIEWS = {
    rates: {
      title: 'Rates in % by maturity',
      unit: '%', dec: 2, tick: 1,
      lines: [
        { name: 'Spot',    color: '#c4452c', x: M,          y: [5.07, 5.14, 5.11, 5.00, 4.85, 4.67, 4.47, 4.27, 4.07, 3.87] },
        { name: 'YTM',     color: '#008878', x: M,          y: [5.07, 5.14, 5.11, 5.00, 4.86, 4.69, 4.51, 4.33, 4.15, 3.98] },
        { name: 'Forward', color: '#9c7212', x: M.slice(1), y: [5.21, 5.04, 4.68, 4.26, 3.78, 3.30, 2.87, 2.45, 2.08] }
      ]
    },
    df: {
      title: 'Discount factor by maturity',
      unit: '', dec: 4, tick: 3,
      lines: [
        { name: 'Discount factor', color: '#c4452c', x: M, y: [0.9517, 0.9046, 0.8612, 0.8227, 0.7892, 0.7604, 0.7361, 0.7156, 0.6985, 0.6842] }
      ]
    }
  };

  var view = 'rates';
  var geom = null;

  function el(name, attrs) {
    var e = document.createElementNS(NS, name);
    for (var k in attrs) { e.setAttribute(k, attrs[k]); }
    return e;
  }

  function draw() {
    var cfg = VIEWS[view];
    var box = svg.getBoundingClientRect();
    var W = Math.max(300, box.width);
    var H = box.height || 340;

    svg.setAttribute('viewBox', '0 0 ' + W + ' ' + H);
    while (svg.firstChild) { svg.removeChild(svg.firstChild); }
    titleEl.textContent = cfg.title;

    var all = [];
    cfg.lines.forEach(function (l) { all = all.concat(l.y); });
    var lo = Math.min.apply(null, all);
    var hi = Math.max.apply(null, all);
    var span = (hi - lo) || 1;
    lo -= span * 0.16;
    hi += span * 0.16;

    var X = function (m) { return PAD_L + (m - 1) / 9 * (W - PAD_L - PAD_R); };
    var Y = function (v) { return PAD_T + (hi - v) / (hi - lo) * (H - PAD_T - PAD_B); };
    geom = { X: X, Y: Y, W: W, H: H, cfg: cfg };

    for (var i = 0; i <= 4; i++) {
      var v = lo + (hi - lo) * i / 4;
      var gy = Y(v);
      svg.appendChild(el('line', { x1: PAD_L, x2: W - PAD_R, y1: gy, y2: gy, 'class': 'gridline' }));
      var yl = el('text', { x: PAD_L - 10, y: gy + 3, 'class': 'axis-text', 'text-anchor': 'end' });
      yl.textContent = v.toFixed(cfg.tick);
      svg.appendChild(yl);
    }

    M.forEach(function (m) {
      var xl = el('text', { x: X(m), y: H - 8, 'class': 'axis-text', 'text-anchor': 'middle' });
      xl.textContent = m + 'Y';
      svg.appendChild(xl);
    });

    cfg.lines.forEach(function (l) {
      var d = l.x.map(function (m, i) {
        return (i ? 'L' : 'M') + X(m) + ' ' + Y(l.y[i]);
      }).join(' ');
      svg.appendChild(el('path', { d: d, 'class': 'series-line', stroke: l.color }));

      l.x.forEach(function (m, i) {
        svg.appendChild(el('circle', {
          cx: X(m), cy: Y(l.y[i]), r: 4, 'class': 'series-dot', fill: l.color
        }));
      });

      /* direct label at the right-hand end, so identity is never colour-alone */
      var last = l.x.length - 1;
      var lab = el('text', {
        x: X(l.x[last]) + 9, y: Y(l.y[last]) + 4, 'class': 'dlabel', fill: l.color
      });
      lab.textContent = l.name;
      svg.appendChild(lab);
    });

    svg.appendChild(el('line', {
      id: 'cross', x1: 0, x2: 0, y1: PAD_T, y2: H - PAD_B, 'class': 'crosshair'
    }));

    legendEl.innerHTML = cfg.lines.length > 1
      ? cfg.lines.map(function (l) {
          return '<span><i style="background:' + l.color + '"></i>' + l.name + '</span>';
        }).join('')
      : '';
  }

  function hover(ev) {
    if (!geom) { return; }
    var box = svg.getBoundingClientRect();
    var cx = ev.touches ? ev.touches[0].clientX : ev.clientX;
    var step = (geom.W - PAD_L - PAD_R) / 9;
    var m = Math.round(1 + (cx - box.left - PAD_L) / step);
    m = Math.max(1, Math.min(10, m));

    var cross = document.getElementById('cross');
    if (cross) {
      cross.setAttribute('x1', geom.X(m));
      cross.setAttribute('x2', geom.X(m));
      cross.style.opacity = 1;
    }

    var rows = geom.cfg.lines.map(function (l) {
      var i = l.x.indexOf(m);
      if (i < 0) { return null; }
      return '<span style="color:' + l.color + '">&#9679;</span> ' + l.name +
             ' <b>' + l.y[i].toFixed(geom.cfg.dec) + geom.cfg.unit + '</b>';
    }).filter(Boolean);

    tip.innerHTML = '<b>' + m + 'Y</b><br>' + rows.join('<br>');
    tip.style.opacity = 1;

    var card = svg.parentNode.getBoundingClientRect();
    var left = (box.left - card.left) + geom.X(m) + 14;
    if (left + tip.offsetWidth > card.width - 10) {
      left = (box.left - card.left) + geom.X(m) - tip.offsetWidth - 14;
    }
    tip.style.left = left + 'px';
    tip.style.top = ((box.top - card.top) + 14) + 'px';
  }

  function leave() {
    tip.style.opacity = 0;
    var c = document.getElementById('cross');
    if (c) { c.style.opacity = 0; }
  }

  svg.addEventListener('mousemove', hover);
  svg.addEventListener('touchmove', hover, { passive: true });
  svg.addEventListener('mouseleave', leave);
  svg.addEventListener('touchend', leave);

  Array.prototype.forEach.call(document.querySelectorAll('.switch button'), function (b) {
    b.addEventListener('click', function () {
      Array.prototype.forEach.call(document.querySelectorAll('.switch button'), function (o) {
        o.classList.remove('active');
        o.setAttribute('aria-pressed', 'false');
      });
      b.classList.add('active');
      b.setAttribute('aria-pressed', 'true');
      view = b.getAttribute('data-view');
      leave();
      draw();
    });
  });

  var t;
  window.addEventListener('resize', function () {
    clearTimeout(t);
    t = setTimeout(draw, 120);
  });

  if (document.fonts && document.fonts.ready) { document.fonts.ready.then(draw); }
  draw();
})();
