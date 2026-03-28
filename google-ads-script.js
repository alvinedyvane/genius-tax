/**
 * Genius Tax — Google Ads Campaign Builder (v7 FINAL)
 * Uses AdsApp.mutate() with separate batches — no temp IDs
 * Each step gets real resource names before proceeding
 *
 * Paste into Google Ads > Tools > Bulk Actions > Scripts
 * Click "Authorize" then "Run"
 */

function main() {
  var customerId = AdsApp.currentAccount().getCustomerId().replace(/-/g, '');
  Logger.log('Account: ' + customerId);
  Logger.log('=== Genius Tax Campaign Builder v4 ===');
  Logger.log('');

  var campaignDefs = [
    { name: '[GeniusTax] MTD High-Intent Search',  budgetGBP: 75 },
    { name: '[GeniusTax] MTD Awareness Search',     budgetGBP: 30 },
    { name: '[GeniusTax] Audience-Specific Search',  budgetGBP: 30 },
    { name: '[GeniusTax] Competitor Conquest',       budgetGBP: 15 }
  ];

  // ==========================================
  // STEP 1: Create Budgets (one at a time)
  // ==========================================
  Logger.log('--- Step 1: Creating Budgets ---');
  var budgetRNs = [];
  for (var i = 0; i < campaignDefs.length; i++) {
    var cd = campaignDefs[i];
    var result = AdsApp.mutate({
      campaignBudgetOperation: {
        create: {
          name: cd.name + ' Budget',
          amountMicros: '' + (cd.budgetGBP * 1000000),
          deliveryMethod: 'STANDARD',
          explicitlyShared: false
        }
      }
    });
    if (result.isSuccessful()) {
      budgetRNs.push(result.getResourceName());
      Logger.log('  OK: ' + cd.name + ' Budget -> ' + result.getResourceName());
    } else {
      budgetRNs.push(null);
      Logger.log('  FAIL: ' + cd.name + ' Budget');
      var errs = result.getErrorMessages();
      for (var e = 0; e < errs.length; e++) Logger.log('    ' + errs[e]);
    }
  }

  // ==========================================
  // STEP 2: Create Campaigns (one at a time)
  // ==========================================
  Logger.log('');
  Logger.log('--- Step 2: Creating Campaigns ---');
  var campRNs = [];
  for (var i = 0; i < campaignDefs.length; i++) {
    if (!budgetRNs[i]) {
      Logger.log('  SKIP: ' + campaignDefs[i].name + ' (no budget)');
      campRNs.push(null);
      continue;
    }
    var campObj = {
      name: campaignDefs[i].name,
      advertisingChannelType: 'SEARCH',
      status: 'PAUSED',
      campaignBudget: budgetRNs[i],
      maximizeConversions: {},
      containsEuPoliticalAdvertising: 'DOES_NOT_CONTAIN_EU_POLITICAL_ADVERTISING',
      networkSettings: {
        targetGoogleSearch: true,
        targetSearchNetwork: false,
        targetContentNetwork: false,
        targetPartnerSearchNetwork: false
      }
    };
    var result = AdsApp.mutate({ campaignOperation: { create: campObj } });
    if (result.isSuccessful()) {
      campRNs.push(result.getResourceName());
      Logger.log('  OK: ' + campaignDefs[i].name + ' -> ' + result.getResourceName());
    } else {
      campRNs.push(null);
      Logger.log('  FAIL: ' + campaignDefs[i].name);
      var errs = result.getErrorMessages();
      for (var e = 0; e < errs.length; e++) Logger.log('    ' + errs[e]);
    }
  }

  // ==========================================
  // STEP 3: Location + Language targeting
  // ==========================================
  Logger.log('');
  Logger.log('--- Step 3: Targeting ---');
  for (var i = 0; i < campRNs.length; i++) {
    if (!campRNs[i]) continue;
    // UK location
    AdsApp.mutate({
      campaignCriterionOperation: {
        create: {
          campaign: campRNs[i],
          location: { geoTargetConstant: 'geoTargetConstants/2826' }
        }
      }
    });
    // English language
    AdsApp.mutate({
      campaignCriterionOperation: {
        create: {
          campaign: campRNs[i],
          language: { languageConstant: 'languageConstants/1000' }
        }
      }
    });
    Logger.log('  OK: Targeting set for campaign ' + i);
  }

  // ==========================================
  // STEP 4: Negative Keywords
  // ==========================================
  Logger.log('');
  Logger.log('--- Step 4: Negative Keywords ---');
  var negatives = [
    'free','free trial','jobs','careers','employment','vat','paye','payroll',
    'corporation tax','limited company','what is mtd','how does mtd work',
    'video','youtube','course','training','news','reddit','forum',
    'diy','template','spreadsheet','excel','manual'
  ];
  var negOps = [];
  for (var i = 0; i < campRNs.length; i++) {
    if (!campRNs[i]) continue;
    for (var n = 0; n < negatives.length; n++) {
      negOps.push({
        campaignCriterionOperation: {
          create: {
            campaign: campRNs[i],
            negative: true,
            keyword: { text: negatives[n], matchType: 'BROAD' }
          }
        }
      });
    }
  }
  if (negOps.length > 0) {
    var negResults = AdsApp.mutateAll(negOps);
    var negErrors = 0;
    for (var i = 0; i < negResults.length; i++) {
      if (!negResults[i].isSuccessful()) negErrors++;
    }
    Logger.log('  Negatives: ' + negOps.length + ' ops, ' + negErrors + ' errors');
  }

  // ==========================================
  // STEP 5: Ad Groups
  // ==========================================
  Logger.log('');
  Logger.log('--- Step 5: Creating Ad Groups ---');
  // Map campaign index: 0=High-Intent, 1=Awareness, 2=Audience, 3=Competitor
  var adGroupDefs = [
    { campIdx: 0, name: 'MTD Registration Core',          cpc: 4000000 },
    { campIdx: 0, name: 'MTD Software/Tool',              cpc: 3500000 },
    { campIdx: 0, name: 'MTD Agent/Accountant',            cpc: 3000000 },
    { campIdx: 0, name: 'Deadline Urgency',                cpc: 3500000 },
    { campIdx: 1, name: 'Problem-Aware (HMRC Quarterly)',  cpc: 2000000 },
    { campIdx: 1, name: 'Digital Tax Returns',              cpc: 2000000 },
    { campIdx: 1, name: 'Self-Employed Tax Digital',        cpc: 2500000 },
    { campIdx: 2, name: 'Landlords MTD',                   cpc: 2500000 },
    { campIdx: 2, name: 'Trades MTD',                      cpc: 2000000 },
    { campIdx: 2, name: 'Freelancers & Contractors',       cpc: 2500000 },
    { campIdx: 2, name: 'Small Business MTD',              cpc: 2250000 },
    { campIdx: 3, name: 'TaxScouts Alternatives',          cpc: 3000000 },
    { campIdx: 3, name: 'FreeAgent MTD',                   cpc: 3000000 },
    { campIdx: 3, name: 'Coconut/GoSimpleTax',             cpc: 3000000 }
  ];

  var agMap = {}; // name -> resourceName
  for (var g = 0; g < adGroupDefs.length; g++) {
    var ag = adGroupDefs[g];
    var campRN = campRNs[ag.campIdx];
    if (!campRN) { Logger.log('  SKIP: ' + ag.name); continue; }
    var result = AdsApp.mutate({
      adGroupOperation: {
        create: {
          name: ag.name,
          campaign: campRN,
          status: 'ENABLED',
          type: 'SEARCH_STANDARD',
          cpcBidMicros: '' + ag.cpc
        }
      }
    });
    if (result.isSuccessful()) {
      agMap[ag.name] = result.getResourceName();
      Logger.log('  OK: ' + ag.name);
    } else {
      Logger.log('  FAIL: ' + ag.name);
      var errs = result.getErrorMessages();
      for (var e = 0; e < errs.length; e++) Logger.log('    ' + errs[e]);
    }
  }

  // ==========================================
  // STEP 6: Keywords (batch per ad group)
  // ==========================================
  Logger.log('');
  Logger.log('--- Step 6: Keywords ---');
  var keywordData = {
    'MTD Registration Core': [
      ['mtd registration','EXACT'],['register for mtd','EXACT'],['making tax digital registration','EXACT'],
      ['how to register for making tax digital','EXACT'],['mtd for income tax','EXACT'],['mtd itsa registration','EXACT'],
      ['making tax digital income tax self assessment','EXACT'],['mtd itsa 2026','EXACT'],
      ['register for making tax digital 2026','EXACT'],
      ['mtd registration','PHRASE'],['making tax digital register','PHRASE'],
      ['mtd for income tax registration','PHRASE'],['sign up for mtd','PHRASE'],
      ['making tax digital registration help','BROAD'],['mtd income tax sign up','BROAD'],['register hmrc digital tax','BROAD']
    ],
    'MTD Software/Tool': [
      ['mtd software','EXACT'],['mtd compliant software','EXACT'],['making tax digital software','EXACT'],
      ['best mtd software','EXACT'],['mtd app uk','EXACT'],['mtd bridging software','EXACT'],
      ['hmrc approved mtd software','EXACT'],['mtd software for self employed','EXACT'],
      ['mtd software','PHRASE'],['making tax digital software','PHRASE'],
      ['mtd accounting software','PHRASE'],['mtd bridging software','PHRASE']
    ],
    'MTD Agent/Accountant': [
      ['mtd agent','EXACT'],['mtd accountant','EXACT'],['making tax digital agent','EXACT'],
      ['hmrc authorised mtd agent','EXACT'],['mtd filing agent','EXACT'],['mtd tax agent uk','EXACT'],
      ['find an mtd agent','EXACT'],['mtd compliance service','EXACT'],
      ['mtd agent','PHRASE'],['making tax digital accountant','PHRASE'],['mtd compliance agent','PHRASE']
    ],
    'Deadline Urgency': [
      ['mtd deadline april 2026','EXACT'],['making tax digital deadline','EXACT'],['mtd deadline april 6','EXACT'],
      ['register mtd before april','EXACT'],['mtd deadline help','EXACT'],['late mtd registration','EXACT'],
      ['mtd april 2026 deadline','PHRASE'],['making tax digital april 6','PHRASE'],['register before mtd deadline','PHRASE']
    ],
    'Problem-Aware (HMRC Quarterly)': [
      ['hmrc quarterly reporting','EXACT'],['quarterly tax returns uk','EXACT'],
      ['hmrc digital reporting self employed','EXACT'],['send quarterly updates hmrc','EXACT'],
      ['hmrc making tax digital quarterly','EXACT'],
      ['quarterly tax updates hmrc','BROAD'],['hmrc digital quarterly returns','BROAD'],['quarterly reporting self employed','BROAD']
    ],
    'Digital Tax Returns': [
      ['digital tax return uk','EXACT'],['online self assessment tax return','EXACT'],
      ['submit tax return digitally','EXACT'],['hmrc digital self assessment','EXACT'],
      ['tax return software uk','EXACT'],
      ['digital tax return','PHRASE'],['online tax return self employed','PHRASE']
    ],
    'Self-Employed Tax Digital': [
      ['self employed making tax digital','EXACT'],['mtd self employed','EXACT'],
      ['freelancer making tax digital','EXACT'],['self employed digital tax','EXACT'],
      ['sole trader mtd','EXACT'],['sole trader making tax digital','EXACT'],
      ['self employed mtd','PHRASE'],['making tax digital sole trader','PHRASE'],['freelancer mtd','PHRASE']
    ],
    'Landlords MTD': [
      ['mtd for landlords','EXACT'],['making tax digital landlords','EXACT'],['landlord digital tax return','EXACT'],
      ['landlord mtd software','EXACT'],['buy to let making tax digital','EXACT'],['property income mtd','EXACT'],
      ['rental income mtd','EXACT'],
      ['mtd landlords','PHRASE'],['making tax digital landlord','PHRASE'],['landlord mtd 2026','PHRASE']
    ],
    'Trades MTD': [
      ['mtd for builders','EXACT'],['making tax digital builder','EXACT'],['mtd for plumbers','EXACT'],
      ['mtd for electricians','EXACT'],['mtd for tradesmen','EXACT'],['cis making tax digital','EXACT'],
      ['construction industry scheme mtd','EXACT'],['trades mtd software','EXACT'],
      ['mtd builder','PHRASE'],['mtd plumber','PHRASE'],['mtd electrician','PHRASE'],['tradesmen making tax digital','PHRASE']
    ],
    'Freelancers & Contractors': [
      ['mtd for contractors','EXACT'],['contractor making tax digital','EXACT'],['it contractor mtd','EXACT'],
      ['freelancer mtd software','EXACT'],['consultant mtd registration','EXACT'],['ir35 making tax digital','EXACT'],
      ['mtd contractor','PHRASE'],['freelancer making tax digital','PHRASE'],['contractor mtd 2026','PHRASE']
    ],
    'Small Business MTD': [
      ['small business making tax digital','EXACT'],['small business mtd','EXACT'],
      ['mtd for small business','EXACT'],['small company mtd','EXACT'],
      ['small business mtd','PHRASE'],['mtd for small business','PHRASE']
    ],
    'TaxScouts Alternatives': [
      ['taxscouts alternative','EXACT'],['taxscouts vs','EXACT'],['better than taxscouts','EXACT'],
      ['taxscouts competitor','BROAD']
    ],
    'FreeAgent MTD': [
      ['freeagent mtd','EXACT'],['freeagent making tax digital','EXACT'],['freeagent alternative','EXACT'],
      ['freeagent mtd alternative','PHRASE']
    ],
    'Coconut/GoSimpleTax': [
      ['coconut tax app alternative','EXACT'],['gosimpletax alternative','EXACT'],
      ['gosimpletax making tax digital','EXACT'],['coconut mtd app','PHRASE']
    ]
  };

  var totalKw = 0;
  var totalKwErr = 0;
  for (var agName in keywordData) {
    var agRN = agMap[agName];
    if (!agRN) { Logger.log('  SKIP keywords: ' + agName); continue; }
    var kws = keywordData[agName];
    var kwOps = [];
    for (var k = 0; k < kws.length; k++) {
      kwOps.push({
        adGroupCriterionOperation: {
          create: {
            adGroup: agRN,
            status: 'ENABLED',
            keyword: { text: kws[k][0], matchType: kws[k][1] }
          }
        }
      });
    }
    var kwResults = AdsApp.mutateAll(kwOps);
    var errs = 0;
    for (var r = 0; r < kwResults.length; r++) {
      if (!kwResults[r].isSuccessful()) {
        errs++;
        if (errs <= 2) {
          var msgs = kwResults[r].getErrorMessages();
          for (var e = 0; e < msgs.length; e++) Logger.log('    KW err: ' + msgs[e]);
        }
      }
    }
    totalKw += kws.length;
    totalKwErr += errs;
    Logger.log('  ' + agName + ': ' + kws.length + ' keywords (' + errs + ' errors)');
  }

  // ==========================================
  // STEP 7: RSA Ads
  // ==========================================
  Logger.log('');
  Logger.log('--- Step 7: Responsive Search Ads ---');
  var adData = {
    'MTD Registration Core': {
      h: ['Genius Tax HMRC Auth Agent','Register for MTD Before Apr 6','11 Days Left to Deadline',
          'MTD Done for You £29/mo','Making Tax Digital','HMRC Authorised No Penalties',
          'MTD Registration Tonight','Quarterly Returns Auto-Filed','Self-Employed & Landlords',
          'Cancel Anytime No Lock-in','Trusted by UK Freelancers','Sign Up in Minutes',
          'April 6 Deadline Alert','Start Today Launch Price','Genius Tax Solutions'],
      d: ['HMRC Authorised. We register you for MTD and file quarterly returns. Act now.',
          'From £29/month. Fully managed Making Tax Digital for self-employed.',
          'Don\'t risk a penalty. Our team handles your MTD registration today.',
          'Essential £29/mo. Growth £49/mo. Premium £149/mo. Launch pricing.'],
      url: 'https://geniustax.co.uk/get-started?utm_source=google&utm_medium=cpc&utm_campaign=mtd_high_intent&utm_content=registration',
      p1: 'pricing', p2: 'mtd'
    },
    'MTD Software/Tool': {
      h: ['Best MTD Software for UK','HMRC Approved MTD','Compliant Software Solution',
          'No More App Downloads','We Handle Your MTD Software','Genius Tax Software Incl',
          'No Integration Headaches','MTD Software Sorted for You','Cloud-Based MTD Platform',
          'UK Simplest MTD Solution','From £29/Month','April 6 Deadline Act Now',
          'Software + Support Included','Risk-Free Trial Available','Sign Up Tonight'],
      d: ['MTD doesn\'t need complicated software. Genius Tax handles everything.',
          'HMRC Approved. Cloud-based platform. From £29/month. No separate tool.',
          'You don\'t need to research MTD software. We provide everything you need.',
          'Automatic updates. Cloud-based. HMRC Approved. Fully managed £29/month.'],
      url: 'https://geniustax.co.uk/get-started?utm_source=google&utm_medium=cpc&utm_campaign=mtd_high_intent&utm_content=software',
      p1: 'pricing', p2: 'mtd'
    },
    'MTD Agent/Accountant': {
      h: ['HMRC Authorised MTD Agent','Find Your MTD Agent Here','MTD Accountant Managed',
          'UK-Based MTD Agent','Professional MTD Compliance','Genius Tax MTD Agents',
          'MTD Filing Agent You Trust','MTD Compliance Sorted','We Do HMRC for You',
          'Expert MTD Support','From £29/Month','April 6 Register Now',
          'Compliance Peace of Mind','MTD Done For You','Work With Experts'],
      d: ['Genius Tax is HMRC Authorised Agent. We register, file, manage your MTD.',
          'Professional team handles your quarterly returns and HMRC submissions.',
          'Self-employed? Landlord? We have the expertise. No jargon, no stress.',
          'Compliance sorted from £29/month. Cancel anytime. HMRC Authorised.'],
      url: 'https://geniustax.co.uk/get-started?utm_source=google&utm_medium=cpc&utm_campaign=mtd_high_intent&utm_content=agent',
      p1: 'pricing', p2: 'mtd'
    },
    'Deadline Urgency': {
      h: ['April 6 Deadline 11 Days','MTD Registration Before Apr 6','Late MTD Registration Help',
          'HMRC Deadline Approaching','Avoid Late Filing Penalty','Register for MTD Now',
          'Time Is Running Out','Last 11 Days to Comply','MTD Deadline This Month',
          'Don\'t Miss April 6','Register in Minutes','Genius Tax Fast Setup',
          'Stop Procrastinating','Act Today','Beat the Deadline'],
      d: ['The April 6 MTD deadline is real. Register now and avoid HMRC penalties.',
          '11 days left. Genius Tax gets you set up and compliant overnight.',
          'Late registration? We handle it. Get compliant before April 6.',
          'Fast registration. Instant compliance. Full HMRC filing from £29/month.'],
      url: 'https://geniustax.co.uk/get-started?utm_source=google&utm_medium=cpc&utm_campaign=mtd_high_intent&utm_content=deadline',
      p1: 'pricing', p2: 'mtd'
    },
    'Problem-Aware (HMRC Quarterly)': {
      h: ['HMRC Quarterly Reporting Easy','Digital Quarterly Tax Returns','Self-Employed Quarterly MTD',
          'Streamline HMRC Reporting','Quarterly Returns Managed','Genius Tax Quarterly Service',
          'Auto Quarterly Submissions','We File Quarterly For You','No Spreadsheets Needed',
          'Digital Tax Reporting','Easy HMRC Submissions','From £29/Month',
          'April 6 Deadline Alert','Sign Up Today','Simplify Quarterly Tax'],
      d: ['HMRC requires quarterly digital tax reporting. We handle it automatically.',
          'Genius Tax files your quarterly returns for you. Simple, compliant, done.',
          'No spreadsheets. No manual filings. Automated quarterly HMRC submissions.',
          'From £29/month. Quarterly returns filed automatically before April 6.'],
      url: 'https://geniustax.co.uk/get-started?utm_source=google&utm_medium=cpc&utm_campaign=mtd_awareness&utm_content=quarterly',
      p1: 'pricing', p2: 'mtd'
    },
    'Digital Tax Returns': {
      h: ['Digital Tax Return Software','Online Self-Assessment MTD','Digital Tax Filing Solution',
          'HMRC Digital Tax Returns','Fully Compliant Tax Returns','Genius Tax Digital Platform',
          'Self-Assessment Made Simple','Genius Tax Gets It Done','Online Tax Return Filing',
          'No Manual Returns Required','Digital Records Kept Safe','From £29/Month',
          'Simple Compliant Service','Register Before April 6','Start Your Digital Journey'],
      d: ['Digital tax returns to HMRC don\'t need to be complicated. We help.',
          'Genius Tax handles your digital tax returns. HMRC Authorised. £29/month.',
          'Online self-assessment made simple. Automated filing. Fully compliant.',
          'Digital tax returns, quarterly submissions, annual filings. All £29/mo.'],
      url: 'https://geniustax.co.uk/get-started?utm_source=google&utm_medium=cpc&utm_campaign=mtd_awareness&utm_content=digital_returns',
      p1: 'pricing', p2: 'mtd'
    },
    'Self-Employed Tax Digital': {
      h: ['Self-Employed MTD Service','Sole Trader MTD Service','Freelancer Digital Tax Setup',
          'Self-Employed Tax Compliant','MTD for Self-Employed Easy','Genius Tax Self-Employed',
          'Sole Trader Support Here','Freelancer-Friendly MTD','Self-Employed Tax Simple',
          'Compliance Made Easy','From £29/Month','April 6 Registration Alert',
          'Work With Experts','Genius Tax Specialises','Simple Tax Solution'],
      d: ['Self-employed? Making Tax Digital applies to you. Genius Tax handles it.',
          'Sole traders, freelancers, contractors. We manage your MTD compliance.',
          'Registration, quarterly returns, annual filings. All handled. £29/month.',
          'Freelancer-friendly MTD service. No jargon. HMRC Authorised.'],
      url: 'https://geniustax.co.uk/get-started?utm_source=google&utm_medium=cpc&utm_campaign=mtd_awareness&utm_content=self_employed',
      p1: 'pricing', p2: 'mtd'
    },
    'Landlords MTD': {
      h: ['MTD for Landlords Sorted','Property Income MTD Service','Landlord Digital Tax Filing',
          'Buy-to-Let MTD Compliance','Rental Income MTD Handled','Genius Tax Landlord Focus',
          'HMO Landlord Support Here','Property Tax Compliance Easy','Landlord MTD Made Simple',
          'Multiple Properties Welcome','From £29/Month','April 6 Registration Alert',
          'Landlords Trust Genius Tax','Start Your Compliance','Complete Landlord Solution'],
      d: ['Landlords earning £50K+ must register for MTD by April 6. We handle it.',
          'HMRC Authorised Agent. We register you, file quarterly rental returns.',
          'One property or ten. Genius Tax keeps you MTD compliant. From £29/month.',
          'Buy-to-let, HMO, property investors. Don\'t miss April 6 deadline.'],
      url: 'https://geniustax.co.uk/get-started?utm_source=google&utm_medium=cpc&utm_campaign=mtd_audience&utm_content=landlords',
      p1: 'pricing', p2: 'property'
    },
    'Trades MTD': {
      h: ['MTD for Builders & Trades','Stop Worrying About HMRC','April 6 Register Now',
          'HMRC Authorised Agent Here','MTD Sorted While You Work','CIS Workers MTD Ready',
          'Self-Employed Builder Focus','From £29/Month','No Paperwork. No Jargon.',
          'Plumber? Electrician? Done','11 Days Left Act Now','HMRC Handled For You',
          'Tradesmen Love Genius Tax','Built for Working Hands','Quick Compliance Setup'],
      d: ['Builder, plumber, electrician earning £50K+? MTD applies April 6.',
          'Genius Tax is HMRC Authorised. We register, file quarterly returns.',
          'No accountant jargon. Simple service from £29/month. HMRC compliant.',
          'CIS subcontractors, sole trader trades. MTD made simple. Sign up now.'],
      url: 'https://geniustax.co.uk/get-started?utm_source=google&utm_medium=cpc&utm_campaign=mtd_audience&utm_content=trades',
      p1: 'pricing', p2: 'trades'
    },
    'Freelancers & Contractors': {
      h: ['MTD for Contractors Ready','Freelancer Digital Tax Setup','IT Contractor MTD Service',
          'Consultant MTD Registration','Contractor Compliance Here','Genius Tax Contractor Focus',
          'IR35-Friendly MTD Service','Contractor Tax Simplified','Freelancer Support Available',
          'From £29/Month','April 6 Deadline Alert','Contractors Welcome Here',
          'Compliance Made Easy','Expert Support Available','Full Contractor Solution'],
      d: ['Contractors earning £50K+ need MTD by April 6. Genius Tax handles it.',
          'HMRC Authorised. We file your quarterly returns and manage submissions.',
          'IT contractors, consultants, freelancers. Simple MTD from £29/month.',
          'Compliance from £29/month. Cancel anytime. Contractor-focused team.'],
      url: 'https://geniustax.co.uk/get-started?utm_source=google&utm_medium=cpc&utm_campaign=mtd_audience&utm_content=freelancers',
      p1: 'pricing', p2: 'contractors'
    },
    'Small Business MTD': {
      h: ['Small Business MTD Solution','Growing Business Tax Filing','Small Company Compliance',
          'Digital Tax for Growth','Business Tax Simplified','Genius Tax Small Business',
          'Scalable MTD Service','Small Business Focus','From £29/Month',
          'April 6 Registration Alert','Business Compliance','Expert Small Biz Team',
          'Growing Business Solution','Simple Compliance Setup','Ready to Scale'],
      d: ['Small business earning £50K+? MTD applies from April 6. Get compliant.',
          'Genius Tax manages MTD for growing businesses. HMRC Authorised Agent.',
          'Simple pricing. Compliant service. Grows with your business. £29/month.',
          'Digital tax filing for small businesses. Quarterly returns handled.'],
      url: 'https://geniustax.co.uk/get-started?utm_source=google&utm_medium=cpc&utm_campaign=mtd_audience&utm_content=small_business',
      p1: 'pricing', p2: 'business'
    },
    'TaxScouts Alternatives': {
      h: ['Better Than TaxScouts','TaxScouts Alternative Here','TaxScouts Competitor',
          'Genius Tax vs TaxScouts','Smarter MTD Solution','HMRC Authorised Alternative',
          'Better Pricing Available','TaxScouts Switch Option','Save on MTD Service',
          'From £29/Month','Full Compliance Included','Quality Support Included',
          'Get Started Today','Switch Today Save Now','Make Your Move'],
      d: ['TaxScouts alternative? Genius Tax is HMRC Authorised and cheaper.',
          'Same compliance but better pricing. From £29/month. No contracts.',
          'Switch to Genius Tax. Save money. Same HMRC approval. Better support.',
          'TaxScouts pricing high? HMRC compliance from £29/month.'],
      url: 'https://geniustax.co.uk/get-started?utm_source=google&utm_medium=cpc&utm_campaign=mtd_competitor&utm_content=taxscouts',
      p1: 'pricing', p2: 'switch'
    },
    'FreeAgent MTD': {
      h: ['FreeAgent Alternative Here','Better Than FreeAgent','FreeAgent Competitor',
          'Genius Tax vs FreeAgent','HMRC Authorised Alternative','Simpler MTD Solution',
          'FreeAgent Too Complex?','FreeAgent Switch Option','Save on FreeAgent',
          'From £29/Month','Full HMRC Compliance','Expert Support Included',
          'Get Started Today','Switch Today Save Money','Better Support Available'],
      d: ['FreeAgent alternative? Genius Tax is simpler and HMRC Authorised.',
          'FreeAgent too complicated? Genius Tax handles everything. £29/month.',
          'Switch to Genius Tax. Simpler. Better pricing. Full HMRC compliance.',
          'FreeAgent expensive? HMRC compliance from £29/month. Cancel anytime.'],
      url: 'https://geniustax.co.uk/get-started?utm_source=google&utm_medium=cpc&utm_campaign=mtd_competitor&utm_content=freeagent',
      p1: 'pricing', p2: 'switch'
    },
    'Coconut/GoSimpleTax': {
      h: ['Coconut Alternative Here','GoSimpleTax Alternative','Better Than Coconut App',
          'HMRC Authorised Alternative','Simplify Your MTD Now','Genius Tax vs Coconut',
          'Genius Tax vs GoSimpleTax','Simpler MTD Solution Here','From £29/Month',
          'Full HMRC Compliance','Expert Support Available','Get Started Today',
          'Switch Today Save Now','Better Pricing Available','Make Your Move'],
      d: ['Coconut or GoSimpleTax alternative? Genius Tax is HMRC Authorised.',
          'We simplify MTD compliance. HMRC Authorised. £29/month. No contracts.',
          'Switch to Genius Tax. Simpler platform. Better pricing. Full support.',
          'Coconut or GoSimpleTax user? Better compliance from £29/month.'],
      url: 'https://geniustax.co.uk/get-started?utm_source=google&utm_medium=cpc&utm_campaign=mtd_competitor&utm_content=coconut',
      p1: 'pricing', p2: 'switch'
    }
  };

  var totalAds = 0;
  var totalAdErr = 0;
  for (var agName in adData) {
    var agRN = agMap[agName];
    if (!agRN) { Logger.log('  SKIP ad: ' + agName); continue; }
    var ad = adData[agName];
    var headlines = [];
    for (var h = 0; h < ad.h.length && h < 15; h++) {
      var hl = { text: ad.h[h] };
      if (h === 0) hl.pinnedField = 'HEADLINE_1';
      if (h === 1) hl.pinnedField = 'HEADLINE_2';
      if (h === 2) hl.pinnedField = 'HEADLINE_3';
      headlines.push(hl);
    }
    var descriptions = [];
    for (var d = 0; d < ad.d.length && d < 4; d++) {
      var desc = { text: ad.d[d] };
      if (d === 0) desc.pinnedField = 'DESCRIPTION_1';
      if (d === 1) desc.pinnedField = 'DESCRIPTION_2';
      descriptions.push(desc);
    }
    var result = AdsApp.mutate({
      adGroupAdOperation: {
        create: {
          adGroup: agRN,
          status: 'ENABLED',
          ad: {
            finalUrls: [ad.url],
            responsiveSearchAd: {
              headlines: headlines,
              descriptions: descriptions,
              path1: ad.p1,
              path2: ad.p2
            }
          }
        }
      }
    });
    if (result.isSuccessful()) {
      totalAds++;
      Logger.log('  OK: RSA for ' + agName);
    } else {
      totalAdErr++;
      Logger.log('  FAIL: RSA for ' + agName);
      var errs = result.getErrorMessages();
      for (var e = 0; e < errs.length; e++) Logger.log('    ' + errs[e]);
    }
  }

  // ==========================================
  // FINAL SUMMARY
  // ==========================================
  Logger.log('');
  Logger.log('========================================');
  Logger.log('=== BUILD COMPLETE ===');
  var campCount = 0;
  for (var i = 0; i < campRNs.length; i++) { if (campRNs[i]) campCount++; }
  var agCount = 0;
  for (var k in agMap) agCount++;
  Logger.log('Campaigns: ' + campCount + '/4');
  Logger.log('Ad Groups: ' + agCount + '/14');
  Logger.log('Keywords: ' + totalKw + ' (' + totalKwErr + ' errors)');
  Logger.log('RSA Ads: ' + totalAds + ' (' + totalAdErr + ' errors)');
  Logger.log('========================================');
  Logger.log('All campaigns PAUSED. Enable when ready.');
}
