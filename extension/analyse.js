    // ── Page switching ──
    function switchPage(name) {
      document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
      document.getElementById('page-' + name).classList.add('active');
      document.getElementById('analyse-menu').classList.remove('open');
      document.getElementById('analyse-trigger').classList.remove('open');
      if (name === 'bullbear') buildChart();
    }

    // ── Dropdown ──
    document.getElementById('analyse-trigger').addEventListener('click', (e) => {
      e.stopPropagation();
      const menu = document.getElementById('analyse-menu');
      const trigger = document.getElementById('analyse-trigger');
      const isOpen = menu.classList.contains('open');
      menu.classList.toggle('open', !isOpen);
      trigger.classList.toggle('open', !isOpen);
    });
    document.getElementById('menu-analyse').addEventListener('click', (e) => {
      e.stopPropagation();
      document.getElementById('analyse-menu').classList.remove('open');
      document.getElementById('analyse-trigger').classList.remove('open');
      doSearch();
    });
    document.getElementById('menu-bullbear').addEventListener('click', (e) => {
      e.stopPropagation();
      switchPage('bullbear');
    });
    document.getElementById('menu-cagr').addEventListener('click', (e) => {
      e.stopPropagation();
      switchPage('cagr');
    });
    document.addEventListener('click', () => {
      document.getElementById('analyse-menu').classList.remove('open');
      document.getElementById('analyse-trigger').classList.remove('open');
    });

    // ── Theme ──
    let isDark = true;
    function toggleTheme() {
      isDark = !isDark;
      if (isDark) {
        document.documentElement.classList.remove('light');
      } else {
        document.documentElement.classList.add('light');
      }
      document.getElementById('theme-btn').textContent = isDark ? '☀️ Light Mode' : '🌙 Dark Mode';
      if (bbChart) { bbChart.destroy(); bbChart = null; buildChart(); }
    }
    document.getElementById('theme-btn').addEventListener('click', (e) => {
      e.stopPropagation();
      toggleTheme();
    });

    // ── Search ──
    document.getElementById('search-input').addEventListener('keydown', e => { if (e.key === 'Enter') doSearch(); });

    async function doSearch() {
      const symbol = document.getElementById('search-input').value.trim().toUpperCase();
      if (!symbol) return;
      const payload = { symbol, investment: 100000, years: 5 };
      document.getElementById('page-status').textContent = '⏳ Calculating...';
      document.getElementById('results-area').style.display = 'none';
      let port = await findPort();
      let data;
      if (port) {
        try {
          const resp = await fetch(`http://localhost:${port}/cagr`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
          data = await resp.json();
        } catch(e) { document.getElementById('page-status').textContent = '❌ ' + e.message; return; }
      } else {
        document.getElementById('page-status').textContent = '⚙️ Starting engine...';
        data = await new Promise(resolve => { chrome.runtime.sendMessage({ action: 'cagrViaNative', payload }, resolve); });
      }
      if (!data || data.error) { document.getElementById('page-status').textContent = '❌ ' + (data?.error || 'Error'); return; }
      showResults(data);
    }

    async function findPort() {
      for (let p = 5758; p <= 5768; p++) {
        try { const r = await fetch(`http://localhost:${p}/ping`, { signal: AbortSignal.timeout(300) }); if (r.ok) return p; } catch(_) {}
      }
      return null;
    }

    function fmt(n) { return Number(n).toLocaleString('en-IN', { maximumFractionDigits: 2 }); }

    function showResults(d) {
      document.getElementById('page-status').textContent = '';
      document.getElementById('results-area').style.display = 'block';
      document.getElementById('r-symbol').textContent = d.symbol;
      const cagrEl = document.getElementById('r-cagr');
      cagrEl.textContent = (d.cagr_pct >= 0 ? '+' : '') + d.cagr_pct.toFixed(2) + '%';
      cagrEl.className = 'cagr-hero-value ' + (d.cagr_pct >= 0 ? 'pos' : 'neg');
      document.getElementById('r-meta').textContent = `${d.start_date} → ${d.end_date}  (${d.years} years)`;
      document.getElementById('r-start-price').textContent = 'Rs. ' + fmt(d.start_price);
      document.getElementById('r-ltp').textContent         = 'Rs. ' + fmt(d.ltp);
      document.getElementById('r-units').textContent       = d.total_units_today + ' kitta';
      document.getElementById('r-market').textContent      = 'Rs. ' + fmt(d.market_value);
      document.getElementById('r-divs').textContent        = 'Rs. ' + fmt(d.total_cash_dividends);
      document.getElementById('r-today').textContent       = 'Rs. ' + fmt(d.todays_value);
      document.getElementById('r-invest').textContent      = 'Rs. ' + fmt(d.initial_investment);
      document.getElementById('r-years').textContent       = d.years + ' yrs';
      const tbody = document.getElementById('r-events');
      tbody.innerHTML = '';
      if (d.events && d.events.length > 0) {
        d.events.forEach(ev => {
          const tr = document.createElement('tr');
          const badge = ev.type === 'bonus'
            ? `<span class="badge badge-bonus">Bonus ${(ev.pct*100).toFixed(0)}%</span>`
            : `<span class="badge badge-cash">Cash ${(ev.pct*100).toFixed(1)}%</span>`;
          tr.innerHTML = `<td>${ev.date}</td><td>${badge}</td><td>${ev.fiscal_year || '—'}</td><td>${ev.units_after.toFixed(4)}</td><td>${ev.type === 'cash' ? 'Rs. ' + fmt(ev.cash_rs) : '—'}</td>`;
          tbody.appendChild(tr);
        });
      } else {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:var(--label);padding:16px">No events in this period</td></tr>';
      }
    }

    // ── Bull & Bear Chart ──
    let bbChart = null;

    const chartLabels = ["2011-01-31","2011-02-28","2011-03-31","2011-04-28","2011-05-31","2011-06-30","2011-07-31","2011-08-30","2011-09-29","2011-10-31","2011-11-28","2011-12-29","2012-01-31","2012-02-29","2012-03-29","2012-04-30","2012-05-31","2012-06-28","2012-07-31","2012-08-30","2012-09-30","2012-10-31","2012-11-29","2012-12-31","2013-01-31","2013-02-28","2013-03-31","2013-04-30","2013-05-30","2013-06-30","2013-07-31","2013-08-29","2013-09-30","2013-10-31","2013-11-28","2013-12-31","2014-01-29","2014-02-26","2014-03-31","2014-04-30","2014-05-28","2014-06-30","2014-07-31","2014-08-31","2014-09-30","2014-10-30","2014-11-30","2014-12-31","2015-01-29","2015-02-26","2015-03-31","2015-04-23","2015-05-31","2015-06-30","2015-07-30","2015-08-31","2015-09-30","2015-10-29","2015-11-30","2015-12-31","2016-01-31","2016-02-29","2016-03-31","2016-04-28","2016-05-31","2016-06-30","2016-07-31","2016-08-31","2016-09-29","2016-10-27","2016-11-30","2016-12-29","2017-01-31","2017-02-28","2017-03-30","2017-04-30","2017-05-31","2017-06-28","2017-07-31","2017-08-31","2017-09-26","2017-10-31","2017-11-30","2017-12-31","2018-01-31","2018-02-28","2018-03-29","2018-04-29","2018-05-31","2018-06-28","2018-07-31","2018-08-30","2018-09-30","2018-10-31","2018-11-29","2018-12-31","2019-01-31","2019-02-27","2019-03-31","2019-04-30","2019-05-30","2019-06-30","2019-07-31","2019-08-29","2019-09-30","2019-10-31","2019-11-28","2019-12-31","2020-01-30","2020-02-27","2020-03-22","2020-05-13","2020-06-30","2020-07-30","2020-08-31","2020-09-30","2020-10-29","2020-11-30","2020-12-31","2021-01-31","2021-02-28","2021-03-31","2021-04-29","2021-05-31","2021-06-30","2021-07-29","2021-08-31","2021-09-30","2021-10-31","2021-11-30","2021-12-29","2022-01-31","2022-02-28","2022-03-31","2022-04-28","2022-05-31","2022-06-30","2022-07-31","2022-08-31","2022-09-29","2022-10-31","2022-11-30","2022-12-29","2023-01-31","2023-02-28","2023-03-30","2023-04-30","2023-05-31","2023-06-28","2023-07-31","2023-08-30","2023-09-27","2023-10-31","2023-11-30","2023-12-28","2024-01-31","2024-02-29","2024-03-31","2024-04-30","2024-05-30","2024-06-30","2024-07-31","2024-08-29","2024-09-30","2024-10-30","2024-11-28","2024-12-31","2025-01-28","2025-02-27","2025-03-30","2025-04-30","2025-05-28","2025-06-30","2025-07-31","2025-08-31","2025-09-28","2025-10-30","2025-11-30","2025-12-31","2026-01-29","2026-02-26","2026-03-31","2026-04-30","2026-05-06"];
    const chartValues = [410.57,391.66,365.0,348.0,337.0,337.0,359.0,340.0,331.0,330.0,323.0,316.0,316.0,315.0,299.0,405.0,374.0,377.0,401.0,406.0,415.0,451.0,489.0,534.0,511.0,542.0,511.0,501.0,500.0,493.0,548.0,551.0,542.0,579.0,644.0,771.0,781.0,826.0,792.0,823.0,867.0,946.0,1066.0,953.0,938.0,930.0,857.0,902.0,987.0,979.0,946.0,938.0,872.0,949.0,1028.0,1200.0,1181.28,1092.04,1034.12,1151.38,1220.7,1283.94,1355.48,1464.91,1532.12,1723.23,1862.76,1797.45,1753.38,1759.71,1608.33,1443.38,1326.6,1299.29,1587.64,1650.78,1608.11,1563.81,1652.69,1580.03,1549.46,1533.53,1537.67,1390.58,1404.49,1345.99,1220.29,1349.01,1307.66,1198.54,1191.47,1181.69,1256.71,1221.46,1148.36,1188.19,1161.63,1105.53,1143.09,1298.6,1319.47,1244.89,1265.57,1196.41,1135.56,1146.17,1112.79,1166.03,1325.38,1632.17,1251.45,1201.57,1260.75,1439.06,1484.99,1550.43,1645.67,1997.05,2087.27,2370.54,2474.39,2619.03,2611.1,2782.68,2823.87,3079.83,2975.84,2633.42,2837.61,2628.37,2524.5,2872.05,2610.58,2544.31,2356.17,2137.92,2037.64,2195.1,1973.38,1853.76,1874.88,1949.85,2029.03,2111.68,2019.93,1908.55,1870.65,1849.79,2150.99,2106.18,1990.59,2004.3,1864.4,1858.53,2068.9,2097.93,1972.09,2018.33,2006.28,2069.53,2037.09,2760.9,2749.57,2508.86,2677.62,2748.05,2576.5,2657.77,2815.04,2693.12,2623.83,2693.06,2631.48,2922.63,2749.83,2663.51,2600.38,2649.52,2633.76,2714.05,2654.93,2851.09,2738.72,2711.22];

    // Bull tops and bear bottoms visible in our CSV range
    const bullTops  = [{ date: "2016-07-31", value: 1862.76, label: "Bull Top 3\n1,881" }, { date: "2021-08-31", value: 3079.83, label: "Bull Top 4\n3,199" }];
    const bearBottoms = [{ date: "2012-03-29", value: 299.0, label: "Bear\n299" }, { date: "2019-03-31", value: 1143.09, label: "Bear\n1,099" }];

    function buildChart() {
      if (bbChart) { bbChart.destroy(); bbChart = null; }
      const lineColor = isDark ? '#4ecdc4' : '#2aa198';
      const gridColor = isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.06)';
      const textColor = isDark ? '#7a9bb5' : '#657b83';

      // Build annotation points
      const bullPointData  = chartLabels.map((l, i) => bullTops.find(b => b.date === l) ? chartValues[i] : null);
      const bearPointData  = chartLabels.map((l, i) => bearBottoms.find(b => b.date === l) ? chartValues[i] : null);

      bbChart = new Chart(document.getElementById('bb-chart'), {
        type: 'line',
        data: {
          labels: chartLabels,
          datasets: [
            {
              label: 'NEPSE Index',
              data: chartValues,
              borderColor: lineColor,
              borderWidth: 2,
              pointRadius: 0,
              pointHoverRadius: 4,
              fill: true,
              backgroundColor: isDark ? 'rgba(78,205,196,0.07)' : 'rgba(42,161,152,0.07)',
              tension: 0.3,
            },
            {
              label: 'Bull Top',
              data: bullPointData,
              borderColor: 'transparent',
              backgroundColor: isDark ? '#4ecdc4' : '#2aa198',
              pointRadius: 8,
              pointStyle: 'triangle',
              pointHoverRadius: 10,
              showLine: false,
            },
            {
              label: 'Bear Bottom',
              data: bearPointData,
              borderColor: 'transparent',
              backgroundColor: isDark ? '#ff6b6b' : '#dc322f',
              pointRadius: 8,
              pointStyle: 'triangle',
              rotation: 180,
              pointHoverRadius: 10,
              showLine: false,
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: { mode: 'index', intersect: false },
          plugins: {
            legend: { display: false },
            tooltip: {
              callbacks: {
                title: ctx => ctx[0].label,
                label: ctx => {
                  if (ctx.datasetIndex === 0) return ' NEPSE: ' + ctx.parsed.y.toLocaleString();
                  if (ctx.datasetIndex === 1 && ctx.parsed.y) return ' 🐂 Bull Top: ' + ctx.parsed.y.toLocaleString();
                  if (ctx.datasetIndex === 2 && ctx.parsed.y) return ' 🐻 Bear Bottom: ' + ctx.parsed.y.toLocaleString();
                  return null;
                },
                filter: item => item.parsed.y !== null
              }
            }
          },
          scales: {
            x: {
              ticks: {
                color: textColor,
                maxTicksLimit: 12,
                maxRotation: 0,
                callback: (val, idx) => {
                  const d = chartLabels[idx];
                  return d ? d.substring(0, 7) : '';
                }
              },
              grid: { color: gridColor }
            },
            y: {
              ticks: { color: textColor, callback: v => v.toLocaleString() },
              grid: { color: gridColor }
            }
          }
        }
      });
    }

    // ── CAGR page period toggle ──
    let cagrUseYears = true;
    document.getElementById('cagr-years-btn').onclick = () => {
      cagrUseYears = true;
      document.getElementById('cagr-years-btn').classList.add('active');
      document.getElementById('cagr-date-btn').classList.remove('active');
      document.getElementById('cagr-years').style.display = '';
      document.getElementById('cagr-date').style.display = 'none';
    };
    document.getElementById('cagr-date-btn').onclick = () => {
      cagrUseYears = false;
      document.getElementById('cagr-date-btn').classList.add('active');
      document.getElementById('cagr-years-btn').classList.remove('active');
      document.getElementById('cagr-years').style.display = 'none';
      document.getElementById('cagr-date').style.display = '';
    };

    // ── CAGR calculate ──
    document.getElementById('cagr-btn').onclick = doCagr;
    document.getElementById('cagr-symbol').addEventListener('keydown', e => { if (e.key === 'Enter') doCagr(); });

    async function doCagr() {
      const symbol = document.getElementById('cagr-symbol').value.trim().toUpperCase();
      if (!symbol) return;
      const investment = parseFloat(document.getElementById('cagr-invest').value) || 100000;
      const payload = { symbol, investment };
      if (cagrUseYears) payload.years = parseFloat(document.getElementById('cagr-years').value) || 5;
      else payload.start_date = document.getElementById('cagr-date').value;

      document.getElementById('cagr-status').textContent = '⏳ Calculating...';
      document.getElementById('cagr-results-area').style.display = 'none';

      let port = await findPort();
      let data;
      if (port) {
        try {
          const resp = await fetch(`http://localhost:${port}/cagr`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
          data = await resp.json();
        } catch(e) { document.getElementById('cagr-status').textContent = '❌ ' + e.message; return; }
      } else {
        document.getElementById('cagr-status').textContent = '⚙️ Starting engine...';
        data = await new Promise(resolve => { chrome.runtime.sendMessage({ action: 'cagrViaNative', payload }, resolve); });
      }
      if (!data || data.error) { document.getElementById('cagr-status').textContent = '❌ ' + (data?.error || 'Error'); return; }
      showCagrResults(data);
    }

    function showCagrResults(d) {
      document.getElementById('cagr-status').textContent = '';
      document.getElementById('cagr-results-area').style.display = 'block';
      document.getElementById('cr-symbol').textContent = d.symbol;
      const el = document.getElementById('cr-cagr');
      el.textContent = (d.cagr_pct >= 0 ? '+' : '') + d.cagr_pct.toFixed(2) + '%';
      el.className = 'cagr-hero-value ' + (d.cagr_pct >= 0 ? 'pos' : 'neg');
      document.getElementById('cr-meta').textContent = `${d.start_date} → ${d.end_date}  (${d.years} years)`;
      document.getElementById('cr-start-price').textContent = 'Rs. ' + fmt(d.start_price);
      document.getElementById('cr-ltp').textContent         = 'Rs. ' + fmt(d.ltp);
      document.getElementById('cr-units').textContent       = d.total_units_today + ' kitta';
      document.getElementById('cr-market').textContent      = 'Rs. ' + fmt(d.market_value);
      document.getElementById('cr-divs').textContent        = 'Rs. ' + fmt(d.total_cash_dividends);
      document.getElementById('cr-today').textContent       = 'Rs. ' + fmt(d.todays_value);
      document.getElementById('cr-invest').textContent      = 'Rs. ' + fmt(d.initial_investment);
      document.getElementById('cr-years').textContent       = d.years + ' yrs';
      const tbody = document.getElementById('cr-events');
      tbody.innerHTML = '';
      if (d.events && d.events.length > 0) {
        d.events.forEach(ev => {
          const tr = document.createElement('tr');
          const badge = ev.type === 'bonus'
            ? `<span class="badge badge-bonus">Bonus ${(ev.pct*100).toFixed(0)}%</span>`
            : `<span class="badge badge-cash">Cash ${(ev.pct*100).toFixed(1)}%</span>`;
          tr.innerHTML = `<td>${ev.date}</td><td>${badge}</td><td>${ev.fiscal_year || '—'}</td><td>${ev.units_after.toFixed(4)}</td><td>${ev.type === 'cash' ? 'Rs. ' + fmt(ev.cash_rs) : '—'}</td>`;
          tbody.appendChild(tr);
        });
      } else {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:var(--label);padding:16px">No events in this period</td></tr>';
      }
    }
