/**
 * static/js/dashboard.js
 * Client-side interactivity for the Bank Ledger & Fraud Screening UI
 */

/* ── Live Clock ──────────────────────────────────────────────────────────── */
function updateClock() {
  const el = document.getElementById('live-clock');
  if (!el) return;
  const now = new Date();
  el.textContent = now.toLocaleTimeString('en-IN', {
    hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false
  });
}
setInterval(updateClock, 1000);
updateClock();

/* ── Auto-dismiss alerts ─────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.alert').forEach(el => {
    // Auto-close after 6 seconds
    setTimeout(() => dismissAlert(el), 6000);

    // Manual close button
    const btn = el.querySelector('.alert-close');
    if (btn) btn.addEventListener('click', () => dismissAlert(el));
  });
});

function dismissAlert(el) {
  if (!el) return;
  el.style.animation = 'fadeOut 0.3s ease forwards';
  setTimeout(() => el.remove(), 300);
}

/* ── Mobile sidebar toggle ───────────────────────────────────────────────── */
const sidebarToggle = document.getElementById('sidebar-toggle');
const sidebar       = document.getElementById('sidebar');
if (sidebarToggle && sidebar) {
  sidebarToggle.addEventListener('click', () => {
    sidebar.classList.toggle('open');
  });
  // Close on outside click
  document.addEventListener('click', (e) => {
    if (!sidebar.contains(e.target) && !sidebarToggle.contains(e.target)) {
      sidebar.classList.remove('open');
    }
  });
}

/* ── Highlight active nav link ───────────────────────────────────────────── */
document.querySelectorAll('.nav-link').forEach(link => {
  if (link.href && window.location.pathname.startsWith(new URL(link.href, location.origin).pathname)) {
    link.classList.add('active');
  }
});

/* ── Transfer form: amount formatter ─────────────────────────────────────── */
const amtInput = document.getElementById('amount-input');
const amtPreview = document.getElementById('amount-preview');

if (amtInput && amtPreview) {
  amtInput.addEventListener('input', () => {
    const val = parseFloat(amtInput.value.replace(/,/g, ''));
    if (!isNaN(val) && val > 0) {
      amtPreview.textContent = '₹' + val.toLocaleString('en-IN', {
        minimumFractionDigits: 2, maximumFractionDigits: 2
      });
    } else {
      amtPreview.textContent = '₹0.00';
    }
  });
}

/* ── Click-to-fill demo credentials ─────────────────────────────────────── */
document.querySelectorAll('.login-demo-value').forEach(el => {
  el.addEventListener('click', () => {
    const target = el.dataset.target;
    const input  = document.getElementById(target);
    if (input) {
      input.value = el.textContent.trim();
      input.dispatchEvent(new Event('input'));
      // Flash highlight
      input.style.transition = 'border-color 0.2s';
      input.style.borderColor = 'var(--accent)';
      setTimeout(() => { input.style.borderColor = ''; }, 800);
    }
  });
});

/* ── Transfer confirmation dialog ────────────────────────────────────────── */
const transferForm = document.getElementById('transfer-form');
if (transferForm) {
  transferForm.addEventListener('submit', (e) => {
    const receiver = document.getElementById('receiver_account')?.value.trim();
    const amount   = document.getElementById('amount-input')?.value.trim();

    if (!receiver || !amount) return; // HTML5 validation will handle

    const preview = amtPreview ? amtPreview.textContent : `₹${amount}`;
    const ok = confirm(
      `Confirm Transfer\n\nAmount : ${preview}\nTo     : ${receiver}\n\nProceed?`
    );
    if (!ok) e.preventDefault();
  });
}

/* ── Risk score animated circle ──────────────────────────────────────────── */
function animateRiskCircle() {
  const circle = document.getElementById('risk-circle');
  if (!circle) return;

  const score = parseInt(circle.dataset.score || '0', 10);
  const level = (circle.dataset.level || 'LOW').toUpperCase();

  const colourMap = {
    LOW:    { colour: '#10b981', glow: 'rgba(16,185,129,0.3)' },
    MEDIUM: { colour: '#f59e0b', glow: 'rgba(245,158,11,0.3)' },
    HIGH:   { colour: '#ef4444', glow: 'rgba(239,68,68,0.3)'  },
  };
  const { colour, glow } = colourMap[level] || colourMap.LOW;

  circle.style.setProperty('--risk-colour', colour);
  circle.style.setProperty('--risk-glow', glow);

  // Animate pct from 0 → score
  let current = 0;
  const interval = setInterval(() => {
    current = Math.min(current + 2, score);
    circle.style.setProperty('--pct', current);
    const numEl = circle.querySelector('.risk-score-number');
    if (numEl) numEl.textContent = current;
    if (current >= score) clearInterval(interval);
  }, 20);
}
animateRiskCircle();

/* ── Table: highlight high-risk rows ─────────────────────────────────────── */
document.querySelectorAll('.bank-table tbody tr').forEach(row => {
  const badge = row.querySelector('.risk-high, [data-risk="HIGH"]');
  if (badge) {
    row.style.borderLeft = '3px solid var(--danger)';
  }
});

/* ── Filter form auto-submit on select change ────────────────────────────── */
document.querySelectorAll('select[data-autosubmit]').forEach(sel => {
  sel.addEventListener('change', () => sel.closest('form')?.submit());
});

/* ── Copy reference number on click ──────────────────────────────────────── */
document.querySelectorAll('[data-copy]').forEach(el => {
  el.title = 'Click to copy';
  el.style.cursor = 'pointer';
  el.addEventListener('click', () => {
    navigator.clipboard.writeText(el.textContent.trim()).then(() => {
      const orig = el.textContent;
      el.textContent = '✓ Copied!';
      setTimeout(() => { el.textContent = orig; }, 1200);
    });
  });
});
