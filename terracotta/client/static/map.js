/// <reference path="./types/leaflet.d.ts" />
/// <reference path="./types/no-ui-slider.d.ts" />

/* BEWARE! THERE BE DRAGONS!

The following file was written by a Python programmer with minimal exposure
to idiomatic Javascript. It should not serve as an authoritive reference on
how a frontend for Terracotta should be written.
*/
/* Constants */

const datasets_per_page = 5;
const thumbnail_size = [128, 128];
const colormaps = [
    { display_name: 'Greyscale', id: 'greys_r' },
    { display_name: 'Viridis', id: 'viridis' },
    { display_name: 'Red-Blue', id: 'rdbu' },
    { display_name: 'Blue-Green', id: 'bugn' },
    { display_name: 'Yellow-Green', id: 'ylgn' },
    { display_name: 'Magma', id: 'magma' },
    { display_name: 'Earth', id: 'gist_earth' },
    { display_name: 'Ocean', id: 'ocean' }
];

/* Convenience functions to get valid Terracotta URLs */

function getKeys() {
    const http_request = new XMLHttpRequest();
    http_request.open('GET', remote_host + '/keys', false);
    http_request.send();

    if (http_request.status === 200) {
        return JSON.parse(http_request.responseText).keys;
    }
    return [];
}

function assembleDatasetURL(key_constraints, limit, page) {
    let request_url = remote_host + '/datasets?limit=' + limit + '&page=' + page;

    for (let i = 0; i < key_constraints.length; i++) {
        request_url += '&' + key_constraints[i].key + '=' + key_constraints[i].value;
    }
    return request_url;
}

function assembleMetadataURL(ds_keys) {
    let request_url = remote_host + '/metadata';
    for (let i = 0; i < ds_keys.length; i++) {
        request_url += '/' + ds_keys[i];
    }
    return request_url;
}

function assembleSinglebandURL(keys, options, preview) {
    let request_url;

    if (preview) {
        request_url =
        remote_host + '/singleband/' + keys.join('/') + '/preview.png?tile_size=' + JSON.stringify(thumbnail_size);
    } else {
        request_url = remote_host + '/singleband/' + keys.join('/') + '/{z}/{x}/{y}.png';
    }

    if (options == null) return request_url;

    var first = true;
    for (var option_key in options) {
        if (!options.hasOwnProperty(option_key)) continue;

        if (first) {
            request_url += '?' + option_key + '=' + options[option_key];
            first = false;
        } else {
            request_url += '&' + option_key + '=' + options[option_key];
        }
    }
    return request_url;
}

function assembleRgbUrl(first_keys, rgb_keys, options, preview) {
    if (preview) {
        var request_url =
        remote_host + '/rgb/' + first_keys.join('/') + '/preview.png?tile_size=' + JSON.stringify(thumbnail_size);
    } else {
        var request_url = remote_host + '/rgb/' + first_keys.join('/') + '/{z}/{x}/{y}.png';
    }

    request_url += '?r=' + rgb_keys[0] + '&g=' + rgb_keys[1] + '&b=' + rgb_keys[2];

    if (options == null) return request_url;

    for (var option_key in options) {
        if (!options.hasOwnProperty(option_key)) continue;
        request_url += '&' + option_key + '=' + options[option_key];
    }
    return request_url;
}

function assembleColormapUrl(colormap, num_values) {
    return remote_host + '/colormap?colormap=' + colormap + '&stretch_range=[0,1]&num_values=' + num_values;
}

/* Initializers */

function getColorbars() {
    for (let i = 0; i < colormaps.length; i++) {
        var cmap = colormaps[i].id;
        var req = new XMLHttpRequest();
        req.open('GET', assembleColormapUrl(cmap, 100));
        req.addEventListener(
            'load',
            function(req, cmap) {
                var response = JSON.parse(req.responseText).colormap;
                if (response != null) {
                    colorbars[cmap] = [];
                    for (var j = 0; j < 100; j++) {
                        colorbars[cmap][j] = response[j].rgb;
                    }
                }
            }.bind(null, req, cmap)
            );
            req.send();
        }
    }

    function initUI(keys) {
        // initialize list of keys and key descriptions
        var keyList = document.getElementById('key-list');
        keyList.innerHTML = '';
        for (let i = 0; i < keys.length; i++) {
            var keyEntry = document.createElement('li');
            keyEntry.innerHTML = '<b>' + keys[i].key + '</b>';
            if (keys[i].description != null) {
                keyEntry.innerHTML += ': ' + keys[i].description;
            }
            keyList.appendChild(keyEntry);
        }

        // initialize colormap selector
        var colormapSelector = document.getElementById('colormap-selector');
        colormapSelector.innerHTML = '';
        for (let i = 0; i < colormaps.length; i++) {
            var cmapOption = document.createElement('option');
            cmapOption.value = colormaps[i].id;
            cmapOption.innerHTML = colormaps[i].display_name;
            if (i == 0) {
                cmapOption.selected = true;
            }
            colormapSelector.appendChild(cmapOption);
        }

        // initialize search fields
        var searchContainer = document.getElementById('search-fields');
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
        var datasetTable = document.getElementById('search-results');
        datasetTable.innerHTML = '';
        var tableHeader = document.createElement('th');
        for (let i = 0; i < keys.length; i++) {
            const headerEntry = document.createElement('td');
            headerEntry.innerHTML = keys[i].key;
            tableHeader.appendChild(headerEntry);
        }
        datasetTable.appendChild(tableHeader);

        // initialize RGB search fields
        var searchContainer = document.getElementById('rgb-search-fields');
        searchContainer.innerHTML = '';
        for (let i = 0; i < keys.length - 1; i++) {
            const searchField = document.createElement('input');
            searchField.placeholder = keys[i].key;
            searchField.addEventListener('change', rgbSearchFieldChanged);
            searchContainer.appendChild(searchField);
        }

        resetRgbSelectors(false);

        // create sliders
        var sliderDummyOptions = {
            start: [0.0, 1.0],
            range: { min: 0, max: 1 },
            connect: true,
            behaviour: 'drag'
        };

        /**
        * @type { noUiSlider.SliderElement }
        */
        var singlebandSlider = document.querySelector('.singleband-slider');
        noUiSlider.create(singlebandSlider, sliderDummyOptions).on('change.one', function() {
            current_singleband_stretch = singlebandSlider.noUiSlider.get();
            var currentKeys = activeSinglebandLayer.keys;
            // reload layer
            toggleSinglebandMapLayer();
            addSinglebandMapLayer(currentKeys, false);
        });
        singlebandSlider.noUiSlider.on('update', function(values, handle) {
            var showValue = [
                document.getElementById('singleband-value-lower'),
                document.getElementById('singleband-value-upper')
            ];
            showValue[handle].innerHTML = values[handle];
        });
        singlebandSlider.setAttribute('disabled', 'true');

        /**
        * @type {  NodeListOf<noUiSlider.SliderElement> }
        */
        var rgbSliders = document.querySelectorAll('.rgb-slider');
        var rgbIds = ['R', 'G', 'B'];
        for (let i = 0; i < rgbSliders.length; i++) {
            noUiSlider.create(rgbSliders[i], sliderDummyOptions).on('change.one', function() {
                current_rgb_stretch = [
                    rgbSliders[0].noUiSlider.get(),
                    rgbSliders[1].noUiSlider.get(),
                    rgbSliders[2].noUiSlider.get()
                ];
                var currentIndexKeys = activeRgbLayer.index_keys;
                var currentRgbKeys = activeRgbLayer.rgb_keys;
                // reload layer
                toggleRgbLayer();
                toggleRgbLayer(currentIndexKeys, currentRgbKeys, false);
            });
            rgbSliders[i].noUiSlider.on(
                'update',
                function(id, values, handle) {
                    var showValue = [
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

        /* Helper functions */

        function serializeKeys(ds_keys) {
            return ds_keys.join('/');
        }

        function getDatasetCenter(metadata) {
            var bounds = metadata.bounds;
            return [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2];
        }

        function storeMetadata(e) {
            var req = e.target;
            var metadata = JSON.parse(req.responseText);
            var ds_keys = serializeKeys(Object.values(metadata.keys));
            dataset_metadata[ds_keys] = metadata;
        }

        /* Handle search results and singleband layers*/

        function updateSearchResults() {
            // initialize table header for search results
            var datasetTable = document.getElementById('search-results');
            datasetTable.innerHTML = '';
            var tableHeader = document.createElement('tr');
            for (let i = 0; i < keys.length; i++) {
                const headerEntry = document.createElement('th');
                headerEntry.innerHTML = keys[i].key;
                tableHeader.appendChild(headerEntry);
            }
            datasetTable.appendChild(tableHeader);

            // get key constraints from UI
            var key_constraints = [];

            /**
            * @type { NodeListOf<HTMLInputElement> }
            */
            var datasetSearchFields = document.querySelectorAll('#search-fields input');
            for (let i = 0; i < datasetSearchFields.length; i++) {
                var ds_field = datasetSearchFields[i];
                if (ds_field.value != '') {
                    key_constraints.push({ key: ds_field.name, value: ds_field.value });
                }
            }

            // request datasets
            var req = new XMLHttpRequest();
            req.open('GET', assembleDatasetURL(key_constraints, datasets_per_page, current_dataset_page));
            req.addEventListener('load', updateDatasetList.bind(null, req));
            req.send();
        }

        function updateDatasetList(request) {
            datasets = JSON.parse(request.responseText).datasets;
            var datasetTable = document.getElementById('search-results');

            // disable next page if there are no more datasets
            /**
            * @type { HTMLButtonElement }
            */
            var next_page_button = document.querySelector('#next-page');
            if (datasets.length < datasets_per_page) {
                next_page_button.disabled = true;
            } else {
                next_page_button.disabled = false;
            }

            // update table rows
            if (datasets == null) {
                var resultRow = document.createElement('tr');
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

            if (datasets.length == 0) {
                var resultRow = document.createElement('tr');
                resultRow.innerHTML = '<td colspan=' + keys.length + '>No datasets found</td>';
                datasetTable.appendChild(resultRow);
                return;
            }

            for (let i = 0; i < datasets.length; i++) {
                var currentDataset = datasets[i];
                var resultRow = document.createElement('tr');
                var ds_keys = [];
                for (var j = 0; j < keys.length; j++) {
                    var resultEntry = document.createElement('td');
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
                var detailsRow = document.createElement('tr');
                var thumbnailUrl = assembleSinglebandURL(ds_keys, null, true);
                detailsRow.innerHTML = '<td colspan=' + keys.length + '><img src="' + thumbnailUrl + '"></td>';
                resultRow.appendChild(detailsRow);

                datasetTable.appendChild(resultRow);

                // retrieve metadata
                var req = new XMLHttpRequest();
                req.open('GET', assembleMetadataURL(ds_keys));
                req.addEventListener('load', storeMetadata);
                req.send();
            }
        }

        function incrementResultsPage(step) {
            current_dataset_page += step;
            updatePageControls();
            updateSearchResults();
        }

        function updatePageControls() {
            document.getElementById('page-counter').innerHTML = current_dataset_page + 1;

            /**
            * @type { HTMLButtonElement }
            */
            var prevPageButton = document.querySelector('#prev-page');
            if (current_dataset_page > 0) {
                prevPageButton.disabled = false;
            } else {
                prevPageButton.disabled = true;
            }
        }

        function updateColormap() {
            /**
            * @type { HTMLSelectElement }
            */
            var colormapSelector = document.querySelector('select#colormap-selector');
            current_colormap = colormapSelector.selectedOptions[0].value;

            /**
            * @type { HTMLElement }
            */
            var slider = document.querySelector('.singleband-slider .noUi-connect');
            var colorbar = colorbars[current_colormap];
            var gradient = 'linear-gradient(to right';
            for (let i = 0; i < colorbar.length; i++) {
                gradient += ', rgb(' + colorbar[i].join(',') + ')';
            }
            gradient += ')';
            slider.style.backgroundImage = gradient;

            if (activeSinglebandLayer == null) return;

            // toggle layer on and off to reload
            var ds_keys = activeSinglebandLayer.keys;
            toggleSinglebandMapLayer();
            addSinglebandMapLayer(ds_keys, false);
        }

        function toggleFootprintOverlay(keys) {
            if (overlayLayer != null) {
                map.removeLayer(overlayLayer);
            }

            if (keys == null) {
                return;
            }
            var layer_id = serializeKeys(keys);
            var metadata = dataset_metadata[layer_id];

            if (metadata == null) return;

            overlayLayer = L.geoJSON(metadata.convex_hull, {
                style: {
                    color: '#ff7800',
                    weight: 5,
                    opacity: 0.65
                }
            }).addTo(map);
        }

        function toggleSinglebandMapLayer(ds_keys, resetView = true) {
            /**
            * @type { noUiSlider.SliderElement }
            */
            var singlebandSlider = document.querySelector('.singleband-slider');

            if (activeSinglebandLayer != null || ds_keys == null) {
                map.removeLayer(activeSinglebandLayer.layer);
                var currentKeys = activeSinglebandLayer.keys;
                activeSinglebandLayer = null;

                var currentActiveRow = document.querySelector('#search-results > .active');
                if (currentActiveRow != null) {
                    currentActiveRow.classList.remove('active');
                }

                singlebandSlider.setAttribute('disabled', 'true');

                if (ds_keys == null || currentKeys == ds_keys) {
                    return;
                }
            }

            if (activeRgbLayer != null) {
                toggleRgbLayer();
            }

            var layer_id = serializeKeys(ds_keys);
            var metadata = dataset_metadata[layer_id];

            if (metadata != null) {
                var last = metadata.percentiles.length - 1;
                current_singleband_stretch = [metadata.percentiles[2], metadata.percentiles[last - 2]];
                singlebandSlider.noUiSlider.updateOptions({
                    start: current_singleband_stretch,
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

        function addSinglebandMapLayer(ds_keys, resetView = true) {
            var layer_id = serializeKeys(ds_keys);
            var metadata = dataset_metadata[layer_id];

            var layer_options = {};
            if (current_colormap != null) {
                layer_options.colormap = current_colormap;
            }
            if (current_singleband_stretch != null) {
                layer_options.stretch_range = JSON.stringify(current_singleband_stretch);
            }
            var layer_url = assembleSinglebandURL(ds_keys, layer_options);

            activeSinglebandLayer = {
                keys: ds_keys,
                layer: L.tileLayer(layer_url).addTo(map)
            };

            document.getElementById('dataset-' + layer_id).classList.add('active');
            document.querySelector('.singleband-slider').removeAttribute('disabled');

            if (resetView && metadata != null) {
                map.flyTo(getDatasetCenter(metadata), 9);
            }
        }

        function searchFieldChanged() {
            current_dataset_page = 0;
            updatePageControls();
            updateSearchResults();
        }

        /* Handle RGB layer controls */

        function resetRgbSelectors(enabled) {
            /**
            * @type { NodeListOf<HTMLInputElement> }
            */
            var rgbSelectors = document.querySelectorAll('.rgb-selector');
            for (let i = 0; i < rgbSelectors.length; i++) {
                rgbSelectors[i].innerHTML = '<option value="">-</option>';
                rgbSelectors[i].disabled = !enabled;
            }
        }

        function rgbSearchFieldChanged() {
            // if all RGB search fields are filled in, populate band selectors
            /**
            * @type { NodeListOf<HTMLSelectElement> }
            */
            var searchFields = document.querySelectorAll('#rgb-search-fields > input');

            var searchKeys = [];
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

            var req = new XMLHttpRequest();
            req.open('GET', assembleDatasetURL(searchKeys, 1000, 0));
            req.addEventListener('load', populateRgbPickers.bind(null, req));
            req.send();
        }

        function populateRgbPickers(request) {
            var rgbDatasets = JSON.parse(request.responseText).datasets;
            var lastKey = keys[keys.length - 1].key;

            resetRgbSelectors(true);

            var rgbSelectors = [
                document.querySelector('.rgb-selector#R'),
                document.querySelector('.rgb-selector#G'),
                document.querySelector('.rgb-selector#B')
            ];

            for (let i = 0; i < rgbDatasets.length; i++) {
                var ds = rgbDatasets[i];
                for (var j = 0; j < rgbSelectors.length; j++) {
                    var option = document.createElement('option');
                    option.innerHTML = ds[lastKey];
                    option.value = ds[lastKey];
                    rgbSelectors[j].appendChild(option);
                }

                // retrieve metadata
                var req = new XMLHttpRequest();
                var dsKeys = [];
                for (var j = 0; j < keys.length; j++) {
                    dsKeys[j] = ds[keys[j].key];
                }
                req.open('GET', assembleMetadataURL(dsKeys));
                req.addEventListener('load', storeMetadata);
                req.send();
            }
        }

        function rgbSelectorChanged() {
            /**
            * @type { NodeListOf<HTMLInputElement> }
            */
            var searchFields = document.querySelectorAll('#rgb-search-fields > input');
            var firstKeys = [];
            for (let i = 0; i < searchFields.length; i++) {
                firstKeys[i] = searchFields[i].value;
            }

            /**
            * @type { Array<HTMLSelectElement> }
            */
            var rgbSelectors = [
                document.querySelector('.rgb-selector#R'),
                document.querySelector('.rgb-selector#G'),
                document.querySelector('.rgb-selector#B')
            ];
            var lastKeys = [];
            for (let i = 0; i < rgbSelectors.length; i++) {
                if (!rgbSelectors[i].value) return toggleRgbLayer();
                lastKeys[i] = rgbSelectors[i].value;
            }

            // initialize sliders
            /**
            * @type { Array<noUiSlider.SliderElement> }
            */
            var rgbSliders = [
                document.querySelector('.rgb-slider#R'),
                document.querySelector('.rgb-slider#G'),
                document.querySelector('.rgb-slider#B')
            ];
            current_rgb_stretch = [];
            for (let i = 0; i < 3; i++) {
                var someKeys = serializeKeys(firstKeys.concat([lastKeys[i]]));
                var metadata = dataset_metadata[someKeys];
                if (metadata != null) {
                    var last = metadata.percentiles.length - 1;
                    current_rgb_stretch[i] = [metadata.percentiles[2], metadata.percentiles[last - 2]];
                    rgbSliders[i].noUiSlider.updateOptions({
                        start: current_rgb_stretch[i],
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
            var rgbControls = document.getElementById('rgb');

            if (activeRgbLayer != null) {
                map.removeLayer(activeRgbLayer.layer);
                var currentFirstKeys = activeRgbLayer.index_keys;
                var currentLastKeys = activeRgbLayer.rgb_keys;
                activeRgbLayer = null;
                rgbControls.classList.remove('active');
                if (firstKeys == null || lastKeys == null) {
                    return;
                }
                if (
                    serializeKeys(currentFirstKeys) == serializeKeys(firstKeys) &&
                    serializeKeys(currentLastKeys) == serializeKeys(lastKeys)
                    ) {
                        return;
                    }
                }

                if (firstKeys == null || lastKeys == null) {
                    return;
                }

                if (activeSinglebandLayer != null) {
                    toggleSinglebandMapLayer(activeSinglebandLayer.keys);
                }

                var layerOptions = {};
                if (current_rgb_stretch != null) {
                    layerOptions.r_range = JSON.stringify(current_rgb_stretch[0]);
                    layerOptions.g_range = JSON.stringify(current_rgb_stretch[1]);
                    layerOptions.b_range = JSON.stringify(current_rgb_stretch[2]);
                }

                var layer_url = assembleRgbUrl(firstKeys, lastKeys, layerOptions, false);

                activeRgbLayer = {
                    index_keys: firstKeys,
                    rgb_keys: lastKeys,
                    layer: L.tileLayer(layer_url).addTo(map)
                };

                rgbControls.classList.add('active');
                var rgbSliders = document.querySelectorAll('.rgb-slider');
                for (let i = 0; i < rgbSliders.length; i++) {
                    rgbSliders[i].removeAttribute('disabled');
                }

                var someKeys = serializeKeys(firstKeys.concat([lastKeys[0]]));
                var metadata = dataset_metadata[someKeys];
                if (resetView && metadata != null) {
                    map.flyTo(getDatasetCenter(metadata), 9);
                }
            }

            /* Initialize global state */

            var remote_host;
            var keys, datasets, dataset_metadata;
            var colorbars;
            var current_dataset_page, current_colormap, current_singleband_stretch, current_rgb_stretch;
            var map, overlayLayer, activeSinglebandLayer, activeRgbLayer;

            /* Main entrypoint */
            function initializeApp(hostname) {
                remote_host = hostname;

                colorbars = {};
                getColorbars();

                keys = getKeys();
                initUI(keys);

                datasets = [];
                dataset_metadata = {};
                current_dataset_page = 0;
                updateSearchResults();

                var osmUrl = 'http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
                var osmAttrib = 'Map data © <a href="http://openstreetmap.org">OpenStreetMap</a> contributors';

                var osmBase = L.tileLayer(osmUrl, { attribution: osmAttrib });

                map = L.map('map', {
                    center: [0, 0],
                    zoom: 2,
                    layers: [osmBase]
                });
            }
