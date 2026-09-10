/* ExpenseFlow dashboard — talks to the Flask JSON API under /api/. */

const CATEGORY_COLORS = {
  Food: "#f0b429", Transport: "#38bdf8", Shopping: "#ec4899",
  Bills: "#6366f1", Entertainment: "#a855f7", Health: "#2dd4bf",
  Education: "#f472b6", Groceries: "#84cc16", Rent: "#7c3aed", Other: "#94a3b8",
};

const money = (v) => "₹" + Number(v).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

let editingId = null;
let pieChart = null;
let barChart = null;

// ------------------------------------------------------------ navigation
function switchView(name) {
  document.querySelectorAll(".view").forEach(v => v.classList.remove("active"));
  document.querySelectorAll(".nav-item").forEach(n => n.classList.toggle("active", n.dataset.view === name));
  document.getElementById("view-" + name).classList.add("active");

  if (name === "dashboard") loadDashboard();
  if (name === "all") loadAllExpenses();
  if (name === "reports") loadReports();
  if (name === "add" && editingId === null) clearForm();
}

document.querySelectorAll(".nav-item").forEach(el => {
  el.addEventListener("click", () => switchView(el.dataset.view));
});
document.querySelectorAll("[data-goto]").forEach(el => {
  el.addEventListener("click", () => switchView(el.dataset.goto));
});

// ----------------------------------------------------------------- toast
let toastTimer = null;
function toast(msg, isError = false) {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.classList.toggle("err", isError);
  el.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove("show"), 3000);
}

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (res.status === 401) {
    window.location.href = "/login";
    return null;
  }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || "Something went wrong.");
  return data;
}

// ---------------------------------------------------------- count-up fx
function countUp(el, target, isMoney) {
  const start = 0;
  const duration = 700;
  const startTime = performance.now();
  function tick(now) {
    const p = Math.min(1, (now - startTime) / duration);
    const eased = 1 - Math.pow(1 - p, 3);
    const value = start + (target - start) * eased;
    el.textContent = isMoney ? money(value) : Math.round(value).toLocaleString("en-IN");
    if (p < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

// --------------------------------------------------------------- catrow
function catDot(category) {
  const color = CATEGORY_COLORS[category] || "#6c7a70";
  return `<span class="cat-dot" style="--dot-color:${color}">${category}</span>`;
}

// ------------------------------------------------------------- dashboard
async function loadDashboard() {
  const todayLabel = document.getElementById("today-label");
  todayLabel.textContent = new Date().toLocaleDateString("en-IN", { weekday: "long", day: "numeric", month: "long" });

  try {
    const s = await api("/api/summary");
    if (!s) return;
    countUp(document.querySelector('[data-stat="total_today"]'), s.total_today, true);
    countUp(document.querySelector('[data-stat="total_month"]'), s.total_month, true);
    countUp(document.querySelector('[data-stat="total_all"]'), s.total_all, true);
    countUp(document.querySelector('[data-stat="count_all"]'), s.count_all, false);

    const rows = await api("/api/expenses");
    const body = document.getElementById("recent-body");
    const empty = document.getElementById("recent-empty");
    body.innerHTML = "";
    const recent = rows.slice(0, 8);
    empty.style.display = recent.length ? "none" : "block";
    recent.forEach(r => {
      const tr = document.createElement("tr");
      tr.className = "row-hover";
      tr.innerHTML = `
        <td>${formatDate(r.date)}</td>
        <td>${escapeHtml(r.title)}</td>
        <td>${catDot(r.category)}</td>
        <td class="amount-cell">${money(r.amount)}</td>`;
      body.appendChild(tr);
    });
  } catch (e) {
    toast(e.message, true);
  }
}

function formatDate(iso) {
  const d = new Date(iso + "T00:00:00");
  return d.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
}
function escapeHtml(s) {
  const div = document.createElement("div");
  div.textContent = s;
  return div.innerHTML;
}

// -------------------------------------------------------------- add form
const form = document.getElementById("expense-form");
document.getElementById("f-date").value = new Date().toISOString().slice(0, 10);

document.getElementById("form-clear-btn").addEventListener("click", clearForm);

function clearForm() {
  editingId = null;
  document.getElementById("form-heading").textContent = "Add expense";
  document.getElementById("form-submit-btn").textContent = "Save expense";
  form.reset();
  document.getElementById("f-date").value = new Date().toISOString().slice(0, 10);
}

function loadIntoForm(expense) {
  editingId = expense.id;
  document.getElementById("form-heading").textContent = "Edit expense";
  document.getElementById("form-submit-btn").textContent = "Update expense";
  document.getElementById("f-title").value = expense.title;
  document.getElementById("f-amount").value = expense.amount;
  document.getElementById("f-category").value = expense.category;
  document.getElementById("f-date").value = expense.date;
  document.getElementById("f-note").value = expense.note;
  switchView("add");
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const payload = {
    title: document.getElementById("f-title").value.trim(),
    amount: document.getElementById("f-amount").value,
    category: document.getElementById("f-category").value,
    date: document.getElementById("f-date").value,
    note: document.getElementById("f-note").value.trim(),
  };
  try {
    if (editingId === null) {
      await api("/api/expenses", { method: "POST", body: JSON.stringify(payload) });
      toast("Expense added ✓");
    } else {
      await api(`/api/expenses/${editingId}`, { method: "PUT", body: JSON.stringify(payload) });
      toast("Expense updated ✓");
    }
    clearForm();
    switchView("all");
  } catch (err) {
    toast(err.message, true);
  }
});

// ---------------------------------------------------------- all expenses
document.getElementById("filter-apply-btn").addEventListener("click", loadAllExpenses);
document.getElementById("filter-reset-btn").addEventListener("click", () => {
  document.getElementById("filter-search").value = "";
  document.getElementById("filter-category").value = "All";
  document.getElementById("filter-from").value = "";
  document.getElementById("filter-to").value = "";
  loadAllExpenses();
});

async function loadAllExpenses() {
  const params = new URLSearchParams();
  const search = document.getElementById("filter-search").value.trim();
  const category = document.getElementById("filter-category").value;
  const from = document.getElementById("filter-from").value;
  const to = document.getElementById("filter-to").value;
  if (search) params.set("search", search);
  if (category !== "All") params.set("category", category);
  if (from) params.set("date_from", from);
  if (to) params.set("date_to", to);

  try {
    const rows = await api("/api/expenses?" + params.toString());
    const body = document.getElementById("all-body");
    const empty = document.getElementById("all-empty");
    body.innerHTML = "";
    empty.style.display = rows.length ? "none" : "block";
    rows.forEach(r => {
      const tr = document.createElement("tr");
      tr.className = "row-hover";
      tr.innerHTML = `
        <td>${formatDate(r.date)}</td>
        <td>${escapeHtml(r.title)}</td>
        <td>${catDot(r.category)}</td>
        <td class="amount-cell">${money(r.amount)}</td>
        <td style="color:var(--text-muted); font-size:13px;">${escapeHtml(r.note || "—")}</td>
        <td>
          <div class="row-actions">
            <button class="icon-btn" title="Edit" data-edit="${r.id}">✎</button>
            <button class="icon-btn danger" title="Delete" data-del="${r.id}">🗑</button>
          </div>
        </td>`;
      body.appendChild(tr);
    });

    body.querySelectorAll("[data-edit]").forEach(btn => {
      btn.addEventListener("click", () => {
        const r = rows.find(x => x.id === Number(btn.dataset.edit));
        if (r) loadIntoForm(r);
      });
    });
    body.querySelectorAll("[data-del]").forEach(btn => {
      btn.addEventListener("click", async () => {
        const r = rows.find(x => x.id === Number(btn.dataset.del));
        if (!r) return;
        if (!confirm(`Delete "${r.title}" (${money(r.amount)})?`)) return;
        try {
          await api(`/api/expenses/${r.id}`, { method: "DELETE" });
          toast("Expense deleted ✓");
          loadAllExpenses();
        } catch (e) {
          toast(e.message, true);
        }
      });
    });
  } catch (e) {
    toast(e.message, true);
  }
}

// -------------------------------------------------------------- reports
async function loadReports() {
  try {
    const breakdown = await api("/api/categories");
    const pieCanvas = document.getElementById("pie-chart");
    const pieEmpty = document.getElementById("pie-empty");
    if (pieChart) pieChart.destroy();
    if (breakdown.length) {
      pieCanvas.style.display = "block";
      pieEmpty.style.display = "none";
      pieChart = new Chart(pieCanvas, {
        type: "doughnut",
        data: {
          labels: breakdown.map(b => b.category),
          datasets: [{
            data: breakdown.map(b => b.total),
            backgroundColor: breakdown.map(b => CATEGORY_COLORS[b.category] || "#6c7a70"),
            borderWidth: 2, borderColor: "#ffffff",
          }],
        },
        options: {
          plugins: { legend: { position: "bottom", labels: { font: { family: "Inter" }, boxWidth: 10 } } },
        },
      });
    } else {
      pieCanvas.style.display = "none";
      pieEmpty.style.display = "block";
    }

    const trend = await api("/api/trend");
    const barCanvas = document.getElementById("bar-chart");
    const barEmpty = document.getElementById("bar-empty");
    if (barChart) barChart.destroy();
    if (trend.length) {
      barCanvas.style.display = "block";
      barEmpty.style.display = "none";
      barChart = new Chart(barCanvas, {
        type: "bar",
        data: {
          labels: trend.map(t => t.label),
          datasets: [{ data: trend.map(t => t.total), backgroundColor: "#7c3aed", borderRadius: 6 }],
        },
        options: {
          plugins: { legend: { display: false } },
          scales: { y: { beginAtZero: true, ticks: { font: { family: "Inter" } } },
                    x: { ticks: { font: { family: "Inter" } } } },
        },
      });
    } else {
      barCanvas.style.display = "none";
      barEmpty.style.display = "block";
    }
  } catch (e) {
    toast(e.message, true);
  }
}

// ------------------------------------------------------------------ init
loadDashboard();
