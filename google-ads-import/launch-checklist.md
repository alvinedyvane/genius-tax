# 🚀 Genius Tax Google Ads Campaign — Launch Checklist

**Target Launch Date:** March 25, 2026 (Tonight)  
**Campaign Duration:** 11 days (March 25 – April 6, 2026)  
**Budget:** £100/day recommended (£1,100 total)  
**Goal:** 14–35 qualified MTD signups before April 6 deadline

---

## 📋 PRE-LAUNCH SETUP (Complete Before Import)

### Account & Administrative
- [ ] Create Google Ads account or confirm access to existing account
- [ ] Ensure billing is set up and payment method is active
- [ ] Link Google Ads to Google Search Console (geniustax.co.uk)
- [ ] Link Google Ads to GA4 property
- [ ] Enable auto-tagging in account settings (Tools → Settings → Account settings → Auto-tagging)

### Conversion Tracking Setup ⚠️ CRITICAL
- [ ] Install Google Tag Manager (GTM) on geniustax.co.uk
  - Add GTM container snippet to `<head>` and `<body>` of all pages
- [ ] Create Google Ads conversion action:
  - Go to: **Tools → Measurement → Conversions → + New Conversion**
  - Type: **Website**
  - Name: `MTD Signup - Stripe`
  - Category: **Purchase**
  - Value: **Use different values** (enable conversion value tracking)
  - Currency: **GBP**
  - Count: **One per click**
  - Click-through window: **30 days**
  - View-through window: **1 day** (for Display/PMax)
  - Attribution model: **Data-driven** (or Last click if insufficient data)
- [ ] Copy the **Global Site Tag (gtag.js)** from conversion settings
- [ ] Add gtag.js snippet to `<head>` of all website pages
- [ ] Create GTM tag for conversion firing:
  - Tag type: **Google Ads Conversion Tracking**
  - Conversion ID & Label: Copy from conversion action created above
  - Trigger: **URL contains** `/thank-you` OR `/success` OR event `purchase`
- [ ] Test conversion tracking:
  - Submit test checkout through Stripe
  - Verify thank-you page loads
  - Check GTM debugger console (should fire conversion event)
  - Allow 2–6 hours, then check Google Ads → Conversions tab for test conversion

### Landing Page Optimisation
- [ ] Add urgency banner to homepage:
  - Text: `⚠️ MTD Deadline: April 6, 2026 — [X] Days Left | Register Now`
  - Sticky: Yes (stays on scroll)
  - Background colour: #FF4444 (red) or amber
  - Update countdown daily
- [ ] Verify above-fold CTA on mobile:
  - Headline visible: "MTD Compliance — Done For You" or "Register Before April 6"
  - CTA button text: "Get Started Tonight" (not "Learn More")
  - Button size: 48px min height (thumb-tappable)
  - CTA links to: `/get-started` or Stripe checkout
- [ ] Add trust signals above CTA:
  - HMRC Authorised Agent badge (high visibility)
  - "Join [X] self-employed workers already compliant"
  - Security badges (padlock, SSL certificate)
  - "Cancel Anytime" text
- [ ] Pricing page:
  - Display all 3 tiers: Essential (£29/mo), Growth (£49/mo early bird), Premium (£149/mo)
  - Highlight Growth as "Most Popular"
  - Show annual pricing with savings: "£199/yr = just £16.58/mo"
  - Include CTA buttons to checkout for each plan
- [ ] Mobile optimisation:
  - Test on multiple devices (iPhone, Android, tablet)
  - Ensure page load <3 seconds (test via PageSpeed Insights)
  - Verify all CTAs are clickable and not hidden below fold
  - Ensure phone number is clickable (use `tel:` link if applicable)
- [ ] Stripe checkout setup:
  - Create products in Stripe for Essential, Growth, Premium plans
  - Set up redirect to `/thank-you` on success
  - Set up redirect to `/cancelled` on cancel
  - Enable automatic email receipts

---

## 📥 GOOGLE ADS EDITOR IMPORT SEQUENCE

### Step 1: Download & Install Google Ads Editor
- [ ] Download Google Ads Editor (Windows or Mac)
- [ ] Install and launch
- [ ] Sign in with your Google Ads account
- [ ] Allow access to all linked accounts
- [ ] Create a backup before importing (File → Backup/Export)

### Step 2: Import Campaigns
- [ ] Open the file: **campaigns.csv**
- [ ] In Google Ads Editor:
  - File → Import → Import from CSV
  - Select **campaigns.csv**
  - Preview settings:
    - Encoding: UTF-8
    - Delimiter: Comma
    - Line terminator: LF
    - Quote character: Double quote
  - Click **Import**
- [ ] Verify import:
  - 6 campaigns should appear: MTD High-Intent, Awareness, Audience-Specific, Competitor, Remarketing, PMax
  - Status: All **Paused** (as expected — we'll activate manually after validation)
  - Location: United Kingdom
  - Language: English
  - Daily budget: Visible and correct

### Step 3: Import Ad Groups
- [ ] Open the file: **ad-groups.csv**
- [ ] In Google Ads Editor:
  - File → Import → Import from CSV
  - Select **ad-groups.csv**
  - Preview settings: Same as above
  - Click **Import**
- [ ] Verify import:
  - 14 ad groups appear nested under correct campaigns
  - Max CPC values visible (£2.00–£4.00 depending on ad group)
  - Status: All **Enabled**

### Step 4: Import Keywords
- [ ] Open the file: **keywords.csv**
- [ ] In Google Ads Editor:
  - File → Import → Import from CSV
  - Select **keywords.csv**
  - Preview settings: Same as above
  - Click **Import**
- [ ] Verify import:
  - 120+ keywords distributed across ad groups
  - Match types visible: **Exact** (in brackets), **Phrase** (in quotes), **Broad** (no markup)
  - Max CPC: Inherited from ad group or custom per keyword
  - Status: All **Enabled**

### Step 5: Import Negative Keywords
- [ ] Open the file: **negative-keywords.csv**
- [ ] In Google Ads Editor:
  - File → Import → Import from CSV
  - Select **negative-keywords.csv**
  - Preview settings: Same as above
  - Click **Import**
- [ ] Verify import:
  - Campaign-level negatives: Appear at campaign level (no ad group specified)
  - Global negatives (free, jobs, careers, etc.): Applied to all campaigns
  - Competitor negatives: Applied to competitor campaigns
  - Total: 180+ negative keywords across all campaigns

### Step 6: Import Ads (Responsive Search Ads)
- [ ] Open the file: **ads.csv**
- [ ] In Google Ads Editor:
  - File → Import → Import from CSV
  - Select **ads.csv**
  - Preview settings: Same as above
  - Click **Import**
- [ ] Verify import:
  - 16 responsive search ads (one or more per ad group)
  - Each RSA displays:
    - 15 headlines (first 3 pinned)
    - 4 descriptions (first 2 pinned)
    - Final URL with UTM parameters
    - Display paths (Path 1 & 2)
  - Status: All **Enabled**

### Step 7: Import Extensions
- [ ] **Sitelink Extensions:**
  - Import **extensions.csv** (sitelink rows only)
  - Each sitelink includes: text, description 1, description 2, final URL
  - 6 sitelinks per campaign (Essential, Growth, Premium, How It Works, About, Get Started)
- [ ] **Callout Extensions:**
  - Import callout rows from **extensions.csv**
  - 10+ callouts per campaign (HMRC Authorised, Pricing, Deadline, etc.)
- [ ] **Structured Snippets:**
  - Import structured snippet rows (Services, Types)
  - Header: "Services" / "Types"
  - Values: Comma-separated (e.g., "MTD Registration, Quarterly Returns, HMRC Submission")
- [ ] **Price Extensions:**
  - Import price extension rows
  - 5 price points (Essential monthly/annual, Growth, Premium)
  - Currency: GBP
  - Include descriptions and final URLs

### Step 8: Review in Editor
- [ ] Click **Campaign** view
- [ ] Expand each campaign to review:
  - [ ] 6 campaigns total, all **Paused**
  - [ ] 14 ad groups total, all **Enabled**
  - [ ] 120+ keywords, all **Enabled**
  - [ ] 180+ negative keywords applied
  - [ ] 16 RSAs with headlines/descriptions visible
  - [ ] Sitelinks, callouts, structured snippets attached to campaigns
- [ ] Check for import warnings/errors:
  - Look for red exclamation marks (!)
  - Resolve any validation issues before posting
  - Common issues: Invalid URLs, character limits exceeded, missing required fields

### Step 9: Validate Quality Score & Ad Strength
- [ ] For each ad group, review:
  - **Quality Score**: Target >6/10 (visible in Keywords tab)
  - **Ad Strength**: Should display "Excellent" or "Good"
    - If "Poor" or "Fair": Improve headlines/descriptions
    - Add more headline variations if needed
- [ ] For each RSA:
  - Verify all 15 headlines are present
  - Verify all 4 descriptions are present
  - Check character limits:
    - Headline: 30 characters max
    - Description: 90 characters max
  - If exceeded, trim copy or use Google's suggested edits

### Step 10: Pre-Launch Checklist
- [ ] UTM parameters in all Final URLs:
  - Format: `https://geniustax.co.uk/get-started?utm_source=google&utm_medium=cpc&utm_campaign={CAMPAIGN}&utm_content={ADGROUP}&utm_term={keyword}&gclid={gclid}`
  - `{keyword}` is auto-filled by Google
  - `{gclid}` requires auto-tagging enabled ✓
- [ ] Verify landing page:
  - [ ] Homepage loads and displays urgency banner
  - [ ] `/get-started` page visible and functional
  - [ ] `/pricing` page displays all 3 tiers
  - [ ] `/thank-you` page displays after Stripe checkout success
  - [ ] Mobile optimisation confirmed (test on multiple devices)
- [ ] Verify conversion tracking firing:
  - [ ] Submit test transaction
  - [ ] Allow 2–6 hours for conversion to appear in Google Ads
  - [ ] Check Conversions column (Tools → Measurement → Conversions)
- [ ] Create a saved backup:
  - File → Export (save as `campaigns-pre-launch-backup.csv`)

---

## 🚀 LAUNCH (Day 1 — Tonight, March 25)

### Final Activation Steps
- [ ] In Google Ads Editor:
  - Right-click on each campaign (all 6)
  - Select **Change Status → Enabled**
  - Status should change from **Paused** to **Enabled**
  - All campaigns are now **Live**
- [ ] Click **Post** in top-right corner
- [ ] Confirm: "Post changes to Google Ads?"
  - This uploads all campaigns, ad groups, keywords, ads, extensions to live
  - Duration: 15 seconds – 5 minutes
- [ ] Allow 2–24 hours for ads to clear Google review
  - Most MTD-related ads clear within 2–4 hours
  - Monitor Ads tab in Google Ads interface for approval status

### Launch Confirmation
- [ ] Log into Google Ads (web interface)
- [ ] Navigate to **Campaigns** tab
- [ ] Verify all 6 campaigns show status **Enabled** (green light)
- [ ] Click into Campaign 1 to verify:
  - Campaign daily budget: £75
  - Bid strategy: Maximize Conversions
  - Location: United Kingdom
  - Language: English
- [ ] Check **Ads & Extensions** tab:
  - All 16 RSAs show status **Eligible** (blue check)
  - Sitelinks visible beneath sample ads
  - Callouts visible
- [ ] Check **Keywords** tab:
  - All keywords show status **Enabled**
  - No warnings (red alerts)
- [ ] Check **Conversions** tab (Tools → Measurement):
  - Conversion action "MTD Signup - Stripe" visible
  - Status: Collecting data

---

## 📊 DAYS 2–5: IMMEDIATE OPTIMISATION

### Day 2 — Morning Check
- [ ] Log into Google Ads
- [ ] Review **Campaigns** dashboard:
  - Impressions: Check if any campaign <100 impr on Day 1 (if so, raise bids by 20%)
  - CTR: Aim for >3% on Search (anything <2% needs ad copy review)
  - CPC: Monitor for runaway bids (if >£5, adjust bid caps)
- [ ] Check **Search Terms** report:
  - Identify irrelevant or brand competitor terms
  - Add top irrelevant terms as negatives immediately (e.g., "free mtd", "mtd jobs")
- [ ] Verify conversion tracking:
  - Check Conversions column
  - Should show 0–2 conversions if traffic flowing (if 0 after 100 clicks, investigate GTM)

### Day 3
- [ ] Confirm >5 conversions tracked ✓
- [ ] Switch bidding strategy (Campaign → Settings):
  - Campaign 1 (High-Intent): **Maximize Conversions** (already set)
  - Campaign 2 (Awareness): Switch from Maximize Clicks → **Maximize Conversions**
  - Campaign 3 (Audience): Already set to Maximize Conversions ✓
- [ ] Pause underperforming ad groups:
  - Any ad group: >20 clicks, 0 conversions → **Pause**
  - Check Ad Group performance (Campaign → Ad Groups tab)
  - Status dropdown → Pause
- [ ] Review ad strength:
  - Navigate to each ad group
  - Check responsive search ads for "Best" label (indicates strong performer)
  - Pin those headlines to position 1 for consistency

### Day 4
- [ ] Launch Campaign 2 (MTD Awareness Search) if not yet live
  - Verify budget, bidding, location, language
  - Check ad approval status in Ads tab
- [ ] Quality Score audit:
  - Campaign → Keywords tab
  - Look for Quality Score <5/10
  - For low scores: Rewrite ad copy, improve landing page relevance
  - Consider pausing low-QS keywords if CPC is uneconomical
- [ ] Display Remarketing setup:
  - If >100 site visitors accumulated, activate Campaign 5
  - Ensure audience list is populated
  - Review Display Network audience bid modifiers

### Day 5
- [ ] Deep Search Terms audit:
  - Campaign → Keywords → Search Terms
  - Identify top converting searches
  - Create exact match keywords from best-converting queries
  - Add non-converting high-volume searches as negatives
- [ ] Device performance analysis:
  - Campaign → Devices (if visible)
  - Compare CPA by device (mobile vs desktop vs tablet)
  - If mobile CPA 2x desktop CPA: Add -20% mobile bid adjustment
- [ ] Competitor campaign validation:
  - Campaign 4 (Competitor): Check CPA sustainability
  - If CPA >£150 and CTR <1.5%: Consider pausing until Day 6 when budget scales

---

## 📈 DAYS 6–11: SCALE & DEADLINE PUSH

### Day 6 — Scale Decision Point
- [ ] Compare performance vs targets:
  - Current CPA < £80? **✓ SCALE**
  - Current CPA £80–£120? Scale cautiously (increase by 30%)
  - Current CPA >£120? Hold budget, optimise further before scaling
- [ ] If scaling:
  - Increase Campaign 1 daily budget: £75 → £120
  - Increase Campaign 3 daily budget: £30 → £45
  - Increase Campaign 6 (PMax): £30 → £40
  - New daily total: £100 → £150+
- [ ] Double budget on best-performing ad groups (highest conversion rate):
  - Adjust Max CPC: Increase by 15–20%
  - Increase impressions, maintain CPA
- [ ] Increase bids on high-potential keywords:
  - Keywords with <50% Impression Share
  - CPC keywords: Increase by 10–15%

### Day 7–9 — Bid Strategy Evolution
- [ ] Confirm >20 conversions tracked ✓
- [ ] Switch Campaign 1 to Target CPA:
  - Campaign → Settings → Bid strategy
  - Change to: **Target CPA £70**
  - (Set 10% below current actual CPA to improve efficiency)
- [ ] Implement countdown timer on ads (if available):
  - Ads → Responsive Search Ads → Edit
  - Add countdown customiser (Ad Customiser feature):
    - Field name: `COUNTDOWN`
    - Format: `COUNTDOWN("2026/04/06 00:00:00","en-GB")`
  - Include in headline rotation: "Last {=COUNTDOWN} — Register Now"
- [ ] Daily reviews:
  - Check CPA trend (should improve or stabilise with Target CPA)
  - Monitor Impression Share (aim >70%)
  - Adjust Target CPA if needed (+/- £5–10)

### Day 10–11 — FINAL PUSH (April 4–5)
**This is the money window. Maximum urgency messaging. Maximum budget.**

- [ ] Increase all campaigns to maximum daily budgets:
  - Campaign 1: £120 → £150
  - Campaign 2: £30 → £50
  - Campaign 3: £45 → £60
  - Campaign 4: £15 → £20
  - Campaign 5 & 6: £15 & £40 → £50 each
  - **Total daily: £180–£200**
- [ ] Increase all keyword bids by 20–30%:
  - Broad match: +30% (capture all volume)
  - Phrase match: +20% (precision + scale)
  - Exact match: +15% (protect best keywords)
- [ ] Update all ad copy to deadline urgency:
  - Edit responsive search ads
  - Replace generic headlines with: "Last 48 Hours", "April 6 Deadline Tomorrow"
  - Update descriptions: "Don't Miss Registration Deadline"
  - Expected ad approval: 1–2 hours
- [ ] Update website urgency banner:
  - Change countdown to "FINAL 2 DAYS"
  - CTA text: "REGISTER NOW — Deadline Tomorrow"
  - Background: Bright red (#FF0000)
- [ ] Email final push (if you have email list):
  - Subject: "MTD Deadline: 48 Hours Left — Register Before April 6"
  - Target: Website visitors, abandoned checkout
- [ ] Monitor live dashboard:
  - Check impressions, clicks every 2 hours
  - If CPC spikes >£6: Lower bids slightly to maintain efficiency
  - If impression share drops: Raise bids to capture more volume

### April 6 — Deadline Day (Last Hours)
- [ ] Keep campaigns active until 23:59 GMT (last possible registration moment)
- [ ] Monitor clicks/conversions in real-time
- [ ] Max out bids on highest-intent campaigns (High-Intent Search)
- [ ] Update messaging: "You Have Until Midnight — Register Now"
- [ ] At 23:59 (or after last conversion): Pause all campaigns

---

## 📊 POST-CAMPAIGN ANALYSIS (April 7+)

### Day 1 Post-Deadline
- [ ] Pause all deadline-urgency ads and campaigns
- [ ] Download full campaign report (Campaigns → Download)
- [ ] Calculate key metrics:
  - **Total ad spend**: Sum of all campaign daily budgets
  - **Total conversions**: Count of all "MTD Signup" events
  - **Blended CPA**: Total spend ÷ Total conversions
  - **ROAS**: (Total revenue from signups) ÷ Total spend
  - **LTV**: (Avg customer monthly revenue) × (Avg retention months)
  - **Payback period**: Total spend ÷ (Monthly revenue generated)

### Decision: Continue or Pivot?
- [ ] If CPA < £80: Plan next phase (post-April 6 retention campaigns, expansion ads)
- [ ] If CPA £80–£120: Acceptable but watch LTV closely
- [ ] If CPA >£120: Investigate what went wrong, optimise, and plan Q2 campaign

### Post-Deadline Messaging (for late registrations)
- [ ] Create new campaign: "[GeniusTax] Missed Deadline — Late Registration Support"
- [ ] Target: People searching "MTD late registration", "missed mtd deadline", etc.
- [ ] Messaging: "Already missed the deadline? We can help with late registration and penalty mitigation."
- [ ] Link to separate landing page: `/missed-deadline` explaining late filing options
- [ ] Budget: £20/day (lower priority)

---

## ✅ SUCCESS METRICS

**Target Campaign Goals (11-day sprint):**
- [ ] 14–35 qualified signups (5–8% conversion rate)
- [ ] CPA ≤ £100 (preferably £70–£80)
- [ ] CTR ≥ 3% on Search campaigns
- [ ] Quality Score ≥ 6/10 on most keywords
- [ ] Ad Strength: "Excellent" or "Good" on all RSAs
- [ ] Conversion tracking operational (firing on 95%+ of completions)

**Post-Campaign Success:**
- [ ] Payback period ≤ 3 months (spend recovers within LTV window)
- [ ] Monthly recurring revenue from campaign ≥ £500
- [ ] Customer retention >60% at 3 months

---

## 🆘 TROUBLESHOOTING

### Conversions Not Tracking
1. Check GTM debugger:
   - Visit site in Chrome
   - Open DevTools (F12) → Google Tag Assistant
   - Submit test transaction
   - Does GTM fire the "purchase" or conversion event?
2. Check Stripe webhook:
   - Log into Stripe dashboard
   - Webhooks → Verify `checkout.session.completed` is configured
   - Check logs for success/failure
3. Check thank-you page:
   - After checkout, does user see `/thank-you` page?
   - If redirected elsewhere, update Stripe success URL
4. Wait 2–6 hours:
   - Google Ads takes up to 6 hours to show conversions
   - Check Conversions tab later

### Low Quality Scores (<5/10)
1. Improve ad copy:
   - Ensure headlines/descriptions match keyword theme
   - For keyword "mtd software", ad headline should include "software"
2. Improve landing page:
   - All traffic to same `/get-started` page?
   - Consider separate landing pages by keyword theme (landlords, trades, etc.)
3. Increase bid:
   - Sometimes low QS is due to low bid (not enough impressions)
   - Raise bid by 20%, allow 1 week, re-check

### Ads Not Approving (Disapproved)
1. Check disapproval reason:
   - Campaign → Ads & Extensions → Click disapproved ad
   - Read Google's feedback
2. Common issues:
   - **"Misleading claim"**: If claiming "free" or "no fees", verify it's true
   - **"Prohibited content"**: Ensure no unsubstantiated tax advice
   - **"Destination URL mismatch"**: Headline says "£29/month" but landing page says £39
3. Fix and resubmit:
   - Edit ad copy
   - Click Submit for review
   - Allow 2–4 hours for re-approval

### CPA Too High (>£150)
1. Pause underperforming ad groups:
   - Any ad group with CPA >£200: Pause for 24 hours
2. Reallocate budget to winners:
   - Campaigns/ad groups with CPA <£80: Increase by 20–30%
3. Improve landing page:
   - Test different headlines on `/get-started`
   - A/B test CTA button colour (red vs blue)
   - Reduce form fields (fewer fields = higher conversion)
4. Check bid strategy:
   - If using "Maximize Clicks", switch to "Maximize Conversions"
   - Maximize Conversions optimises for cost-per-conversion

### Impression Share Below 30%
1. Increase daily budget
   - Raise campaign budget by £10–20
2. Increase bids:
   - Keywords with <50% IS: Raise CPC by 15–20%
   - Broad match keywords: Raise by 20–30%
3. Expand keyword coverage:
   - Add new exact match keywords from Search Terms report
   - Lower match type restrictions

---

## 📞 SUPPORT & ESCALATION

### If Issues Persist
- Review Google Ads Help: https://support.google.com/google-ads
- Check Google Ads Editor help: https://support.google.com/google-ads/answer/35299
- Verify HMRC Authorised status on geniustax.co.uk (may affect ad approval)

---

## 🎯 QUICK REFERENCE — DAILY CHECKLIST (Print & Post)

```
EVERY MORNING (5 min check):
[ ] Log into Google Ads
[ ] Check Impressions (growing?)
[ ] Check CTR (>3% target?)
[ ] Check CPC (£2–£5 target?)
[ ] Check Conversions (firing?)
[ ] Check Quality Score (>6/10?)
[ ] Check search terms for negatives

IF METRICS OFF TARGET:
[ ] Impressions low? Raise bids +20%
[ ] CTR low? Rewrite ads
[ ] CPC high? Lower bids or adjust targets
[ ] No conversions? Check landing page + GTM
[ ] Low QS? Improve ad relevance

WEEKLY (Deeper dive):
[ ] Device performance analysis
[ ] Competitor campaign ROI check
[ ] Pause zero-converting ad groups
[ ] Update negative keywords

DAYS 6–11 (Scale & Push):
[ ] Compare CPA vs £80 target
[ ] Scale budget if CPA <£80
[ ] Increase bids 20–30%
[ ] Update urgency messaging
[ ] Monitor cash burn rate
```

---

**Prepared by:** Genius Tax Google Ads Team  
**Last Updated:** March 25, 2026  
**Questions?** Review the full campaign plan at ~/Projects/genius-tax/google-ads-plan.md

