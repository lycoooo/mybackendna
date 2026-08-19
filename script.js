/* ============================================================
   Netflix Trial Sender — script.js
   ------------------------------------------------------------
   UI na konektado sa server.py (ang net.py logic sa server-side).
   Lahat ng Netflix request (banner scan + signup) ay dadaan sa
   server — totoong Cookie headers, walang CORS, walang proxy.
   Patakbuhin:  python server.py
   ============================================================ */

'use strict';

/* =====================================================================
   1) CONFIG — ang mga endpoint ng server.py
   ===================================================================== */
const API_RUN = '/api/run'; // buong daloy (scan + signup) ay nasa server.py

/* =====================================================================
   2) MGA BAHAGI NG PAGE (ang mga input/button)
   ===================================================================== */
const startBtn    = document.getElementById('startBtn');
const emailInput  = document.getElementById('emailInput');
const nfvdidInput = document.getElementById('nfvdidInput');
const nfvdidGroup = document.getElementById('nfvdidGroup');
const injectBtn   = document.getElementById('injectBtn');
const clearBtn    = document.getElementById('clearBtn');
const statusDot   = document.getElementById('statusDot');
const statusText  = document.getElementById('statusText');
const consoleBox  = document.getElementById('console');

let running = false; // para hindi makapag-click ng doble habang tumatakbo

/* =====================================================================
   3) CONSOLE — parang terminal output (✓ / ⚠ / ✗ / •)
   ===================================================================== */
function logLine(text, kind) {
  const line = document.createElement('div');
  line.className = 'log-line ' + (kind || 'plain');
  line.textContent = text;
  consoleBox.appendChild(line);
  consoleBox.scrollTop = consoleBox.scrollHeight;
}
const logOk   = (m) => logLine('  ✓ ' + m, 'ok');
const logWarn = (m) => logLine('  ⚠ ' + m, 'warn');
const logErr  = (m) => logLine('  ✗ ' + m, 'err');
const logInfo = (m) => logLine('  • ' + m, 'info');
const logHead = (m) => logLine('─ ' + m, 'section');

function setStatus(text, color) {
  statusText.textContent = text;
  statusDot.style.backgroundColor = color;
}

/* =====================================================================
   4) ANG FLOW — ito ang nangyayari kapag pinindot ang "Send Trial"
   ===================================================================== */
async function handleSend() {
  if (running) return; // anti double-click

  const email = emailInput.value.trim();
  if (!email || !email.includes('@')) {
    alert('Please enter a valid email address.');
    emailInput.focus();
    return;
  }

  running = true;
  startBtn.disabled = true;
  startBtn.textContent = 'Working…';
  setStatus('Working…', '#ffbd2e');

  logOk('Email: ' + email);

  try {
    // Isang tawag lang sa server.py — dito na ang buong daloy
    // (banner scan + signup), gaya ng net.py.
    const customNfvdid = nfvdidInput.value.trim();
    const url = API_RUN + '?email=' + encodeURIComponent(email) +
      (customNfvdid ? '&nfvdid=' + encodeURIComponent(customNfvdid) : '');

    const res = await fetch(url);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || ('Server ' + res.status));

    render(data); // ipakita ang tugon ng server
    finish(data.success);
  } catch (err) {
    logErr(err.message);
    if (/Failed to fetch|server/i.test(err.message)) {
      logInfo('Patakbuhin muna ang server:  python server.py');
    }
    finish(false);
  }
}

// Ipakita ang tugon ng server nang sunod-sunod (gaya ng console ng net.py)
function render(d) {
  if (d.nfvdid) logInfo('nfvdid: ' + d.nfvdid);
  if (d.flwssn) logInfo('flwssn: ' + d.flwssn);

  // 1) Trial Scan
  logHead('Trial Scan (banner check)');
  if (d.detected) logOk('30 Days Trial Detect');
  else logInfo('Walang trial banner; susubukan pa ring i-activate.');

  // 2) Signup
  if (d.success) {
    logHead('Signup 1/2 — CLCSWebInitSignup (server)');
    logOk('Init signup OK (HTTP ' + d.status1 + ').');
    logHead('Signup 2/2 — CLCSScreenUpdate (server)');
    logOk('Trial activated for ' + (d.email || ''));
    if (!d.detected) logOk('30 Days Trial Detect'); // kumpirmado ang activation
  } else if (d.step === 1) {
    logErr('Signup rejected (HTTP ' + d.status1 + ').');
  } else if (d.step === 2) {
    logErr('Signup failed (HTTP ' + d.status2 + ').');
  } else if (d.error) {
    logErr(d.error);
  }
}

// Ipakita/itago ang nfvdid input
function showNfvdid(show) {
  nfvdidGroup.style.display = show ? 'block' : 'none';
  if (show) nfvdidInput.focus();
}

function finish(ok) {
  running = false;
  startBtn.disabled = false;
  startBtn.textContent = 'Send Trial';
  if (ok === true)      setStatus('Success', '#27c93f'); // berde = success
  else if (ok === false) setStatus('Error', '#ff5f56');   // pula = error
  else                   setStatus('Retry needed', '#ffbd2e'); // dilaw
}

/* =====================================================================
   5) MGA BUTTON AT EVENTS
   ===================================================================== */

// "inject nfvdid" — ipakita/itago ang nfvdid input
injectBtn.addEventListener('click', () => {
  showNfvdid(nfvdidGroup.style.display === 'none');
});

// "clear" — linisin ang console
clearBtn.addEventListener('click', () => {
  consoleBox.innerHTML = '';
});

// Pwede ring Send sa pagpindot ng Enter
[emailInput, nfvdidInput].forEach((el) => {
  el.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') handleSend();
  });
});

// Ang pangunahing button
startBtn.addEventListener('click', handleSend);


