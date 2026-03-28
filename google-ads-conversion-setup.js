/**
 * Genius Tax — Conversion Action Setup
 * Creates a "Calls from Ads" primary conversion action
 *
 * Paste into: Google Ads > Tools > Bulk Actions > Scripts
 * Click "Authorize" then "Run"
 */

function main() {
  Logger.log('=== Genius Tax Conversion Setup ===');

  // Check if conversion action already exists
  var existing = AdsApp.conversionActions()
    .withCondition("Name = 'Genius Tax - Calls from Ads'")
    .get();

  if (existing.hasNext()) {
    Logger.log('Conversion action already exists — checking status...');
    var ca = existing.next();
    Logger.log('Name: ' + ca.getName());
    Logger.log('Done — already set up.');
    return;
  }

  // Create the conversion action
  var result = AdsApp.mutate({
    conversionActionOperation: {
      create: {
        name: 'Genius Tax - Calls from Ads',
        type: 'AD_CALL',
        status: 'ENABLED',
        category: 'PHONE_CALL_LEAD',
        primaryForGoal: true,
        phoneCallDurationSeconds: 30,
        countingType: 'ONE_PER_CLICK',
        valueSettings: {
          defaultValue: 0,
          alwaysUseDefaultValue: true
        }
      }
    }
  });

  if (result.isSuccessful()) {
    Logger.log('SUCCESS — Conversion action created: ' + result.getResourceName());
    Logger.log('Bidding will activate within the next few hours.');
  } else {
    Logger.log('ERROR: ' + JSON.stringify(result.getErrorMessages()));
  }
}
