/**
 * LUNARIS ACTION — reproducible Google Earth Engine Code Editor starter.
 * Execute in https://code.earthengine.google.com after signing into a licensed EE account.
 * Exports NEIGHBORHOOD-SCALE INDICATORS, NOT planting/solar project coordinates.
 * Before public deployment: inspect cloud masking, Landsat temporal coverage, spatial
 * support, licensing and cloud probabilities with an earth-observation specialist.
 * Source docs: https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1
 * https://developers.google.com/earth-engine/datasets/catalog/LANDSAT_LC08_C02_T1_L2
 */
var anchors = [
 ['marina-shade',25.0801,55.1404],['jbr-cooling',25.0771,55.1312],
 ['jlt-biodiversity',25.0663,55.1412],['downtown-cooling',25.1923,55.2814],
 ['business-bay-solar',25.1853,55.2708],['deira-waste',25.2701,55.3075],
 ['bur-dubai-green',25.2600,55.2933],['al-quoz-materials',25.1447,55.2352],
 ['barsha-water',25.1063,55.2054],['silicon-oasis-solar',25.1249,55.3782],
 ['international-city-greening',25.1657,55.4040],['creek-biodiversity',25.2057,55.3471]
];
var areas = ee.FeatureCollection(anchors.map(function(a) {
 return ee.Feature(ee.Geometry.Point([a[2],a[1]]).buffer(600), {area_id:a[0],radius_m:600});
}));
// Use a common historical period, because surface temperature may differ by season/time.
var start = '2025-01-01', end = '2026-01-01';
var dw = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1').filterDate(start,end).filterBounds(areas.geometry());
var cover = dw.select(['trees','grass','built','bare','water']).mean();
var ndvi = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
 .filterDate(start,end).filterBounds(areas.geometry()).filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE',20))
 .map(function(image){
  // Screen clouds and shadows via SCL; reflectance scales cancel in NDVI.
  var scl=image.select('SCL');
  var mask=scl.neq(3).and(scl.neq(8)).and(scl.neq(9)).and(scl.neq(10)).and(scl.neq(11));
  return image.updateMask(mask).normalizedDifference(['B8','B4']).rename('ndvi');
 }).median();
// Landsat collection 2 L2 surface-temperature band. Product QA must be screened.
var landsat = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2').filterDate(start,end).filterBounds(areas.geometry())
 .filter(ee.Filter.eq('PROCESSING_LEVEL','L2SP'))
 .map(function(image){
  var qa=image.select('QA_PIXEL');
  var mask=qa.bitwiseAnd(1 << 1).eq(0)
    .and(qa.bitwiseAnd(1 << 2).eq(0))
    .and(qa.bitwiseAnd(1 << 3).eq(0))
    .and(qa.bitwiseAnd(1 << 4).eq(0));
  return image.select('ST_B10').multiply(0.00341802).add(149).subtract(273.15)
    .rename('lst_c').updateMask(mask);
 });
var lst = landsat.median();
var stack=cover.addBands(ndvi).addBands(lst);
var result=stack.reduceRegions({collection:areas,reducer:ee.Reducer.mean(),scale:30,tileScale:4});
print('Area-level exploratory observations (check masked pixels and counts)',result);
Map.centerObject(areas,10);Map.addLayer(areas,{color:'lime'},'600m indicator study circles');
Map.addLayer(cover.select('trees'),{min:0,max:1,palette:['#181c19','#b9e975']},'Dynamic World tree probability');
Export.table.toDrive({collection:result,description:'lunaris_dubai_area_indicators_2025',fileFormat:'CSV'});
