// Front end for the Card Validation API. Plain JavaScript, no build step.
// Every check calls the real API; nothing here decides validity on its own.

const $ = (id) => document.getElementById(id);
const els = {
  input: $("number"), card: $("card"), cardNumber: $("card-number"),
  cardBrand: $("card-brand"), cardVerdict: $("card-verdict"), result: $("result"),
  luhnDigits: $("luhn-digits"), luhnTotal: $("luhn-total"), wake: $("wake"),
  form: $("pay-form"), amount: $("amount"), currency: $("currency"),
  payBtn: $("pay-btn"), payResult: $("pay-result"), txList: $("tx-list"),
};

const BRAND_NAMES = { visa: "Visa", mastercard: "Mastercard", amex: "American Express", discover: "Discover" };
const STATUS_TEXT = {
  approved: "Approved",
  flagged: "Flagged for review",
  declined: "Declined",
};
const REASON_SHORT = { POSSIBLE_DUPLICATE: "possible duplicate", OVER_LIMIT: "over the limit" };
const REASON_TEXT = {
  POSSIBLE_DUPLICATE: "same card, amount and currency in the last 60 seconds",
  OVER_LIMIT: "over the 10,000 mock limit",
};

// --- API calls, with a notice if the free server is waking up ------------

async function api(path, body) {
  const slow = setTimeout(() => (els.wake.hidden = false), 2500);
  try {
    const res = await fetch(path, body
      ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }
      : {});
    const data = await res.json().catch(() => ({}));
    return { status: res.status, data };
  } finally {
    clearTimeout(slow);
    els.wake.hidden = true;
  }
}

// --- Card preview ---------------------------------------------------------

const digitsOf = (s) => s.replace(/[\s-]/g, "");

function groupDigits(d) {
  // Amex is grouped 4-6-5, everything else in fours.
  if (/^3[47]/.test(d)) return [d.slice(0, 4), d.slice(4, 10), d.slice(10, 15)].filter(Boolean).join(" ");
  return d.replace(/(.{4})/g, "$1 ").trim();
}

function formatInput() {
  const raw = els.input.value;
  // Keep unexpected characters so the server can report them, but tidy pure digits.
  if (/^[\d\s-]*$/.test(raw)) {
    const pos = els.input.selectionStart;
    const before = raw.length;
    els.input.value = groupDigits(digitsOf(raw).slice(0, 19));
    const shift = els.input.value.length - before;
    els.input.setSelectionRange(pos + shift, pos + shift);
  }
}

function renderCard(digits, result) {
  const shown = digits ? groupDigits(digits.replace(/\D/g, "").padEnd(16, "•").slice(0, 19)) : "•••• •••• •••• ••••";
  els.cardNumber.textContent = shown;
  els.card.dataset.brand = result?.brand || "";
  els.cardBrand.textContent = result?.brand ? BRAND_NAMES[result.brand] : "Card";
  const state = !digits ? "empty" : result ? (result.valid ? "valid" : "invalid") : "typing";
  if (els.card.dataset.state !== state) {
    els.card.dataset.state = "";
    void els.card.offsetWidth; // restart the nudge animation
    els.card.dataset.state = state;
  }
  els.cardVerdict.textContent = state === "valid" ? "Valid" : state === "invalid" ? "Not valid" : "";
}

// --- Luhn walkthrough -----------------------------------------------------

function renderLuhn(digits) {
  els.luhnDigits.replaceChildren();
  if (!/^\d{2,19}$/.test(digits)) {
    els.luhnTotal.textContent = "Enter at least two digits to see the steps.";
    return;
  }
  let total = 0;
  const n = digits.length;
  [...digits].forEach((ch, i) => {
    const fromRight = n - 1 - i;
    const doubled = fromRight % 2 === 1;
    let val = Number(ch);
    if (doubled) { val *= 2; if (val > 9) val -= 9; }
    total += val;
    const li = document.createElement("li");
    if (doubled) li.className = "doubled";
    li.innerHTML = `<span class="orig"></span><span class="val"></span>`;
    li.firstChild.textContent = doubled ? `${ch}×2` : ch;
    li.lastChild.textContent = val;
    li.setAttribute("aria-label", doubled ? `${ch} doubled gives ${val}` : `${ch} stays ${val}`);
    els.luhnDigits.append(li);
  });
  const ok = total % 10 === 0;
  els.luhnTotal.textContent = ok
    ? `Total ${total}. That is a multiple of 10, so the checksum passes.`
    : `Total ${total}. That is not a multiple of 10 (remainder ${total % 10}), so the checksum fails.`;
}

// --- Validation result ----------------------------------------------------

function renderResult(res) {
  els.result.replaceChildren();
  if (!res) {
    els.result.innerHTML = `<p class="result-empty">Results appear here.</p>`;
    return;
  }
  const head = document.createElement("p");
  head.className = `verdict ${res.valid ? "ok" : "bad"}`;
  head.innerHTML = `<span class="dot"></span><span></span>`;
  head.lastChild.textContent = res.valid ? "Valid card number" : "Not a valid card number";

  const facts = document.createElement("p");
  facts.className = "facts";
  const parts = [];
  if (res.brand) parts.push(BRAND_NAMES[res.brand]);
  parts.push(res.luhn_valid ? "Luhn check passed" : "Luhn check failed");
  if (res.masked_number) parts.push(`stored as ${res.masked_number}`);
  facts.textContent = parts.join(", ");

  els.result.append(head, facts);
  if (res.errors.length) {
    const ul = document.createElement("ul");
    ul.className = "errors";
    for (const e of res.errors) {
      const li = document.createElement("li");
      const code = document.createElement("code");
      code.textContent = e.code;
      li.append(code, e.message);
      ul.append(li);
    }
    els.result.append(ul);
  }
}

let timer, latest = 0;
function onNumberChange() {
  formatInput();
  const value = els.input.value;
  const digits = digitsOf(value);
  renderCard(digits, null);
  renderLuhn(digits);
  clearTimeout(timer);
  if (!value.trim()) { renderResult(null); return; }
  timer = setTimeout(async () => {
    const id = ++latest;
    const { status, data } = await api("/validate", { number: value });
    if (id !== latest) return; // a newer keystroke already won
    if (status === 200) { renderResult(data); renderCard(digits, data); }
  }, 250);
}

els.input.addEventListener("input", onNumberChange);
document.querySelectorAll(".samples button").forEach((b) =>
  b.addEventListener("click", () => { els.input.value = b.dataset.num; onNumberChange(); els.input.focus(); })
);

// --- Payments -------------------------------------------------------------

function setPayResult(kind, text) {
  els.payResult.className = `pay-result ${kind}`;
  els.payResult.textContent = text;
}

els.form.addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const card = els.input.value.trim();
  if (!card) { setPayResult("bad", "Enter a card number at the top first."); els.input.focus(); return; }
  const amount = els.amount.value.trim();
  if (!/^\d+(\.\d{1,2})?$/.test(amount) || Number(amount) <= 0) {
    setPayResult("bad", "Enter an amount greater than 0, with at most two decimals, like 25.00.");
    els.amount.focus();
    return;
  }
  els.payBtn.disabled = true;
  els.payBtn.textContent = "Sending…";
  try {
    const { status, data } = await api("/transactions", { card_number: card, amount, currency: els.currency.value });
    if (status === 201) {
      const kind = data.status === "approved" ? "ok" : data.status === "flagged" ? "warn" : "bad";
      const why = data.reason ? `: ${REASON_TEXT[data.reason] || data.reason}` : "";
      setPayResult(kind, `${STATUS_TEXT[data.status]}${why}. ${data.amount} ${data.currency} on ${data.masked_card}.`);
      await loadHistory(data.id);
    } else if (status === 422 && data.detail?.errors) {
      setPayResult("bad", `Payment not sent. ${data.detail.errors.map((e) => e.message).join(" ")}`);
    } else {
      setPayResult("bad", "Payment not sent. Check the amount and card number, then try again.");
    }
  } catch {
    setPayResult("bad", "Couldn't reach the server. Check your connection and try again.");
  } finally {
    els.payBtn.disabled = false;
    els.payBtn.textContent = "Send payment";
  }
});

// --- History --------------------------------------------------------------

let filter = "";
const timeFmt = new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" });

async function loadHistory(highlightId) {
  const q = new URLSearchParams({ limit: "8" });
  if (filter) q.set("status", filter);
  const { status, data } = await api(`/transactions?${q}`);
  els.txList.replaceChildren();
  if (status !== 200) {
    els.txList.innerHTML = `<li class="tx-empty">Couldn't load payments. Refresh the page to try again.</li>`;
    return;
  }
  if (!data.length) {
    const li = document.createElement("li");
    li.className = "tx-empty";
    li.textContent = filter ? `No ${filter} payments yet.` : "No payments yet. Send one to see it here.";
    els.txList.append(li);
    return;
  }
  for (const t of data) {
    const li = document.createElement("li");
    if (t.id === highlightId) li.className = "new";
    li.innerHTML = `<span class="tx-card"></span><span class="tx-amount"></span><span class="tx-meta"></span><span class="badge"></span>`;
    const [card, amt, meta, badge] = li.children;
    const digits = document.createElement("span");
    digits.className = "digits";
    digits.textContent = t.masked_card;
    card.append(BRAND_NAMES[t.brand], digits);
    amt.textContent = `${t.amount} ${t.currency}`;
    meta.textContent = timeFmt.format(new Date(t.created_at)) + (t.reason ? `, ${REASON_SHORT[t.reason] || t.reason}` : "");
    badge.className = `badge ${t.status}`;
    badge.textContent = STATUS_TEXT[t.status].split(" ")[0];
    els.txList.append(li);
  }
}

document.querySelectorAll(".filter button").forEach((b) =>
  b.addEventListener("click", () => {
    filter = b.dataset.status;
    document.querySelectorAll(".filter button").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
    loadHistory();
  })
);

renderLuhn("");
loadHistory();
