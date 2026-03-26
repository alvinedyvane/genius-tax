/**
 * Genius Tax — Add Wales to Campaigns (one-time run)
 * England is already set. This just adds Wales (20343).
 * Run once, no schedule needed.
 */

function main() {
  Logger.log('=== Adding Wales to All GeniusTax Campaigns ===');

  var campaigns = [
    '[GeniusTax] MTD High-Intent Search',
    '[GeniusTax] MTD Awareness Search',
    '[GeniusTax] Audience-Specific Search',
    '[GeniusTax] Competitor Conquest'
  ];

  var WALES_GEO = 'geoTargetConstants/20343';

  for (var i = 0; i < campaigns.length; i++) {
    var campName = campaigns[i];
    Logger.log('--- ' + campName + ' ---');

    var query = "SELECT campaign.resource_name FROM campaign WHERE campaign.name = '" + campName + "'";
    var rows = AdsApp.search(query);

    if (!rows.hasNext()) {
      Logger.log('  NOT FOUND — skipping');
      continue;
    }

    var campRN = rows.next().campaign.resourceName;
    Logger.log('  Campaign: ' + campRN);

    // Check if Wales already exists
    var checkQuery = "SELECT campaign_criterion.resource_name, campaign_criterion.location.geo_target_constant " +
                     "FROM campaign_criterion " +
                     "WHERE campaign.resource_name = '" + campRN + "' " +
                     "AND campaign_criterion.type = 'LOCATION'";
    var existing = AdsApp.search(checkQuery);
    var hasWales = false;
    while (existing.hasNext()) {
      var crit = existing.next();
      Logger.log('  Existing location: ' + crit.campaignCriterion.location.geoTargetConstant);
      if (crit.campaignCriterion.location.geoTargetConstant === WALES_GEO) {
        hasWales = true;
      }
    }

    if (hasWales) {
      Logger.log('  Wales already set — skipping');
      continue;
    }

    // Add Wales
    var result = AdsApp.mutate({
      campaignCriterionOperation: {
        create: {
          campaign: campRN,
          location: { geoTargetConstant: WALES_GEO }
        }
      }
    });

    if (result.isSuccessful()) {
      Logger.log('  OK: Wales added -> ' + result.getResourceName());
    } else {
      Logger.log('  FAIL: ' + result.getErrorMessages().join(', '));
    }
  }

  Logger.log('');
  Logger.log('=== DONE ===');
}
