function getKeys() {
    var http_request = new XMLHttpRequest();
    http_request.open("GET", remote_host + "/keys", false);
    http_request.send();

    if (http_request.status === 200) {
        return JSON.parse(http_request.responseText).keys;
    }
    return [];
}


function assembleDatasetURL(key_constraints, limit, page) {
    var request_url = remote_host + "/datasets?limit=" + limit + "&page=" + page;

    for (var i = 0; i < key_constraints.length; i++) {
        request_url += "&" + key_constraints[i].key + "=" + key_constraints[i].value;
    }
    return request_url;
}


function assembleMetadataURL(ds_keys) {
    var request_url = remote_host + "/metadata"
    for(var i = 0; i < ds_keys.length; i++) {
        request_url += "/" + ds_keys[i];
    }
    return request_url;
}


function assembleSinglebandURL(keys, options, preview) {
    if (preview) {
        var request_url = remote_host + "/singleband/" + keys.join("/") + "/preview.png";
    } else {
        var request_url = remote_host + "/singleband/" + keys.join("/") + "/{z}/{x}/{y}.png";
    }

    if (options == null)
        return request_url;
    
    var first = true;
    for (var option_key in options) {
        if (!options.hasOwnProperty(option_key))
            continue;

        if (first) {
            request_url += "?" + option_key + "=" + options[option_key];
            first = false;
        } else {
            request_url += "&" + option_key + "=" + options[option_key];
        }
    }
    return request_url;
}


function assembleRGBURL(first_keys, rgb_keys, options, preview) {
    if (preview) {
        var request_url = remote_host + "/rgb/" + first_keys.join("/") + "/preview.png?";
    } else {
        var request_url = remote_host + "/rgb/" + first_keys.join("/") + "/{z}/{x}/{y}.png";
    }

    if (options == null)
        return request_url;

    var first = true;
    for (var option_key in options) {
        if (!options.hasOwnProperty(option_key))
            continue;

        if (first) {
            request_url += "?" + option_key + "=" + options[option_key];
            first = false;
        } else {
            request_url += "&" + option_key + "=" + options[option_key];
        }
    }
    return request_url;
}


function getDatasetCenter(metadata){
    var bounds = metadata.bounds;
    return [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2];
}


function initUI(keys){
    // initialize list of keys and key descriptions
    var keyList = document.getElementById("key-list");
    keyList.innerHTML = '';
    for(var i = 0; i < keys.length; i++){
        var keyEntry = document.createElement("li");
        keyEntry.innerHTML = "<b>" + keys[i].key + "</b>";
        if (keys[i].description != null){
            keyEntry.innerHTML += ": " + keys[i].description;
        }
        keyList.appendChild(keyEntry);
    }

    // initialize search fields
    var searchContainer = document.getElementById("search-fields");
    searchContainer.innerHTML = "";
    for (var i = 0; i < keys.length; i++) {
        searchField = document.createElement("input");
        searchField.type = "text";
        searchField.placeholder = keys[i].key;
        searchField.name = keys[i].key;
        searchField.addEventListener("change", updateSearchResults);
        searchContainer.appendChild(searchField);
    }

    // initialize table header for search results
    var datasetTable = document.getElementById("search-results");
    datasetTable.innerHTML = "";
    var tableHeader = document.createElement("th");
    for (var i = 0; i < keys.length; i++) {
        headerEntry = document.createElement("td");
        headerEntry.innerHTML = keys[i].key;
        tableHeader.appendChild(headerEntry);
    }
    datasetTable.appendChild(tableHeader);

    // initialize RGB search fields
    var searchContainer = document.getElementById("rgb-search-fields");
    searchContainer.innerHTML = "";
    for (var i = 0; i < keys.length - 1; i++) {
        searchField = document.createElement("input");
        searchField.placeholder = keys[i].key;
        searchField.addEventListener("change", updateRGBSearchResults);
        searchContainer.appendChild(searchField);
    }
    resetRGBSelectors(false);
}


function updateColormap() {
    var colormapSelector = document.getElementById("colormap");
    current_colormap = colormapSelector.selectedOptions[0].value;
    if (activeSinglebandLayer == null)
        return;

    // toggle layer on and off to reload
    var ds_keys = activeSinglebandLayer.keys;
    toggleSinglebandMapLayer(ds_keys);
    toggleSinglebandMapLayer(ds_keys);
}


function serializeKeys(ds_keys) {
    return ds_keys.join("__");
}


function storeMetadata(e) {
    var req = e.target;
    var metadata = JSON.parse(req.responseText);
    var ds_keys = serializeKeys(Object.values(metadata.keys));
    dataset_metadata[ds_keys] = metadata;
}


function updateDatasetList(request) {
    datasets = JSON.parse(request.responseText).datasets;
    var datasetTable = document.getElementById("search-results");

    // disable next page if there are no more datasets
    var next_page_button = document.getElementById("next-page");
    if (datasets.length < datasets_per_page) {
        next_page_button.disabled = true;
    } else{
        next_page_button.disabled = false;
    }
    
    // update table rows
    if (datasets == null) {
        var resultRow = document.createElement("tr");
        resultRow.innerHTML = [
            "<td colspan=", keys.length, ">",
                "<span class=\"error\">",
                    "Error while querying datasets",
                "</span>",
            "</td>"
        ].join("");
        datasetTable.appendChild(resultRow);
        return;
    }

    if (datasets.length == 0) {
        var resultRow = document.createElement("tr");
        resultRow.innerHTML = "<td colspan=" + keys.length + ">No datasets found</td>";
        datasetTable.appendChild(resultRow);
        return;
    }

    for (var i = 0; i < datasets.length; i++) {
        var currentDataset = datasets[i];
        var resultRow = document.createElement("tr");
        var ds_keys = [];
        for (var j = 0; j < keys.length; j++) {
            var resultEntry = document.createElement("td");
            ds_keys[j] = currentDataset[keys[j].key];
            resultEntry.innerHTML = ds_keys[j];
            resultRow.appendChild(resultEntry);
        }
        resultRow.id = "dataset-" + serializeKeys(ds_keys);
        resultRow.addEventListener("click", toggleSinglebandMapLayer.bind(null, ds_keys));
        resultRow.addEventListener("mouseenter", toggleFootprintOverlay.bind(null, ds_keys));
        resultRow.addEventListener("mouseleave", toggleFootprintOverlay.bind(null, null));

        // show thumbnails
        var detailsRow = document.createElement("tr");
        detailsRow.innerHTML = "<td colspan=" + keys.length + "><img src=\"" + assembleSinglebandURL(ds_keys, null, true) + "\"></td>"
        resultRow.appendChild(detailsRow);

        datasetTable.appendChild(resultRow);

        // retrieve metadata
        var req = new XMLHttpRequest();
        req.open("GET", assembleMetadataURL(ds_keys));
        req.addEventListener("load", storeMetadata);
        req.send();
    }
}

function incrementResultsPage(step) {
    current_dataset_page += step;
    document.getElementById("page-counter").innerHTML = current_dataset_page + 1;
    var prevPageButton = document.getElementById("prev-page");
    if (current_dataset_page > 0) {
        prevPageButton.disabled = false;
    } else {
        prevPageButton.disabled = true;
    }
    updateSearchResults();
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

    if (metadata == null) 
        return;

    overlayLayer = L.geoJSON(metadata.convex_hull, {
        style: {
            "color": "#ff7800",
            "weight": 5,
            "opacity": 0.65
        }
    }).addTo(map);
}


function toggleSinglebandMapLayer(ds_keys) {
    var layer_id = serializeKeys(ds_keys);
    var resultRow = document.getElementById("dataset-" + layer_id);

    if (activeSinglebandLayer != null) {
        map.removeLayer(activeSinglebandLayer.layer);
        activeSinglebandLayer = null;

        var currentActiveRow = document.querySelector("#search-results > .active");
        if (currentActiveRow != null) {
            currentActiveRow.classList.remove("active");

            if (currentActiveRow == resultRow) {
                return;
            }
        }
    }

    var metadata = dataset_metadata[layer_id];
    var layer_options = {};
    if (current_colormap != null) {
        layer_options.colormap = current_colormap;
    }
    if (metadata != null) {
        var last = metadata.percentiles.length - 1;
        layer_options.range = JSON.stringify([
            metadata.percentiles[2],
            metadata.percentiles[last - 2]
        ]);
    }
    var layer_url = assembleSinglebandURL(ds_keys, layer_options);
    
    activeSinglebandLayer = {
        keys: ds_keys,
        layer: L.tileLayer(layer_url).addTo(map)
    };
    resultRow.classList.add("active");
    if (metadata != null) {
        map.flyTo(getDatasetCenter(metadata), 9);
    }
}


function updateSearchResults() {
    // initialize table header for search results
    var datasetTable = document.getElementById("search-results");
    datasetTable.innerHTML = "";
    var tableHeader = document.createElement("tr");
    for (var i = 0; i < keys.length; i++) {
        headerEntry = document.createElement("th");
        headerEntry.innerHTML = keys[i].key;
        tableHeader.appendChild(headerEntry);
    }
    datasetTable.appendChild(tableHeader);

    // get key constraints from UI
    var key_constraints = [];
    var datasetSearchFields = document.querySelectorAll("#search-fields input");
    for (var i = 0; i < datasetSearchFields.length; i++) {
        var ds_field = datasetSearchFields[i];
        if (ds_field.value != "") {
            key_constraints.push({key: ds_field.name, value: ds_field.value});
        }
    }

    // request datasets
    var req = new XMLHttpRequest();
    req.open("GET", assembleDatasetURL(key_constraints, datasets_per_page, current_dataset_page));
    req.addEventListener("load", updateDatasetList.bind(null, req));
    req.send();
}


function resetRGBSelectors(enabled) {
    var rgbSelectors = document.querySelectorAll("#rgb-selectors > select");
    var placeholders = ["--R--", "--G--", "--B--"];
    for (var i = 0; i < rgbSelectors.length; i++) {
        rgbSelectors[i].innerHTML = "<option value=\"null\">" + placeholders[i] + "</option>";
        rgbSelectors[i].disabled = !enabled;
    }
}


function updateRGBSearchResults() {
    // if all RGB search fields are filled in, populate band selectors
    var searchFields = document.querySelectorAll("#rgb-search-fields > input");

    var searchKeys = [];
    for (var i = 0; i < searchFields.length; i++) {
        if (!searchFields[i].value) {
            resetRGBSelectors(false);
            return;
        }
        searchKeys[i] = {
            key: keys[i].key,
            value: searchFields[i].value
        };
    }

    var req = new XMLHttpRequest();
    req.open("GET", assembleDatasetURL(searchKeys, 1000, 0));
    req.addEventListener("load", populateRGBPickers.bind(null, req));
    req.send();
}


function populateRGBPickers(request) {
    var rgbDatasets = JSON.parse(request.responseText).datasets;
    var last_key = keys[keys.length - 1].key;

    var rgbSelectors = document.querySelectorAll("#rgb-selectors > select");
    resetRGBSelectors(true);

    for (var i = 0; i < rgbDatasets.length; i++) {
        var ds = rgbDatasets[i];
        for (var j = 0; j < rgbSelectors.length; j++) {
            var option = document.createElement("option");
            option.innerHTML = ds[last_key];
            option.value = ds[last_key];
            rgbSelectors[j].appendChild(option);
        }
    }
}


function toggleRGBLayer() {
    var searchFields = document.querySelectorAll("#rgb-search-fields > input");
    var firstKeys = [];
    for (var i = 0; i < searchFields.length; i++) {
        firstKeys[i] = searchFields[i].value;
    }

    var rgbSelectors = document.querySelectorAll("#rgb-selectors > select");
    var lastKeys = [];
    for (var i = 0; i < rgbSelectors.length; i++) {
        if (rgbSelectors[i].value == "null")
            return;
        lastKeys[i] = rgbSelectors[i].value;
    }

    if (activeSinglebandLayer != null) {
        map.removeLayer(activeSinglebandLayer.layer);
        activeSinglebandLayer = null;

        var currentActiveRow = document.querySelector("#search-results > .active");
        if (currentActiveRow != null) {
            currentActiveRow.classList.remove("active");

            if (currentActiveRow == resultRow) {
                return;
            }
        }
    }

    var metadata = dataset_metadata[layer_id];
    var layer_options = {};
    if (current_colormap != null) {
        layer_options.colormap = current_colormap;
    }
    if (metadata != null) {
        var last = metadata.percentiles.length - 1;
        layer_options.range = JSON.stringify([
            metadata.percentiles[2],
            metadata.percentiles[last - 2]
        ]);
    }
    var layer_url = assembleSinglebandURL(ds_keys, layer_options);

    activeSinglebandLayer = {
        keys: ds_keys,
        layer: L.tileLayer(layer_url).addTo(map)
    };
    resultRow.classList.add("active");
    if (metadata != null) {
        map.flyTo(getDatasetCenter(metadata), 9);
    }
}


var remote_host;
var keys, datasets, dataset_metadata;
var datasets_per_page, current_dataset_page;
var map, overlayLayer, activeSinglebandLayer, activeRGBLayer, current_colormap;


function initializeApp(hostname){
    remote_host = hostname;

    keys = getKeys();
    initUI(keys);

    datasets = [];
    dataset_metadata = {};
    datasets_per_page = 5;
    current_dataset_page = 0;
    updateSearchResults();

    var osmUrl = 'http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
    var osmAttrib = 'Map data © <a href="http://openstreetmap.org">OpenStreetMap</a> contributors';

    var osmBase = L.tileLayer(osmUrl, {attribution: osmAttrib});

    map = L.map('map', {
        center: [0, 0],
        zoom: 2,
        layers: [osmBase]
    });
}