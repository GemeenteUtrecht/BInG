const BASE_URL = 'https://geodata.nationaalgeoregister.nl/tiles/service/wmts';

const LAYER = 'bgtachtergrond';
const CRS = 'EPSG:28992';

const DEFAULT_QS_PARAMS = {
    SERVICE: 'WMTS',
    VERSION: '1.0.0',
    REQUEST: 'GetFeatureInfo',
    LAYER: LAYER,
    FORMAT: 'image/png',
    TileMatrixSet: CRS,
    infoformat: 'application/json',
    FEATURE_COUNT: 8,
};


const getFeatureInfo = (tileCol, tileRow, zoomLevel, i, j) => {
    const extraParams = {
        TileCol: tileCol,
        TileRow: tileRow,
        TileMatrix: `${CRS}:${zoomLevel}`,
        I: i,
        J: j,
    };
    const params = Object.assign({}, DEFAULT_QS_PARAMS, extraParams);
    console.log(params);
};


const getTile = (long, lat, zoom) => {
    const xTile = parseInt(
      Math.floor( (long + 180) / 360 * Math.pow(2, zoom) ),
      10
    );

    const y = lat * Math.PI / 180;

    const yTile = parseInt(
      Math.floor(
        (1 - Math.log(Math.tan(y) + 1 / Math.cos(y)) / Math.PI) / 2 * Math.pow(2, zoom)
      ),
      10
    );

    return {xTile, yTile};
};

export { getFeatureInfo, getTile };
