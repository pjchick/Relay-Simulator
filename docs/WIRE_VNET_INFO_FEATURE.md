# Wire VNET Information Feature

## Overview

When running in simulation mode, clicking on a wire now displays a dialog showing all components connected to that wire's VNET (Virtual Network).

## Feature Details

### Dialog Information

The wire info dialog displays:

1. **VNET ID**: The unique identifier of the virtual network
2. **VNET State**: Current state (HIGH or FLOAT) with color coding
3. **Component Count**: Total number of components connected to the network
4. **Component List**: Detailed table with:
   - **Page**: The page name where the component is located
   - **Component ID**: The unique identifier of the component
   - **Type**: Component type (Switch, Indicator, DPDTRelay, etc.)
   - **Label**: User-defined label for the component
   - **Driving**: Whether the component is currently driving the wire state (outputting HIGH)

### Visual Features

- Components that are driving the wire (outputting HIGH) are highlighted in light blue
- The VNET state is color-coded:
  - GREEN for HIGH state
  - GRAY for FLOAT state
- The dialog is modal and blocks interaction with the main window until closed
- Press ESC or click Close to dismiss the dialog

### Implementation Details

#### Files Modified

1. **relay_simulator/gui/wire_info_dialog.py** (NEW)
   - New dialog class for displaying wire VNET information
   - Implements sortable table with component details
   - Highlights driving components

2. **relay_simulator/gui/main_window.py**
   - Modified `_handle_wire_selection()` to show dialog in simulation mode
   - Added `_show_wire_vnet_info()` to gather and display VNET data
   - Added `_build_vnet_info_dict()` to collect component information
   - Added `_is_component_driving_vnet()` to determine if a component is driving the wire

#### How It Works

1. User clicks on a wire in simulation mode
2. System finds all tabs connected to the wire using `wire.get_all_connected_tabs()`
3. System looks up the VNET containing one of these tabs
4. System enumerates all tabs in the VNET
5. For each tab, system finds the parent component
6. System determines if the component is driving (outputting HIGH to the VNET)
7. Dialog displays all component information in a sorted table

#### Component Driving Logic

A component is considered "driving" the wire if:
- It has at least one pin connected to the VNET
- That pin's state is HIGH
- The pin is in output mode (for components like switches, VCC)

Driving components are sorted to the top of the list and highlighted.

### Usage

1. Load or create a circuit document
2. Start simulation mode (Tools > Start Simulation)
3. Click on any wire in the circuit
4. The Wire VNET Information dialog appears
5. Review all connected components and their driving status
6. Close the dialog to continue

### Benefits

- **Circuit Analysis**: Quickly see all components connected to a specific wire
- **Debugging**: Identify which components are driving a wire state
- **Learning**: Understand how VNETs group electrically connected components
- **Cross-Page Visualization**: See components from different pages that are connected via the same VNET

### Future Enhancements

Possible improvements for future versions:
- Show link names if the VNET includes cross-page links
- Show bridge information for relay-connected VNETs
- Add "Jump to Component" feature to navigate to a component's page
- Add pin-level information showing which pins are connected
- Export VNET information to text or CSV
- Show historical state changes (if recording is enabled)
