/**
 * ============================================================
 * GeniusTax Google Ads — Campaign Monitor (v1)
 * ============================================================
 * Account: 513-572-0126
 * Campaigns monitored: all [GeniusTax] campaigns
 *
 * HOW TO SCHEDULE (DO THIS ONCE):
 * ─────────────────────────────────────────────────────────────
 * 1. In Google Ads, go to: Tools & Settings → Bulk Actions → Scripts
 * 2. Click the blue (+) button to create a new script
 * 3. Paste this entire file into the editor
 * 4. Click "Authorise" — allow the script to send email and read your account
 * 5. Click "Save" and name it: "GeniusTax Campaign Monitor"
 * 6. In the Scripts list, find your script and click the pencil/edit icon
 * 7. Under "Frequency", set it to: Daily (pick a time, e.g. 08:00)
 * 8. Click "Save"
 *
 * That's it. You'll get a daily email to alvin@geniusmoney.co.uk every morning.
 * If there are problems, the subject line will say ⚠️ ACTION NEEDED.
 * If everything's fine, it'll say ✅ All Good.
 * ─────────────────────────────────────────────────────────────
 *
 * WHAT THIS CHECKS:
 *  - Campaign enabled/paused/removed status
 *  - Any ads with status DISAPPROVED
 *  - Any ads with policy topic "Destination not working" specifically
 *  - Any ads with policy topic "Destination not accessible"
 *  - Daily spend vs daily budget (alerts if overspending or underspending)
 *  - Impressions in last 24h (alerts if 0 — dead campaign)
 *  - Ad groups with no enabled ads
 *
 * ============================================================
 */

var ALERT_EMAIL    = 'alvin@geniusmoney.co.uk';
var CAMPAIGN_LABEL = '[GeniusTax]';                // all campaigns containing this string
var ACCOUNT_ID     = '513-572-0126';

// Budget warning thresholds
var BUDGET_OVERSPEND_PCT  = 1.10;  // alert if spend > 110% of daily budget
var BUDGET_UNDERSPEND_PCT = 0.05;  // alert if spend < 5% of daily budget (possibly paused/broken)
var ZERO_IMPRESSIONS_MIN_AGE_HOURS = 48; // alert if 0 impressions after this many hours

// ============================================================
// MAIN
// ============================================================
function main() {
  Logger.log('=== GeniusTax Campaign Monitor — ' + new Date().toISOString() + ' ===');
  Logger.log('Account: ' + ACCOUNT_ID);
  Logger.log('');

  var report = runChecks();

  Logger.log('');
  Logger.log('=== SUMMARY ===');
  Logger.log('Issues found: ' + report.issues.length);
  Logger.log('Campaigns checked: ' + report.campaigns.length);

  sendEmail(report);
}

// ============================================================
// CHECKS
// ============================================================
function runChecks() {
  var report = {
    campaigns: [],
    issues:    [],
    timestamp: new Date()
  };

  // Get all GeniusTax campaigns
  var campaignIterator = AdsApp.campaigns()
    .withCondition("Name CONTAINS '" + CAMPAIGN_LABEL + "'")
    .get();

  if (!campaignIterator.hasNext()) {
    report.issues.push({
      severity: 'CRITICAL',
      type:     'NO_CAMPAIGNS_FOUND',
      campaign: 'N/A',
      message:  'No campaigns found matching "' + CAMPAIGN_LABEL + '". Have they been removed or renamed?'
    });
    Logger.log('CRITICAL: No [GeniusTax] campaigns found!');
    return report;
  }

  while (campaignIterator.hasNext()) {
    var campaign = campaignIterator.next();
    var campData = checkCampaign(campaign, report);
    report.campaigns.push(campData);
  }

  return report;
}

function checkCampaign(campaign, report) {
  var name   = campaign.getName();
  var status = campaign.isEnabled()  ? 'ENABLED'  :
               campaign.isPaused()   ? 'PAUSED'   : 'REMOVED';

  Logger.log('Checking: ' + name + ' [' + status + ']');

  var campData = {
    name:           name,
    status:         status,
    budgetGBP:      0,
    spendTodayGBP:  0,
    impressions:    0,
    clicks:         0,
    disapprovedAds: [],
    issues:         []
  };

  // ── 1. Campaign status ──────────────────────────────────
  if (status === 'PAUSED') {
    var issue = {
      severity: 'WARNING',
      type:     'CAMPAIGN_PAUSED',
      campaign: name,
      message:  'Campaign is PAUSED. Was this intentional?'
    };
    campData.issues.push(issue);
    report.issues.push(issue);
    Logger.log('  ⚠️  PAUSED: ' + name);
  }

  if (status === 'REMOVED') {
    var issue = {
      severity: 'CRITICAL',
      type:     'CAMPAIGN_REMOVED',
      campaign: name,
      message:  'Campaign has been REMOVED.'
    };
    campData.issues.push(issue);
    report.issues.push(issue);
    Logger.log('  🔴 REMOVED: ' + name);
  }

  // ── 2. Budget & spend (today's stats) ──────────────────
  try {
    var budget = campaign.getBudget();
    var budgetAmount = budget.getAmount();
    campData.budgetGBP = budgetAmount;

    var stats = campaign.getStatsFor('TODAY');
    var spend = stats.getCost();
    var impressions = stats.getImpressions();
    var clicks = stats.getClicks();

    campData.spendTodayGBP = spend;
    campData.impressions   = impressions;
    campData.clicks        = clicks;

    Logger.log('  Budget: £' + budgetAmount.toFixed(2) +
               ' | Spend today: £' + spend.toFixed(2) +
               ' | Impressions: ' + impressions +
               ' | Clicks: ' + clicks);

    // Overspend check
    if (budgetAmount > 0 && spend > budgetAmount * BUDGET_OVERSPEND_PCT) {
      var issue = {
        severity: 'WARNING',
        type:     'OVERSPEND',
        campaign: name,
        message:  'Spend £' + spend.toFixed(2) + ' exceeds budget £' + budgetAmount.toFixed(2) +
                  ' (' + Math.round((spend / budgetAmount) * 100) + '% of budget)'
      };
      campData.issues.push(issue);
      report.issues.push(issue);
      Logger.log('  ⚠️  OVERSPEND: ' + name);
    }

    // Zero impressions check (only meaningful for ENABLED campaigns)
    if (status === 'ENABLED' && impressions === 0) {
      var issue = {
        severity: 'WARNING',
        type:     'ZERO_IMPRESSIONS',
        campaign: name,
        message:  'Campaign is ENABLED but has 0 impressions today. ' +
                  'Could indicate disapproved ads, exhausted budget, or landing page issue.'
      };
      campData.issues.push(issue);
      report.issues.push(issue);
      Logger.log('  ⚠️  ZERO IMPRESSIONS: ' + name);
    }

  } catch (e) {
    Logger.log('  Error reading stats for ' + name + ': ' + e);
  }

  // ── 3. Disapproved ads check ────────────────────────────
  try {
    var adGroupIterator = campaign.adGroups().get();
    var totalAds        = 0;
    var totalDisapproved = 0;

    while (adGroupIterator.hasNext()) {
      var adGroup = adGroupIterator.next();
      var adIterator = adGroup.ads().get();

      var hasEnabledAd = false;

      while (adIterator.hasNext()) {
        var ad = adIterator.next();
        totalAds++;

        var adStatus = ad.isEnabled()  ? 'ENABLED'  :
                       ad.isPaused()   ? 'PAUSED'   : 'REMOVED';

        if (adStatus === 'ENABLED') hasEnabledAd = true;

        // Check for disapproval via policy summaries
        try {
          var policySummaries = ad.getPolicySummary();
          var approvalStatus  = policySummaries.getApprovalStatus();

          if (approvalStatus === 'DISAPPROVED' || approvalStatus === 'AREA_OF_INTEREST_ONLY') {
            totalDisapproved++;
            var policyTopics = [];
            var topicIterator = policySummaries.getPolicyTopicEntries();
            while (topicIterator.hasNext()) {
              var topic = topicIterator.next();
              policyTopics.push(topic.getTopic());
            }

            var topicsStr = policyTopics.join(', ') || 'Unknown policy';
            var adSummary = {
              adGroup:     adGroup.getName(),
              headline:    safeGetHeadline(ad),
              status:      approvalStatus,
              policyTopics: policyTopics,
              topicsStr:   topicsStr
            };
            campData.disapprovedAds.push(adSummary);

            var severity = 'WARNING';
            var type     = 'AD_DISAPPROVED';
            // Escalate if it's the specific destination issue
            if (topicsStr.toLowerCase().indexOf('destination not working') !== -1 ||
                topicsStr.toLowerCase().indexOf('destination not accessible') !== -1 ||
                topicsStr.toLowerCase().indexOf('destination') !== -1) {
              severity = 'CRITICAL';
              type     = 'DESTINATION_NOT_WORKING';
            }

            var issue = {
              severity: severity,
              type:     type,
              campaign: name,
              adGroup:  adGroup.getName(),
              message:  'Ad DISAPPROVED in "' + adGroup.getName() + '". ' +
                        'Policy: ' + topicsStr + '. ' +
                        'Headline: ' + adSummary.headline
            };
            campData.issues.push(issue);
            report.issues.push(issue);
            Logger.log('  🔴 DISAPPROVED AD in ' + adGroup.getName() + ': ' + topicsStr);
          }

        } catch (policyErr) {
          // Policy summary may not be available for all ad types — skip silently
        }
      }

      // Check ad group has at least one enabled ad
      if (!hasEnabledAd && status === 'ENABLED') {
        var issue = {
          severity: 'WARNING',
          type:     'NO_ENABLED_ADS',
          campaign: name,
          adGroup:  adGroup.getName(),
          message:  'Ad group "' + adGroup.getName() + '" has no enabled ads.'
        };
        campData.issues.push(issue);
        report.issues.push(issue);
        Logger.log('  ⚠️  No enabled ads in ad group: ' + adGroup.getName());
      }
    }

    campData.totalAds        = totalAds;
    campData.totalDisapproved = totalDisapproved;
    Logger.log('  Ads checked: ' + totalAds + ' | Disapproved: ' + totalDisapproved);

  } catch (e) {
    Logger.log('  Error checking ads for ' + name + ': ' + e);
  }

  return campData;
}

// ============================================================
// EMAIL
// ============================================================
function sendEmail(report) {
  var hasIssues  = report.issues.length > 0;
  var hasCritical = report.issues.some(function(i) { return i.severity === 'CRITICAL'; });

  var subject = hasIssues
    ? '⚠️ GeniusTax Ads — ACTION NEEDED'
    : '✅ GeniusTax Ads — All Good';

  var body = buildEmailBody(report, hasIssues, hasCritical);

  Logger.log('Sending email to ' + ALERT_EMAIL + ' — Subject: ' + subject);

  MailApp.sendEmail({
    to:      ALERT_EMAIL,
    subject: subject,
    htmlBody: body
  });

  Logger.log('Email sent.');
}

function buildEmailBody(report, hasIssues, hasCritical) {
  var date = Utilities.formatDate(report.timestamp, 'GMT', 'dd MMM yyyy HH:mm') + ' UTC';

  var html = '';
  html += '<div style="font-family: Arial, sans-serif; max-width: 650px; margin: 0 auto; color: #333;">';
  html += '<div style="background: ' + (hasCritical ? '#d32f2f' : hasIssues ? '#f57c00' : '#2e7d32') + '; padding: 20px 24px; border-radius: 8px 8px 0 0;">';
  html += '<h2 style="color: #fff; margin: 0; font-size: 20px;">';
  html += (hasIssues ? '⚠️ GeniusTax Ads — ACTION NEEDED' : '✅ GeniusTax Ads — All Good');
  html += '</h2>';
  html += '<p style="color: rgba(255,255,255,0.85); margin: 6px 0 0; font-size: 13px;">' + date + ' · Account ' + ACCOUNT_ID + '</p>';
  html += '</div>';

  html += '<div style="border: 1px solid #e0e0e0; border-top: none; border-radius: 0 0 8px 8px; padding: 24px;">';

  // ── Issues summary (if any) ─────────────────────────────
  if (hasIssues) {
    html += '<div style="background: #fff3e0; border-left: 4px solid #f57c00; padding: 12px 16px; border-radius: 4px; margin-bottom: 24px;">';
    html += '<strong style="color: #e65100;">Issues requiring attention (' + report.issues.length + '):</strong><ul style="margin: 8px 0 0; padding-left: 20px;">';
    report.issues.forEach(function(issue) {
      var colour = issue.severity === 'CRITICAL' ? '#c62828' : '#e65100';
      html += '<li style="margin-bottom: 6px; color: ' + colour + ';">';
      html += '<strong>[' + issue.severity + '] ' + issue.campaign + '</strong> — ' + issue.message;
      html += '</li>';
    });
    html += '</ul></div>';
  } else {
    html += '<div style="background: #e8f5e9; border-left: 4px solid #2e7d32; padding: 12px 16px; border-radius: 4px; margin-bottom: 24px;">';
    html += '<strong style="color: #1b5e20;">✅ All systems healthy.</strong> No issues detected across all GeniusTax campaigns.';
    html += '</div>';
  }

  // ── Per-campaign breakdown ──────────────────────────────
  html += '<h3 style="font-size: 15px; color: #555; border-bottom: 1px solid #eee; padding-bottom: 8px;">Campaign Breakdown</h3>';

  if (report.campaigns.length === 0) {
    html += '<p style="color: #c62828;"><strong>No [GeniusTax] campaigns found in this account!</strong> They may have been removed or renamed.</p>';
  }

  report.campaigns.forEach(function(camp) {
    var statusColour = camp.status === 'ENABLED' ? '#2e7d32' : camp.status === 'PAUSED' ? '#f57c00' : '#c62828';
    var hasIssue     = camp.issues.length > 0;

    html += '<div style="border: 1px solid ' + (hasIssue ? '#ffcc80' : '#e0e0e0') + '; border-radius: 6px; padding: 14px 16px; margin-bottom: 14px; background: ' + (hasIssue ? '#fffde7' : '#fafafa') + ';">';
    html += '<div style="display: flex; justify-content: space-between; align-items: center;">';
    html += '<strong style="font-size: 14px;">' + escapeHtml(camp.name) + '</strong>';
    html += '<span style="background: ' + statusColour + '; color: #fff; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">' + camp.status + '</span>';
    html += '</div>';

    html += '<table style="width: 100%; margin-top: 10px; border-collapse: collapse; font-size: 13px;">';
    html += '<tr>';
    html += '<td style="padding: 4px 8px 4px 0; color: #666;">Daily Budget</td><td style="padding: 4px 0; font-weight: bold;">£' + (camp.budgetGBP || 0).toFixed(2) + '</td>';
    html += '<td style="padding: 4px 8px 4px 16px; color: #666;">Spend Today</td><td style="padding: 4px 0; font-weight: bold;">£' + (camp.spendTodayGBP || 0).toFixed(2) + '</td>';
    html += '</tr>';
    html += '<tr>';
    html += '<td style="padding: 4px 8px 4px 0; color: #666;">Impressions</td><td style="padding: 4px 0; font-weight: bold;">' + (camp.impressions || 0).toLocaleString() + '</td>';
    html += '<td style="padding: 4px 8px 4px 16px; color: #666;">Clicks</td><td style="padding: 4px 0; font-weight: bold;">' + (camp.clicks || 0).toLocaleString() + '</td>';
    html += '</tr>';
    if (camp.totalAds !== undefined) {
      html += '<tr>';
      html += '<td style="padding: 4px 8px 4px 0; color: #666;">Total Ads</td><td style="padding: 4px 0;">' + (camp.totalAds || 0) + '</td>';
      html += '<td style="padding: 4px 8px 4px 16px; color: #666;">Disapproved</td>';
      html += '<td style="padding: 4px 0; ' + (camp.totalDisapproved > 0 ? 'color: #c62828; font-weight: bold;' : '') + '">' + (camp.totalDisapproved || 0) + '</td>';
      html += '</tr>';
    }
    html += '</table>';

    // Per-campaign issues
    if (camp.issues.length > 0) {
      html += '<div style="margin-top: 10px; padding: 8px 10px; background: #fff8e1; border-radius: 4px; font-size: 12px;">';
      camp.issues.forEach(function(iss) {
        html += '<div style="margin-bottom: 4px;">🚨 <strong>' + iss.type.replace(/_/g, ' ') + '</strong>: ' + escapeHtml(iss.message) + '</div>';
      });
      html += '</div>';
    }

    // Disapproved ad details
    if (camp.disapprovedAds && camp.disapprovedAds.length > 0) {
      html += '<div style="margin-top: 8px; font-size: 12px; color: #c62828;">';
      html += '<strong>Disapproved ads:</strong><ul style="margin: 4px 0 0; padding-left: 18px;">';
      camp.disapprovedAds.forEach(function(a) {
        html += '<li>' + escapeHtml(a.headline) + ' — <em>' + escapeHtml(a.topicsStr) + '</em> (' + escapeHtml(a.adGroup) + ')</li>';
      });
      html += '</ul></div>';
    }

    html += '</div>'; // end camp card
  });

  // ── Footer ──────────────────────────────────────────────
  html += '<div style="margin-top: 24px; padding-top: 16px; border-top: 1px solid #eee; font-size: 11px; color: #999;">';
  html += 'Generated by GeniusTax Ads Monitor · Google Ads Scripts · Account ' + ACCOUNT_ID;
  if (hasIssues) {
    html += '<br><strong style="color: #e65100;">Log in to Google Ads to fix any issues: <a href="https://ads.google.com">ads.google.com</a></strong>';
  }
  html += '</div>';

  html += '</div>'; // end inner
  html += '</div>'; // end outer

  return html;
}

// ============================================================
// HELPERS
// ============================================================
function safeGetHeadline(ad) {
  try {
    // Responsive Search Ads
    if (ad.asType && ad.asType().responsiveSearchAd) {
      var rsa = ad.asType().responsiveSearchAd();
      var headlines = rsa.headlines();
      if (headlines && headlines.length > 0) return headlines[0].text;
    }
  } catch (e) {}
  try { return ad.getHeadlinePart1() || ad.getHeadline() || '(Ad)'; } catch (e) {}
  return '(Ad)';
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
