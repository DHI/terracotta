/// <reference path="./types/leaflet.d.ts" />
/// <reference path="./types/no-ui-slider.d.ts" />
/// <reference path="./types/map.d.ts" />

/* BEWARE! THERE BE DRAGONS! 🐉

Big parts of following file were written by a Python programmer with minimal exposure
to idiomatic Javascript. It should not serve as an authoritive reference on how a
frontend for Terracotta should be written.

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

const DATASETS_PER_PAGE = 5;
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
    current_singleband_stretch: [],
    current_rgb_stretch: [],
    map: undefined,
    overlayLayer: undefined,
    activeSinglebandLayer: undefined,
    activeRgbLayer: undefined
};


// ===================================================
// Convenience functions to get valid Terracotta URLs.
// ===================================================

/**
 * As it says, gets keys so the app can be initialized.
 *
 * @param {string} remote_host
 *
 * @return { Promise<Array<Terracotta.IKey>> }
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
        request_url += '/' + ds_keys[i];
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
        request_url =
            remote_host + '/singleband/' + keys.join('/') + '/preview.png?tile_size=' + JSON.stringify(THUMBNAIL_SIZE);
    } else {
        request_url = remote_host + '/singleband/' + keys.join('/') + '/{z}/{x}/{y}.png';
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
    return request_url;
}

/**
 * @param {Array<string>} first_keys
 * @param {Array<number>} rgb_keys
 * @param {Terracotta.IOptions} options
 * @param {boolean} preview
 * @param {string} remote_host
 *
 * @return {string} rgb URL.
 */
function assembleRgbUrl(remote_host, first_keys, rgb_keys, options, preview) {
    let request_url;

    if (preview) {
        request_url =
            remote_host + '/rgb/' + first_keys.join('/') + '/preview.png?tile_size=' + JSON.stringify(THUMBNAIL_SIZE);
    } else {
        request_url = remote_host + '/rgb/' + first_keys.join('/') + '/{z}/{x}/{y}.png';
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
        keyEntry.innerHTML = '<b>' + keys[i].key + '</b>';
        if (keys[i].description != null) {
            keyEntry.innerHTML += ': ' + keys[i].description;
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
        searchField.placeholder = keys[i].key;
        searchField.addEventListener('change', rgbSearchFieldChanged);
        rgbSearchContainer.appendChild(searchField);
    }

    resetRgbSelectors(false);

    // create sliders
    let sliderDummyOptions = {
        start: [0.0, 1.0],
        range: { min: 0, max: 1 },
        connect: true,
        behaviour: 'drag'
    };

    /**
     * @type { noUiSlider.SliderElement }
     */
    let singlebandSlider = document.querySelector('.singleband-slider');
    noUiSlider.create(singlebandSlider, sliderDummyOptions).on('change.one', function() {
        STATE.current_singleband_stretch = singlebandSlider.noUiSlider.get();
        let currentKeys = STATE.activeSinglebandLayer.keys;
        // reload layer
        toggleSinglebandMapLayer();
        addSinglebandMapLayer(currentKeys, false);
    });
    singlebandSlider.noUiSlider.on('update', function(values, handle) {
        let showValue = [
            document.getElementById('singleband-value-lower'),
            document.getElementById('singleband-value-upper')
        ];
        showValue[handle].innerHTML = values[handle];
    });
    singlebandSlider.setAttribute('disabled', 'true');

    /**
     * @type {  NodeListOf<noUiSlider.SliderElement> }
     */
    let rgbSliders = document.querySelectorAll('.rgb-slider');
    let rgbIds = ['R', 'G', 'B'];
    for (let i = 0; i < rgbSliders.length; i++) {
        noUiSlider.create(rgbSliders[i], sliderDummyOptions).on('change.one', function() {
            STATE.current_rgb_stretch = [
                rgbSliders[0].noUiSlider.get(),
                rgbSliders[1].noUiSlider.get(),
                rgbSliders[2].noUiSlider.get()
            ];
            let currentIndexKeys = STATE.activeRgbLayer.index_keys;
            let currentRgbKeys = STATE.activeRgbLayer.rgb_keys;
            // reload layer
            toggleRgbLayer();
            toggleRgbLayer(currentIndexKeys, currentRgbKeys, false);
        });

        rgbSliders[i].noUiSlider.on(
            'update',
            function(id, values, handle) {
                let showValue = [
                    document.querySelector('.rgb-value-lower#' + id),
                    document.querySelector('.rgb-value-upper#' + id)
                ];
                showValue[handle].innerHTML = values[handle];
            }.bind(null, rgbIds[i])
        );

        rgbSliders[i].setAttribute('disabled', 'true');
    }

    updateColormap();
}

// ===================================================
// Helper functions
// ===================================================

/**
 * Concats an array of strings, separated by '/'.
 *
 * @param {Array<string>} keys
 *
 * @return {string}
 */
function serializeKeys(keys) {
    return keys.join('/');
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
                <span onclick="dismissError.call(null, ${index})">
                    &times;
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
 * @param { Array<Terracotta.IKey> } keys The keys to update results for.
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
     * @type { NodeListOf<HTMLInputElement> }
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
function updateDatasetList(remote_host, datasets, keys) {
    let datasetTable = document.getElementById('search-results');

    // disable next page if there are no more datasets
    /**
     * @type { HTMLButtonElement }
     */
    let next_page_button = document.querySelector('#next-page');
    if (datasets.length < DATASETS_PER_PAGE) {
        next_page_button.disabled = true;
    } else {
        next_page_button.disabled = false;
    }

    // update table rows
    if (datasets == null) {
        let resultRow = document.createElement('tr');
        resultRow.innerHTML = [
            '<td colspan=',
            keys.length,
            '>',
            '<span class="error">',
            'Error while querying datasets',
            '</span>',
            '</td>'
        ].join('');
        datasetTable.appendChild(resultRow);
        return;
    }

    if (datasets.length === 0) {
        let resultRow = document.createElement('tr');
        resultRow.innerHTML = '<td colspan=' + keys.length + '>No datasets found</td>';
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
        resultRow.id = 'dataset-' + serializeKeys(ds_keys);
        resultRow.classList.add('clickable');
        resultRow.addEventListener('click', toggleSinglebandMapLayer.bind(null, ds_keys));
        resultRow.addEventListener('mouseenter', toggleFootprintOverlay.bind(null, ds_keys));
        resultRow.addEventListener('mouseleave', toggleFootprintOverlay.bind(null, null));

        // show thumbnails
        let detailsRow = document.createElement('tr');
        let thumbnailUrl = assembleSinglebandURL(remote_host, ds_keys, null, true);
        detailsRow.innerHTML = '<td colspan=' + keys.length + '><img src="' + thumbnailUrl + '"></td>';
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
    document.getElementById('page-counter').innerHTML = `${STATE.current_dataset_page + 1}`;

    /**
     * @type { HTMLButtonElement }
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
     * @type { HTMLSelectElement }
     */
    const colormapSelector = document.querySelector('select#colormap-selector');
    STATE.current_colormap = colormapSelector.selectedOptions[0].value;

    /**
     * @type { HTMLElement }
     */
    let slider = document.querySelector('.singleband-slider .noUi-connect');
    let colorbar = STATE.colormap_values[STATE.current_colormap];

    if (!colorbar) {
        return false;
    }

    let gradient = 'linear-gradient(to right';
    for (let i = 0; i < colorbar.length; i++) {
        gradient += ', rgb(' + colorbar[i].join(',') + ')';
    }
    gradient += ')';
    slider.style.backgroundImage = gradient;

    if (STATE.activeSinglebandLayer == null) return;

    // toggle layer on and off to reload
    let ds_keys = STATE.activeSinglebandLayer.keys;
    toggleSinglebandMapLayer();
    addSinglebandMapLayer(ds_keys, false);
}

/**
 * Adds a footprint overlay to map
 * @param {Array<string>} keys
 */
function toggleFootprintOverlay(keys) {
    if (STATE.overlayLayer != null) {
        STATE.map.removeLayer(STATE.overlayLayer);
    }

    if (keys == null) {
        return;
    }
    const layer_id = serializeKeys(keys);
    const metadata = STATE.dataset_metadata[layer_id];

    if (metadata == null) return;

    STATE.overlayLayer = L.geoJSON(metadata.convex_hull, {
        style: {
            color: '#ff7800',
            weight: 5,
            opacity: 0.65
        }
    }).addTo(STATE.map);
}

/**
 * @param {Array<string>} [ds_keys]
 * @param {boolean} [resetView]
 */
function toggleSinglebandMapLayer(ds_keys, resetView = true) {
    /**
     * @type { noUiSlider.SliderElement }
     */
    let singlebandSlider = document.querySelector('.singleband-slider');

    if (STATE.activeSinglebandLayer != null || ds_keys == null) {
        STATE.map.removeLayer(STATE.activeSinglebandLayer.layer);
        const currentKeys = STATE.activeSinglebandLayer.keys;
        STATE.activeSinglebandLayer = null;

        const currentActiveRow = document.querySelector('#search-results > .active');
        if (currentActiveRow != null) {
            currentActiveRow.classList.remove('active');
        }

        singlebandSlider.setAttribute('disabled', 'true');

        if (ds_keys === null || currentKeys === ds_keys) {
            return;
        }
    }

    if (STATE.activeRgbLayer !== null) {
        toggleRgbLayer();
    }

    if (ds_keys) {
        const layer_id = serializeKeys(ds_keys);
        const metadata = STATE.dataset_metadata[layer_id];

        if (metadata != null) {
            const last = metadata.percentiles.length - 1;
            STATE.current_singleband_stretch = [metadata.percentiles[2], metadata.percentiles[last - 2]];
            singlebandSlider.noUiSlider.updateOptions({
                start: STATE.current_singleband_stretch,
                range: {
                    min: metadata.range[0],
                    '20%': metadata.percentiles[2],
                    '80%': metadata.percentiles[last - 2],
                    max: metadata.range[1]
                }
            });
        }

        addSinglebandMapLayer(ds_keys, resetView);
    }
}

function addSinglebandMapLayer(ds_keys, resetView = true) {
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

    const dataset_layer = document.getElementById('dataset-' + layer_id);

    if (dataset_layer) {
        // Depending on search, the dataset layer might not be present in the DOM.
        dataset_layer.classList.add('active');
    }

    document.querySelector('.singleband-slider').removeAttribute('disabled');

    if (resetView && metadata) {
        const [minLng, minLat, maxLng, maxLat] = metadata.bounds;
        STATE.map.flyToBounds(L.latLngBounds([minLat, minLng], [maxLat, maxLng]));
    }
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
function resetRgbSelectors(enabled) {
    /**
     * @type { NodeListOf<HTMLInputElement> }
     */
    let rgbSelectors = document.querySelectorAll('.rgb-selector');
    for (let i = 0; i < rgbSelectors.length; i++) {
        rgbSelectors[i].innerHTML = '<option value="">-</option>';
        rgbSelectors[i].disabled = !enabled;
    }
}

function rgbSearchFieldChanged() {
    const remote_host = STATE.remote_host;
    const keys = STATE.keys;

    // if all RGB search fields are filled in, populate band selectors
    /**
     * @type { NodeListOf<HTMLSelectElement> }
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

function populateRgbPickers(remote_host, rgbDatasets, keys) {
    const lastKey = keys[keys.length - 1].key;

    resetRgbSelectors(true);

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
    /**
     * @type { NodeListOf<HTMLInputElement> }
     */
    let searchFields = document.querySelectorAll('#rgb-search-fields > input');
    let firstKeys = [];
    for (let i = 0; i < searchFields.length; i++) {
        firstKeys[i] = searchFields[i].value;
    }

    /**
     * @type { Array<HTMLSelectElement> }
     */
    const rgbSelectors = [
        document.querySelector('.rgb-selector#R'),
        document.querySelector('.rgb-selector#G'),
        document.querySelector('.rgb-selector#B')
    ];
    let lastKeys = [];
    for (let i = 0; i < rgbSelectors.length; i++) {
        if (!rgbSelectors[i].value) return toggleRgbLayer();
        lastKeys[i] = rgbSelectors[i].value;
    }

    // initialize sliders
    /**
     * @type { Array<noUiSlider.SliderElement> }
     */
    const rgbSliders = [
        document.querySelector('.rgb-slider#R'),
        document.querySelector('.rgb-slider#G'),
        document.querySelector('.rgb-slider#B')
    ];
    STATE.current_rgb_stretch = [];
    for (let i = 0; i < 3; i++) {
        let someKeys = serializeKeys(firstKeys.concat([lastKeys[i]]));
        let metadata = STATE.dataset_metadata[someKeys];
        if (metadata != null) {
            let last = metadata.percentiles.length - 1;
            STATE.current_rgb_stretch[i] = [metadata.percentiles[2], metadata.percentiles[last - 2]];
            rgbSliders[i].noUiSlider.updateOptions({
                start: STATE.current_rgb_stretch[i],
                range: {
                    min: metadata.range[0],
                    '20%': metadata.percentiles[2],
                    '80%': metadata.percentiles[last - 2],
                    max: metadata.range[1]
                }
            });
        }
    }

    toggleRgbLayer(firstKeys, lastKeys);
}

function toggleRgbLayer(firstKeys, lastKeys, resetView = true) {
    const rgbControls = document.getElementById('rgb');

    if (STATE.activeRgbLayer != null) {
        STATE.map.removeLayer(STATE.activeRgbLayer.layer);
        let currentFirstKeys = STATE.activeRgbLayer.index_keys;
        let currentLastKeys = STATE.activeRgbLayer.rgb_keys;
        STATE.activeRgbLayer = null;
        rgbControls.classList.remove('active');

        if (firstKeys == null || lastKeys == null) {
            return;
        }

        if (
            serializeKeys(currentFirstKeys) === serializeKeys(firstKeys) &&
            serializeKeys(currentLastKeys) === serializeKeys(lastKeys)
        ) {
            return;
        }
    }

    if (firstKeys == null || lastKeys == null) {
        return;
    }

    if (STATE.activeSinglebandLayer != null) {
        toggleSinglebandMapLayer(STATE.activeSinglebandLayer.keys);
    }

    let layerOptions = {};
    if (STATE.current_rgb_stretch != null) {
        layerOptions.r_range = JSON.stringify(STATE.current_rgb_stretch[0]);
        layerOptions.g_range = JSON.stringify(STATE.current_rgb_stretch[1]);
        layerOptions.b_range = JSON.stringify(STATE.current_rgb_stretch[2]);
    }

    let layer_url = assembleRgbUrl(STATE.remote_host, firstKeys, lastKeys, layerOptions, false);

    STATE.activeRgbLayer = {
        index_keys: firstKeys,
        rgb_keys: lastKeys,
        layer: L.tileLayer(layer_url).addTo(STATE.map)
    };

    rgbControls.classList.add('active');
    let rgbSliders = document.querySelectorAll('.rgb-slider');
    for (let i = 0; i < rgbSliders.length; i++) {
        rgbSliders[i].removeAttribute('disabled');
    }

    let someKeys = serializeKeys(firstKeys.concat([lastKeys[0]]));
    let metadata = STATE.dataset_metadata[someKeys];

    if (resetView && metadata != null) {
        const [minLng, minLat, maxLng, maxLat] = metadata.bounds;
        STATE.map.flyToBounds(L.latLngBounds([minLat, minLng], [maxLat, maxLng]));
    }
}


/**
 *  Main entrypoint.
 *  Called in app.html on window.onload.
 *
 * @param {string} hostname The hostname of the remote Terracotta server (evaluated in map.html).
 * @global
 */
function initializeApp(hostname) {
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
}
