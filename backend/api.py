from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any
from COG_GDAL_aggregator import COGAggregatorGDAL

app = FastAPI()
agg = COGAggregatorGDAL()

# Allow your HTML/JS page to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # in dev, allow all – you can tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#Create class representing the polygon object
class PolygonPayload(BaseModel):
    polygon: Any   # should be a GeoJSON geometry object
    max_depth: int = 0

@app.post("/population")
def get_population(payload: PolygonPayload):
    """
    Expects:
    {
        "polygon": { "type": "Polygon", "coordinates": [...] },
        "max_depth": 0
    }
    """
    pop = agg.aggregate_polygon(
        polygon_geojson=payload.polygon,
        max_depth=payload.max_depth
    )
    return {"population": pop}
