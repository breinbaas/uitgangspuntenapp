import psycopg2
import math
from postgis.psycopg import register
from postgis import LineString, MultiLineString
#import numpy as np
from app import app
from app.coordconvertor import RDWGS84Converter

MAX_DISTANCE = 10

conn = psycopg2.connect(
    host=app.config['DB_SERVER'],
    database=app.config['DB_NAME'],
    user=app.config['DB_USER'],
    password=app.config['DB_PASSWORD']
)

register(conn)

rdwgs = RDWGS84Converter()

def select(sql):
    try:
        cur = conn.cursor()
        cur.execute(sql)
        result = cur.fetchall()        
        cur.close()
        return result
    except (Exception, psycopg2.Error) as error:
        print(f"Got database error; {error}")        

def get_all_codes():
    rows = select("select code from routegeometrie order by code asc;")
    return [r[0] for r in rows]
    

def get_reflijn(dtcode):
    rows = select(f"select geom from routegeometrie where code = '{dtcode}';")
    geom = rows[0][0]
    if type(geom) == MultiLineString:
        pts = []
        for ls in geom:
            pts += [p for p in ls.coords]        
    elif type(geom) == LineString:
        pts = [p for p in geom.coords]

    final_points = []
    for i, p in enumerate(pts):
        if i==0:
            lat, lon = rdwgs.from_rd(p[0], p[1])
            final_points.append((0, p[0], p[1], lat, lon))
        else:
            x = p[0]
            y = p[1]

            lat, lon = rdwgs.from_rd(x, y)

            dx = pts[0][0] - x
            dy = pts[0][1] - y
            final_points.append((math.sqrt(dx**2 + dy**2), p[0], p[1], lat, lon))
    return final_points

def interpolate(points, chainage):
    for i in range(1,len(points)):
        p1 = points[i-1]
        p2 = points[i]

        if p1[0] <= chainage and chainage <= p2[0]:
            c1, c2 = p1[0], p2[0]
            x1, y1 = p1[1], p1[2]
            x2, y2 = p2[1], p2[2]

            x = x1 + (chainage - c1) / (c2 - c1) * (x2 - x1)
            y = y1 + (chainage - c1) / (c2 - c1) * (y2 - y1)
            return x, y

    raise ValueError("Interpolation error encountered.")


def get_uitgangspunten(dtcode, dtchainage):
    # get reflijn
    reflijn = get_reflijn(dtcode)

    # get naam
    dtnaam = select(f"select naam from routegeometrie where code = '{dtcode}';")[0][0]
    
    #x, y = interpolate(reflijn, ch)
    if dtchainage < reflijn[0][0]: dtchainage = reflijn[0][0]
    if dtchainage > reflijn[-1][0]: dtchainage = reflijn[-1][0]

    x, y = interpolate(reflijn, dtchainage)
    chainagepoint = rdwgs.from_rd(x,y)


    # MHW, KRUINHOOGTE AND KADEKLASSE
    kadeinfo = select("SELECT mhw, kruinhoogte, kadeklasse,ST_Distance(ST_Buffer(r.geom,20),"\
        f"ST_SetSRID(ST_MakePoint({x}, {y}),28992))"\
        "FROM kadeinfo r ORDER BY 4 ASC LIMIT 1;")[0]
    if kadeinfo[-1] > MAX_DISTANCE:
        mhw = -9999.
        kruinhoogte = -9999.
        kadeklasse = -9999.
    else:
        mhw = kadeinfo[0]
        kruinhoogte = kadeinfo[1]
        kadeklasse = kadeinfo[2]

    
    # PEILEN
    afwijkendpeil = select("SELECT vastpeil, laagpeil, hoogpeil, zomerpeil, winterpeil,"\
        f"ST_Distance(r.geom,ST_SetSRID(ST_MakePoint({x}, {y}),28992)) FROM afwijkendpeil r ORDER BY 6 ASC LIMIT 1;")[0]
    ingesteldpeil = select("SELECT vastpeil, laagpeil, hoogpeil, zomerpeil, winterpeil,"\
        f"ST_Distance(r.geom,ST_SetSRID(ST_MakePoint({x}, {y}),28992)) FROM ingesteldpeil r ORDER BY 6 ASC LIMIT 1;")[0]
    praktijkpeil = select("SELECT vastpeil, laagpeil, hoogpeil, zomerpeil, winterpeil,"\
        f"ST_Distance(r.geom,ST_SetSRID(ST_MakePoint({x}, {y}),28992)) FROM praktijkpeil r ORDER BY 6 ASC LIMIT 1;")[0]
    vigerendpeil = select("SELECT vastpeil, laagpeil, hoogpeil, zomerpeil, winterpeil,"\
        f"ST_Distance(r.geom,ST_SetSRID(ST_MakePoint({x}, {y}),28992)) FROM vigerendpeil r ORDER BY 6 ASC LIMIT 1;")[0]
    
    
    stijghoogte = select(f"SELECT stijghoogte, ST_Distance(r.geom,ST_SetSRID(ST_MakePoint({x}, {y}),28992)) FROM stijghoogte r ORDER BY 2 ASC LIMIT 1;")[0]

    if stijghoogte[-1] >= MAX_DISTANCE:
        stijghoogte = ""
    else:
        stijghoogte = round(stijghoogte[0],2)

    
    if afwijkendpeil[-1] <= MAX_DISTANCE:
        afwijkendpeil = [v for v in afwijkendpeil[:-2] if v]
        if len(afwijkendpeil) > 0:
            afwijkendpeil = min(afwijkendpeil)
    else:
        afwijkendpeil = ""

    if ingesteldpeil[-1] <= MAX_DISTANCE:
        ingesteldpeil = [v for v in ingesteldpeil[:-2] if v]
        if len(ingesteldpeil) > 0:
            ingesteldpeil = min(ingesteldpeil)
    else:
        ingesteldpeil = ""

    if praktijkpeil[-1] <= MAX_DISTANCE:
        praktijkpeil = [v for v in praktijkpeil[:-2] if v]
        if len(praktijkpeil) > 0:
            praktijkpeil = min(praktijkpeil)
    else:
        praktijkpeil = ""
    
    if vigerendpeil[-1] <= MAX_DISTANCE:
        vigerendpeil = [v for v in vigerendpeil[:-2] if v]
        if len(vigerendpeil) > 0:
            vigerendpeil = min(vigerendpeil)
    else:
        vigerendpeil = ""
    
    # find middle point
    lats = [p[3] for p in reflijn]
    lons = [p[4] for p in reflijn]
    midpoint = ((sum(lats) / len(lats)), (sum(lons)/len(lons)))


    return {        
        "reflijn":reflijn,
        "midpoint":midpoint,
        "chainagepoint":chainagepoint,
        "dtcode":dtcode,
        "metrering":int(dtchainage),
        "afwijkendpeil":afwijkendpeil,
        "ingesteldpeil":ingesteldpeil,
        "praktijkpeil":praktijkpeil,
        "vigerendpeil":vigerendpeil,
        "naam":dtnaam,
        "kruinhoogte":kruinhoogte,
        "mhw":mhw,
        "kadeklasse":kadeklasse,
        "stijghoogte":stijghoogte,
    }


