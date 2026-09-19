(() => {
  "use strict";
  const DATA = window.RETAIL_DASHBOARD_DATA;
  const colors = ["#0b6f55", "#28b985", "#64d9b0", "#f59d2e", "#aab9c9", "#20b8c1"];
  const icons = { overview: "⌂", customer: "♟", basket: "▣", category: "◆", promotion: "➤", campaign: "%", root: "◷" };
  const pages = {
    overview: { label: "Overview", title: "Retail Customer & Commercial Intelligence", subtitle: "From Data to Decisions  |  Customers · Products · Promotions · Profitability" },
    customer: { label: "Customer Engagement", title: "Customer Engagement & Segmentation", subtitle: "Observed panel households, trajectories and segment contribution" },
    basket: { label: "Basket & Category", title: "Basket & Category Intelligence", subtitle: "Basket behaviour, category penetration and cross-category patterns" },
    category: { label: "Category & Brand", title: "Category, Brand & Private Label", subtitle: "Department and commodity mix, brand type and private-label depth" },
    promotion: { label: "Promotion & Campaign", title: "Promotion & Merchandising", subtitle: "Promotion-state association, dependency and product-store-week activity" },
    campaign: { label: "Campaign & Coupon", title: "Campaign & Coupon Intelligence", subtitle: "Recipients, redeemers, observed response and campaign-linked behaviour" },
    root: { label: "Root Cause Analysis", title: "Root Cause Analysis", subtitle: "Verified drivers, evidence-backed cases and decision actions" },
  };
  const state = { page: "overview", segment: "All", department: "All", commodity: "All", promo: "All", campaignType: "All", minWeek: DATA.meta.observation_index.min_week, maxWeek: DATA.meta.observation_index.max_week };
  const drills = new Map();
  let drillId = 0;

  const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[char]));
  const num = (value, digits = 0) => { digits = typeof digits === "number" ? digits : 0; return value == null || Number.isNaN(Number(value)) ? "—" : Number(value).toLocaleString("en-US", { maximumFractionDigits: digits, minimumFractionDigits: digits }); };
  const money = (value, digits = 0) => { digits = typeof digits === "number" ? digits : 0; return value == null || Number.isNaN(Number(value)) ? "—" : `${Number(value) < 0 ? "−" : ""}$${Math.abs(Number(value)).toLocaleString("en-US", { maximumFractionDigits: digits, minimumFractionDigits: digits })}`; };
  const compactMoney = (value) => value == null || Number.isNaN(Number(value)) ? "—" : Math.abs(value) >= 1e6 ? `$${(value / 1e6).toFixed(2)}M` : Math.abs(value) >= 1e3 ? `$${(value / 1e3).toFixed(1)}K` : money(value, 0);
  const pct = (value, digits = 1) => { digits = typeof digits === "number" ? digits : 1; return value == null || Number.isNaN(Number(value)) ? "—" : `${(Number(value) * 100).toFixed(digits)}%`; };
  const signedPct = (value, digits = 1) => value == null || Number.isNaN(Number(value)) ? "—" : `${value >= 0 ? "+" : "−"}${Math.abs(Number(value) * 100).toFixed(digits)}%`;
  const signed = (value, digits = 0) => { digits = typeof digits === "number" ? digits : 0; return value == null || Number.isNaN(Number(value)) ? "—" : `${value >= 0 ? "+" : "−"}${num(Math.abs(value), digits)}`; };
  const label = (value) => String(value ?? "").replaceAll("_", " ").replace(/\b\w/g, (c) => c.toUpperCase());
  const group = (rows, key) => [...new Set(rows.map((r) => r[key]).filter((v) => v != null))].sort((a, b) => String(a).localeCompare(String(b)));
  const filteredWeeks = (rows) => rows.filter((r) => Number(r.week_number) >= Number(state.minWeek) && Number(r.week_number) <= Number(state.maxWeek));
  const registerDrill = (payload) => { const id = `d${++drillId}`; drills.set(id, payload); return id; };
  const drillAttr = (payload) => `data-drill-id="${registerDrill(payload)}"`;

  function svgBar(rows, key, labelKey, options = {}) {
    if (!rows?.length) return '<div class="empty">No source-backed rows match the selected filters.</div>';
    const horizontal = options.horizontal !== false;
    const limit = rows.slice(0, options.limit || 10);
    const max = Math.max(...limit.map((r) => Number(r[key]) || 0), 1);
    const width = 640, height = horizontal ? Math.max(160, limit.length * 30 + 25) : 220;
    let body = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${esc(options.title || "bar chart")}">`;
    if (horizontal) {
      const left = options.left || 145, barWidth = width - left - 48, rowH = (height - 16) / limit.length;
      limit.forEach((r, i) => {
        const y = 5 + i * rowH, w = Math.max(2, (Number(r[key]) || 0) / max * barWidth), text = String(r[labelKey] ?? "");
        const payload = { title: text, subtitle: options.title, data: r, source: options.source || "Source-backed aggregate" };
        body += `<text x="${left - 8}" y="${y + 17}" text-anchor="end">${esc(text.length > 21 ? `${text.slice(0, 20)}…` : text)}</text><line class="axis" x1="${left}" x2="${width - 22}" y1="${y + 23}" y2="${y + 23}"/><rect class="bar" ${drillAttr(payload)} x="${left}" y="${y + 7}" width="${w}" height="16" rx="7" fill="${colors[i % colors.length]}"/><text x="${Math.min(left + w + 6, width - 35)}" y="${y + 19}" fill="#0b6f55">${esc(options.format ? options.format(r[key]) : num(r[key], 0))}</text>`;
      });
    } else {
      const base = height - 35, chartH = base - 18, groupW = (width - 55) / limit.length;
      limit.forEach((r, i) => {
        const x = 34 + i * groupW + groupW * .18, barH = (Number(r[key]) || 0) / max * chartH, payload = { title: r[labelKey], subtitle: options.title, data: r, source: options.source || "Source-backed aggregate" };
        body += `<line class="axis" x1="30" x2="${width - 18}" y1="${base}" y2="${base}"/><rect class="bar" ${drillAttr(payload)} x="${x}" y="${base - barH}" width="${groupW * .62}" height="${Math.max(2, barH)}" rx="4" fill="${colors[i % colors.length]}"/><text x="${x + groupW * .31}" y="${base + 17}" text-anchor="middle">${esc(String(r[labelKey] ?? "").slice(0, 13))}</text><text x="${x + groupW * .31}" y="${Math.max(11, base - barH - 5)}" text-anchor="middle" fill="#0b6f55">${esc(options.format ? options.format(r[key]) : num(r[key], 0))}</text>`;
      });
    }
    return `${body}</svg>`;
  }

  function svgLine(rows, key, options = {}) {
    if (!rows?.length) return '<div class="empty">No source-backed rows match the selected filters.</div>';
    const data = rows.slice().sort((a, b) => Number(a.week_number) - Number(b.week_number));
    const width = 640, height = 220, pad = { l: 40, r: 18, t: 17, b: 31 }, max = Math.max(...data.map((r) => Number(r[key]) || 0), 1), min = Math.min(...data.map((r) => Number(r[key]) || 0), 0);
    const x = (i) => pad.l + i * (width - pad.l - pad.r) / Math.max(1, data.length - 1);
    const y = (v) => pad.t + (max - Number(v || 0)) / Math.max(1, max - min) * (height - pad.t - pad.b);
    const points = data.map((r, i) => `${x(i)},${y(r[key])}`).join(" ");
    let body = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${esc(options.title || "line chart")}"><line class="axis" x1="${pad.l}" x2="${width - pad.r}" y1="${height - pad.b}" y2="${height - pad.b}"/><line class="axis" x1="${pad.l}" x2="${pad.l}" y1="${pad.t}" y2="${height - pad.b}"/><polyline points="${points}" fill="none" stroke="${options.color || colors[1]}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>`;
    data.forEach((r, i) => { const p = { title: `Week ${r.week_number}`, subtitle: options.title, data: r, source: options.source || "Source-backed weekly mart" }; body += `<circle class="point" ${drillAttr(p)} cx="${x(i)}" cy="${y(r[key])}" r="${data.length > 60 ? 2.1 : 3.5}" fill="${options.color || colors[1]}"/>`; if (i === 0 || i === data.length - 1 || i === Math.floor(data.length / 2)) body += `<text x="${x(i)}" y="${height - 10}" text-anchor="middle">W${esc(r.week_number)}</text>`; });
    return `${body}</svg>`;
  }

  function svgCombo(rows, barKey, lineKey, options = {}) {
    if (!rows?.length) return '<div class="empty">No source-backed rows match the selected filters.</div>';
    const data = rows.slice();
    const width = 640, height = 220, pad = { l: 40, r: 38, t: 17, b: 35 };
    const barMax = Math.max(...data.map((r) => Number(r[barKey]) || 0), 1);
    const lineMax = Math.max(...data.map((r) => Number(r[lineKey]) || 0), 1);
    const chartW = width - pad.l - pad.r, chartH = height - pad.t - pad.b;
    const x = (i) => pad.l + (i + .5) * chartW / data.length;
    const yBar = (v) => pad.t + (barMax - Number(v || 0)) / barMax * chartH;
    const yLine = (v) => pad.t + (lineMax - Number(v || 0)) / lineMax * chartH;
    const points = data.map((r, i) => `${x(i)},${yLine(r[lineKey])}`).join(" ");
    let body = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${esc(options.title || "combo chart")}"><line class="axis" x1="${pad.l}" x2="${width - pad.r}" y1="${height - pad.b}" y2="${height - pad.b}"/><line class="axis" x1="${pad.l}" x2="${pad.l}" y1="${pad.t}" y2="${height - pad.b}"/><line class="axis" x1="${width - pad.r}" x2="${width - pad.r}" y1="${pad.t}" y2="${height - pad.b}"/><polyline points="${points}" fill="none" stroke="${options.lineColor || colors[1]}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>`;
    data.forEach((r, i) => {
      const barH = Math.max(2, (Number(r[barKey]) || 0) / barMax * chartH);
      const barW = Math.max(10, chartW / data.length * .58);
      const payload = { title: r.label || `Week ${r.week_number}`, subtitle: options.title, data: r, source: options.source || "Source-backed aggregate" };
      body += `<rect class="bar" ${drillAttr(payload)} x="${x(i) - barW / 2}" y="${height - pad.b - barH}" width="${barW}" height="${barH}" rx="2" fill="${options.barColor || colors[0]}" opacity=".9"/><circle class="point" ${drillAttr(payload)} cx="${x(i)}" cy="${yLine(r[lineKey])}" r="3.5" fill="${options.lineColor || colors[1]}"/>`;
      body += `<text x="${x(i)}" y="${height - 12}" text-anchor="middle">${esc(r.label || `W${r.week_number}`)}</text>`;
    });
    return `${body}</svg>`;
  }

  function legend(items) { return `<div class="legend">${items.map((x, i) => `<span><i class="dot" style="background:${colors[i % colors.length]}"></i>${esc(x)}</span>`).join("")}</div>`; }
  function card(title, body, extra = "") { return `<section class="card ${extra}"><div class="card-head"><h2>${title}</h2></div>${body}</section>`; }
  function table(rows, columns, sourceTitle) {
    if (!rows?.length) return '<div class="empty">No source-backed rows match the selected filters.</div>';
    return `<div class="table-wrap"><table><thead><tr>${columns.map((c) => `<th class="${c.number ? "number" : ""}">${esc(c.label)}</th>`).join("")}</tr></thead><tbody>${rows.map((row) => `<tr ${drillAttr({ title: row[columns[0].key], subtitle: sourceTitle, data: row, source: sourceTitle })}>${columns.map((c) => `<td class="${c.number ? "number" : ""}">${c.render ? c.render(row[c.key], row) : esc(row[c.key])}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
  }
  function sparkline(rows, key, color = colors[1]) {
    if (!rows?.length || !key) return "";
    const data = rows.slice().sort((a, b) => Number(a.week_number) - Number(b.week_number));
    const width = 92, height = 30, pad = 2;
    const values = data.map((r) => Number(r[key])).filter((v) => Number.isFinite(v));
    if (!values.length) return "";
    const min = Math.min(...values), max = Math.max(...values), span = Math.max(max - min, 1);
    const points = data.map((r, i) => {
      const value = Number(r[key]);
      if (!Number.isFinite(value)) return null;
      const x = pad + i * (width - pad * 2) / Math.max(1, data.length - 1);
      const y = height - pad - (value - min) / span * (height - pad * 2);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    }).filter(Boolean).join(" ");
    return `<svg class="kpi-spark" viewBox="0 0 ${width} ${height}" role="img" aria-label="Source-backed trend"><polyline points="${points}" fill="none" stroke="${color}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
  }
  function kpis(items, variant = "") {
    return `<div class="kpis ${variant}">${items.map((x) => {
      const hasDelta = Number.isFinite(Number(x.delta));
      const trend = hasDelta ? `<div class="kpi-trend"><span class="${x.delta >= 0 ? "positive" : "negative"}">${x.delta >= 0 ? "▲" : "▼"} ${signedPct(x.delta, 1)}</span><span class="kpi-vs">${esc(x.vs || "vs first 13-week window")}</span></div>` : `<div class="kpi-note">${esc(x.note || "Source-backed metric")}</div>`;
      return `<div class="kpi"><div class="kpi-top"><span class="kpi-icon">${x.icon || "●"}</span><span>${esc(x.label)}</span></div><div class="kpi-value">${x.value}</div>${trend}${sparkline(x.spark, x.sparkKey, x.sparkColor)}</div>`;
    }).join("")}</div>`;
  }
  function note(text) { return `<div class="data-note">${esc(text)}</div>`; }

  function observationBands(rows, count = 12) {
    const data = rows.slice().sort((a, b) => Number(a.week_number) - Number(b.week_number));
    const size = Math.max(1, Math.ceil(data.length / count));
    return Array.from({ length: Math.ceil(data.length / size) }, (_, i) => {
      const band = data.slice(i * size, (i + 1) * size);
      const first = band[0], last = band[band.length - 1];
      return {
        label: `W${first.week_number}–W${last.week_number}`,
        panel_net_spend: band.reduce((s, r) => s + (Number(r.panel_net_spend) || 0), 0),
        baskets: band.reduce((s, r) => s + (Number(r.baskets) || 0), 0),
        active_households: Math.max(...band.map((r) => Number(r.active_households) || 0)),
      };
    });
  }

  function departmentSales(rows) {
    return rows.slice().sort((a, b) => Number(b.total_spend || 0) - Number(a.total_spend || 0)).map((r) => ({ department: r.department, spend: r.total_spend, private_share: (Number(r.PRIVATE) || 0) / Math.max(Number(r.total_spend) || 1, 1) }));
  }

  function overview() {
    const d = DATA.overview, weekly = filteredWeeks(d.weekly), k = d.kpis;
    const bands = observationBands(weekly), top = d.top_commodities[0] || {}, leadSegment = d.segments[0] || {};
    const first = DATA.root.window_comparison?.first || {}, last = DATA.root.window_comparison?.last || {};
    const change = (current, baseline) => Number.isFinite(Number(current)) && Number.isFinite(Number(baseline)) && Number(baseline) !== 0 ? Number(current) / Number(baseline) - 1 : null;
    const departments = departmentSales(DATA.category.department_brand);
    const promo = d.promo_states.slice().sort((a, b) => Number(b.panel_sales || 0) - Number(a.panel_sales || 0)).map((r) => ({ ...r, label: label(r.promo_state_group) }));
    const topCategories = d.top_commodities.slice().sort((a, b) => Number(b.spend || 0) - Number(a.spend || 0)).map((r) => ({ ...r, label: r.commodity }));
    const customerBands = bands.map((r) => ({ ...r, label: r.label }));
    const takeaways = [
      `Panel net spend totals ${compactMoney(k.panel_net_spend)} across ${num(k.baskets)} observed baskets.`,
      `${leadSegment.segment || "Leading segment"} contributes ${compactMoney(leadSegment.spend)} across ${num(leadSegment.households)} observed households.`,
      `${top.commodity || "Top observed commodity"} leads the category view at ${compactMoney(top.spend)} panel net spend.`,
      `Promotion-state results are observational associations; the highest observed sales state is ${promo[0]?.label || "—"}.`,
    ];
    return `${kpis([
      { icon: "▥", label: "Total Panel Spend", value: compactMoney(k.panel_net_spend), delta: change(last.panel_net_spend, first.panel_net_spend), spark: weekly, sparkKey: "panel_net_spend" },
      { icon: "▣", label: "Observed Baskets", value: num(k.baskets / 1000, 1) + "K", delta: change(last.baskets, first.baskets), spark: weekly, sparkKey: "baskets" },
      { icon: "♟", label: "Active Panel Households", value: num(k.active_households / 1000, 1) + "K", delta: change(last.active_households_avg, first.active_households_avg), spark: weekly, sparkKey: "active_households" },
      { icon: "↗", label: "Trips per Household", value: num(k.trips_per_household, 2), delta: change(last.trips_per_household_avg, first.trips_per_household_avg), spark: weekly, sparkKey: "trips_per_household" },
      { icon: "▤", label: "Spend per Basket", value: money(k.spend_per_basket, 2), delta: change(last.spend_per_basket_avg, first.spend_per_basket_avg), spark: weekly, sparkKey: "spend_per_basket" },
      { icon: "◆", label: "Private Label Share", value: pct(k.private_label_share), note: "Observed brand mix; no comparable baseline" },
    ], "reference-kpis")}
      <div class="grid overview-row overview-top">${card("Sales Trend", `${legend(["Panel Net Spend", "Observed Baskets"])}<div class="chart">${svgCombo(bands, "panel_net_spend", "baskets", { title: "Panel net spend and baskets by observation window", barColor: colors[0], lineColor: colors[1], barFormat: compactMoney, lineFormat: compact, source: "Mart_Panel_Weekly" })}</div>`, "overview-chart")}${card("Sales by Promotion State", `${legend(promo.map((r) => r.label))}${donut(promo, "panel_sales", "label", "Observed sales")}`)}${card("Sales by Department", table(departments.slice(0, 6), [{ key: "department", label: "Department" }, { key: "spend", label: "Sales", number: true, render: compactMoney }, { key: "private_share", label: "PL share", number: true, render: pct }], "Mart_Brand_Category"))}</div>
      <div class="grid overview-row">${card("Top 10 Product Categories by Sales", `<div class="chart">${svgBar(topCategories.filter((r) => state.commodity === "All" || r.commodity === state.commodity), "spend", "commodity", { title: "Top commodities by panel net spend", format: compactMoney, source: "Mart_Category_Household" })}</div>`)}${card("Customer Segment Contribution", donut(d.segments, "spend", "segment", "Panel spend"))}${card("Top 10 Commodities by Sales", table(d.top_commodities.slice(0, 10), [{ key: "commodity", label: "Commodity" }, { key: "department", label: "Department" }, { key: "spend", label: "Sales", number: true, render: compactMoney }, { key: "penetration", label: "Penetration", number: true, render: pct }], "Mart_Category_Household"))}</div>
      <div class="grid overview-row">${card("Promotion Performance", `${legend(["Promotion sales", "Sales / PSW"])}<div class="chart">${svgCombo(promo, "panel_sales", "sales_per_product_store_week", { title: "Promotion-state sales and sales per product-store-week", barColor: colors[0], lineColor: colors[3], barFormat: compactMoney, lineFormat: money, source: "Mart_Promotion_Category_Week" })}</div>`)}${card("Customer Base & Basket Activity", `${legend(["Active households", "Baskets"])}<div class="chart">${svgCombo(customerBands, "active_households", "baskets", { title: "Active households and baskets by observation window", barColor: colors[0], lineColor: colors[1], source: "Mart_Panel_Weekly" })}</div>`)}${card("Key Takeaways", `<div class="takeaways">${takeaways.map((text, i) => `<div class="insight-row"><div class="insight-badge">${i + 1}</div><div><span>${esc(text)}</span></div></div>`).join("")}</div>${note("Click a bar, donut slice, point or table row to open the source-backed drill-through drawer.")}`, "insight")}</div>`;
  }

  function customer() {
    const d = DATA.customer, weekly = filteredWeeks(d.weekly), k = d.kpis;
    const segments = d.segments.filter((r) => state.segment === "All" || r.segment === state.segment);
    return `${kpis([{ icon: "♟", label: "Active Panel Households", value: num(k.active_households / 1000, 1) + "K", note: "Observed panel only" }, { icon: "▣", label: "Baskets", value: num(k.baskets / 1000, 1) + "K", note: "Distinct observed baskets" }, { icon: "╱", label: "Trips per Active HH", value: num(k.trips_per_household, 2), note: "Observed frequency" }, { icon: "▤", label: "Spend per Active HH", value: money(k.spend_per_household, 0), note: "Net spend / active HH" }, { icon: "▱", label: "Spend per Basket", value: money(k.spend_per_basket, 2), note: "Net spend / basket" }, { icon: "%", label: "Coupon Basket Rate", value: pct(k.coupon_basket_rate), note: "Observed coupon baskets" }])}
      <div class="grid main">${card("Panel Households & Baskets Trend", `${legend(["Active households", "Baskets"])}<div class="chart">${svgLine(weekly, "active_households", { title: "Active panel households by observation week", color: colors[0] })}</div>`)}${card("Segment Household Count", `<div class="chart">${svgBar(segments, "households", "segment", { title: "Household count by segment", format: (v) => num(v / 1000, 1) + "K", source: "Mart_Customer_Segment" })}</div>`)}${card("Segment Performance", table(segments, [{ key: "segment", label: "Segment" }, { key: "households", label: "Households", number: true, render: (v) => num(v) }, { key: "spend", label: "Spend", number: true, render: money }, { key: "spend_per_basket", label: "Spend / basket", number: true, render: (v) => money(v, 2) }], "Mart_Customer_Segment"))}</div>
      <div class="grid two">${card("Household Trajectory by Segment", `${legend(["Growing", "Stable", "Declining", "Insufficient History"])}<div class="chart">${svgBar(d.trajectories.filter((r) => state.segment === "All" || r.segment === state.segment), "households", "trajectory", { title: "Household trajectory counts", format: num, source: "Mart_Customer_Segment" })}</div>`)}${card("High-Value Declining Households", table(d.declining_households, [{ key: "household_key", label: "Household" }, { key: "observed_lifetime_spend", label: "Lifetime spend", number: true, render: money }, { key: "absolute_change", label: "Change", number: true, render: (v) => signed(v, 2) }, { key: "trajectory", label: "Trajectory", render: (v) => `<span class="pill">${esc(v)}</span>` }], "Mart_Household_Summary"))}</div>`;
  }

  function basket() {
    const d = DATA.basket, k = d.kpis, cats = d.top_categories.filter((r) => (state.department === "All" || r.department === state.department) && (state.commodity === "All" || r.commodity === state.commodity));
    return `${kpis([{ icon: "▣", label: "Panel Net Spend", value: compactMoney(k.panel_net_spend), note: "Observed panel total" }, { icon: "♧", label: "Baskets", value: num(k.baskets / 1000, 1) + "K", note: "Distinct baskets" }, { icon: "▤", label: "Spend per Basket", value: money(k.spend_per_basket, 2), note: "Net spend / basket" }, { icon: "♟", label: "Buying Households", value: num(k.buying_households / 1000, 1) + "K", note: "Observed households" }, { icon: "◇", label: "Category Baskets", value: num(k.category_baskets / 1000, 1) + "K", note: "Category-level baskets" }, { icon: "%", label: "Category Penetration", value: pct(k.category_penetration), note: "Households / panel HH" }])}
      <div class="grid main">${card("Panel Net Spend and Baskets Trend", `${legend(["Panel Net Spend"])}<div class="chart">${svgLine(filteredWeeks(d.weekly), "panel_net_spend", { title: "Panel net spend trend", color: colors[0] })}</div>`)}${card("Top Categories by Panel Net Spend", `<div class="chart">${svgBar(cats, "spend", "commodity", { title: "Top categories by panel net spend", format: compactMoney, source: "Mart_Category_Household" })}</div>`)}${card("Category Household Penetration", `<div class="chart">${svgBar(cats.slice().sort((a, b) => (b.penetration || 0) - (a.penetration || 0)), "penetration", "commodity", { title: "Category household penetration", format: pct, source: "Mart_Category_Household" })}</div>`)}</div>
      <div class="grid two">${card(`Category Detail — ${esc(d.selected_category)}`, `${legend(["Selected category spend"])}<div class="chart">${svgLine(d.selected_category_weekly, "spend", { title: `${d.selected_category} weekly category spend`, color: colors[1], source: "Mart_Category_Weekly" })}</div>${note("Click a weekly point or category bar to inspect its source-backed row.")}`)}${card("Cross-Category Pair Affinity", `<div class="chart">${heatmap(d.pair_affinity, d.selected_category)}</div>${note("Attach rate = shared buying households / left-category buying households, derived from Mart_Category_Household.")}`)}</div>`;
  }
  function heatmap(rows) {
    const names = [...new Set(rows.map((r) => r.left))]; if (!names.length) return '<div class="empty">No category pair rows.</div>';
    const s = 48, left = 126, top = 24, width = left + names.length * s + 10, height = top + names.length * s + 10;
    let out = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="category pair affinity"><text x="${left}" y="13">category attach rate</text>`;
    names.forEach((n, i) => { out += `<text x="${left + i * s + 24}" y="21" transform="rotate(-50 ${left + i * s + 24} 21)" font-size="8">${esc(n.slice(0, 11))}</text><text x="${left - 5}" y="${top + i * s + 28}" text-anchor="end" font-size="8">${esc(n.slice(0, 18))}</text>`; });
    rows.forEach((r) => { const x = names.indexOf(r.right), y = names.indexOf(r.left); if (x < 0 || y < 0) return; const intensity = Math.min(1, (r.attach_rate || 0) / .65); out += `<rect class="bar" ${drillAttr({ title: `${r.left} × ${r.right}`, subtitle: "Cross-category pair affinity", data: r, source: "Mart_Category_Household" })} x="${left + x * s}" y="${top + y * s}" width="${s - 3}" height="${s - 3}" rx="4" fill="rgba(40,185,133,${.14 + intensity * .76})"/><text x="${left + x * s + 22}" y="${top + y * s + 28}" text-anchor="middle">${r.attach_rate == null ? "—" : pct(r.attach_rate, 0)}</text>`; });
    return `${out}</svg>`;
  }

  function category() {
    const d = DATA.category, k = d.kpis;
    return `${kpis([{ icon: "◆", label: "Private Label Spend", value: compactMoney(k.private_label_spend), note: "Brand/category mart" }, { icon: "◔", label: "Private Label Share", value: pct(k.private_label_share), note: "Observed spend mix" }, { icon: "♟", label: "Category Households", value: num(k.category_households / 1000, 1) + "K", note: "Household/category grain" }, { icon: "▣", label: "Top Category Spend", value: compactMoney(k.top_category_spend), note: "Highest commodity" }, { icon: "↗", label: "Brand Mix Coverage", value: pct(k.brand_mix_coverage), note: "Commodity rows covered" }, { icon: "▥", label: "Source Brand Rows", value: num(DATA.meta.source_files.brand_category.rows), note: "Mart_Brand_Category" }])}
      <div class="grid main">${card("Private Label vs. National Brand by Department", `${legend(["Private", "National", "Other"])}<div class="chart">${svgBar(d.department_brand, "total_spend", "department", { title: "Department brand mix", format: compactMoney, source: "Mart_Brand_Category" })}</div>`)}${card("Top Commodities by Panel Spend", `<div class="chart">${svgBar(d.top_commodities, "spend", "commodity", { title: "Top commodity spend", format: compactMoney, source: "Mart_Category_Household" })}</div>`)}${card("Brand Mix Composition", donut(d.brand_mix, "spend", "brand_type", "Observed spend"))}</div>
      <div class="grid two">${card("Top Categories by Spend, Penetration and Private Label Share", table(d.detail, [{ key: "commodity", label: "Commodity" }, { key: "department", label: "Department" }, { key: "spend", label: "Spend", number: true, render: compactMoney }, { key: "penetration", label: "Penetration", number: true, render: pct }, { key: "private_label_share", label: "PL share", number: true, render: pct }], "Mart_Category_Household"))}${card(`Panel-Weekly Private Label Spend — ${esc(d.top_commodities[0]?.commodity || "top commodity")}`, `<div class="chart">${svgLine(d.weekly_selected, "private_label_share", { title: "Selected commodity private-label share", color: colors[3], source: "Mart_Category_Weekly" })}</div>${note("The private-label trend is the exact source field at commodity × observation-week grain.")}`)}</div>`;
  }
  function donut(rows, key, labelKey, centerLabel) {
    const total = rows.reduce((s, r) => s + (Number(r[key]) || 0), 0); if (!total) return '<div class="empty">No composition rows.</div>';
    let angle = 0, slices = "", legendRows = "";
    rows.forEach((r, i) => { const pctValue = (Number(r[key]) || 0) / total; const start = angle * 360, end = (angle + pctValue) * 360; slices += `<div class="donut-slice" style="--start:${start}deg;--end:${end}deg;--slice:${colors[i % colors.length]}" ${drillAttr({ title: r[labelKey], subtitle: centerLabel, data: r, source: "Mart_Brand_Category" })}></div>`; legendRows += `<span><i class="dot" style="background:${colors[i % colors.length]}"></i>${esc(r[labelKey])} ${pct(pctValue)}</span>`; angle += pctValue; });
    return `<div class="donut-wrap"><div class="donut">${slices}<div class="donut-hole"><b>${compactMoney(total)}</b><small>${esc(centerLabel)}</small></div></div><div class="donut-legend">${legendRows}</div></div>`;
  }

  function promotion() {
    const d = DATA.promotion, k = d.kpis, states = d.states.filter((r) => state.promo === "All" || r.promo_state_group === state.promo);
    return `${kpis([{ icon: "◆", label: "Promoted-State Sales Share", value: pct(k.promoted_sales_share), note: "Promotion state association" }, { icon: "↗", label: "Product-Store-Weeks", value: compact(k.product_store_weeks), note: "Observed activity rows" }, { icon: "▣", label: "Panel Sales", value: compactMoney(k.panel_sales), note: "Promotion mart" }, { icon: "▥", label: "Avg Sales / Product-Store-Week", value: money(k.sales_per_product_store_week, 2), note: "Descriptive average" }, { icon: "◌", label: "Promotion States", value: num(d.states.length), note: "Source states" }, { icon: "!", label: "Interpretation", value: "ASSOCIATION", note: "No causal lift claim" }])}
      <div class="grid main">${card("Sales and Product-Store-Weeks by Promotion State", `<div class="chart">${svgBar(states, "panel_sales", "promo_state_group", { title: "Panel sales by promotion state", format: compactMoney, source: "Mart_Promotion_Category_Week" })}</div>`)}${card("Promotion-State Activity Over Time", `<div class="chart">${svgLine(d.weekly.filter((r) => state.promo === "All" || r.promo_state_group === state.promo), "product_store_weeks", { title: "Product-store-week activity", color: colors[1], source: "Mart_Promotion_Category_Week" })}</div>`)}${card("Promotion State Summary", table(states, [{ key: "promo_state_group", label: "State" }, { key: "product_store_weeks", label: "Product-store-weeks", number: true, render: compact }, { key: "panel_sales", label: "Panel sales", number: true, render: compactMoney }, { key: "sales_per_product_store_week", label: "Sales / PSW", number: true, render: (v) => money(v, 2) }], "Mart_Promotion_Category_Week"))}</div>
      <div class="grid two">${card("Promotion Dependency by Department", `<div class="chart">${svgBar(departmentPromo(d.departments), "dependency", "department", { title: "Non-none product-store-week share", format: pct, source: "Mart_Promotion_Category_Week" })}</div>`)}${card("Observational Guardrails", `<div class="callout"><b>Important:</b> Promotion-state results are descriptive association from observed panel sales and preserved product-store-week activity. Promotion assignment is not random, and this export has no causal holdout or margin economics.</div>${note("Click a state, department bar or weekly point for the exact supporting aggregate row.")}`, "insight")}</div>`;
  }
  function compact(value) { return value == null ? "—" : Math.abs(value) >= 1e6 ? `${(value / 1e6).toFixed(2)}M` : Math.abs(value) >= 1e3 ? `${(value / 1e3).toFixed(1)}K` : num(value); }
  function departmentPromo(rows) { const map = {}; rows.forEach((r) => { map[r.department] ||= { department: r.department, total: 0, promoted: 0 }; map[r.department].total += Number(r.product_store_weeks) || 0; if (r.promo_state_group !== "none") map[r.department].promoted += Number(r.product_store_weeks) || 0; }); return Object.values(map).map((r) => ({ department: r.department, dependency: r.total ? r.promoted / r.total : null })).sort((a, b) => (b.dependency || 0) - (a.dependency || 0)); }

  function campaign() {
    const d = DATA.campaign, k = d.kpis, types = d.types.filter((r) => state.campaignType === "All" || r.campaign_type === state.campaignType);
    return `${kpis([{ icon: "♟", label: "Campaign Recipients", value: compact(k.recipients), note: "Recipient households" }, { icon: "▣", label: "Campaign Redeemers", value: compact(k.redeemers), note: "Redeemed coupon flag" }, { icon: "%", label: "Campaign Redemption Rate", value: pct(k.redemption_rate), note: "Redeemers / recipients" }, { icon: "▱", label: "Observable Post-28d Rows", value: compact(k.observable_post_28d_rows), note: "Censoring retained" }, { icon: "◇", label: "Campaigns", value: num(k.campaigns), note: "Campaign summary rows" }, { icon: "!", label: "Data Basis", value: "OBSERVED", note: "No causal lift claim" }])}
      <div class="grid main">${card("Campaign Response Funnel", `<div class="chart">${svgBar(d.funnel, "value", "stage", { title: "Campaign response funnel", format: compact, source: "Mart_Campaign_Summary" })}</div>`)}${card("Redemption Rate by Campaign Type", `<div class="chart">${svgBar(types, "redemption_rate", "campaign_type", { title: "Redemption rate by campaign type", format: pct, source: "Mart_Campaign_Summary" })}</div>`)}${card("Recipients and Redeemers by Customer Segment", table(d.segments, [{ key: "segment", label: "Segment" }, { key: "recipients", label: "Recipients", number: true, render: compact }, { key: "redeemers", label: "Redeemers", number: true, render: compact }, { key: "redemption_rate", label: "Rate", number: true, render: pct }], "Mart_Campaign_Household"))}</div>
      <div class="grid two">${card("Campaign Performance Detail", table(d.campaigns, [{ key: "campaign_id", label: "Campaign" }, { key: "campaign_type", label: "Type" }, { key: "campaign_recipients", label: "Recipients", number: true, render: compact }, { key: "campaign_redeemers", label: "Redeemers", number: true, render: compact }, { key: "campaign_redemption_rate", label: "Rate", number: true, render: pct }, { key: "post_28d_observable_rows", label: "Post-28d rows", number: true, render: compact }], "Mart_Campaign_Summary"))}${card("Key Insight", `<div class="callout"><b>${d.weak_campaign?.[0] ? `Campaign ${d.weak_campaign[0].campaign_id} (${d.weak_campaign[0].campaign_type})` : "Weakest observed campaign"}</b><br/>Lowest redemption among campaigns with at least 50 recipients: ${d.weak_campaign?.[0] ? `${num(d.weak_campaign[0].campaign_redeemers)}/${num(d.weak_campaign[0].campaign_recipients)} = ${pct(d.weak_campaign[0].campaign_redemption_rate)}` : "—"}.<br/>Post-28d observable rows remain visible for interpretation.</div>${note("Funnel stages are limited to fields present in the campaign marts. Related-product purchase was not manufactured because it is not present in the supplied export.")}`, "insight")}</div>`;
  }

  function root() {
    const d = DATA.root, k = d.kpis, comp = d.window_comparison;
    return `${kpis([{ icon: "▥", label: "First 13-Week Panel Net Spend", value: compactMoney(k.first_13_week_spend), note: "Computed from panel mart" }, { icon: "▥", label: "Last 13-Week Panel Net Spend", value: compactMoney(k.last_13_week_spend), note: "Computed from panel mart" }, { icon: "↗", label: "13-Week Spend Movement", value: signedPct(k.spend_change_percent), note: "Accounting movement" }, { icon: "♟", label: "Largest Driver Movement", value: signedPct(comp.drivers.slice().sort((a, b) => Math.abs(b.percent || 0) - Math.abs(a.percent || 0))[0]?.percent), note: "Driver tree, not causality" }, { icon: "✓", label: "Blocking QA Gate", value: k.qa_gate, note: "Project run status" }, { icon: "▤", label: "Source Files Verified", value: num(k.source_files_verified), note: "Drive-curated marts" }])}
      <div class="grid two">${card("Panel Net Spend — first vs last 13-week windows", `<div class="chart">${svgBar([{ label: "First 13 weeks", spend: comp.first.panel_net_spend }, { label: "Last 13 weeks", spend: comp.last.panel_net_spend }], "spend", "label", { title: "First vs last observation windows", format: compactMoney, horizontal: false, source: "Mart_Panel_Weekly" })}</div><div class="callout"><b>Spend change ${signedPct(comp.spend_change.percent)}</b><br/>${money(comp.spend_change.absolute)} absolute movement between the two observed windows.</div>`)}${card("Verified Root-Cause Signals", d.signals.map((s) => `<div class="insight-row" ${drillAttr({ title: `Case ${s.case}`, subtitle: s.title, data: s.evidence, source: "Project root-cause evidence" })}><div class="insight-badge">${s.case}</div><div><b>${esc(s.title)}</b><span>${esc(s.finding)}</span></div></div>`).join(""))}${card("Data Foundation", `<div class="detail-grid">${Object.entries(DATA.meta.source_files).slice(0, 4).map(([name, info]) => `<div class="detail-cell"><small>${esc(label(name))}</small><b>${num(info.rows)}</b></div>`).join("")}</div>${note("All values are generated from current Drive-curated parquet marts. Raw data is not committed to the website.")}`)}</div>
      <div class="grid two">${card("Decision Layer — what the dashboard should drive", `<div class="decision-list">${d.decisions.map((x) => `<div class="decision" ${drillAttr({ title: x.id, subtitle: x.title, data: x, source: x.source })}><strong>${x.id}</strong><span>${esc(x.title)}</span><em>›</em></div>`).join("")}</div>`)}${card("Interpretation Guardrails", d.guardrails.map((g, i) => `<div class="insight-row"><div class="insight-badge">${i + 1}</div><div><span>${esc(g)}</span></div></div>`).join(""), "insight")}</div>`;
  }

  function renderFilters() {
    const allRows = [...DATA.overview.top_commodities, ...DATA.basket.category_detail];
    const segments = group(DATA.customer.segments, "segment"), departments = group(allRows, "department"), commodities = group(allRows, "commodity"), promos = group(DATA.promotion.states, "promo_state_group"), types = group(DATA.campaign.types, "campaign_type");
    const select = (key, title, options) => `<div class="filter"><label>${title}</label><select data-filter="${key}"><option>All</option>${options.map((v) => `<option ${state[key] === v ? "selected" : ""}>${esc(v)}</option>`).join("")}</select></div>`;
    if (state.page === "overview") return `<div class="filters overview-filters"><div class="filter overview-window"><label>Observation window</label><div class="week-range"><input type="number" min="${DATA.meta.observation_index.min_week}" max="${DATA.meta.observation_index.max_week}" value="${state.minWeek}" data-filter="minWeek" aria-label="Minimum observation week"/><input type="number" min="${DATA.meta.observation_index.min_week}" max="${DATA.meta.observation_index.max_week}" value="${state.maxWeek}" data-filter="maxWeek" aria-label="Maximum observation week"/></div></div>${select("department", "Department", departments)}${select("promo", "Promotion state", promos)}${select("segment", "Customer segment", segments)}</div>`;
    return `<div class="filters"><div class="filter"><label>Observation window</label><div class="week-range"><input type="number" min="${DATA.meta.observation_index.min_week}" max="${DATA.meta.observation_index.max_week}" value="${state.minWeek}" data-filter="minWeek" aria-label="Minimum observation week"/><input type="number" min="${DATA.meta.observation_index.min_week}" max="${DATA.meta.observation_index.max_week}" value="${state.maxWeek}" data-filter="maxWeek" aria-label="Maximum observation week"/></div></div>${select("segment", "Customer segment", segments)}${select("department", "Department", departments)}${select("commodity", "Commodity", commodities)}${select("promo", "Promotion state", promos)}${select("campaignType", "Campaign type", types)}<button class="reset" id="resetFilters">Reset</button></div>`;
  }

  function render() {
    drills.clear();
    const page = pages[state.page], content = { overview, customer, basket, category, promotion, campaign, root }[state.page]();
    document.getElementById("app").innerHTML = `<div class="app"><aside class="sidebar"><div class="brand"><div class="brand-mark">🛒</div><div class="brand-copy"><strong>RETAIL CUSTOMER</strong><span>&amp; Commercial Intelligence</span></div></div><nav class="nav">${Object.entries(pages).map(([key, p]) => `<button class="${key === state.page ? "active" : ""}" data-page="${key}"><span class="nav-icon">${icons[key]}</span><span class="nav-label">${p.label}</span></button>`).join("")}</nav><div class="sidebar-foot"><b>Retail Customer<br/>&amp; Commercial Intelligence</b><span>v1.0 | Powered by Data</span></div></aside><main class="content"><header class="topbar"><div class="title-block"><div class="eyebrow">Source-backed retail intelligence</div><h1>${page.title}</h1><p class="subtitle">${page.subtitle}</p></div>${renderFilters()}<div class="slogan">Understand<br/>Customers.<br/>Grow Smarter.</div></header>${content}<div class="footer-line">Source: Drive-curated retail marts · ${esc(DATA.meta.observation_index.label)} · click a chart mark or table row for drill-down · observational association only.</div></main></div><div class="drawer-backdrop" id="drawerBackdrop"><aside class="drawer" role="dialog" aria-modal="true" aria-labelledby="drawerTitle"><button class="drawer-close" id="drawerClose" aria-label="Close">×</button><div class="eyebrow">Power BI-style drill-through</div><h2 id="drawerTitle">Detail</h2><p class="drawer-subtitle" id="drawerSubtitle"></p><div id="drawerBody"></div></aside></div>`;
    bindEvents();
  }

  function bindEvents() {
    document.querySelectorAll("[data-page]").forEach((button) => button.addEventListener("click", () => { state.page = button.dataset.page; render(); }));
    document.querySelectorAll("[data-filter]").forEach((control) => control.addEventListener("change", () => { state[control.dataset.filter] = control.type === "number" ? Math.max(Number(control.min), Math.min(Number(control.max), Number(control.value))) : control.value; render(); }));
    document.getElementById("resetFilters")?.addEventListener("click", () => { state.segment = "All"; state.department = "All"; state.commodity = "All"; state.promo = "All"; state.campaignType = "All"; state.minWeek = DATA.meta.observation_index.min_week; state.maxWeek = DATA.meta.observation_index.max_week; render(); });
    document.querySelectorAll("[data-drill-id]").forEach((el) => el.addEventListener("click", () => openDrawer(drills.get(el.dataset.drillId))));
    document.getElementById("drawerClose")?.addEventListener("click", closeDrawer);
    document.getElementById("drawerBackdrop")?.addEventListener("click", (event) => { if (event.target.id === "drawerBackdrop") closeDrawer(); });
    document.addEventListener("keydown", keyClose, { once: true });
  }
  function keyClose(event) { if (event.key === "Escape") closeDrawer(); }
  function openDrawer(payload) {
    if (!payload) return;
    document.getElementById("drawerTitle").textContent = payload.title || "Selected detail";
    document.getElementById("drawerSubtitle").textContent = payload.subtitle || "Source-backed selection";
    const row = payload.data || {};
    const cells = Object.entries(row).filter(([, value]) => value !== null && value !== undefined && value !== "").slice(0, 16).map(([key, value]) => `<div class="detail-cell"><small>${esc(label(key))}</small><b>${typeof value === "number" ? num(value, Math.abs(value) < 1 ? 4 : 2) : esc(value)}</b></div>`).join("");
    document.getElementById("drawerBody").innerHTML = `<div class="detail-grid">${cells || '<div class="empty">No row fields available.</div>'}</div><div class="source-chip"><b>Evidence source</b><br/>${esc(payload.source || "Drive-curated mart")}.<br/>This is a drill-through view of the selected source-backed row; it does not add a synthetic value.</div>`;
    document.getElementById("drawerBackdrop").classList.add("open");
  }
  function closeDrawer() { document.getElementById("drawerBackdrop")?.classList.remove("open"); }
  render();
})();

