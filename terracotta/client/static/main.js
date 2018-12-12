/// <reference path='./types/leaflet.d.ts' />
/// <reference path='./types/no-ui-slider.d.ts' />
/// <reference path='./types/main.d.ts' />

/* BEWARE! THERE BE DRAGONS! 🐉

Big parts of following file were written by a Python programmer with minimal exposure
to idiomatic Javascript. It should not serve as an authoritive reference on how a
frontend for Terracotta should be written.
*/

/*
Some notes:
- methods marked with @global are expected to be available in the DOM (i.e. app.html).
*/

// ===================================================
// Constants
// ===================================================

/**
 * Updates errors when error Array changes.
 * @param {Array<Terracotta.IMapError>} arr
 */
const errorProxy = (arr) =>
    new Proxy(arr, {
        set: (target, property, value) => {
            target[property] = value;
            renderErrors(target);
            return true;
        }
    });


const rgbStretchProxy = (arr) =>
    new Proxy(arr, {
        set: (target, property, value) => {
            target[property] = value;
            updateRGBStretch();
            return true;
        }
    });

const singlebandStretchProxy = (arr) =>
    new Proxy(arr, {
        set: (target, property, value) => {
            target[property] = value;
            updateSinglebandStretch();
            return true;
        }
    });

const DATASETS_PER_PAGE = 16;
const THUMBNAIL_SIZE = [128, 128];
const COLORMAPS = [
    { display_name: 'Greyscale', id: 'greys_r' },
    { display_name: 'Viridis', id: 'viridis' },
    { display_name: 'Blue-Red', id: 'rdbu_r' },
    { display_name: 'Blue-Green', id: 'bugn' },
    { display_name: 'Yellow-Green', id: 'ylgn' },
    { display_name: 'Magma', id: 'magma' },
    { display_name: 'Earth', id: 'gist_earth' },
    { display_name: 'Ocean', id: 'ocean' }
];

const STATE = {
    keys: [],
    errors: errorProxy([]),
    remote_host: '',
    current_dataset_page: 0,
    dataset_metadata: {},
    colormap_values: {},
    current_colormap: '',
    current_singleband_stretch: singlebandStretchProxy([0, 1]),
    current_rgb_stretch: [
        rgbStretchProxy([0, 1]), 
        rgbStretchProxy([0, 1]),
        rgbStretchProxy([0, 1])
    ],
    map: undefined,
    overlayLayer: undefined,
    activeSinglebandLayer: undefined,
    activeRgbLayer: undefined,
    m_pos: 0
};



// ===================================================
// Convenience functions to get valid Terracotta URLs.
// ===================================================

/**
 * As it says, gets keys so the app can be initialized.
 *
 * @param {string} remote_host
 *
 * @return {Promise<Array<Terracotta.IKey>>}
 */
function getKeys(remote_host) {
    const keyUrl = `${remote_host}/keys`;
    return httpGet(keyUrl).then((response) => response.keys || []);
}

/**
 * @param {string} remote_host
 * @param {Array<Terracotta.IKeyConstraint>} key_constraints Key/val pairs of constraints.
 * @param {number} limit Items per page
 * @param {number} page Page number
 *
 * @return {string} dataset URL.
 */
function assembleDatasetURL(remote_host, key_constraints, limit, page) {
    let request_url = `${remote_host}/datasets?limit=${limit}&page=${page}`;

    for (let i = 0; i < key_constraints.length; i++) {
        request_url += `&${key_constraints[i].key}=${key_constraints[i].value}`;
    }
    return request_url;
}

/**
 * @param {string} remote_host
 * @param {Array<string>} ds_keys Dataset keys i.e. [<type>, <date>, <id>, <band>].
 *
 * @return {string} metadata URL.
 */
function assembleMetadataURL(remote_host, ds_keys) {
    let request_url = `${remote_host}/metadata`;
    for (let i = 0; i < ds_keys.length; i++) {
        request_url += `/${ds_keys[i]}`;
    }
    return request_url;
}

/**
 * @param {string} remote_host
 * @param {Array<string>} keys
 * @param {Terracotta.IOptions} [options]
 * @param {boolean} [preview]
 *
 * @return {string} singleband URL.
 */
function assembleSinglebandURL(remote_host, keys, options, preview) {
    let request_url;

    if (preview) {
        request_url = `${remote_host}/singleband/${keys.join('/')}/preview.png?tile_size=${JSON.stringify(THUMBNAIL_SIZE)}`;
    } else {
        request_url = `${remote_host}/singleband/${keys.join('/')}/{z}/{x}/{y}.png`;
    }

    if (options == null) return request_url;

    let first = true;
    for (let option_key in options) {
        if (!options.hasOwnProperty(option_key)) continue;

        if (first) {
            request_url += `?${option_key}=${options[option_key]}`;
            first = false;
        } else {
            request_url += `&${option_key}=${options[option_key]}`;
        }
    }
    updateComputedUrl(request_url, keys);
    return request_url;
}

/**
 * @param {string} remote_host
 * @param {Array<string>} first_keys
 * @param {Array<string>} rgb_keys
 * @param {Terracotta.IOptions} options
 * @param {boolean} preview
 *
 * @return {string} rgb URL.
 */
function assembleRgbUrl(remote_host, first_keys, rgb_keys, options, preview) {
    let request_url = `${remote_host}/rgb/`;

    if (first_keys.length > 0) {
        request_url += `${first_keys.join('/')}/`;
    }
   
    if (preview) {
        request_url += `preview.png?tile_size=${JSON.stringify(THUMBNAIL_SIZE)}`;
    } else {
        request_url += '{z}/{x}/{y}.png';
    }

    const [r, g, b] = rgb_keys;
    request_url += `?r=${r}&g=${g}&b=${b}`;

    if (!options) {
        return request_url;
    }

    for (let option_key in options) {
        if (!options.hasOwnProperty(option_key)) continue;
        request_url += `&${option_key}=${options[option_key]}`;
    }
    return request_url;
}

/**
 * @param {string} colormap The id of the color map
 * @param {number} num_values The number of values to return
 *
 * @return {string} color map URL
 */
function assembleColormapUrl(remote_host, colormap, num_values) {
    return `${remote_host}/colormap?colormap=${colormap}&stretch_range=[0,1]&num_values=${num_values}`;
}

// ===================================================
// Initializers
// ===================================================

/**
 * Gets colorbar values for a given range.
 *
 * @param {string} remote_host
 * @param {number} [num_values=100] The number of values to get colors for.
 */
function getColormapValues(remote_host, num_values = 100) {
    const requestColorMap = (colormap) => {
        const cmapId = colormap.id;

        return httpGet(assembleColormapUrl(remote_host, cmapId, num_values)).then((response) => {
            if (response && response.colormap) {
                STATE.colormap_values[cmapId] = [];

                for (let j = 0; j < num_values; j++) {
                    STATE.colormap_values[cmapId][j] = response.colormap[j].rgb;
                }
            }
        });
    };

    return Promise.all(COLORMAPS.map(requestColorMap));
}

/**
 * Sets up the UI.
 *
 * @param {Array<Terracotta.IKey>} keys
 */
function initUI(remote_host, keys) {
    // initialize list of keys and key descriptions
    let keyList = document.getElementById('key-list');
    keyList.innerHTML = '';
    for (let i = 0; i < keys.length; i++) {
        let keyEntry = document.createElement('li');
        keyEntry.innerHTML = `<b>${keys[i].key}</b>`;
        if (keys[i].description != null) {
            keyEntry.innerHTML += `: ${keys[i].description}`;
        }
        keyList.appendChild(keyEntry);
    }

    // initialize colormap selector
    let colormapSelector = document.getElementById('colormap-selector');
    colormapSelector.innerHTML = '';
    for (let i = 0; i < COLORMAPS.length; i++) {
        let cmapOption = document.createElement('option');
        cmapOption.value = COLORMAPS[i].id;
        cmapOption.innerHTML = COLORMAPS[i].display_name;
        if (i === 0) {
            cmapOption.selected = true;
        }
        colormapSelector.appendChild(cmapOption);
    }

    // initialize search fields
    let searchContainer = document.getElementById('search-fields');
    searchContainer.innerHTML = '';
    for (let i = 0; i < keys.length; i++) {
        const searchField = document.createElement('input');
        searchField.type = 'text';
        searchField.placeholder = keys[i].key;
        searchField.name = keys[i].key;
        searchField.addEventListener('change', searchFieldChanged);
        searchContainer.appendChild(searchField);
    }

    // initialize table header for search results
    let datasetTable = document.getElementById('search-results');
    datasetTable.innerHTML = '';
    let tableHeader = document.createElement('th');
    for (let i = 0; i < keys.length; i++) {
        const headerEntry = document.createElement('td');
        headerEntry.innerHTML = keys[i].key;
        tableHeader.appendChild(headerEntry);
    }
    datasetTable.appendChild(tableHeader);

    // initialize RGB search fields
    let rgbSearchContainer = document.getElementById('rgb-search-fields');
    rgbSearchContainer.innerHTML = '';
    for (let i = 0; i < keys.length - 1; i++) {
        const searchField = document.createElement('input');
        searchField.type = 'text';
        searchField.placeholder = keys[i].key;
        searchField.name = keys[i].key;
        searchField.addEventListener('change', rgbSearchFieldChanged);
        rgbSearchContainer.appendChild(searchField);
    }

    resetRgbSelectors(false);
    rgbSearchFieldChanged();

    // create sliders
    let sliderDummyOptions = {
        start: [0.0, 1.0],
        range: { min: 0, max: 1 },
        connect: true,
        behaviour: 'drag'
    };

    /**
     * @type {noUiSlider.SliderElement}
     */
    let singlebandSlider = document.querySelector('.singleband-slider');
    noUiSlider.create(singlebandSlider, sliderDummyOptions).on(
        'change.one',
        function (values, handle) {
            STATE.current_singleband_stretch[handle] = values[handle];
        }
    );

    const rgbIds = ['R', 'G', 'B'];
    for (let i = 0; i < rgbIds.length; i++) {
        let id = rgbIds[i];
        let slider = document.querySelector(`.rgb-slider#${id}`);
        noUiSlider.create(slider, sliderDummyOptions).on(
            'change.one',
            function(id, values, handle) {
                STATE.current_rgb_stretch[id][handle] = values[handle];
            }.bind(null, i)
        );
    }
    resetLayerState();
    updateColormap();
    removeSpinner();
}

// ===================================================
// Helper functions
// ===================================================

/**
 * Serializes an array of keys to a single string
 *
 * @param {Array<string>} keys
 *
 * @return {string}
 */
function serializeKeys(keys) {
    return keys.join('/');
}

/**
 * Compares whether two arrays are equal element-wise
 * 
 * @param {Array} arr1 
 * @param {Array} arr2 
 */
function compareArray(arr1, arr2){
  if (arr1 == null || arr2 == null) return false;
  if (arr1.length !== arr2.length) return false;
  for(let i = 0; i < arr1.length; i++){
    if(arr1[i] !== arr2[i]) return false;
  }
  return true;
}

/**
 * Stores metadata.
 *
 * @param {Terracotta.IMetadata} metadata
 */
function storeMetadata(metadata) {
    const ds_keys = serializeKeys(Object.values(metadata.keys));
    STATE.dataset_metadata[ds_keys] = metadata;
}

/**
 * Performs a GET call via the fetch API.
 * @param {string} url
 *
 * @return {Promise<any>} A JSON server response.
 */
function httpGet(url) {
    return fetch(url)
        .then((response) => {
            if (response.ok) {
                return response.json();
            }

            return Promise.reject(response.status);
        })
        .catch((errorStatus) => {
            const error_str = `API request failed: ${errorStatus}`;
            STATE.errors.push({ text: error_str, url });
            console.error(error_str);
            throw errorStatus;
        });
}

/**
 * Renders errors in the '.errors' div.
 *
 * @param {Array<Terracotta.IMapError>} errors
 */
function renderErrors(errors) {
    const errorHtml = errors
        .map(
            (error, index) => `
            <li>
                ${error.text} <br/>
                <small>${error.url}</small>
                <span onclick='dismissError.call(null, ${index})'>
                    ×
                </span>
            </li>
        `
        )
        .join('');
    document.querySelector('#errors').innerHTML = errorHtml;
}

/**
 * Removes error at index.
 * @param {number} errorIndex
 */
function dismissError(errorIndex) {
    delete STATE.errors[errorIndex];
    renderErrors(STATE.errors);
}

/**
 * Handle search results and singleband layers.
 *
 * @param {Array<Terracotta.IKey>} keys The keys to update results for.
 */
function updateSearchResults(remote_host = STATE.remote_host, keys = STATE.keys) {
    // initialize table header for search results
    const datasetTable = document.getElementById('search-results');
    datasetTable.innerHTML = '';
    const tableHeader = document.createElement('tr');
    for (let i = 0; i < keys.length; i++) {
        const headerEntry = document.createElement('th');
        headerEntry.innerHTML = keys[i].key;
        tableHeader.appendChild(headerEntry);
    }
    datasetTable.appendChild(tableHeader);

    // get key constraints from UI
    let key_constraints = [];

    /**
     * @type {NodeListOf<HTMLInputElement>}
     */
    const datasetSearchFields = document.querySelectorAll('#search-fields input');
    for (let i = 0; i < datasetSearchFields.length; i++) {
        const ds_field = datasetSearchFields[i];
        if (ds_field.value !== '') {
            key_constraints.push({ key: ds_field.name, value: ds_field.value });
        }
    }

    // Request datasets
    const datasetURL = assembleDatasetURL(remote_host, key_constraints, DATASETS_PER_PAGE, STATE.current_dataset_page);
    return httpGet(datasetURL).then((res) => {
        updateDatasetList(remote_host, res.datasets, keys);
    });
}

/**
 * Refreshes the dataset list.
 *
 * @param {string} remote_host
 * @param {Array<Terracotta.IDataset>} datasets
 * @param {Array<Terracotta.IKey>} keys
 */
function updateDatasetList(remote_host = STATE.remote_host, datasets, keys) {
    let datasetTable = document.getElementById('search-results');

    // disable next page if there are no more datasets
    /**
     * @type {HTMLButtonElement }
     */
    let next_page_button = document.querySelector('#next-page');
    if (datasets.length < DATASETS_PER_PAGE) {
        next_page_button.disabled = true;
    } else {
        next_page_button.disabled = false;
    }

    // update table rows
    if (datasets.length === 0) {
        let resultRow = document.createElement('tr');
        resultRow.innerHTML = `<td colspan=${keys.length}>No datasets found</td>`;
        datasetTable.appendChild(resultRow);
        return;
    }

    for (let i = 0; i < datasets.length; i++) {
        let currentDataset = datasets[i];
        let resultRow = document.createElement('tr');
        let ds_keys = [];
        for (let j = 0; j < keys.length; j++) {
            let resultEntry = document.createElement('td');
            ds_keys[j] = currentDataset[keys[j].key];
            resultEntry.innerHTML = ds_keys[j];
            resultRow.appendChild(resultEntry);
        }
        resultRow.id = `dataset-${serializeKeys(ds_keys)}`;
        if (STATE.activeSinglebandLayer && compareArray(STATE.activeSinglebandLayer.keys, ds_keys)) {
            resultRow.classList.add('active');
        }
        resultRow.classList.add('clickable');
        resultRow.addEventListener('click', toggleSinglebandMapLayer.bind(null, ds_keys));
        resultRow.addEventListener('mouseenter', toggleDatasetMouseover.bind(null, resultRow));
        resultRow.addEventListener('mouseleave', toggleDatasetMouseover.bind(null, null));

        // show thumbnails
        let detailsRow = document.createElement('tr');
        let thumbnailUrl = assembleSinglebandURL(remote_host, ds_keys, null, true);
        detailsRow.innerHTML = `<td colspan=${keys.length}><img src=${thumbnailUrl} class='thumbnail-image'></td>`;
        resultRow.appendChild(detailsRow);

        datasetTable.appendChild(resultRow);

        // retrieve metadata
        httpGet(assembleMetadataURL(remote_host, ds_keys)).then((metadata) => storeMetadata(metadata));
    }
}

/**
 * Increments the dataset result page by the provided step.
 * This method is called from app.html.
 *
 * @param {number} step
 * @global
 */
function incrementResultsPage(step) {
    STATE.current_dataset_page += step;
    updatePageControls();
    updateSearchResults();
}

/**
 * Updates the page counter & prev page button.
 */
function updatePageControls() {
    document.getElementById('page-counter').innerHTML = String(STATE.current_dataset_page + 1);
    /**
     * @type {HTMLButtonElement}
     */
    let prevPageButton = document.querySelector('#prev-page');
    if (STATE.current_dataset_page > 0) {
        prevPageButton.disabled = false;
    } else {
        prevPageButton.disabled = true;
    }
}

/**
 * Triggered by a change in the colormap selector in app.html.
 * @global
 */
function updateColormap() {
    /**
     * @type {HTMLSelectElement}
     */
    const colormapSelector = document.querySelector('select#colormap-selector');
    STATE.current_colormap = colormapSelector.selectedOptions[0].value;

    /**
     * @type {HTMLElement}
     */
    let slider = document.querySelector('.singleband-slider .noUi-connect');
    let colorbar = STATE.colormap_values[STATE.current_colormap];

    if (!colorbar) {
        return false;
    }

    let gradient = 'linear-gradient(to right';
    for (let i = 0; i < colorbar.length; i++) { 
        gradient += `, rgb(${colorbar[i].join(',')})`;
    }
    gradient += ')';
    slider.style.backgroundImage = gradient;

    if (STATE.activeSinglebandLayer == null) return;

    // toggle layer on and off to reload
    const ds_keys = STATE.activeSinglebandLayer.keys;
    updateSinglebandLayer(ds_keys, false);
}


/**
 * Updates thumbnail preview
 * @param {HTMLImageElement} img 
 * @param {boolean} show 
 */
function showCurrentThumnbnail(img, show) {
    const thumbnail = document.getElementById('thumbnail-holder');
    if (show) {
        var backgroundProperty = `url(${img.src})`;
        thumbnail.style.backgroundImage = backgroundProperty;
    }
    else {
        thumbnail.style.backgroundImage = 'none';
    }
}


/**
 * Adds a footprint overlay to map
 * @param {HTMLElement} datasetTable
 */
function toggleDatasetMouseover(datasetTable) {
    if (STATE.overlayLayer != null) {
        STATE.map.removeLayer(STATE.overlayLayer);
    }

    if (datasetTable == null) {
        showCurrentThumnbnail(null, false);
        return;
    }
    showCurrentThumnbnail(datasetTable.querySelector('img'), true);
    /**
     * @type {NodeListOf<HTMLTableCellElement>}
     */
    const tdElements = datasetTable.querySelectorAll('td');
    const keys = [];
    for (let i = 0; i < tdElements.length; i++) {
        if (tdElements[i].parentElement.classList.contains('clickable')) keys.push(tdElements[i].innerHTML);
    }

    const layer_id = serializeKeys(keys);
    const metadata = STATE.dataset_metadata[layer_id];
 
    if (!metadata) return;

    STATE.overlayLayer = L.geoJSON(metadata.convex_hull, {
        style: {
            color: '#0B4566',
            weight: 5,
            opacity: 0.65
        }
    }).addTo(STATE.map);
}


/**
 * Toggle active singleband layer.
 * 
 * @global
 * @param {Array<string>} ds_keys
 * @param {boolean} resetView
 */
function toggleSinglebandMapLayer(ds_keys, resetView = true) {
    let currentKeys;
    if (STATE.activeSinglebandLayer) {
        currentKeys = STATE.activeSinglebandLayer.keys;
    }

    resetLayerState();

    if (!ds_keys || compareArray(currentKeys, ds_keys)) {
        return;
    }

    const layer_id = serializeKeys(ds_keys);
    const metadata = STATE.dataset_metadata[layer_id];
    /**
     * @type {noUiSlider.SliderElement}
     */
    const singlebandSlider = document.querySelector('#singlebandSlider');

    if (metadata) {
        const last = metadata.percentiles.length - 1;
        STATE.current_singleband_stretch = singlebandStretchProxy([
            metadata.percentiles[2],
            metadata.percentiles[last - 2]
        ]);
        singlebandSlider.noUiSlider.updateOptions({
            range: {
                min: metadata.range[0],
                max: metadata.range[1]
            }
        });
    }
    updateSinglebandStretch(false);
    updateSinglebandLayer(ds_keys, resetView);
}


/**
 * Switch current active layer to the given singleband dataset.
 * 
 * @param {Array<string>} ds_keys Keys of new layer
 * @param {boolean} resetView Fly to new dataset if not already on screen
 */
function updateSinglebandLayer(ds_keys, resetView = true) {
    removeRasterLayer();
    activateRGBorSingleBand(false, true);

    const layer_id = serializeKeys(ds_keys);
    const metadata = STATE.dataset_metadata[layer_id];

    let layer_options = {};
    if (STATE.current_colormap) {
        layer_options.colormap = STATE.current_colormap;
    }
    if (STATE.current_singleband_stretch) {
        layer_options.stretch_range = JSON.stringify(STATE.current_singleband_stretch);
    }
    const layer_url = assembleSinglebandURL(STATE.remote_host, ds_keys, layer_options);
    STATE.activeSinglebandLayer = {
        keys: ds_keys,
        layer: L.tileLayer(layer_url).addTo(STATE.map)
    };

    const dataset_layer = document.getElementById(`dataset-${layer_id}`);

    if (dataset_layer) {
        // Depending on search, the dataset layer might not be present in the DOM.
        dataset_layer.classList.add('active');
    }

    document.querySelector('.singleband-slider').removeAttribute('disabled');

    if (resetView && metadata) {
        const screen = STATE.map.getBounds();
        const screenBounds = [
            screen._southWest.lng,
            screen._southWest.lat,
            screen._northEast.lng,
            screen._northEast.lat
        ];
        const dsBounds = metadata.bounds;
        const screenCover = calcScreenCovered(dsBounds, screenBounds);
        if (screenCover < 0.1) STATE.map.flyToBounds(L.latLngBounds([dsBounds[1], dsBounds[0]], [dsBounds[3], dsBounds[2]]));
    }
}

/**
 * Checks how much of area is in screen to determine zooming behavior
 * @param {Array[number]} dsBounds bounding box of TC dataset [w, s, e, n]
 * @param {Array[number]} screenBounds bouding box of user's screen [w, s, e, n]
 *
 * @return {number} ratio of screen covered by dataset in range (0, 1)
 */ 
function calcScreenCovered(dsBounds, screenBounds){
    const x_overlap = Math.max(0, Math.min(dsBounds[2], screenBounds[2]) - Math.max(dsBounds[0], screenBounds[0]));
    const y_overlap = Math.max(0, Math.min(dsBounds[3], screenBounds[3]) - Math.max(dsBounds[1], screenBounds[1]));
    const overlapArea = x_overlap * y_overlap;
    const screenArea = (screenBounds[3] - screenBounds[1]) * (screenBounds[2] - screenBounds[0]);
    return overlapArea / screenArea;
}

/**
 * Updates page controls & search results when search changes.
 */
function searchFieldChanged() {
    STATE.current_dataset_page = 0;
    updatePageControls();
    updateSearchResults();
}

// ===================================================
// Handle RGB layer controls
// ===================================================

/**
 * Reset RGB band selectors
 * 
 * @param {boolean} enabled 
 */
function resetRgbSelectors(enabled) {
    /**
     * @type {NodeListOf<HTMLInputElement>}
     */
    let rgbSelectors = document.querySelectorAll('.rgb-selector');
    for (let i = 0; i < rgbSelectors.length; i++) {
        rgbSelectors[i].innerHTML = '<option value="">-</option>';
        rgbSelectors[i].disabled = !enabled;
    }
}

/**
 * Triggered when a search field is changed.
 * Does nothing unless all search fields are filled in.
 */
function rgbSearchFieldChanged() {
    const remote_host = STATE.remote_host;
    const keys = STATE.keys;

    // if all RGB search fields are filled in, populate band selectors
    /**
     * @type {NodeListOf<HTMLSelectElement>}
     */
    let searchFields = document.querySelectorAll('#rgb-search-fields > input');

    let searchKeys = [];
    for (let i = 0; i < searchFields.length; i++) {
        if (!searchFields[i].value) {
            resetRgbSelectors(false);
            return;
        }
        searchKeys[i] = {
            key: keys[i].key,
            value: searchFields[i].value
        };
    }

    const datasetURL = assembleDatasetURL(remote_host, searchKeys, 1000, 0);
    return httpGet(datasetURL).then((res) => {
        populateRgbPickers(remote_host, res.datasets, keys);
    });
}

/**
 * Populate RGB band pickers after all search fields are filled in
 * 
 * @param {string} remote_host 
 * @param {Array<Terracotta.IDataset>} rgbDatasets 
 * @param {Array<Terracotta.IKey>} keys 
 */
function populateRgbPickers(remote_host, rgbDatasets, keys) {
    const lastKey = keys[keys.length - 1].key;

    resetRgbSelectors(true);
    rgbSelectorChanged();

    const rgbSelectors = [
        document.querySelector('.rgb-selector#R'),
        document.querySelector('.rgb-selector#G'),
        document.querySelector('.rgb-selector#B')
    ];

    const rgbDataPromises = rgbDatasets.map((ds) => {
        for (let j = 0; j < rgbSelectors.length; j++) {
            let option = document.createElement('option');
            option.innerHTML = ds[lastKey];
            option.value = ds[lastKey];
            rgbSelectors[j].appendChild(option);
        }

        // retrieve metadata
        let ds_keys = [];
        for (let j = 0; j < keys.length; j++) {
            ds_keys[j] = ds[keys[j].key];
        }

        return httpGet(assembleMetadataURL(remote_host, ds_keys)).then((metadata) => storeMetadata(metadata));
    });

    return Promise.all(rgbDataPromises);
}


/**
 * Used in app.html as 'onchange' event for .rgb-selector.
 * @global
 */
function rgbSelectorChanged() {
    const currentRgbLayer = STATE.activeRgbLayer;
    resetLayerState();

    /**
     * @type {NodeListOf<HTMLInputElement>}
     */
    let searchFields = document.querySelectorAll('#rgb-search-fields > input');

    let firstKeys = [];
    for (let i = 0; i < searchFields.length; i++) {
        firstKeys[i] = searchFields[i].value;
    }

    /**
     * @type {Array<HTMLSelectElement>}
     */
    const rgbSelectors = [
        document.querySelector('.rgb-selector#R'),
        document.querySelector('.rgb-selector#G'),
        document.querySelector('.rgb-selector#B')
    ];

    let lastKeys = [];
    for (let i = 0; i < rgbSelectors.length; i++) {
        if (!rgbSelectors[i].value){
            return;
     }
       lastKeys[i] = rgbSelectors[i].value;
    }

    if (currentRgbLayer &&
        compareArray(firstKeys, currentRgbLayer.index_keys) &&
        compareArray(lastKeys, currentRgbLayer.rgb_keys)) {
            return;
        }

    // initialize sliders
    /**
     * @type {Array<noUiSlider.SliderElement>}
     */
    const rgbSliders = [
        document.querySelector('.rgb-slider#R'),
        document.querySelector('.rgb-slider#G'),
        document.querySelector('.rgb-slider#B')
    ];
    for (let i = 0; i < 3; i++) {
        const someKeys = serializeKeys(firstKeys.concat([lastKeys[i]]));
        const metadata = STATE.dataset_metadata[someKeys];
        if (metadata != null) {
            const last = metadata.percentiles.length - 1;
            rgbSliders[i].noUiSlider.updateOptions({
                range: {
                    min: metadata.range[0],
                    max: metadata.range[1]
                }
            });
            STATE.current_rgb_stretch[i] = rgbStretchProxy([
                metadata.percentiles[2],
                metadata.percentiles[last - 2]
            ]);
        }
    }
    updateRGBStretch(false);
    updateRGBLayer(firstKeys, lastKeys);
}


/** 
 * Reset all layer state
 * (remove layers from map, deactivate navigation section, clear info box)
 */
function resetLayerState() {
    removeRasterLayer();
    activateRGBorSingleBand(false, false);
    document.getElementById('layerInfo__container').style.display = 'none';
}


/**
 * Remove all current layers from map
 */
function removeRasterLayer() {
    if (STATE.activeRgbLayer != null) {
        STATE.map.removeLayer(STATE.activeRgbLayer.layer);
        STATE.activeRgbLayer = null;
    }

    if (STATE.activeSinglebandLayer != null) {
        STATE.map.removeLayer(STATE.activeSinglebandLayer.layer);
        STATE.activeSinglebandLayer = null;
    }
}


/**
 * Toggle RGB layer on map
 * @param {Array<string>} firstKeys first keys of the layer
 * @param {Array<string>} lastKeys last keys of the layer [r, g, b]
 * @param {boolean} resetView fly to dataset location if not already visible
 */
function updateRGBLayer(firstKeys, lastKeys, resetView = true) {
    removeRasterLayer();
    activateRGBorSingleBand(true, false);

    let layerOptions = {};
    layerOptions.r_range = JSON.stringify(STATE.current_rgb_stretch[0]);
    layerOptions.g_range = JSON.stringify(STATE.current_rgb_stretch[1]);
    layerOptions.b_range = JSON.stringify(STATE.current_rgb_stretch[2]);

    const layer_url = assembleRgbUrl(STATE.remote_host, firstKeys, lastKeys, layerOptions, false);

    updateComputedUrl(layer_url, null);
    
    STATE.activeRgbLayer = {
        index_keys: firstKeys,
        rgb_keys: lastKeys,
        layer: L.tileLayer(layer_url).addTo(STATE.map)
    };

    const someKeys = serializeKeys(firstKeys.concat([lastKeys[0]]));
    const metadata = STATE.dataset_metadata[someKeys];

    if (resetView && metadata != null) {
        const screen = STATE.map.getBounds();
        const screenBounds = [
            screen._southWest.lng,
            screen._southWest.lat,
            screen._northEast.lng,
            screen._northEast.lat
        ];
        const dsBounds = metadata.bounds;
        const screenCover = calcScreenCovered(dsBounds, screenBounds);
        if (screenCover < 0.1) STATE.map.flyToBounds(L.latLngBounds([dsBounds[1], dsBounds[0]], [dsBounds[3], dsBounds[2]]));
    }
}

/**
 * Toggles 'disabled' and styling on  element when switching between RGB and Singleband
 * @param {boolean} rgbActive
 * @param {boolean} singlebandActive
 */ 
function activateRGBorSingleBand(rgbActive, singlebandActive){
    /**
     * @type {NodeListOf<noUiSlider.SliderElement>}
     */
    const rgbSliders = document.querySelectorAll('#rgb-selectors .rgb-slider');

    /**
     * @type {NodeListOf<HTMLInputElement>}
     */
    const rgbSliderInput = document.querySelectorAll('#rgb-selectors input');

    if(rgbActive){
        for(let i = 0; i < rgbSliders.length; i++){
            rgbSliders[i].removeAttribute('disabled');
            rgbSliders[i].style.filter = 'grayscale(0)';
        }
        for(let j = 0; j < rgbSliderInput.length; j++){ rgbSliderInput[j].disabled = false; }
    } else {
        for (let i = 0; i < rgbSliders.length; i++) {
            rgbSliders[i].setAttribute('disabled', 'true');
            rgbSliders[i].style.filter = 'grayscale(1)';
        }
        for (let j = 0; j < rgbSliderInput.length; j++) { rgbSliderInput[j].disabled = true; }
    }

    /**
     * @type {noUiSlider.SliderElement}
     */
    const singleBandSlider = document.querySelector('#singlebandSlider');
    /**
     * @type {NodeListOf<noUiSlider.SliderElement>}
     */
    const singleBandInputs = document.querySelectorAll('#contrast-wrapper input');
    const colormapSelector = document.querySelector('#colormap-selector');

    if (singlebandActive) {
        colormapSelector.removeAttribute('disabled');
        singleBandSlider.removeAttribute('disabled');
        singleBandSlider.style.filter = 'grayscale(0)';
        for (let k = 0; k < singleBandInputs.length; k++) { singleBandInputs[k].removeAttribute('disabled'); }
    } else {
        colormapSelector.setAttribute('disabled', 'true');
        singleBandSlider.setAttribute('disabled', 'true');
        singleBandSlider.style.filter = 'grayscale(1)';
        const currentActiveRows = document.querySelectorAll('#search-results .active');
        for (let i = 0; i < currentActiveRows.length; i++) {
            currentActiveRows[i].classList.remove('active');
        }
        for (let k = 0; k < singleBandInputs.length; k++) { singleBandInputs[k].setAttribute('disabled', 'true'); }
    }
}

/**
 * Updates Layer info container with current URL and metadata 
 * @param {string} url
 * @param {Array<string>} keys Dataset keys i.e. [<type>, <date>, <id>, <band>].
 */ 
function updateComputedUrl(url, keys = null){
    const computedUrl = document.getElementById('layerInfo__URL');
    const layerInfoParent = document.getElementById('layerInfo__container');
    if(layerInfoParent.style.display !== 'block'){
        layerInfoParent.style.display = 'block';
        computedUrl.parentElement.style.display = 'block';
    }
    computedUrl.innerHTML = `<b>current XYZ URL - </b>${url}`;
    let metadata = null;
    if (keys != null) {
        metadata = STATE.dataset_metadata[serializeKeys(keys)];
    }
    updateMetadataText(metadata);
}

/**
 * Updates Layer info container with metadata text
 * @param {Terracotta.IMetadata} metadata Dataset metadata
 */ 
function updateMetadataText(metadata){
    const metadataField = document.getElementById('layerInfo__metadata');
    if(!metadata){
        metadataField.style.display = 'none';
        return;
    }
    metadataField.style.display = 'block'
    metadataField.innerHTML = '<b>current metadata -</b> ';
    if(metadata.mean) metadataField.innerHTML += `mean: ${metadata.mean.toFixed(2)}`;
    if(metadata.range) metadataField.innerHTML += ` range: ${JSON.stringify(metadata.range)}`;
    if(metadata.stdev) metadataField.innerHTML += ` stdev: ${metadata.stdev.toFixed(2)}`;
    if(metadata.valid_percentage) metadataField.innerHTML += ` valid_percentage: ${metadata.valid_percentage.toFixed(2)}`;
    if(Object.keys(metadata.metadata).length > 0) metadataField.innerHTML += ` metadata: ${JSON.stringify(metadata.metadata)}`;
}


/**
 *  Called in app.html on Details info toggle
 * @global
 */
function toggleDetails() {
    const details = document.getElementById('details__content');
    details.style.display = details.style.display === 'block' ? 'none' : 'block';
}


/**
 *  Called after initializeApp. adds event listeners to Text fields for controlling sliders through text input.
 */
function addListenersToSliderRanges(){
    document.querySelector('#singleband-value-lower').addEventListener(
        'change',
        function(){STATE.current_singleband_stretch[0] = parseFloat(this.value);}
    );
    document.querySelector('#singleband-value-upper').addEventListener(
        'change',
        function(){STATE.current_singleband_stretch[1] = parseFloat(this.value);}
    );

    const rgbIds = ['R', 'G', 'B'];
    const handles = ['lower', 'upper'];
    for (let i = 0; i < rgbIds.length; i++) {
        for (let j = 0; j < handles.length; j++) { 
            let rgbInput = document.querySelector(`.rgb-value-${handles[j]}#${rgbIds[i]}`);
            rgbInput.addEventListener(
                'change',
                function () { STATE.current_rgb_stretch[i][j] = parseFloat(this.value); }
            );
        }
    }
}


/**
 *  Called in app.html on Layer info toggle
 * @global
 */
function toggleLayerInfo(){
    const layerContent = document.getElementById('layerInfo__container--content');
    const layerToggle = document.getElementById('layerInfo__toggle--icon');
    layerToggle.innerHTML = layerToggle.innerHTML === '×' ? 'i' : '×';
    layerContent.style.display = layerContent.style.display === 'block' ? 'none' : 'block';
}

/**
 *  Updates layer after slider interaction
 */
function updateSinglebandStretch(reloadLayer = true){
    const bandStretch = STATE.current_singleband_stretch;

    /**
     * @type {noUiSlider.SliderElement}
     */
    const slider = document.querySelector('.singleband-slider');
    slider.noUiSlider.set(bandStretch);

    /**
     * @type {HTMLInputElement}
     */
    const lowerLabel = document.querySelector('#singleband-value-lower');
    lowerLabel.value = bandStretch[0];

    /**
     * @type {HTMLInputElement}
     */
    const upperLabel = document.querySelector('#singleband-value-upper');
    upperLabel.value = bandStretch[1];

    if (reloadLayer && STATE.activeSinglebandLayer) {
        const currentKeys = STATE.activeSinglebandLayer.keys;
        updateSinglebandLayer(currentKeys, false);
    }
}

/**
 *  Updates layer after slider interaction
 */
function updateRGBStretch(reloadLayer = true){
    const rgbIds = ['R', 'G', 'B'];
    for (let i = 0; i < rgbIds.length; i++) {
        const id = rgbIds[i];
        const bandStretch = STATE.current_rgb_stretch[i];

        /**
         * @type {noUiSlider.SliderElement}
         */
        const slider = document.querySelector(`.rgb-slider#${id}`);
        slider.noUiSlider.set(bandStretch);

        /**
         * @type {HTMLInputElement}
         */
        const lowerLabel = document.querySelector(`.rgb-value-lower#${id}`);
        lowerLabel.value = String(bandStretch[0]);

        /**
         * @type {HTMLInputElement}
         */
        const upperLabel = document.querySelector(`.rgb-value-upper#${id}`);
        upperLabel.value = String(bandStretch[1]);
    }

    if (reloadLayer && STATE.activeRgbLayer) {
        const currentIndexKeys = STATE.activeRgbLayer.index_keys;
        const currentRgbKeys = STATE.activeRgbLayer.rgb_keys;
        updateRGBLayer(currentIndexKeys, currentRgbKeys, false);
    }
}


/**
 *  Called after initializeApp. adds event listeners to resize bar
 */
function addResizeListeners() {
    const BORDER_SIZE = 6;
    const panel = document.getElementById('resizable__buffer');
    panel.addEventListener('mousedown', function (e) {
        e.preventDefault();
        if (e.offsetX < BORDER_SIZE) {
            STATE.m_pos = e.x;
            document.addEventListener('mousemove', resize, false);
        }
    }, false);

    document.addEventListener('mouseup', function () {
        document.removeEventListener('mousemove', resize, false);
    }, false);
}

/**
 *  Called after InitUI, removes spinner.
 */
function removeSpinner() {
    document.getElementById('loader__container').style.display = 'none';
}


/**
 *  Resizes map and sidebar, repositions resize bar
 */
function resize(e) {
    const sidebar = document.getElementById('controls');
    const resizeBuffer = document.getElementById('resizable__buffer');
    const map = document.getElementById('map');
    const panel = document.getElementById('resizable__buffer');

    const dx = e.x - STATE.m_pos;
    STATE.m_pos = e.x;

    let posX = (parseInt(getComputedStyle(panel, '').marginLeft) + dx) + 'px';
    sidebar.style.width = (parseInt(getComputedStyle(panel, '').marginLeft) + dx - 50) + 'px';
    resizeBuffer.style.marginLeft = posX;
    map.style.left = posX;
}


/**
 *  Main entrypoint.
 *  Called in app.html on window.onload.
 *
 * @param {string} hostname The hostname of the remote Terracotta server (evaluated in map.html).
 * @global
 */
function initializeApp(hostname) {
    // sanitize hostname
    if (hostname.charAt(hostname.length - 1) === '/') {
        hostname = hostname.slice(0, hostname.length - 1);
    }

    STATE.remote_host = hostname;

    getColormapValues(hostname)
        .then(() => getKeys(hostname))
        .then((keys) => {
            STATE.keys = keys;
            initUI(hostname, keys);
            updateSearchResults();
            let osmUrl = 'http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
            let osmAttrib = 'Map data © <a href="http://openstreetmap.org">OpenStreetMap</a> contributors';
            let osmBase = L.tileLayer(osmUrl, { attribution: osmAttrib });
            STATE.map = L.map('map', {
                center: [0, 0],
                zoom: 2,
                layers: [osmBase]
            });
        });
    addListenersToSliderRanges();
    addResizeListeners();
}
