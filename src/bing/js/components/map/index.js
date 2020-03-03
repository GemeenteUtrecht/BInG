/**
 * taken from https://github.com/geo-frontend/nlmaps/ as it fails to install on node 13
 */

import * as L from 'leaflet';

const BASE_URL = 'https://geodata.nationaalgeoregister.nl/tiles/service';

// 3857 -> pseudo mercator = WGS 84
const TILE_LAYER_URL = `${BASE_URL}/wmts/brtachtergrondkaart/EPSG:3857/{z}/{x}/{y}.png`;


const CENTER = {
  latitude: 52.093249,
  longitude: 5.111994,
  zoom: 13,
};


class Map {

  constructor(node) {
    this.node = node;
    this._map = this.init(node);
  }

  init(node) {
    const options = {
      target: node,
      attributionControl: false,
      center: [CENTER.latitude, CENTER.longitude],
      zoom: CENTER.zoom,
    };

    const map = L.map(node, options);
    const tileLayer = L.tileLayer(
      TILE_LAYER_URL,
      {
        attribution: "Kaartgegevens &copy; <a href='https://www.kadaster.nl'>Kadaster</a> | \
        <a href='https://www.verbeterdekaart.nl'>Verbeter de kaart</a>",
        minZoom: 6,
        maxZoom: 19,
        // type: 'wmts',
      }
    );

    map.addLayer(tileLayer);

    return map;
  }
}


const maps = document.querySelectorAll('.map');
Array.from(maps).forEach(node => new Map(node));
