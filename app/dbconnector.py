import psycopg2
import math
from postgis.psycopg import register
from postgis import LineString, MultiLineString
from app import app
from app.coordconvertor import RDWGS84Converter

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

def get_uitgangspunten(dtcode):
    # get reflijn
    reflijn = get_reflijn(dtcode)

    dtnaam = select(f"select naam from routegeometrie where code = '{dtcode}';")[0][0]
    lats = [p[3] for p in reflijn]
    lons = [p[4] for p in reflijn]
    midpoint = ((sum(lats) / len(lats)), (sum(lons)/len(lons)))

    return {
        "reflijn":reflijn,
        "midpoint":midpoint,
        "dtcode":dtcode,
        "afwijkendpeil":0.0,
        "ingesteldpeil":0.0,
        "praktijkpeil":0.0,
        "vigerendpeil":0.0,
        "naam":dtnaam,
        "kruinhoogte":0.0,
        "mhw":0.0,
        "kadeklasse":0,
        "stijghoogte":0.0,
    }


