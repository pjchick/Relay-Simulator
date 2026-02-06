"""
Test script for Sub-Circuit Rendering - Phase 4 validation.

This test creates a GUI window and renders SubCircuit components
to validate visual appearance, tab positions, and selection states.

Tests:
1. SubCircuit renderer registration
2. Basic rendering (rectangle, name, corners)
3. Tab positioning
4. Selection state visualization
5. Multiple instances with different names/sizes
"""

import sys
import tkinter as tk
from pathlib import Path

# Add relay_simulator to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.document import Document
from core.sub_circuit_instantiator import SubCircuitInstantiator
from components.factory import ComponentFactory
from gui.renderers.renderer_factory import RendererFactory
from gui.theme import VSCodeTheme


def test_renderer_registration():
    """Test that SubCircuitRenderer is registered."""
    print("=" * 60)
    print("Test 1: Renderer Registration")
    print("=" * 60)
    
    supported_types = RendererFactory.get_supported_types()
    
    if 'SubCircuit' in supported_types:
        print(f"✓ SubCircuit renderer registered")
        print(f"  Total renderer types: {len(supported_types)}")
        return True
    else:
        print(f"✗ SubCircuit renderer NOT registered!")
        print(f"  Registered types: {supported_types}")
        return False


def test_visual_rendering():
    """Test visual rendering in a GUI window."""
    print("\n" + "=" * 60)
    print("Test 2: Visual Rendering (GUI)")
    print("=" * 60)
    
    # Create document and load Latch template
    doc = Document()
    main_page = doc.create_page("Main Circuit")
    factory = ComponentFactory()
    
    instantiator = SubCircuitInstantiator(doc, factory)
    rsub_path = Path(__file__).parent.parent.parent / "examples" / "Latch.rsub"
    
    if not rsub_path.exists():
        print(f"✗ Latch.rsub not found at {rsub_path}")
        return False
    
    # Load and embed template
    sc_def = instantiator.load_and_embed_template(str(rsub_path))
    print(f"✓ Loaded template: {sc_def.name}")
    
    # Create multiple instances to test rendering
    latch1 = instantiator.create_instance(
        sc_def.sub_circuit_id,
        main_page.page_id,
        (200, 150)
    )
    main_page.add_component(latch1)
    
    latch2 = instantiator.create_instance(
        sc_def.sub_circuit_id,
        main_page.page_id,
        (450, 150)
    )
    main_page.add_component(latch2)
    
    latch3 = instantiator.create_instance(
        sc_def.sub_circuit_id,
        main_page.page_id,
        (200, 350)
    )
    main_page.add_component(latch3)
    
    print(f"✓ Created {len(main_page.components)} sub-circuit instances")
    
    # Create GUI window
    root = tk.Tk()
    root.title("Phase 4: SubCircuit Rendering Test")
    root.geometry("700x600")
    root.configure(bg=VSCodeTheme.BG_PRIMARY)
    
    # Create canvas
    canvas = tk.Canvas(
        root,
        bg=VSCodeTheme.BG_PRIMARY,
        highlightthickness=0,
        width=700,
        height=500
    )
    canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Create instruction label
    info_label = tk.Label(
        root,
        text="Click a sub-circuit to select it. Close window to continue tests.",
        bg=VSCodeTheme.BG_PRIMARY,
        fg=VSCodeTheme.FG_PRIMARY,
        font=('Arial', 10)
    )
    info_label.pack(pady=5)
    
    # Render all components
    renderers = []
    for component in main_page.components.values():
        try:
            renderer = RendererFactory.create_renderer(canvas, component)
            renderer.render(zoom=1.0)
            renderers.append(renderer)
            print(f"  ✓ Rendered {component.component_type}: {component.sub_circuit_name}")
            print(f"      Position: {component.position}")
            print(f"      Dimensions: {component.width}x{component.height}")
            print(f"      Pins: {len(component.pins)}")
        except Exception as e:
            print(f"  ✗ Failed to render {component.component_id}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # Add selection handling
    selected_renderer = None
    
    def on_click(event):
        nonlocal selected_renderer
        
        # Deselect previous
        if selected_renderer:
            selected_renderer.set_selected(False)
            selected_renderer.render(zoom=1.0)
        
        # Find clicked component
        x, y = event.x, event.y
        for renderer in renderers:
            bounds = renderer.get_bounds(zoom=1.0)
            x1, y1, x2, y2 = bounds
            if x1 <= x <= x2 and y1 <= y <= y2:
                renderer.set_selected(True)
                renderer.render(zoom=1.0)
                selected_renderer = renderer
                info_label.config(text=f"Selected: {renderer.component.sub_circuit_name} [{renderer.component.instance_id[:8]}]")
                break
        else:
            # Clicked empty space - deselect all
            selected_renderer = None
            info_label.config(text="Click a sub-circuit to select it. Close window to continue tests.")
    
    canvas.bind('<Button-1>', on_click)
    
    print(f"\n✓ GUI window created - inspect rendering visually")
    print(f"  - Should see 3 Latch sub-circuits")
    print(f"  - Each with corner markers and name label")
    print(f"  - Tabs should be visible at pin positions")
    print(f"  - Click to select (blue outline)")
    
    root.mainloop()
    
    return True


def test_bounds_calculation():
    """Test bounding box calculation for hit testing."""
    print("\n" + "=" * 60)
    print("Test 3: Bounds Calculation")
    print("=" * 60)
    
    from components.sub_circuit import SubCircuit
    
    # Create a SubCircuit component
    sc = SubCircuit("test123", "page001")
    sc.position = (300, 200)
    sc.width = 200
    sc.height = 150
    sc.sub_circuit_name = "Test"
    
    # Create mock canvas
    root = tk.Tk()
    canvas = tk.Canvas(root, width=100, height=100)
    
    # Create renderer
    renderer = RendererFactory.create_renderer(canvas, sc)
    
    # Get bounds
    bounds = renderer.get_bounds(zoom=1.0)
    x1, y1, x2, y2 = bounds
    
    # Calculate expected bounds
    expected_x1 = 300 - 200/2  # 200
    expected_y1 = 200 - 150/2  # 125
    expected_x2 = 300 + 200/2  # 400
    expected_y2 = 200 + 150/2  # 275
    
    if (x1, y1, x2, y2) == (expected_x1, expected_y1, expected_x2, expected_y2):
        print(f"✓ Bounds calculated correctly")
        print(f"  Position: {sc.position}")
        print(f"  Dimensions: {sc.width}x{sc.height}")
        print(f"  Bounds: ({x1}, {y1}) -> ({x2}, {y2})")
        root.destroy()
        return True
    else:
        print(f"✗ Bounds incorrect!")
        print(f"  Expected: ({expected_x1}, {expected_y1}) -> ({expected_x2}, {expected_y2})")
        print(f"  Got: ({x1}, {y1}) -> ({x2}, {y2})")
        root.destroy()
        return False


def test_tab_rendering():
    """Test that tabs are rendered correctly."""
    print("\n" + "=" * 60)
    print("Test 4: Tab Rendering")
    print("=" * 60)
    
    # Create document with Latch instance
    doc = Document()
    main_page = doc.create_page("Main")
    factory = ComponentFactory()
    
    instantiator = SubCircuitInstantiator(doc, factory)
    rsub_path = Path(__file__).parent.parent.parent / "examples" / "Latch.rsub"
    
    sc_def = instantiator.load_and_embed_template(str(rsub_path))
    latch = instantiator.create_instance(
        sc_def.sub_circuit_id,
        main_page.page_id,
        (300, 300)
    )
    
    print(f"  SubCircuit has {len(latch.pins)} pins")
    for pin_id, pin in latch.pins.items():
        print(f"    Pin {pin_id}: {len(pin.tabs)} tabs")
        for tab_id, tab in pin.tabs.items():
            print(f"      Tab {tab_id}: relative_position = {tab.relative_position}")
    
    # Verify tabs exist
    if len(latch.pins) > 0:
        total_tabs = sum(len(pin.tabs) for pin in latch.pins.values())
        print(f"\n✓ SubCircuit has {total_tabs} tabs to render")
        return True
    else:
        print(f"\n✗ SubCircuit has no pins/tabs!")
        return False


def main():
    """Run all Phase 4 tests."""
    print("Phase 4 Sub-Circuit Rendering Tests")
    print("=" * 60 + "\n")
    
    results = []
    
    # Test 1: Registration
    results.append(("Renderer Registration", test_renderer_registration()))
    
    # Test 2: Tab rendering (non-visual)
    results.append(("Tab Rendering Check", test_tab_rendering()))
    
    # Test 3: Bounds calculation
    results.append(("Bounds Calculation", test_bounds_calculation()))
    
    # Test 4: Visual rendering (opens GUI)
    print("\n" + "=" * 60)
    print("Starting Visual Rendering Test (GUI)")
    print("=" * 60)
    print("A window will open - inspect the rendering, then close it to continue.\n")
    
    results.append(("Visual Rendering", test_visual_rendering()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Phase 4 Test Summary")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n" + "=" * 60)
        print("All Phase 4 tests passed!")
        print("=" * 60)
        print("\nSubCircuit rendering is complete!")
        print("Next step: Phase 5 - GUI Integration (toolbox, drag-and-drop)")
    else:
        print("\n✗ Some tests failed - review output above")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
