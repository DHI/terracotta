"""handlers/wmts.py

Handle /wmts API endpoint.
"""

import importlib.resources
from typing import Tuple
import xml.etree.ElementTree as ET

import terracotta.handlers as package
from terracotta import get_driver, get_settings
from terracotta.profile import trace


@trace('wmts_handler')
def wmts(url_root: str, dimension: str = None) -> str:
    """  """
    settings = get_settings()
    driver = get_driver(settings.DRIVER_PATH, provider=settings.DRIVER_PROVIDER)

    assert dimension is None or dimension in driver.key_names
    key_indices = {key: i for i, key in enumerate(driver.key_names)}
    dimension_index = key_indices[dimension] if dimension is not None else None

    def dataset_without_dimension(dataset: Tuple[str,...]) -> Tuple[str, ...]:
        if dimension is None:
            return dataset
        else:
            return dataset[:dimension_index] + dataset[dimension_index + 1:]

    datasets = driver.get_datasets()
    summarised_datasets = set(map(dataset_without_dimension, datasets))

    for _, (prefix, uri) in ET.iterparse(importlib.resources.open_text(package, 'wmts.xml'), events=['start-ns']):
        ET.register_namespace(prefix, uri)

    get_capabilities_xml_tree = ET.parse(importlib.resources.open_text(package, 'wmts.xml'))
    for el in get_capabilities_xml_tree.getroot().findall('.//{http://www.opengis.net/ows/1.1}Get'):
        el.set('xlink:href', f'{url_root}wmts')
    get_capabilities_xml_tree.find('.//{http://www.opengis.net/wmts/1.0}ServiceMetadataURL').set('xlink:href', f'{url_root}wmts')
    contents_element = get_capabilities_xml_tree.find('.//{http://www.opengis.net/wmts/1.0}Contents')

    for dataset in summarised_datasets:
        dimension_datasets = list(filter(lambda ds: dataset_without_dimension(ds) == dataset, datasets))

        layer = ET.Element('Layer')
        ET.SubElement(layer, 'ows:Title').text = 'Title'
        ET.SubElement(layer, 'ows:Identifier').text = 'Layer name'
        ET.SubElement(layer, 'ows:Abstract').text = 'Description'
        bbox = ET.SubElement(layer, 'ows:WGS84BoundingBox', crs='urn:ogc:def:crs:OGC:2:84')
        bounds = driver.get_metadata(dimension_datasets[0])['bounds']
        ET.SubElement(bbox, 'ows:LowerCorner').text = ' '.join(map(str, bounds[:2]))
        ET.SubElement(bbox, 'ows:UpperCorner').text = ' '.join(map(str, bounds[2:]))
        style = ET.SubElement(layer, 'Style', isDefault='true')
        ET.SubElement(style, 'ows:Identifier').text = 'default'
        ET.SubElement(layer, 'Format').text = 'image/png'
        if dimension:
            dimension_values = [ds[dimension_index] for ds in dimension_datasets]
            dimension_element = ET.SubElement(layer, 'Dimension')
            ET.SubElement(dimension_element, 'ows:Identifier').text = dimension
            ET.SubElement(dimension_element, 'Default').text = dimension_values[0]
            for dimension_value in dimension_values:
                ET.SubElement(dimension_element, 'Value').text = dimension_value
        tile_matrix_set_link = ET.SubElement(layer, 'TileMatrixSetLink')
        ET.SubElement(tile_matrix_set_link, 'TileMatrixSet').text = 'WorldWebMercatorQuad'
        dataset_keys = '/'.join(dataset if dimension is None else dataset[:dimension_index] + (f'{{{dimension}}}',) + dataset[dimension_index:])
        ET.SubElement(
            layer, 'ResourceURL',
            format='image/png',
            resourceType='tile',
            template=f'{url_root}singleband/{dataset_keys}/{{TileMatrix}}/{{TileCol}}/{{TileRow}}.png'
        )
        contents_element.append(layer)

    return ET.tostring(get_capabilities_xml_tree.getroot(), encoding='unicode')
