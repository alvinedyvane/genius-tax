/**
 * Genius Tax — Update Geo Targeting
 * Removes UK-wide targeting, adds England + Wales only
 * Run once in Google Ads Scripts (Tools > Bulk Actions > Scripts)
 */

function main() {
  Logger.log('=== Geo Targeting Update: England + Wales Only ===');

  var campaigns = [
    '[GeniusTax] MTD High-Intent Search',
    '[GeniusTax] MTD Awareness Search',
    '[GeniusTax] Audience-Specific Search',
    '[GeniusTax] Competitor Conquest'
  ];

  // Geo target constants
  var UK_GEO      = 'geoTargetConstants/2826';   // United Kingdom (to remove)
  var ENGLAND_GEO = 'geoTargetConstants/20339';  // England
  var WALES_GEO   = 'geoTargetConstants/20340';  // Wales

  for (var i = 0; i < campaigns.length; i++) {
    var campName = campaigns[i];
    Logger.log('');
    Logger.log('--- ' + campName + ' ---');

    // Find campaign resource name
    var query = "SELECT campaign.resource_name, campaign.name " +
                "FROM campaign " +
                "WHERE campaign.name = '" + campName + "'";
    var rows = AdsApp.search(query);

    if (!rows.hasNext()) {
      Logger.log('  NOT FOUND — skipping');
      continue;
    }

    var row = rows.next();
    var campRN = row.campaign.resourceName;
    Logger.log('  Found: ' + campRN);

    // Step 1: Remove existing UK location criterion
    var criteriaQuery = "SELECT campaign_criterion.resource_name, " +
                        "campaign_criterion.location.geo_target_constant " +
                        "FROM campaign_criterion " +
                        "WHERE campaign.resource_name = '" + campRN + "' " +
                        "AND campaign_criterion.type = 'LOCATION'";
    var criteria = AdsApp.search(criteriaQuery);

    while (criteria.hasNext()) {
      var crit = criteria.next();
      var geoConst = crit.campaignCriterion.location.geoTargetConstant;
      var critRN = crit.campaignCriterion.resourceName;
      Logger.log('  Removing location: ' + geoConst);
      var removeResult = AdsApp.mutate({
        campaignCriterionOperation: { remove: critRN }
      });
      if (removeResult.isSuccessful()) {
        Logger.log('    OK removed');
      } else {
        Logger.log('    FAIL: ' + removeResult.getErrorMessages().join(', '));
      }
    }

    // Step 2: Add England
    var engResult = AdsApp.mutate({
      campaignCriterionOperation: {
        create: {
          campaign: campRN,
          location: { geoTargetConstant: ENGLAND_GEO }
        }
      }
    });
    Logger.log('  Add England: ' + (engResult.isSuccessful() ? 'OK' : 'FAIL — ' + engResult.getErrorMessages().join(', ')));

    // Step 3: Add Wales
    var walesResult = AdsApp.mutate({
      campaignCriterionOperation: {
        create: {
          campaign: campRN,
          location: { geoTargetConstant: WALES_GEO }
        }
      }
    });
    Logger.log('  Add Wales: ' + (walesResult.isSuccessful() ? 'OK' : 'FAIL — ' + walesResult.getErrorMessages().join(', ')));
  }

  Logger.log('');
  Logger.log('=== DONE — All campaigns now target England + Wales only ===');
}
