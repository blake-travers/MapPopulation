from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any

from COG_GDAL_aggregator import COGAggregatorGDAL  # adjust if name differs

app = FastAPI()

# Create aggregator instance
agg = COGAggregatorGDAL()

# Allow frontend → backend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class PolygonPayload(BaseModel):
    polygon: Any
    max_depth: int = 0

@app.post("/population")
def population(payload: PolygonPayload):
    pop = agg.aggregate_polygon(
        polygon_geojson=payload.polygon,
        max_depth=payload.max_depth
    )
    return {"population": pop}
