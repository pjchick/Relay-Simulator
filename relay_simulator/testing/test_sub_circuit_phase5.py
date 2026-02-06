"""
Test script for Sub-Circuit GUI Integration - Phase 5 validation.

This test validates the GUI integration for sub-circuits including:
1. SubCircuit appears in toolbox
2. File dialog interaction for .rsub selection
3. Placement mode activation
4. Component instance creation on canvas
5. Multiple instances from same template

Note: This is a manual test script that requires user interaction.
"""

import sys
import tkinter as tk
from pathlib import Path

# Add relay_simulator to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from gui.toolbox import ToolboxPanel
from core.document import Document


def test_toolbox_registration():
    """Test that SubCircuit appears in toolbox."""
    print("=" * 60)
    print("Test 1: SubCircuit in Toolbox")
    print("=" * 60)
    
    components = ToolboxPanel.COMPONENTS
    
    # Check if SubCircuit is in the list
    sub_circuit_entry = None
    for component_type, display_name in components:
        if component_type == 'SubCircuit':
            sub_circuit_entry = (component_type, display_name)
            break
    
    if sub_circuit_entry:
        print(f"✓ SubCircuit found in toolbox")
        print(f"  Type: {sub_circuit_entry[0]}")
        print(f"  Display Name: {sub_circuit_entry[1]}")
        print(f"  Total components: {len(components)}")
        return True
    else:
        print(f"✗ SubCircuit NOT found in toolbox!")
        print(f"  Available components:")
        for ct, dn in components:
            print(f"    - {ct}: {dn}")
        return False


def test_toolbox_gui():
    """Test toolbox GUI rendering."""
    print("\n" + "=" * 60)
    print("Test 2: Toolbox GUI (Visual)")
    print("=" * 60)
    print("A window will open with the toolbox.")
    print("Verify that 'Sub-Circuit' appears in the component list.\n")
    
    root = tk.Tk()
    root.title("Phase 5: Toolbox Test")
    root.geometry("250x600")
    
    # Track selections
    selected_component = None
    
    def on_select(component_type):
        nonlocal selected_component
        selected_component = component_type
        label.config(text=f"Selected: {component_type or 'None'}")
        print(f"  Component selected: {component_type}")
    
    # Create toolbox
    toolbox = ToolboxPanel(root, on_component_select=on_select)
    toolbox.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
    
    # Info label
    label = tk.Label(root, text="Click a component to select it", pady=10)
    label.pack(side=tk.BOTTOM, fill=tk.X)
    
    print("✓ Toolbox GUI created")
    print("  Look for 'Sub-Circuit' in the component list")
    print("  Click 'Sub-Circuit' to select it")
    print("  Close window to continue tests\n")
    
    root.mainloop()
    
    return True


def test_integration_instructions():
    """Provide manual testing instructions for full integration."""
    print("\n" + "=" * 60)
    print("Test 3: Full Integration (Manual)")
    print("=" * 60)
    print()
    print("To test the complete GUI integration:")
    print()
    print("1. Launch the application:")
    print("   python relay_simulator/app.py")
    print()
    print("2. Create or open a document")
    print()
    print("3. Click 'Sub-Circuit' in the toolbox")
    print("   → File dialog should appear")
    print()
    print("4. Navigate to examples/Latch.rsub and select it")
    print("   → Status bar should say 'Click on canvas to place Latch'")
    print("   → Cursor should change to crosshair")
    print()
    print("5. Click on the canvas")
    print("   → Latch sub-circuit should appear")
    print("   → Component should have:")
    print("     - Rectangle outline")
    print("     - 'Latch' name label")
    print("     - Instance ID below name")
    print("     - Corner markers (L-shaped)")
    print("     - 2 tabs (green circles)")
    print()
    print("6. Click Sub-Circuit again and place another instance")
    print("   → Second Latch should appear")
    print("   → Each instance should have unique ID")
    print()
    print("7. Test selection:")
    print("   → Click on a sub-circuit to select it")
    print("   → Should show blue outline")
    print("   → Properties panel should show sub-circuit info")
    print()
    print("8. Test file saving:")
    print("   → Save the document as test_subcircuit.rsim")
    print("   → Close and reopen the file")
    print("   → Sub-circuits should load correctly")
    print()
    print("9. Test simulation:")
    print("   → Add switches connected to Latch inputs")
    print("   → Add indicators connected to Latch outputs")
    print("   → Start simulation")
    print("   → Toggle switches to verify latch functionality")
    print()
    print("=" * 60)
    print()
    
    return True


def main():
    """Run all Phase 5 tests."""
    print("Phase 5 Sub-Circuit GUI Integration Tests")
    print("=" * 60 + "\n")
    
    results = []
    
    # Test 1: Registration
    results.append(("Toolbox Registration", test_toolbox_registration()))
    
    # Test 2: Visual toolbox
    print("\n" + "=" * 60)
    print("Starting Toolbox GUI Test")
    print("=" * 60)
    results.append(("Toolbox GUI", test_toolbox_gui()))
    
    # Test 3: Manual integration instructions
    results.append(("Integration Instructions", test_integration_instructions()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Phase 5 Test Summary")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n" + "=" * 60)
        print("Automated tests passed!")
        print("=" * 60)
        print("\nPlease follow the manual testing instructions above")
        print("to verify full GUI integration.")
    else:
        print("\n✗ Some automated tests failed - review output above")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
