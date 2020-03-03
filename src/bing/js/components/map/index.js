/**
 * taken from https://github.com/geo-frontend/nlmaps/ as it fails to install on node 13
 */

import * as L from 'leaflet';

import { getFeatureInfo, getTile } from './features.js';
import { RD_CRS } from './transform.js';

const BASE_URL = 'https://geodata.nationaalgeoregister.nl/tiles/service';
const attribution = 'Kaartgegevens &copy; <a href="https://www.kadaster.nl">Kadaster</a> | <a href="https://www.verbeterdekaart.nl">Verbeter de kaart</a>';

// 3857 -> pseudo mercator = WGS 84
const BRT_TILE_LAYER_URL = `${BASE_URL}/wmts/brtachtergrondkaart/EPSG:28992/{z}/{x}/{y}.png`;
const BGT_TILE_LAYER_URL = `${BASE_URL}/wmts/bgtachtergrond/EPSG:28992/{z}/{x}/{y}.png`;

const CENTER = {
  latitude: 52.093249,
  longitude: 5.111994,
  zoom: 3,
};


class Map {

  constructor(node) {
    this.node = node;
    this._map = this.init(node);
    window._map = this._map;

    this._zoomNode = document.getElementById('zoomLevel');
  }

  init(node) {
    const options = {
      continuousWorld: true,
      crs: RD_CRS,
      attributionControl: false,
      center: [CENTER.latitude, CENTER.longitude],
      zoom: CENTER.zoom,
    };

    const map = L.map(node, options);
    const tileLayer = L.tileLayer(
      BRT_TILE_LAYER_URL,
      {
        attribution: attribution,
        minZoom: 6,
        maxZoom: 19,
        // type: 'wmts',
      }
    );

    map.addLayer(tileLayer);
    this._tileLayer = tileLayer;

    map.on('click', (e) => this.onClick(e));
    map.on('zoomend', () => {
      this._zoomNode.innerText = this._map.getZoom();
    });

    return map;
  }

  onClick(event) {
    const lng = event.latlng.lng;
    const lat = event.latlng.lat;
    const z = this._map.getZoom();

    const {xTile, yTile} = getTile(lng, lat, z);

    const {x, y} = this._tileLayer.getTileSize();

    const relativeX = event.containerPoint.x % x;
    const relativeY = event.containerPoint.y % y;

    console.log(relativeX, relativeY);

    const features = getFeatureInfo(xTile, yTile, z, 0, 0);
    console.log(features);
  }
}


const maps = document.querySelectorAll('.map');
Array.from(maps).forEach(node => new Map(node));
