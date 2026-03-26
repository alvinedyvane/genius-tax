/**
 * Find Wales Geo Target Constant ID
 * Run this once to discover the correct ID, then we'll update the geo script
 */
function main() {
  Logger.log('=== Looking up Wales geo target ID ===');
  
  // Method 1: Try locationSuggestions (older API)
  try {
    var suggestions = AdsApp.targeting().locationSuggestions()
      .withLimit(20)
      .get();
    
    while (suggestions.hasNext()) {
      var s = suggestions.next();
      var name = s.getName ? s.getName() : 'unknown';
      Logger.log('Suggestion: ' + name + ' ID: ' + (s.getId ? s.getId() : 'n/a'));
    }
  } catch(e) {
    Logger.log('locationSuggestions failed: ' + e);
  }
  
  // Method 2: Query geo_target_constant via GAQL
  try {
    var query = "SELECT geo_target_constant.id, geo_target_constant.name, geo_target_constant.country_code, geo_target_constant.target_type " +
                "FROM geo_target_constant " +
                "WHERE geo_target_constant.name = 'Wales' " +
                "AND geo_target_constant.country_code = 'GB'";
    
    var result = AdsApp.search(query);
    if (!result.hasNext()) {
      Logger.log('No results for Wales query');
    }
    while (result.hasNext()) {
      var row = result.next();
      Logger.log('Wales: id=' + row.geoTargetConstant.id + 
                 ' name=' + row.geoTargetConstant.name +
                 ' type=' + row.geoTargetConstant.targetType +
                 ' resourceName=' + row.geoTargetConstant.resourceName);
    }
  } catch(e) {
    Logger.log('GAQL query failed: ' + e);
  }

  // Method 3: Search broadly for UK regions
  try {
    var query2 = "SELECT geo_target_constant.id, geo_target_constant.name, geo_target_constant.country_code, geo_target_constant.target_type " +
                 "FROM geo_target_constant " +
                 "WHERE geo_target_constant.country_code = 'GB' " +
                 "AND geo_target_constant.target_type = 'State'";
    
    var result2 = AdsApp.search(query2);
    Logger.log('GB States/Regions:');
    while (result2.hasNext()) {
      var row = result2.next();
      Logger.log('  ' + row.geoTargetConstant.name + ' — id: ' + row.geoTargetConstant.id);
    }
  } catch(e) {
    Logger.log('State query failed: ' + e);
  }
}
