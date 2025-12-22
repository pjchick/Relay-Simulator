"""Regression tests for Memory bus reactivity."""

import unittest
from pathlib import Path

from fileio.document_loader import load_document
from core.vnet_builder import VnetBuilder
from core.link_resolver import LinkResolver
from simulation.engine_factory import SimulationEngineFactory


class TestMemoryAddressUpdates(unittest.TestCase):
    def test_memory_updates_on_address_change_with_read_enabled(self):
        repo_root = Path(__file__).resolve().parents[2]
        filepath = repo_root / "Memory.rsim"
        if not filepath.exists():
            self.skipTest(f"Test file not found: {filepath}")

        doc = load_document(str(filepath))

        builder = VnetBuilder()
        vnets_list = []
        for page in doc.pages.values():
            vnets_list.extend(builder.build_vnets_for_page(page))

        vnets = {v.vnet_id: v for v in vnets_list}
        result = LinkResolver().resolve_links(doc, vnets_list)
        self.assertEqual(result.errors, [])

        components = {}
        tabs = {}
        bridges = {}
        for page in doc.pages.values():
            for comp in page.components.values():
                components[comp.component_id] = comp
                for pin in comp.pins.values():
                    for tab in pin.tabs.values():
                        tabs[tab.tab_id] = tab

        engine = SimulationEngineFactory.create_single_threaded(vnets, tabs, bridges, components)
        self.assertTrue(engine.initialize())

        mem = components["a2515771"]
        addr_lo = components["0c12a9f0"]
        en_sw = components["230d9483"]
        rd_sw = components["17702f08"]

        # Enable + Read on
        for sw in (en_sw, rd_sw):
            if sw.interact("toggle"):
                sw.simulate_logic(engine.vnet_manager)

        engine.run()

        expected = {
            0: 85,
            1: 170,
            2: 17,
            3: 34,
        }

        for address, expected_value in expected.items():
            addr_lo.properties["value"] = address
            addr_lo.simulate_logic(engine.vnet_manager)
            engine.run()

            self.assertEqual(mem.last_operation, "read")
            self.assertEqual(mem.last_address, address)
            self.assertEqual(mem.last_data, expected_value)
