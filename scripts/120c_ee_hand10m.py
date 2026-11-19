import ee, os, requests, numpy as np, rasterio, io
from rasterio.transform import from_origin
from rasterio.io import MemoryFile
ee.Initialize(project='YOUR_EARTH_ENGINE_PROJECT')
B=r'.'; DG=os.path.join(B,'data','processed','diag')
X0,Y0,NX,NY=498000,560000,7600,7000
hand=ee.Image('MERIT/Hydro/v1_0_1').select('hnd').unmask(0).float()
full=np.zeros((NY,NX),'float32'); tx,ty=4,4; w=NX//tx; h=NY//ty
for i in range(ty):
    for j in range(tx):
        x=X0+j*w*10; y=Y0-i*h*10
        reg=ee.Geometry.Rectangle([x,y-h*10,x+w*10,y],'EPSG:32638',geodesic=False)
        url=hand.getDownloadURL({'region':reg,'scale':10,'crs':'EPSG:32638','format':'GEO_TIFF'})
        r=requests.get(url,timeout=900); r.raise_for_status()
        with MemoryFile(r.content) as mf, mf.open() as s:
            a=s.read(1); assert abs(s.transform.c-x)<1e-6 and abs(s.transform.f-y)<1e-6 and a.shape==(h,w),(s.transform,a.shape); print(i,j,a.shape,flush=True)
        full[i*h:(i+1)*h,j*w:(j+1)*w]=a
with rasterio.open(os.path.join(DG,'hand_10m.tif'),'w',driver='GTiff',height=NY,width=NX,count=1,dtype='float32',crs='EPSG:32638',transform=from_origin(X0,Y0,10,10),compress='deflate') as d: d.write(full,1)
print('done')

