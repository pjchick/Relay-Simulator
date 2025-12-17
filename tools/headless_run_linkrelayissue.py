import os
import sys
from pathlib import Path


# Ensure repo root and package dir are on sys.path so imports work both when:
# - running via `python tools/...py`
# - running via `python -m ...`
REPO_ROOT = Path(__file__).resolve().parents[1]
PKG_ROOT = REPO_ROOT / "relay_simulator"
for path in (str(REPO_ROOT), str(PKG_ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)

from relay_simulator.fileio.document_loader import load_document
from relay_simulator.core.vnet_builder import VnetBuilder
from relay_simulator.core.link_resolver import LinkResolver
from relay_simulator.simulation.simulation_engine import SimulationEngine


def main() -> None:
    doc_path = REPO_ROOT / "LinkRelayissue.rsim"
    doc = load_document(str(doc_path))

    vnets = {}
    tabs = {}
    bridges = {}
    components = {}

    for page in doc.get_all_pages():
        for comp in page.get_all_components():
            components[comp.component_id] = comp
            for pin in comp.get_all_pins().values():
                for tab in pin.tabs.values():
                    tabs[tab.tab_id] = tab

    builder = VnetBuilder(doc.id_manager)
    for page in doc.get_all_pages():
        for vnet in builder.build_vnets_for_page(page):
            vnets[vnet.vnet_id] = vnet

    LinkResolver().resolve_links(doc, list(vnets.values()))

    engine = SimulationEngine(vnets, tabs, bridges, components, max_iterations=200, timeout_seconds=5.0)
    engine.initialize()
    stats = engine.run()
    print("DONE", stats)


if __name__ == "__main__":
    main()
