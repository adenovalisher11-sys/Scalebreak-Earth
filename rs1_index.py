import requests, re, json, sys, pathlib, rasterio
from concurrent.futures import ThreadPoolExecutor
B="https://radarsat-r1-l1-cog.s3.ca-central-1.amazonaws.com"
def keys(prefix):
    out=[];tok=None
    while True:
        p={"list-type":"2","prefix":prefix,"max-keys":"1000"}
        if tok: p["continuation-token"]=tok
        t=requests.get(B,params=p,timeout=60).text
        out+=re.findall(r"<Key>([^<]+)</Key>",t)
        m=re.search(r"<NextContinuationToken>([^<]+)<",t)
        if not m: return out
        tok=m.group(1)
ks=[]
for y in range(1996,2014):
    for m in (6,7,8,9):
        ks+= [k for k in keys(f"{y}/{m}/") if k.endswith(("SGF.tif","SGX.tif","SCN.tif"))]
print("candidate scenes",len(ks),flush=True)
env=dict(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif",GDAL_HTTP_MAX_RETRY="2")
def bounds(k):
    try:
        with rasterio.Env(**env), rasterio.open(f"/vsicurl/{B}/{k}") as ds:
            if ds.crs and ds.crs.is_valid:
                from rasterio.warp import transform_bounds
                return k, list(transform_bounds(ds.crs,"EPSG:4326",*ds.bounds))
            g,crs=ds.gcps
            if g:
                xs=[p.x for p in g]; ys=[p.y for p in g]; return k,[min(xs),min(ys),max(xs),max(ys)]
    except Exception as e: return k,None
    return k,None
with ThreadPoolExecutor(24) as ex: res=dict(ex.map(bounds,ks))
kz={k:b for k,b in res.items() if b and b[2]>46 and b[0]<88 and b[3]>40 and b[1]<56}
print("readable",sum(1 for v in res.values() if v),"over Kazakhstan box",len(kz))
json.dump(kz,open("data/rs1_kz_scenes.json","w"),indent=1)
