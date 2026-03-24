/**
 * chatbot.js — Genius Tax MTD Assistant Widget
 * Pure client-side, no frameworks, no dependencies.
 *
 * KNOWLEDGE BASE TOPICS (>= 8):
 *  1. What is MTD?
 *  2. Who is affected? (threshold, self-employed / landlords)
 *  3. Penalties for non-compliance
 *  4. Pricing overview (all three plans)
 *  5. Essential plan (£199/year / £20/month, 24-month commitment)
 *  6. Growth plan (£299/year / £30/month early bird before 5 April 2026)
 *  7. Premium plan (£149/month)
 *  8. How to sign up (the 3-step process)
 *  9. Early bird deadline (5 April 2026)
 * 10. Contact / I have a question
 *
 * WEBHOOK NOTIFICATION (wire to Telegram later):
 * --------------------------------------------------
 * To receive a Telegram message every time someone chats:
 *
 *   1. Create a Telegram bot via @BotFather → get BOT_TOKEN
 *   2. Get your chat ID (send /start to the bot and check
 *      https://api.telegram.org/bot<TOKEN>/getUpdates)
 *   3. Replace WEBHOOK_URL below with:
 *      "https://api.telegram.org/bot<BOT_TOKEN>/sendMessage"
 *   4. In notifyWebhook(), change the fetch body to:
 *      JSON.stringify({ chat_id: "<YOUR_CHAT_ID>", text: payload.message })
 *
 * For a generic webhook (Zapier, Make, n8n, etc.):
 *   Just set WEBHOOK_URL to your endpoint — the function POSTs JSON.
 * --------------------------------------------------
 */

(function () {
  'use strict';

  /* ──────────────────────────────────────────────
     CONFIG
  ────────────────────────────────────────────── */

  /**
   * AI Chat API endpoint (Cloudflare tunnel → Mac mini Express server).
   * Set to '' to disable AI and use keyword matching only.
   */
  var CHAT_API = 'https://chat.greedisgood.co/chat';

  /**
   * Set to your webhook URL to receive notifications when someone chats.
   * Leave empty ('') to disable.
   * Example: 'https://hooks.zapier.com/hooks/catch/xxxxx/yyyyy/'
   */
  var WEBHOOK_URL = '';

  /** Auto-open the chat after this many milliseconds (30 s). Set 0 to disable. */
  var AUTO_OPEN_DELAY_MS = 30000;

  /** localStorage key for persisting conversations. */
  var LS_KEY = 'gtax_chat_history';

  /* ──────────────────────────────────────────────
     INJECT HTML
  ────────────────────────────────────────────── */

  function injectHTML() {
    var html = [
      /* Bubble toggle button */
      '<button id="gtax-bubble" onclick="gtaxToggle()"',
      '  aria-label="Open Genius Tax chat"',
      '  aria-expanded="false"',
      '  aria-controls="gtax-window">',
      '  <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">',
      '    <path d="M12 2C6.477 2 2 6.253 2 11.5c0 2.304.861 4.412 2.28 6.048L3 21',
      '      l3.75-1.182A10.05 10.05 0 0 0 12 21c5.523 0 10-4.253 10-9.5S17.523 2 12 2z"/>',
      '  </svg>',
      '  <span class="gtax-icon-close" aria-hidden="true">✕</span>',
      '</button>',

      /* Chat window */
      '<div id="gtax-window" role="dialog"',
      '     aria-label="Genius Tax Chat Assistant"',
      '     aria-modal="true">',

      '  <!-- Header -->',
      '  <div class="gtax-hdr">',
      '    <div class="gtax-hdr-avatar" aria-hidden="true">💬</div>',
      '    <div class="gtax-hdr-info">',
      '      <div class="gtax-hdr-name">Genius Tax Assistant</div>',
      '      <div class="gtax-hdr-status">Online — MTD expert</div>',
      '    </div>',
      '    <button class="gtax-reset-btn" onclick="gtaxReset()" aria-label="New conversation" title="Start new chat" style="background:rgba(255,255,255,0.2);border:1px solid rgba(255,255,255,0.4);color:#fff;font-size:0.7rem;cursor:pointer;padding:4px 10px;border-radius:12px;margin-right:6px;backdrop-filter:blur(4px);transition:background 0.2s;" onmouseover="this.style.background=\'rgba(255,255,255,0.35)\'" onmouseout="this.style.background=\'rgba(255,255,255,0.2)\'">🔄 New</button>',
      '    <button class="gtax-close-btn" onclick="gtaxToggle()" aria-label="Close chat">✕</button>',
      '  </div>',

      '  <!-- Messages -->',
      '  <div class="gtax-msgs" id="gtax-msgs"',
      '       aria-live="polite" aria-atomic="false"></div>',

      '  <!-- Quick-reply buttons (dynamic) -->',
      '  <div class="gtax-qr-wrap" id="gtax-qr" style="display:none;"></div>',

      '  <!-- Free-text input -->',
      '  <div class="gtax-input-row" id="gtax-input-row" style="display:flex;align-items:center;gap:0.5rem;padding:0.75rem;border-top:1px solid #e8e8e8;background:#fff;">',
      '    <input type="text" id="gtax-user-input" style="flex:1;padding:0.6rem 0.9rem;border:1px solid #ddd;border-radius:1.5rem;font-size:0.85rem;outline:none;background:#f9f9f9;color:#333;"',
      '           placeholder="Type a message…"',
      '           autocomplete="off"',
      '           onkeydown="if(event.key===\'Enter\')gtaxSendText()" />',
      '    <button class="gtax-send-btn" style="width:36px;height:36px;border-radius:50%;background:#E5007D;border:none;cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0;padding:7px;color:#fff;" onclick="gtaxSendText()" aria-label="Send message">',
      '      <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">',
      '        <path d="M22 2L11 13" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',
      '        <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',
      '      </svg>',
      '    </button>',
      '  </div>',

      '  <!-- Contact form (shown on "I have a question") -->',
      '  <div class="gtax-cf" id="gtax-cf" style="display:none;">',
      '    <input type="text"  id="gtax-cf-name"    placeholder="Your name *"',
      '           autocomplete="name" />',
      '    <input type="email" id="gtax-cf-email"   placeholder="Your email *"',
      '           autocomplete="email" />',
      '    <textarea           id="gtax-cf-message" placeholder="Your question (optional)…"></textarea>',
      '    <button class="gtax-cf-submit" id="gtax-cf-submit" onclick="gtaxSendForm()">',
      '      Send message →',
      '    </button>',
      '    <button class="gtax-cf-cancel" onclick="gtaxCancelForm()">← Go back</button>',
      '  </div>',

      '</div>'
    ].join('\n');

    var div = document.createElement('div');
    div.innerHTML = html;
    while (div.firstChild) {
      document.body.appendChild(div.firstChild);
    }
  }

  /* ──────────────────────────────────────────────
     STATE
  ────────────────────────────────────────────── */

  var _open         = false;
  var _interacted   = false;   /* set true on first user action; blocks auto-open */
  var _autoTimer    = null;
  var _conversation = [];      /* persisted to localStorage (HTML) */
  var _apiHistory   = [];      /* clean text history for AI API {role, content} */
  var _aiPending    = false;   /* prevents double-sends while awaiting AI */

  /* ──────────────────────────────────────────────
     INIT (called once DOM is ready)
  ────────────────────────────────────────────── */

  function init() {
    injectHTML();
    loadHistory();

    /* Auto-open after delay if user hasn't interacted */
    if (AUTO_OPEN_DELAY_MS > 0) {
      _autoTimer = setTimeout(function () {
        if (!_interacted && !_open) gtaxToggle();
      }, AUTO_OPEN_DELAY_MS);
    }
  }

  /* ──────────────────────────────────────────────
     TOGGLE OPEN / CLOSE
  ────────────────────────────────────────────── */

  window.gtaxReset = function () {
    /* Clear conversation history and restart */
    localStorage.removeItem(LS_KEY);
    _conversation = [];
    if (typeof _apiHistory !== 'undefined') _apiHistory = [];
    var msgs = document.getElementById('gtax-msgs');
    if (msgs) msgs.innerHTML = '';
    gtaxInit();
  };

  window.gtaxToggle = function () {
    _open       = !_open;
    _interacted = true;
    clearTimeout(_autoTimer);

    var win    = document.getElementById('gtax-window');
    var bubble = document.getElementById('gtax-bubble');

    if (_open) {
      win.classList.add('open');
      bubble.classList.add('open');
      bubble.setAttribute('aria-expanded', 'true');

      /* Show greeting if no history */
      var msgs = document.getElementById('gtax-msgs');
      if (!msgs.children.length) {
        if (_conversation.length) {
          restoreHistory();
        } else {
          gtaxInit();
        }
      }
    } else {
      win.classList.remove('open');
      bubble.classList.remove('open');
      bubble.setAttribute('aria-expanded', 'false');
    }
  };

  /* ──────────────────────────────────────────────
     GREETING
  ────────────────────────────────────────────── */

  function gtaxInit() {
    addMsg('bot', 'Hi! 👋 I\'m here to help with any questions about Making Tax Digital. What would you like to know?');
    setQR([
      { label: 'What is MTD?',           action: 'mtd'     },
      { label: 'Pricing',                action: 'cost'    },
      { label: 'Am I affected?',         action: 'mtd-affects' },
      { label: 'Sign up',                action: 'signup'  }
    ]);
  }

  /* ──────────────────────────────────────────────
     MESSAGES
  ────────────────────────────────────────────── */

  function addMsg(who, html) {
    var wrap = document.getElementById('gtax-msgs');
    var el   = document.createElement('div');
    el.className = 'gtax-msg ' + who;
    el.innerHTML = html;
    wrap.appendChild(el);
    setTimeout(function () { wrap.scrollTop = wrap.scrollHeight; }, 40);

    /* Persist to history */
    _conversation.push({ who: who, html: html });
    saveHistory();

    return el;
  }

  /* ──────────────────────────────────────────────
     QUICK-REPLY BUTTONS
  ────────────────────────────────────────────── */

  function setQR(btns) {
    var wrap = document.getElementById('gtax-qr');
    wrap.innerHTML = '';
    if (!btns || !btns.length) { wrap.style.display = 'none'; return; }
    btns.forEach(function (b) {
      var btn = document.createElement('button');
      btn.className   = 'gtax-qr-btn';
      btn.textContent = b.label;
      btn.onclick     = function () { gtaxHandle(b.action, b.label); };
      wrap.appendChild(btn);
    });
    wrap.style.display = 'flex';
  }

  /* ──────────────────────────────────────────────
     TEXT INPUT HANDLER — wires the free-text box
  ────────────────────────────────────────────── */

  window.gtaxSendText = function () {
    var input = document.getElementById('gtax-user-input');
    if (!input) return;
    var text = (input.value || '').trim();
    if (!text || _aiPending) return;
    input.value = '';

    _interacted = true;
    notifyWebhook({ type: 'free_text', message: text });
    addMsg('user', escapeHTML(text));
    setQR([]);

    /* Intercept qualification-wizard trigger phrases before sending to AI */
    var _lower = text.toLowerCase();
    if (_lower.indexOf('do i need') !== -1 ||
        _lower.indexOf('am i affected') !== -1 ||
        _lower.indexOf('qualify') !== -1) {
      setTimeout(function () { startQualWizard(); }, 380);
      return;
    }

    sendMessage(text);
  };

  /* ──────────────────────────────────────────────
     AI API — sendMessage with keyword fallback
  ────────────────────────────────────────────── */

  function escapeHTML(str) {
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function showTypingIndicator() {
    var wrap = document.getElementById('gtax-msgs');
    var el   = document.createElement('div');
    el.className = 'gtax-msg bot gtax-typing';
    el.id        = 'gtax-typing-indicator';
    el.innerHTML = '<span class="gtax-dot"></span><span class="gtax-dot"></span><span class="gtax-dot"></span>';
    wrap.appendChild(el);
    setTimeout(function () { wrap.scrollTop = wrap.scrollHeight; }, 40);
  }

  function removeTypingIndicator() {
    var el = document.getElementById('gtax-typing-indicator');
    if (el) el.parentNode.removeChild(el);
  }

  function sendMessage(text) {
    /* Try AI API first; fall back to keyword matching if unavailable */
    if (!CHAT_API) {
      /* API disabled — use keyword matching directly */
      setTimeout(function () {
        var action = gtaxMatchKeyword(text);
        gtaxHandle(action, null);
      }, 380);
      return;
    }

    _aiPending = true;
    var inputEl = document.getElementById('gtax-user-input');
    if (inputEl) inputEl.disabled = true;

    showTypingIndicator();

    /* Record in clean API history */
    _apiHistory.push({ role: 'user', content: text });
    if (_apiHistory.length > 20) _apiHistory = _apiHistory.slice(-20);

    /* Send last 10 turns as history (excluding the current message, already in body) */
    var historyToSend = _apiHistory.slice(-11, -1);

    fetch(CHAT_API, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ message: text, history: historyToSend }),
      signal:  AbortSignal.timeout ? AbortSignal.timeout(15000) : undefined
    })
    .then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    })
    .then(function (data) {
      removeTypingIndicator();
      _aiPending = false;
      if (inputEl) inputEl.disabled = false;

      var reply = (data && data.reply) ? data.reply : null;
      if (!reply) throw new Error('empty reply');

      /* Record assistant reply in API history */
      _apiHistory.push({ role: 'assistant', content: reply });
      if (_apiHistory.length > 20) _apiHistory = _apiHistory.slice(-20);

      addMsg('bot', escapeHTML(reply).replace(/\n/g, '<br>'));
      /* No quick-reply buttons after AI response — let conversation flow naturally */
      setQR([
        { label: 'See pricing',       action: 'cost'    },
        { label: 'Sign up',           action: 'signup'  },
        { label: 'Contact the team',  action: 'contact' }
      ]);
    })
    .catch(function (err) {
      console.warn('[GeniusTax chat] AI API unavailable, falling back to keyword matching.', err);
      removeTypingIndicator();
      _aiPending = false;
      if (inputEl) inputEl.disabled = false;

      /* Remove the failed user message from API history since we're falling back */
      if (_apiHistory.length && _apiHistory[_apiHistory.length - 1].role === 'user') {
        _apiHistory.pop();
      }

      /* Keyword matching fallback */
      var action = gtaxMatchKeyword(text);
      setTimeout(function () {
        switch (action) {
          case 'mtd':          answerMTD();       break;
          case 'mtd-affects':  answerAffects();   break;
          case 'mtd-penalty':  answerPenalty();   break;
          case 'cost':         answerCost();      break;
          case 'plan-std':     answerStandard();  break;
          case 'plan-mtd':     answerMTDPlan();   break;
          case 'plan-premium': answerPremium();   break;
          case 'signup':       answerSignup();    break;
          case 'contact':      showContactForm(); break;
          default:             answerFallback();  break;
        }
      }, 200);
    });
  }

  /* ──────────────────────────────────────────────
     KEYWORD MATCHING (free-text input, optional)
     Used as AI fallback and for quick-reply routing.
     Call gtaxMatchKeyword(text) to get an action.
  ────────────────────────────────────────────── */

  var KB = [
    { patterns: ['what is mtd','making tax digital','mtd mean','mtd is','what mtd'],
      action: 'mtd' },
    { patterns: ['affects me','do i need','am i','threshold','£50','50k','50,000','qualify','affected'],
      action: 'mtd-affects' },
    { patterns: ['penalty','penalt','fine','miss','late','points'],
      action: 'mtd-penalty' },
    { patterns: ['price','pricing','cost','how much','£29','£49','£79','£149','£199','£299','£25','20','plan','plans','monthly'],
      action: 'cost' },
    { patterns: ['essential','standard','£29','£199','29/month','29 month','199/year','20','annual'],
      action: 'plan-std' },
    { patterns: ['growth','mtd compliance','£49','£299','£25','49/month','early bird','49 month','299/year','25/month'],
      action: 'plan-mtd' },
    { patterns: ['premium','£149','149/month','payroll','cis','vat'],
      action: 'plan-premium' },
    { patterns: ['sign up','signup','get started','register','join'],
      action: 'signup' },
    { patterns: ['contact','email','hello@','question','speak','talk','human','advisor','team'],
      action: 'contact' },
    { patterns: ['deadline','april 2026','april 5','april 6','6 april','5 april','2026','2027','£30','30k','30,000'],
      action: 'mtd-affects' }
  ];

  function gtaxMatchKeyword(text) {
    var lower = text.toLowerCase();
    for (var i = 0; i < KB.length; i++) {
      var entry = KB[i];
      for (var j = 0; j < entry.patterns.length; j++) {
        if (lower.indexOf(entry.patterns[j]) !== -1) return entry.action;
      }
    }
    return 'fallback';
  }

  /* ──────────────────────────────────────────────
     ROUTE ACTIONS
  ────────────────────────────────────────────── */

  window.gtaxHandle = function (action, label) {
    _interacted = true;
    if (label) addMsg('user', label);
    setQR([]);
    notifyWebhook({ type: 'quick_reply', action: action, label: label || '' });

    setTimeout(function () {
      switch (action) {
        case 'mtd':                   answerMTD();              break;
        case 'mtd-affects':           startQualWizard();        break;
        case 'mtd-penalty':           answerPenalty();          break;
        case 'cost':                  answerCost();             break;
        case 'plan-std':              answerStandard();         break;
        case 'plan-mtd':              answerMTDPlan();          break;
        case 'plan-premium':          answerPremium();          break;
        case 'signup':                answerSignup();           break;
        case 'early-bird':            answerEarlyBird();        break;
        case 'genius-tax':            answerGeniusTax();        break;
        case 'contact':               showContactForm();        break;
        case 'main-menu':             mainMenu();               break;
        case 'fallback':              answerFallback();         break;
        /* ── Qualification wizard steps ── */
        case 'qualify-step1-yes':     wizardStep2Yes();         break;
        case 'qualify-step1-no':      wizardStep2No();          break;
        case 'qualify-step2-over50k': wizardStep3Over50K();     break;
        case 'qualify-step2-under50k':wizardStep3Under50K();    break;
        case 'qualify-growth-details': wizardGrowthDetails();   break;
        case 'qualify-growth-signup':  wizardGrowthSignup();    break;
        case 'qualify-essential-details': wizardEssentialDetails(); break;
        case 'qualify-essential-signup':  wizardEssentialSignup();  break;
        default:                      answerFallback();         break;
      }
    }, 380);
  };

  /* ──────────────────────────────────────────────
     ANSWER FLOWS  (10 distinct topics)
  ────────────────────────────────────────────── */

  /* TOPIC 1 — What is MTD? */
  function answerMTD() {
    addMsg('bot',
      '<strong>Making Tax Digital (MTD)</strong> is HMRC\'s programme to digitalise the UK tax system. 📋<br><br>' +
      'From <strong>6 April 2026</strong>, sole traders and landlords with gross income over <strong>£50,000</strong> must:<br>' +
      '&nbsp;✓ Keep digital records<br>' +
      '&nbsp;✓ Submit <strong>4 quarterly updates</strong> to HMRC<br>' +
      '&nbsp;✓ Use HMRC-approved software (Genius Tax uses <strong>Sage</strong>)<br>' +
      '&nbsp;✓ File an End of Period Statement + Final Declaration<br><br>' +
      'The threshold <strong>drops to £30,000 in April 2027</strong> — so even if you\'re under now, you may not be for long.'
    );
    setQR([
      { label: 'Am I affected?',          action: 'mtd-affects'  },
      { label: 'What are the penalties?', action: 'mtd-penalty'  },
      { label: 'Pricing',                 action: 'cost'         },
      { label: 'Sign up',                 action: 'signup'       }
    ]);
  }

  /* TOPIC 2 — Who is affected? */
  function answerAffects() {
    addMsg('bot',
      'MTD ITSA is mandatory from <strong>6 April 2026</strong> if your <em>gross</em> self-employment or property income exceeds <strong>£50,000</strong> in 2024/25. 🎯<br><br>' +
      'PAYE / umbrella income <strong>doesn\'t count</strong> toward the threshold.<br><br>' +
      'Between <strong>£30K–£50K</strong> today? The threshold drops to £30,000 in <strong>April 2027</strong> — now is the right time to get set up.<br><br>' +
      '<button class="gtax-cta" onclick="gtaxScrollToSignup()">Get compliant — from £20/month →</button>'
    );
    setQR([
      { label: 'What are the penalties?', action: 'mtd-penalty' },
      { label: 'Pricing',                 action: 'cost'        },
      { label: 'Sign up',                 action: 'signup'      }
    ]);
  }

  /* ──────────────────────────────────────────────
     QUALIFICATION WIZARD
     Triggered by: "Am I affected?" button (mtd-affects action)
     or free-text containing "do i need" / "am i affected" / "qualify"
  ────────────────────────────────────────────── */

  /** Step 1 — are you self-employed / freelancer / contractor / landlord? */
  function startQualWizard() {
    addMsg('bot', "Let\u2019s find out! \uD83D\uDC4B Are you self-employed, a freelancer, contractor, or landlord?");
    setQR([
      { label: 'Yes \u2705', action: 'qualify-step1-yes' },
      { label: 'No \u274C',  action: 'qualify-step1-no'  }
    ]);
  }

  /** Step 2a — over £50K? */
  function wizardStep2Yes() {
    addMsg('bot', 'Do you earn over \u00A350,000 a year from self-employment or rental income?');
    setQR([
      { label: 'Yes, over \u00A350K',  action: 'qualify-step2-over50k'  },
      { label: 'No, under \u00A350K',  action: 'qualify-step2-under50k' }
    ]);
  }

  /** Step 2b — not self-employed */
  function wizardStep2No() {
    addMsg('bot',
      'No worries! Genius Tax is designed for self-employed people, freelancers, contractors, and landlords. ' +
      'If your situation changes, we\u2019ll be here! \uD83D\uDE0A'
    );
    setQR([{ label: 'Back to menu', action: 'main-menu' }]);
  }

  /** Step 3a — MTD mandatory → Growth / MTD Compliance plan */
  function wizardStep3Over50K() {
    addMsg('bot',
      'You\u2019ll need MTD compliance from April 2026 \u2014 it\u2019s mandatory. ' +
      'Our <strong>Growth plan</strong> at \u00A3299/year (just \u00A330/month) \u2014 early bird, normally \u00A3588/year handles it all.'
    );
    setQR([
      { label: 'Tell me more \u2139\uFE0F', action: 'qualify-growth-details' },
      { label: 'Sign up \u2014 \u00A3299/year \u2192', action: 'qualify-growth-signup' }
    ]);
  }

  function wizardGrowthDetails() {
    addMsg('bot',
      '<strong>Here\u2019s what you get with Growth:</strong><br><br>' +
      '\u2705 Full quarterly HMRC submissions \u2014 we handle all 4 per year<br>' +
      '\u2705 Sage software (HMRC-approved) \u2014 all set up for you<br>' +
      '\u2705 Dedicated account manager who calls you monthly<br>' +
      '\u2705 Annual accounts prepared and filed<br>' +
      '\u2705 Compliance alerts so you never miss a deadline<br>' +
      '\u2705 HMRC agent authorisation \u2014 we deal with HMRC on your behalf<br><br>' +
      'No penalties. No stress. No surprises.'
    );
    setQR([
      { label: 'Sign up now \u2014 \u00A3299/year \u2192', action: 'qualify-growth-signup' }
    ]);
  }

  function wizardGrowthSignup() {
    addMsg('bot',
      'Great choice! \uD83C\uDF89 Click below to get started \u2014 takes 2 minutes:<br><br>' +
      '<a href="https://buy.stripe.com/dRm14n46c6OXfZwcr99EI0b" ' +
      '   target="_blank" rel="noopener noreferrer" ' +
      '   class="gtax-cta" ' +
      '   style="display:inline-block;text-decoration:none;min-height:44px;line-height:44px;padding:0 1.2rem;background:#E5007D;color:#fff;border-radius:8px;font-weight:600;text-align:center;">' +
      'Sign up for Growth \u2014 \u00A3299/year \u2192' +
      '</a>'
    );
    setQR([]);
  }

  /** Step 3b — not yet mandatory → Essential / Standard plan */
  function wizardStep3Under50K() {
    addMsg('bot',
      'You don\u2019t need MTD yet, but you still need your annual self-assessment sorted. ' +
      'Our <strong>Essential plan</strong> handles it for just \u00A3199/year (\u00A320/month).'
    );
    setQR([
      { label: 'Tell me more \u2139\uFE0F', action: 'qualify-essential-details' },
      { label: 'Sign up \u2014 \u00A3199/year \u2192', action: 'qualify-essential-signup' }
    ]);
  }

  function wizardEssentialDetails() {
    addMsg('bot',
      '<strong>Here\u2019s what you get with Essential:</strong><br><br>' +
      '\u2705 Full self-assessment tax return prepared and filed<br>' +
      '\u2705 Bookkeeping guidance and support<br>' +
      '\u2705 HMRC filing handled on your behalf<br>' +
      '\u2705 Email support from our tax team<br>' +
      '\u2705 Compliance reminders so you never miss a deadline<br><br>' +
      'Simple, affordable, sorted.'
    );
    setQR([
      { label: 'Sign up now \u2014 \u00A3199/year \u2192', action: 'qualify-essential-signup' }
    ]);
  }

  function wizardEssentialSignup() {
    addMsg('bot',
      'Great choice! \uD83C\uDF89 Click below to get started \u2014 takes 2 minutes:<br><br>' +
      '<a href="https://buy.stripe.com/6oU7sLauAddlbJg2Qz9EI0a" ' +
      '   target="_blank" rel="noopener noreferrer" ' +
      '   class="gtax-cta" ' +
      '   style="display:inline-block;text-decoration:none;min-height:44px;line-height:44px;padding:0 1.2rem;background:#E5007D;color:#fff;border-radius:8px;font-weight:600;text-align:center;">' +
      'Sign up for Essential \u2014 \u00A3199/year \u2192' +
      '</a>'
    );
    setQR([]);
  }

  /* TOPIC 3 — Penalties */
  function answerPenalty() {
    addMsg('bot',
      'HMRC uses a <strong>points-based penalty system</strong> for MTD. ⚠️<br><br>' +
      'Every missed quarterly deadline earns <strong>1 penalty point</strong>. Hit 4 points:<br>' +
      '&nbsp;→ <strong>£200 fine</strong> issued immediately<br>' +
      '&nbsp;→ <strong>£200 for each missed submission</strong> after that<br><br>' +
      'Unlike the old SA system, the clock starts from <strong>6 April 2026</strong> — not end of year. Getting sorted early removes all risk.<br><br>' +
      '<button class="gtax-cta" onclick="gtaxScrollToSignup()">Get compliant now →</button>'
    );
    setQR([
      { label: 'Pricing',           action: 'cost'    },
      { label: 'Sign up',           action: 'signup'  },
      { label: 'I have a question', action: 'contact' }
    ]);
  }

  /* TOPIC 4 — Pricing overview */
  function answerCost() {
    addMsg('bot',
      'Three plans — all include <strong>HMRC agent authorisation</strong> and no setup fees: 💷<br><br>' +
      '<strong>📦 Essential — £199/year</strong> <em style="color:#888">(£20/month, 24-month commitment)</em><br>' +
      'Annual self-assessment. Ideal for income under £50K.<br><br>' +
      '<strong>⭐ Growth — £299/year</strong> <em style="color:#888">(just £30/month — early bird before 5 Apr 2026)</em><br>' +
      'Full quarterly MTD reporting via Sage. Early Bird — <strong>save £289/year vs standard rate</strong>. Most popular.<br><br>' +
      '<strong>🏆 Premium — £149/month</strong><br>' +
      'Growth + payroll, CIS, VAT &amp; senior accountant.<br><br>' +
      '<em style="color:#e5007d;font-weight:700;">🐣 Early Bird ends 5th April 2026 — don\'t miss it!</em>'
    );
    setQR([
      { label: 'Essential — £199/year',  action: 'plan-std'     },
      { label: 'Growth — £299/year',     action: 'plan-mtd'     },
      { label: 'Premium — £149/month',   action: 'plan-premium' },
      { label: 'Sign up',                action: 'signup'       }
    ]);
  }

  /* TOPIC 5 — Standard plan */
  function answerStandard() {
    addMsg('bot',
      '<strong>Essential Plan — £199/year</strong> <em style="color:#888">(£20/month, 24-month commitment)</em> 📦<br><br>' +
      'Perfect for self-employed, freelancers and sole traders with income under £50K who need annual self-assessment taken care of.<br><br>' +
      '&nbsp;✓ Tax return preparation<br>' +
      '&nbsp;✓ HMRC filing &amp; confirmation<br>' +
      '&nbsp;✓ Bookkeeping guidance<br>' +
      '&nbsp;✓ Email support<br><br>' +
      '<button class="gtax-cta" onclick="gtaxScrollToSignup()">Get started on Essential →</button>'
    );
    setQR([
      { label: 'See all plans',     action: 'cost'    },
      { label: 'Sign up',           action: 'signup'  },
      { label: 'I have a question', action: 'contact' }
    ]);
  }

  /* TOPIC 6 — MTD Compliance plan */
  function answerMTDPlan() {
    addMsg('bot',
      '<strong>Growth — £299/year ⭐</strong> <em style="color:#888">(just £30/month)</em><br>' +
      '<em style="color:#e5007d;">Early Bird before 5 April 2026 — normally £588/year (£49/mo). 3-year commitment.</em><br><br>' +
      'Our most popular plan. Full quarterly digital MTD reporting via <strong>Sage</strong> for income over £50K.<br><br>' +
      '&nbsp;✓ MTD quarterly digital reporting via Sage<br>' +
      '&nbsp;✓ Full annual accounts<br>' +
      '&nbsp;✓ Dedicated account manager<br>' +
      '&nbsp;✓ Phone &amp; email support<br>' +
      '&nbsp;✓ Compliance alerts &amp; reminders<br>' +
      '&nbsp;✓ HMRC agent authorisation<br>' +
      '&nbsp;✓ End of Period Statement + Final Declaration<br><br>' +
      '<em>Early Bird: Year 1 £299/year. Year 2 £49/mo. Year 3 £79/mo. Ends 5th April 2026.</em><br><br>' +
      '<button class="gtax-cta" onclick="gtaxScrollToSignup()">Claim Early Bird — £299/year →</button>'
    );
    setQR([
      { label: 'See all plans',     action: 'cost'    },
      { label: 'Sign up',           action: 'signup'  },
      { label: 'I have a question', action: 'contact' }
    ]);
  }

  /* TOPIC 7 — Premium plan */
  function answerPremium() {
    addMsg('bot',
      '<strong>Premium Plan — £149/month</strong> 🏆<br><br>' +
      'For contractors, CIS workers and sole traders who need the full service. Everything in MTD Compliance, plus:<br><br>' +
      '&nbsp;✓ Payroll management<br>' +
      '&nbsp;✓ CIS deduction handling<br>' +
      '&nbsp;✓ VAT returns &amp; compliance<br>' +
      '&nbsp;✓ Senior accountant assigned to your account<br><br>' +
      'Ideal if you have employees, run CIS, or need complex tax handled end-to-end.<br><br>' +
      '<button class="gtax-cta" onclick="gtaxScrollToSignup()">Get started on Premium →</button>'
    );
    setQR([
      { label: 'See all plans',     action: 'cost'    },
      { label: 'Sign up',           action: 'signup'  },
      { label: 'I have a question', action: 'contact' }
    ]);
  }

  /* TOPIC 8 — How to sign up */
  function answerSignup() {
    addMsg('bot',
      'Signing up takes under <strong>5 minutes</strong> — most clients are fully active within <strong>48 hours</strong>. 🚀<br><br>' +
      '<strong>1. Fill in the form</strong> — name, email, income band, preferred plan.<br><br>' +
      '<strong>2. Upload your records</strong> — each quarter, drop your receipts &amp; invoices into our secure portal (most people spend under 20 min/quarter).<br><br>' +
      '<strong>3. We handle HMRC</strong> — we prepare and file every submission directly. You get confirmation every time. Zero stress.<br><br>' +
      'No payment taken until your account is fully active. HMRC agent authorisation included.<br><br>' +
      '<button class="gtax-cta" onclick="gtaxScrollToSignup()">Sign up now — from £20/month →</button>'
    );
    setQR([
      { label: 'Pricing',           action: 'cost'    },
      { label: 'I have a question', action: 'contact' }
    ]);
  }

  /* TOPIC 9 — Early bird */
  function answerEarlyBird() {
    addMsg('bot',
      '🐣 <strong>Early Bird offer</strong><br><br>' +
      'Our Growth plan normally costs <strong>£49/month (£588/year)</strong> in Year 1. Sign up before <strong>5th April 2026</strong> and lock in just <strong>£299/year (£30/month)</strong> — a 3-year commitment.<br><br>' +
      'Year 2: £49/month. Year 3: £79/month. Early bird year-1 rate ends 5 April 2026.<br><br>' +
      '<button class="gtax-cta" onclick="gtaxScrollToSignup()">Claim Early Bird →</button>'
    );
    setQR([
      { label: 'Sign up now',   action: 'signup'  },
      { label: 'See all plans', action: 'cost'    }
    ]);
  }

  /* TOPIC 10 — About Genius Tax */
  function answerGeniusTax() {
    addMsg('bot',
      '<strong>About Genius Tax</strong> 🛡️<br><br>' +
      'Genius Tax is powered by <strong>Genius Money (Genius Payroll Limited)</strong> — an <strong>AML-approved HMRC authorised tax agent</strong> with years of experience managing payroll and tax compliance for thousands of UK contractors and self-employed workers.<br><br>' +
      '&nbsp;✓ HMRC-authorised agent<br>' +
      '&nbsp;✓ AML approved<br>' +
      '&nbsp;✓ Uses HMRC-compliant Sage software<br>' +
      '&nbsp;✓ Files <em>directly</em> with HMRC on your behalf<br><br>' +
      'Questions? Email us at <a href="mailto:hello@geniustax.co.uk" style="color:#e5007d;font-weight:700;">hello@geniustax.co.uk</a>'
    );
    setQR([
      { label: 'Pricing',   action: 'cost'    },
      { label: 'Sign up',   action: 'signup'  }
    ]);
  }

  /* FALLBACK */
  function answerFallback() {
    addMsg('bot',
      'That\'s a great question! Let me connect you with our team. 😊<br><br>' +
      'You can email us at <a href="mailto:hello@geniustax.co.uk" style="color:#e5007d;font-weight:700;">hello@geniustax.co.uk</a>, or leave your details below and we\'ll get back to you.'
    );
    setQR([
      { label: 'Leave my details', action: 'contact'    },
      { label: 'Back to menu',     action: 'main-menu'  }
    ]);
  }

  /* Main menu */
  function mainMenu() {
    addMsg('bot', 'Anything else I can help you with? 👇');
    setQR([
      { label: 'What is MTD?',  action: 'mtd'         },
      { label: 'Pricing',       action: 'cost'        },
      { label: 'Am I affected?',action: 'mtd-affects' },
      { label: 'Sign up',       action: 'signup'      }
    ]);
  }

  /* ──────────────────────────────────────────────
     CONTACT FORM
  ────────────────────────────────────────────── */

  function showContactForm() {
    addMsg('bot', 'No problem! 😊 Fill in your details below and a Genius Tax advisor will be in touch within one working day.');
    document.getElementById('gtax-qr').style.display = 'none';
    document.getElementById('gtax-cf').style.display = 'flex';
    setTimeout(function () { document.getElementById('gtax-cf-name').focus(); }, 120);
  }

  window.gtaxCancelForm = function () {
    document.getElementById('gtax-cf').style.display = 'none';
    mainMenu();
  };

  window.gtaxSendForm = function () {
    var name    = (document.getElementById('gtax-cf-name').value    || '').trim();
    var email   = (document.getElementById('gtax-cf-email').value   || '').trim();
    var message = (document.getElementById('gtax-cf-message').value || '').trim();
    var re      = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!name)           { alert('Please enter your name.');            return; }
    if (!re.test(email)) { alert('Please enter a valid email address.'); return; }

    var btn = document.getElementById('gtax-cf-submit');
    btn.disabled    = true;
    btn.textContent = 'Sending…';

    /* Notify webhook */
    notifyWebhook({ type: 'contact_form', name: name, email: email, message: message });

    fetch('https://api.web3forms.com/submit', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body: JSON.stringify({
        access_key: '869a7fca-8813-4924-837c-524d27de33ba',
        subject:    'Genius Tax Chat Enquiry from ' + name,
        from_name:  'Genius Tax Chatbot',
        name:       name,
        email:      email,
        message:    message || '(no message entered)',
        replyto:    email
      })
    })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      document.getElementById('gtax-cf').style.display = 'none';
      btn.disabled    = false;
      btn.textContent = 'Send message →';
      document.getElementById('gtax-cf-name').value    = '';
      document.getElementById('gtax-cf-email').value   = '';
      document.getElementById('gtax-cf-message').value = '';

      if (data.success) {
        addMsg('bot',
          '✅ <strong>Message sent!</strong> Thanks ' + name + ' — a Genius Tax advisor will be in touch within one working day. Check your inbox (and spam folder just in case)!<br><br>' +
          '<button class="gtax-cta" onclick="gtaxScrollToSignup()">Or sign up right now →</button>'
        );
      } else {
        addMsg('bot',
          'Hmm, something went wrong on our end. 😕 Please email us directly at ' +
          '<a href="mailto:hello@geniustax.co.uk" style="color:#e5007d;font-weight:700;">hello@geniustax.co.uk</a> ' +
          'and we\'ll get back to you fast.'
        );
      }
      setQR([{ label: 'Back to menu', action: 'main-menu' }]);
    })
    .catch(function () {
      document.getElementById('gtax-cf').style.display = 'none';
      btn.disabled    = false;
      btn.textContent = 'Send message →';
      addMsg('bot',
        'Hmm, something went wrong. Please email us at ' +
        '<a href="mailto:hello@geniustax.co.uk" style="color:#e5007d;font-weight:700;">hello@geniustax.co.uk</a> ' +
        'and we\'ll get back to you promptly.'
      );
      setQR([{ label: 'Back to menu', action: 'main-menu' }]);
    });
  };

  /* ──────────────────────────────────────────────
     SCROLL TO SIGNUP + CLOSE CHAT
  ────────────────────────────────────────────── */

  window.gtaxScrollToSignup = function () {
    if (_open) gtaxToggle();
    var target = document.getElementById('signup');
    if (!target) return;
    var navEl = document.querySelector('.nav');
    var navH  = navEl ? navEl.offsetHeight : 0;
    var y     = target.getBoundingClientRect().top + window.scrollY - navH - 16;
    window.scrollTo({ top: y, behavior: 'smooth' });
  };

  /* ──────────────────────────────────────────────
     WEBHOOK NOTIFICATION
     ─────────────────────────────────────────────
     Fires whenever a visitor sends a message.
     POSTs JSON: { type, label/name/email/message, timestamp, url }

     TO WIRE TO TELEGRAM:
       1. Set WEBHOOK_URL = 'https://api.telegram.org/bot<TOKEN>/sendMessage'
       2. Change the fetch body to:
          JSON.stringify({ chat_id: '<YOUR_CHAT_ID>', text: msg })
          where msg = 'Genius Tax Chat: ' + JSON.stringify(payload)
  ────────────────────────────────────────────── */

  function notifyWebhook(payload) {
    if (!WEBHOOK_URL) return;   /* no-op when URL not set */
    try {
      payload.timestamp = new Date().toISOString();
      payload.url       = window.location.href;
      fetch(WEBHOOK_URL, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify(payload)
      }).catch(function () { /* silently ignore webhook failures */ });
    } catch (e) { /* never break the chat */ }
  }

  /* ──────────────────────────────────────────────
     LOCALSTORAGE PERSISTENCE
  ────────────────────────────────────────────── */

  function saveHistory() {
    try {
      /* Keep last 40 messages to avoid bloating storage */
      var trimmed = _conversation.slice(-40);
      localStorage.setItem(LS_KEY, JSON.stringify(trimmed));
    } catch (e) { /* ignore quota errors */ }
  }

  function loadHistory() {
    try {
      var raw = localStorage.getItem(LS_KEY);
      if (raw) _conversation = JSON.parse(raw) || [];
    } catch (e) { _conversation = []; }
  }

  function restoreHistory() {
    _conversation.forEach(function (m) {
      var wrap = document.getElementById('gtax-msgs');
      var el   = document.createElement('div');
      el.className = 'gtax-msg ' + m.who;
      el.innerHTML = m.html;
      wrap.appendChild(el);
    });
    setTimeout(function () {
      var wrap = document.getElementById('gtax-msgs');
      wrap.scrollTop = wrap.scrollHeight;
    }, 60);
    /* Restore main menu buttons */
    mainMenu();
  }

  /* ──────────────────────────────────────────────
     BOOT
  ────────────────────────────────────────────── */

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

}());
