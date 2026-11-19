import ee, os, requests, rasterio
ee.Initialize(project='YOUR_EARTH_ENGINE_PROJECT')
DG=r'.\data\processed\diag'
AOI = ee.Geometry.Rectangle([45.00, 4.45, 45.65, 5.05], proj='EPSG:4326', geodesic=False)
def dl(img, step, name):
    nx=int(round(0.65/step)); ny=int(round(0.60/step))
    url=img.getDownloadURL({'crs':'EPSG:4326','crsTransform':[step,0,45.00,0,-step,5.05],'dimensions':'%dx%d'%(nx,ny),'format':'GEO_TIFF'})
    r=requests.get(url,timeout=900); r.raise_for_status(); open(os.path.join(DG,name),'wb').write(r.content)
    with rasterio.open(os.path.join(DG,name)) as s: print(name,s.shape,s.bounds,s.dtypes)
hand=ee.Image('MERIT/Hydro/v1_0_1').select('hnd').unmask(0).float()
dl(hand,3/3600,'hand_native.tif')
dem=ee.ImageCollection('COPERNICUS/DEM/GLO30').select('DEM').mosaic().setDefaultProjection('EPSG:4326',None,30.9)
dl(ee.Terrain.slope(dem).float(),1/3600,'slope_native.tif')
