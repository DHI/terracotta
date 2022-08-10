"""handlers/wmts.py

Handle /wmts API endpoint.
"""

from typing import Any, Mapping, List, Sequence, Union  # noqa: F401
from collections import OrderedDict

from terracotta import get_settings, get_driver
from terracotta.profile import trace

import xml.etree.ElementTree as ET
import importlib.resources
import terracotta.handlers as package


@trace('wmts_handler')
def wmts(url_root: str) -> Any:
    """  """
    settings = get_settings()
    driver = get_driver(settings.DRIVER_PATH, provider=settings.DRIVER_PROVIDER)

    datasets = driver.get_datasets()
    dataset = list(datasets.keys())[0]

    # dataset = ('2020', '1')

    for _, (prefix, uri) in ET.iterparse(importlib.resources.open_text(package, 'wmts.xml'), events=['start-ns']):
        ET.register_namespace(prefix, uri)

    get_capabilities_xml_tree = ET.parse(importlib.resources.open_text(package, 'wmts.xml'))
    for el in get_capabilities_xml_tree.getroot().findall('.//{http://www.opengis.net/ows/1.1}Get'):
        el.set('xlink:href', f'{url_root}wmts')
    get_capabilities_xml_tree.find('.//{http://www.opengis.net/wmts/1.0}ServiceMetadataURL').set('xlink:href', f'{url_root}wmts')
    contents_element = get_capabilities_xml_tree.find('.//{http://www.opengis.net/wmts/1.0}Contents')

    layer = ET.Element('Layer')
    ET.SubElement(layer, 'ows:Title').text = 'Title'
    ET.SubElement(layer, 'ows:Identifier').text = 'Layer name'
    ET.SubElement(layer, 'ows:Abstract').text = 'Description'
    bbox = ET.SubElement(layer, 'ows:WGS84BoundingBox', crs='urn:ogc:def:crs:OGC:2:84')
    ET.SubElement(bbox, 'ows:LowerCorner').text = ' '.join(map(str, driver.get_metadata(dataset)['bounds'][:2]))
    ET.SubElement(bbox, 'ows:UpperCorner').text = ' '.join(map(str, driver.get_metadata(dataset)['bounds'][2:]))
    style = ET.SubElement(layer, 'Style', isDefault='true')
    ET.SubElement(style, 'ows:Identifier').text = 'default'
    ET.SubElement(layer, 'Format').text = 'image/png'
    tile_matrix_set_link = ET.SubElement(layer, 'TileMatrixSetLink')
    ET.SubElement(tile_matrix_set_link, 'TileMatrixSet').text = 'WorldWebMercatorQuad'
    ET.SubElement(
        layer, 'ResourceURL',
        format='image/png',
        resourceType='tile',
        template=f'{url_root}singleband/{"/".join(dataset)}/' + '{TileMatrix}/{TileCol}/{TileRow}.png'
    )
    contents_element.append(layer)

    return ET.tostring(get_capabilities_xml_tree.getroot(), encoding='unicode')
