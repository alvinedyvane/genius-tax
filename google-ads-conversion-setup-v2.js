/**
 * Genius Tax — Conversion Action Setup v2
 * Creates "Calls from Ads" primary conversion action
 * Paste into Google Ads Scripts editor → Authorize → Run
 */

function main() {
  Logger.log('=== Genius Tax Conversion Setup v2 ===');

  var result = AdsApp.mutate({
    conversionActionOperation: {
      create: {
        name: 'Genius Tax - Calls from Ads',
        type: 'AD_CALL',
        status: 'ENABLED',
        category: 'PHONE_CALL_LEAD',
        primaryForGoal: true,
        phoneCallDurationSeconds: 30,
        countingType: 'ONE_PER_CLICK'
      }
    }
  });

  if (result.isSuccessful()) {
    Logger.log('SUCCESS: ' + result.getResourceName());
    Logger.log('Primary conversion action created. Bidding will activate shortly.');
  } else {
    var errors = result.getErrorMessages();
    Logger.log('FAILED: ' + JSON.stringify(errors));
  }
}
