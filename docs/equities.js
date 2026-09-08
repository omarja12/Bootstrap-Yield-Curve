/* Chapter 05 visuals, drawn from window.EQ (see equities_data.js).

   Five series on one axis cannot be told apart by colour alone -- at five
   slots the all-pairs CVD separation fails whatever hues you pick. So this
   uses small multiples instead: one panel per ticker, one series each, on a
   shared y-scale so the panels stay comparable. Colour then carries no
   identity and the labels do all the work. */
(function () {
  var host = document.getElementById('eq-panels');
  if (!host || !window.EQ) { return; }

  var EQ = window.EQ;
  var NS = 'http://www.w3.org/2000/svg';
  var TICKERS = Object.keys(EQ.series);
  var LINE = '#c4452c';

  // relative luminance of an hsl() colour, so cell text can be chosen not guessed
  function hslLum(h, sPct, lPct) {
    var sN = sPct / 100, lN = lPct / 100;
    var c = (1 - Math.abs(2 * lN - 1)) * sN;
    var x = c * (1 - Math.abs(((h / 60) % 2) - 1));
    var m = lN - c / 2;
    var r, g, b;
    if (h < 60) { r = c; g = x; b = 0; }
    else if (h < 120) { r = x; g = c; b = 0; }
    else if (h < 180) { r = 0; g = c; b = x; }
    else if (h < 240) { r = 0; g = x; b = c; }
    else if (h < 300) { r = x; g = 0; b = c; }
    else { r = c; g = 0; b = x; }
    return [r + m, g + m, b + m].map(function (v) {
      return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
    }).reduce(function (acc, v, i) { return acc + [0.2126, 0.7152, 0.0722][i] * v; }, 0);
  }
  function bestInk(h, s, l) {
    var L = hslLum(h, s, l);
    var vsWhite = 1.05 / (L + 0.05);
    var vsInk = (L + 0.05) / (0.0175 + 0.05); // #16211d
    return vsWhite >= vsInk ? '#fff' : '#16211d';
  }

  function el(name, attrs) {
    var e = document.createElementNS(NS, name);
    for (var k in attrs) { e.setAttribute(k, attrs[k]); }
    return e;
  }

  // one shared scale across every panel, so the panels can be compared
  var hi = 0;
  TICKERS.forEach(function (t) {
    EQ.series[t].forEach(function (v) { if (v > hi) { hi = v; } });
  });
  hi = Math.ceil(hi / 5) * 5;

  var n = EQ.labels.length;

  function panel(t) {
    var wrap = document.createElement('div');
    wrap.className = 'eq-panel';

    var head = document.createElement('div');
    head.className = 'eq-head';
    head.innerHTML = '<span class="eq-t">' + t + '</span>' +
                     '<span class="eq-v">&times;' + EQ.final[t].toFixed(1) + '</span>';
    wrap.appendChild(head);

    var W = 240, H = 96, PB = 2;
    var svg = el('svg', {
      viewBox: '0 0 ' + W + ' ' + H,
      preserveAspectRatio: 'none',
      'class': 'eq-spark',
      role: 'img',
      'aria-label': t + ' grew to ' + EQ.final[t].toFixed(1) +
                    ' times its starting value between ' + EQ.start + ' and ' + EQ.end
    });

    var X = function (i) { return i / (n - 1) * W; };
    var Y = function (v) { return H - PB - (v / hi) * (H - PB * 2); };

    // baseline at 1x — the "no growth" reference
    var base = Y(1);
    svg.appendChild(el('line', { x1: 0, x2: W, y1: base, y2: base, 'class': 'eq-base' }));

    var d = EQ.series[t].map(function (v, i) { return (i ? 'L' : 'M') + X(i).toFixed(1) + ' ' + Y(v).toFixed(1); }).join(' ');
    var area = d + ' L' + W + ' ' + Y(0).toFixed(1) + ' L0 ' + Y(0).toFixed(1) + ' Z';

    svg.appendChild(el('path', { d: area, 'class': 'eq-area' }));
    svg.appendChild(el('path', { d: d, 'class': 'eq-line', stroke: LINE }));
    svg.appendChild(el('circle', {
      cx: X(n - 1), cy: Y(EQ.series[t][n - 1]), r: 3.5, 'class': 'eq-dot', fill: LINE
    }));

    wrap.appendChild(svg);
    return wrap;
  }

  TICKERS.forEach(function (t) { host.appendChild(panel(t)); });

  var scale = document.getElementById('eq-scale');
  if (scale) {
    scale.textContent = 'Shared scale, 0 to ' + hi + '× · month-end · ' +
                        EQ.start + ' to ' + EQ.end;
  }

  /* ---- correlation matrix: one hue, light to dark (sequential) ---- */
  var cm = document.getElementById('eq-corr');
  if (cm && EQ.corr) {
    var vals = [];
    TICKERS.forEach(function (a) {
      TICKERS.forEach(function (b) { if (a !== b) { vals.push(EQ.corr[a][b]); } });
    });
    var lo = Math.min.apply(null, vals), top = Math.max.apply(null, vals);

    var html = '<table class="corr"><caption>Correlation of daily returns. One hue, ' +
               'light to dark &mdash; darker means the pair moves together more.</caption><thead><tr><th></th>';
    TICKERS.forEach(function (t) { html += '<th>' + t + '</th>'; });
    html += '</tr></thead><tbody>';

    TICKERS.forEach(function (a) {
      html += '<tr><td class="rh">' + a + '</td>';
      TICKERS.forEach(function (b) {
        var v = EQ.corr[a][b];
        if (a === b) {
          html += '<td class="diag">&mdash;</td>';
        } else {
          var f = (v - lo) / ((top - lo) || 1);            // 0..1 within the observed range
          var light = 94 - f * 52;                          // lightness walks one direction only
          // pick whichever of ink/white actually contrasts with this cell
          var ink = bestInk(172, 62, light);
          html += '<td style="background:hsl(172 62% ' + light.toFixed(0) + '%);color:' + ink + '">' +
                  v.toFixed(2) + '</td>';
        }
      });
      html += '</tr>';
    });
    html += '</tbody></table>';
    cm.innerHTML = html;
  }
})();
