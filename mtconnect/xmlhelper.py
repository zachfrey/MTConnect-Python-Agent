# general imports
import re
from xml.etree import ElementTree

# MTConnect imports
from .device import MTDevice, MTComponent, MTDataItem


#
# Namespace Helpers
#

# Regex pattern to match namespace prefix: {namespace_uri}
_NAMESPACE_PATTERN = re.compile(r"\{[^}]+\}")


def strip_namespace(tag):
    """Remove namespace prefix from an XML element tag.

    Args:
        tag: Element tag string, possibly with namespace like '{uri}Name'

    Returns:
        Tag name without namespace prefix
    """
    if not tag:
        return tag
    return _NAMESPACE_PATTERN.sub("", tag)


def find_child(element, tag_name):
    """Find a child element by tag name, ignoring XML namespaces.

    Args:
        element: Parent XML element to search in
        tag_name: Local tag name to find (without namespace)

    Returns:
        First matching child element, or None if not found
    """
    for child in element:
        if strip_namespace(child.tag) == tag_name:
            return child
    return None


def find_children(element, tag_name):
    """Find all child elements by tag name, ignoring XML namespaces.

    Args:
        element: Parent XML element to search in
        tag_name: Local tag name to find (without namespace)

    Returns:
        List of matching child elements
    """
    return [child for child in element if strip_namespace(child.tag) == tag_name]


def _get_description_text(element):
    """Extract description text from an element's Description child.

    Args:
        element: XML element that may contain a Description child

    Returns:
        Description text string, or None if not found
    """
    description = find_child(element, "Description")
    if description is not None:
        return description.text
    return None


def _get_device_elements(root):
    """Find Device elements from the XML root, handling different formats.

    Supports:
    - Simple format: <Devices><Device>...</Device></Devices>
    - MTConnect format: <MTConnectDevices><Header/><Devices><Device/></Devices></MTConnectDevices>

    Args:
        root: Root element of the parsed XML tree

    Returns:
        List of Device elements
    """
    root_tag = strip_namespace(root.tag)

    if root_tag == "Devices":
        return find_children(root, "Device")
    elif root_tag == "MTConnectDevices":
        # Try <Devices> wrapper first (standard MTConnect format)
        devices_container = find_child(root, "Devices")
        if devices_container is not None:
            return find_children(devices_container, "Device")
        # Fallback: Device directly under MTConnectDevices (simplified format)
        return find_children(root, "Device")
    else:
        # Fallback: try to find Device elements directly under root
        return find_children(root, "Device")


#
# AGENT XML Helpers
#
def process_path(device_xml, path, item_dict, component_dict):
    xml_list = device_xml.findall(path)
    component_list = []
    for element in xml_list:

        id = element.get("id")
        if id in item_dict:
            component_list.append(item_dict[id])

        if id in component_dict:
            component_list.append(component_dict[id])
    return component_list


#
# DEVICE XML Helpers
#

# function to process all of the dataitems on a component
def process_dataitem(item_list, device, component):
    for item in item_list:
        # get required objects
        id = item.get("id")
        category = item.get("category")
        type = item.get("type")
        name = item.get("name")

        new_item = MTDataItem(id, name, type, category, device, component)

        for attribute in item.items():
            new_item.add_attribute(attribute[0], attribute[1])
        component.add_item(new_item)
        device.add_sub_item(new_item)


# function to recursively add components
def process_components(component_list, device, parent_component):
    for component in component_list:
        # get component attributes
        name = component.get("name")
        type = strip_namespace(component.tag)  # Strip namespace from component type
        id = component.get("id")
        description = _get_description_text(component)

        # create top level component
        new_component = MTComponent(
            id, name, type, component, parent_component, device, description
        )
        device.add_sub_component(new_component)

        parent_component.add_subcomponent(new_component)

        # get list of attributes
        for attribute in component.items():
            new_component.add_attribute(attribute[0], attribute[1])

        # get list of data items
        component_items = find_child(component, "DataItems")
        if component_items is not None:
            process_dataitem(component_items, device, new_component)

        # get list of subcomponents
        sub_component_item = find_child(component, "Components")
        if sub_component_item is not None:
            sub_component_list = list(sub_component_item)
            process_components(sub_component_list, device, new_component)


# read device xml from file
def read_devices(file):
    # read data file
    try:
        device_tree = ElementTree.parse(file)
    except FileNotFoundError:
        raise ValueError("{} is not a valid file".format(file))

    # list of devices
    device_list = {}

    # get devices - handle both simple format and MTConnect format with namespaces
    root = device_tree.getroot()
    device_elements = _get_device_elements(root)

    for device in device_elements:
        # get identifiers for device
        device_name = device.get("name")
        device_uuid = device.get("uuid")
        device_id = device.get("id")
        device_description = _get_description_text(device)

        # create device
        new_device = MTDevice(
            device_id, device_name, device, device_uuid, device_description
        )

        # get list of attributes
        for attribute in device.items():
            new_device.add_attribute(attribute[0], attribute[1])

        # get list of data items
        device_items = find_child(device, "DataItems")
        if device_items is not None:
            process_dataitem(device_items, new_device, new_device)

        # get list of subcomponents
        component_item = find_child(device, "Components")
        if component_item is not None:
            component_list = list(component_item)
            process_components(component_list, new_device, new_device)

        device_list[new_device.id] = new_device

    return (device_list, device_tree)
