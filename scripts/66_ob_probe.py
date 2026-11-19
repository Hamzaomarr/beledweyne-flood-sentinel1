import ee, json, os, io, requests, numpy as np
ee.Initialize(project='YOUR_EARTH_ENGINE_PROJECT')
AOI = ee.Geometry.Rectangle([45.00, 4.45, 45.65, 5.05])
ob = ee.FeatureCollection('GOOGLE/Research/open-buildings/v3/polygons').filterBounds(AOI)
print('all', ob.size().getInfo()); ob7 = ob.filter(ee.Filter.gte('confidence', 0.7)); print('conf>=0.7', ob7.size().getInfo())
print(ob.first().toDictionary().getInfo())
