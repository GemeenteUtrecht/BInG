
const getFeatures = ({ lng, lat }) => {
    const url = `/aanmelden/map/features/${lng}/${lat}/`;
    return window
        .fetch(url)
        .then(response => response.json())
        .catch(console.error)
    ;
};


const getFeaturesInBBox = (bb) => {
    const url = `/aanmelden/map/features/bb/${bb.toBBoxString()}/`;
    return window
        .fetch(url)
        .then(response => response.json())
        .catch(console.error)
    ;
};


export { getFeatures, getFeaturesInBBox };
