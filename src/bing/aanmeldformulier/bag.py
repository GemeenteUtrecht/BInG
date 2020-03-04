from dataclasses import dataclass

from django.conf import settings

import requests

BASE = "https://bag.basisregistraties.overheid.nl/api/v1/"


HEADERS = {
    "X-Api-Key": settings.BAG_API_KEY,
    # "Content-Crs": "urn:ogc:def:crs:OGC:1.3:CRS84",
    # "Accept-Crs": "urn:ogc:def:crs:EPSG::28992",
}


@dataclass
class Pand:
    url: str
    identificatiecode: str
    oorspronkelijkBouwjaar: int
    geometrie: dict

    @classmethod
    def construct(cls, data) -> "Pand":
        params = {
            "url": data["_links"]["self"]["href"],
            "identificatiecode": data["identificatiecode"],
            "oorspronkelijkBouwjaar": data["oorspronkelijkBouwjaar"],
            # Een geneste lijst van coördinaten in lengte- en breedtegraden in ETRS89,
            # EPSG:4258. Deze is nagenoeg gelijk aan WGS84 EPSG:4326 en kan als standaard
            # lengte- en breedtegraden worden gebruikt.
            "geometrie": data["_embedded"]["geometrie"],
        }
        return cls(**params)

    def serialize(self) -> dict:
        properties = {
            "type": "pand",
            "url": self.url,
            "identificatiecode": self.identificatiecode,
            "oorspronkelijkBouwjaar": self.oorspronkelijkBouwjaar,
        }
        return {"type": "Feature", "properties": properties, "geometry": self.geometrie}


def get_panden(point: dict):
    point = point.copy()

    # urn:ogc:def:crs:OGC:1.3:CRS84
    # urn:ogc:def:crs:EPSG::4326
    # urn:ogc:def:crs:EPSG::28992
    # urn:ogc:def:crs:EPSG::4258

    # point["crs"] = {
    #     "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"},
    #     "type": "name",
    # }

    response = requests.post(
        f"{BASE}panden", json={"geometrie": {"contains": point}}, headers=HEADERS
    )
    response.raise_for_status()
    response_data = response.json()

    panden = [Pand.construct(raw) for raw in response_data["_embedded"]["panden"]]

    return [pand.serialize() for pand in panden]
