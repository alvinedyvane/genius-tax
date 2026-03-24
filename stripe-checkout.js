// =============================================================
// stripe-checkout.js — Genius Tax Stripe Integration
// =============================================================
//
// ██████████████████████████████████████████████████████████
// ██  SETUP — REPLACE THESE VALUES BEFORE GOING LIVE      ██
// ██████████████████████████████████████████████████████████
//
//  1. Log in to https://dashboard.stripe.com/
//  2. Publishable key:
//       Developers → API Keys → "Publishable key"
//       (starts with pk_live_ in production, pk_test_ in test mode)
//  3. Price IDs:
//       Products → [Your Product] → Pricing tab → copy the Price ID
//       (starts with price_)
//  4. Swap out the PLACEHOLDER values in STRIPE_CONFIG below.
//
// =============================================================

const STRIPE_CONFIG = {

  // ──────────────────────────────────────────────────────────
  // 🔑  YOUR STRIPE PUBLISHABLE KEY
  //     Replace with: pk_test_xxxx  (test) or pk_live_xxxx (live)
  // ──────────────────────────────────────────────────────────
  publishableKey: 'pk_test_PLACEHOLDER',

  // ──────────────────────────────────────────────────────────
  // 💷  STRIPE PRICE IDs  (one per plan)
  //     Create a Product in Stripe with a recurring price,
  //     then paste the price_xxxx ID here.
  // ──────────────────────────────────────────────────────────
  prices: {
    standard:  'price_PLACEHOLDER_29',   // £29/month  — Standard plan
    earlyBird: 'price_PLACEHOLDER_49',   // £49/month  — MTD Compliance Early Bird  ← PRIMARY CONVERSION
    premium:   'price_PLACEHOLDER_149'   // £149/month — Premium plan
  },

  // ──────────────────────────────────────────────────────────
  // 🔗  REDIRECT URLs
  //     successUrl: where Stripe sends the customer after payment
  //     cancelUrl:  where Stripe sends them if they hit "Back"
  // ──────────────────────────────────────────────────────────
  successUrl: 'https://geniustax.co.uk/?success=true',
  cancelUrl:  'https://geniustax.co.uk/#pricing'

};

// =============================================================
// STRIPE INSTANCE  (lazy-initialised on first checkout click)
// =============================================================

let _stripe = null;

function getStripe() {
  if (!_stripe) {
    if (STRIPE_CONFIG.publishableKey.includes('PLACEHOLDER')) {
      console.warn(
        '[GeniusTax] ⚠️  Stripe publishable key is still a placeholder. ' +
        'Checkout will fall back to the signup form until you swap in a real key.'
      );
    }
    _stripe = Stripe(STRIPE_CONFIG.publishableKey); // eslint-disable-line no-undef
  }
  return _stripe;
}

// =============================================================
// CHECKOUT HANDLER
// =============================================================
// Called by the onclick on each pricing card button.
// plan: 'standard' | 'earlyBird' | 'premium'
// buttonEl: the <button> DOM element (for loading state)
// =============================================================

window.gtaxCheckout = function (plan, buttonEl) {
  var priceId = STRIPE_CONFIG.prices[plan];

  // ── Placeholder / not-yet-configured guard ──────────────────
  // While keys are placeholders, smoothly scroll to the signup
  // form so the page still converts.
  if (!priceId || priceId.includes('PLACEHOLDER') || STRIPE_CONFIG.publishableKey.includes('PLACEHOLDER')) {
    console.info('[GeniusTax] Stripe not yet configured — redirecting to signup form instead.');
    _scrollToSignup();
    return;
  }

  // ── Show loading state on the button ───────────────────────
  var originalHTML = buttonEl.innerHTML;
  buttonEl.disabled = true;
  buttonEl.setAttribute('aria-busy', 'true');
  buttonEl.innerHTML =
    '<span class="gtax-spinner" aria-hidden="true"></span>' +
    '<span> Redirecting…</span>';

  // ── Redirect to Stripe Checkout ─────────────────────────────
  // Uses stripe.redirectToCheckout() with a price ID.
  // This is a client-side-only flow — no backend needed.
  //
  // NOTE: If you later add a backend, replace this with a
  // server-side Checkout Session for more control (e.g. applying
  // trial periods, metadata, custom emails).
  // ─────────────────────────────────────────────────────────────
  getStripe()
    .redirectToCheckout({
      lineItems: [{ price: priceId, quantity: 1 }],
      mode: 'subscription',
      successUrl: STRIPE_CONFIG.successUrl,
      cancelUrl:  STRIPE_CONFIG.cancelUrl
    })
    .then(function (result) {
      if (result.error) {
        // Redirect failed — restore button and show a brief error
        console.error('[GeniusTax] Stripe error:', result.error.message);
        _restoreButton(buttonEl, originalHTML);
        _showButtonError(buttonEl, 'Something went wrong. Please try again or contact us at hello@geniustax.co.uk');
      }
      // If we reach here without an error it means the redirect happened —
      // the user has left the page so no further action is needed.
    })
    .catch(function (err) {
      console.error('[GeniusTax] Unexpected error:', err);
      _restoreButton(buttonEl, originalHTML);
      _showButtonError(buttonEl, 'Unable to open checkout. Please refresh and try again.');
    });
};

// =============================================================
// HELPERS
// =============================================================

function _restoreButton(btn, html) {
  btn.disabled = false;
  btn.removeAttribute('aria-busy');
  btn.innerHTML = html;
}

function _showButtonError(btn, msg) {
  var existing = btn.parentNode.querySelector('.gtax-checkout-error');
  if (existing) existing.remove();

  var errEl = document.createElement('p');
  errEl.className = 'gtax-checkout-error';
  errEl.style.cssText =
    'color:#c00;font-size:0.78rem;margin-top:0.5rem;text-align:center;line-height:1.4;';
  errEl.textContent = msg;
  btn.parentNode.insertBefore(errEl, btn.nextSibling);
  setTimeout(function () { if (errEl.parentNode) errEl.remove(); }, 7000);
}

function _scrollToSignup() {
  var target = document.getElementById('signup');
  if (!target) return;
  var navEl = document.querySelector('.nav');
  var navH  = navEl ? navEl.offsetHeight : 0;
  var y     = target.getBoundingClientRect().top + window.scrollY - navH - 16;
  window.scrollTo({ top: y, behavior: 'smooth' });
}

// =============================================================
// THANK-YOU PAGE DETECTION
// =============================================================
// After successful payment Stripe appends ?success=true to the
// successUrl. This block detects that and reveals the thank-you
// banner, then cleans the URL so a page refresh doesn't re-show it.
// =============================================================

document.addEventListener('DOMContentLoaded', function () {
  var params = new URLSearchParams(window.location.search);

  if (params.get('success') === 'true') {
    var thankYou = document.getElementById('gtax-thankyou');
    if (thankYou) {
      thankYou.style.display = 'flex';
      // Small delay so the page layout settles before scrolling
      setTimeout(function () {
        thankYou.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 200);
    }
    // Clean the URL (removes ?success=true without a full reload)
    if (window.history && window.history.replaceState) {
      history.replaceState(null, document.title, window.location.pathname);
    }
  }
});
