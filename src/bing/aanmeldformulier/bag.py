from dataclasses import dataclass

import requests

from bing.config.models import BInGConfig


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

    config = BInGConfig.get_solo()
    base = config.bag_root
    if not base.endswith("/"):
        base = f"{base}/"

    headers = {}
    if config.bag_api_key:
        headers.update({"X-Api-Key": config.bag_api_key})
    if config.bag_nlx_headers:
        headers.update(config.bag_nlx_headers)

    # urn:ogc:def:crs:OGC:1.3:CRS84
    # urn:ogc:def:crs:EPSG::4326
    # urn:ogc:def:crs:EPSG::28992
    # urn:ogc:def:crs:EPSG::4258

    # point["crs"] = {
    #     "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"},
    #     "type": "name",
    # }

    response = requests.post(
        f"{base}panden", json={"geometrie": {"contains": point}}, headers=headers
    )
    response.raise_for_status()
    response_data = response.json()

    panden = [Pand.construct(raw) for raw in response_data["_embedded"]["panden"]]

    return [pand.serialize() for pand in panden]
