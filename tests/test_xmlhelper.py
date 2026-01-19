# import unittest
import unittest

# import xml helper functions
from mtconnect.xmlhelper import read_devices

# import libraries for testing
import os


class XmlHelperTest(unittest.TestCase):
    """Tests for xmlhelper.py parsing functionality."""

    def test_read_devices_simple_format(self):
        """Test that the existing simple format (no namespace) still works."""
        device_list, device_tree = read_devices("tests/test_device.xml")

        self.assertEqual(len(device_list), 1)
        device = device_list["d1"]
        self.assertEqual(device.name, "MFMS10-MC1")
        self.assertEqual(device.uuid, "MAZAK-M77KP290337")
        self.assertEqual(device.id, "d1")

    def test_read_devices_with_namespace(self):
        """Test parsing XML with MTConnect namespace."""
        device_list, device_tree = read_devices("tests/fixtures/haas_probe.xml")

        # Should successfully parse despite namespace
        self.assertGreater(len(device_list), 0)

    def test_read_devices_skips_header(self):
        """Test that Header element is skipped during parsing."""
        device_list, device_tree = read_devices("tests/fixtures/haas_probe.xml")

        # Should not raise an error about missing 'id' attribute
        # (Header elements don't have id attributes)
        self.assertGreater(len(device_list), 0)

        # Verify no device has empty/None id
        for device_id, device in device_list.items():
            self.assertIsNotNone(device.id)
            self.assertNotEqual(device.id, "")

    def test_read_devices_unwraps_devices_container(self):
        """Test that Device elements inside <Devices> container are found."""
        device_list, device_tree = read_devices("tests/fixtures/haas_probe.xml")

        # Should find the actual Device element inside Devices container
        self.assertGreater(len(device_list), 0)

    def test_read_devices_haas_device_attributes(self):
        """Test that Haas device attributes are correctly parsed."""
        device_list, device_tree = read_devices("tests/fixtures/haas_probe.xml")

        # Should have exactly one device with id "dev1"
        self.assertIn("dev1", device_list)
        device = device_list["dev1"]

        # Verify the actual Haas TM-1P attributes
        self.assertEqual(device.id, "dev1")
        self.assertEqual(device.name, "TM-1P")
        self.assertEqual(device.uuid, "000")

    def test_read_devices_haas_components(self):
        """Test that components are correctly parsed from namespaced XML."""
        device_list, device_tree = read_devices("tests/fixtures/haas_probe.xml")

        device = device_list["dev1"]

        # Device should have components (Controller, Axes, Settings, Spindles, etc.)
        self.assertGreater(len(device.component_dict), 0)

        # Check for specific known components from the Haas file
        component_ids = list(device.component_dict.keys())
        self.assertIn("cont1", component_ids)  # Controller
        self.assertIn("axes", component_ids)  # Axes

    def test_read_devices_haas_dataitems(self):
        """Test that DataItems are correctly parsed from namespaced XML."""
        device_list, device_tree = read_devices("tests/fixtures/haas_probe.xml")

        device = device_list["dev1"]

        # Device should have data items
        self.assertGreater(len(device.item_dict), 0)

        # Check for specific known DataItems from the Haas file
        item_ids = list(device.item_dict.keys())
        self.assertIn("avail", item_ids)  # Availability at device level
        self.assertIn("mode", item_ids)  # Controller mode
        self.assertIn("estop", item_ids)  # Emergency stop

    def test_namespace_stripped_from_component_types(self):
        """Test that namespace prefixes are stripped from component type names."""
        device_list, device_tree = read_devices("tests/fixtures/haas_probe.xml")

        device = device_list["dev1"]

        # Component types should not contain namespace URI
        for comp_id, component in device.component_dict.items():
            self.assertNotIn("{", component.type)
            self.assertNotIn("urn:mtconnect", component.type)

        # Verify specific component types are clean
        controller = device.component_dict["cont1"]
        self.assertEqual(controller.type, "Controller")


class XmlHelperNamespaceStripTest(unittest.TestCase):
    """Tests for namespace stripping utility function."""

    def test_strip_namespace_with_namespace(self):
        """Test stripping namespace from tag with namespace."""
        # This test will need to import the helper function once implemented
        from mtconnect.xmlhelper import strip_namespace

        tag = "{urn:mtconnect.org:MTConnectDevices:1.2}Device"
        result = strip_namespace(tag)
        self.assertEqual(result, "Device")

    def test_strip_namespace_without_namespace(self):
        """Test that tags without namespace are unchanged."""
        from mtconnect.xmlhelper import strip_namespace

        tag = "Device"
        result = strip_namespace(tag)
        self.assertEqual(result, "Device")

    def test_strip_namespace_empty_string(self):
        """Test handling of empty string."""
        from mtconnect.xmlhelper import strip_namespace

        tag = ""
        result = strip_namespace(tag)
        self.assertEqual(result, "")


if __name__ == "__main__":
    unittest.main()
