# Frontend Implementation Plan - Relay Simulator III

## Overview
This plan outlines the implementation of a modern tkinter-based GUI for the Relay Simulator III. The interface will provide a professional, IDE-style experience with a dark VS Code theme, dual-mode operation (Design/Simulation), and comprehensive editing capabilities.

## Design Principles
- **Modern Aesthetics**: Dark theme matching VS Code style
- **Dual-Mode Operation**: Clear separation between Design and Simulation modes
- **Multi-Document Support**: Multiple open files with tab management
- **Multi-Page Documents**: Tab-based page navigation within each document
- **Professional Workflow**: Standard keyboard shortcuts and menu operations
- **Persistent State**: Save canvas position/zoom and user settings
- **Responsive Canvas**: Grid snapping, zoom, pan, and precise component placement

---

## Phase 8: Window Framework and Theme ✅ COMPLETE

**Status**: All subsections complete - 79/79 tests passing
- Phase 8.1: Application Window and Theme - 20 tests ✅
- Phase 8.2: Menu System - 35 tests ✅  
- Phase 8.3: Settings System - 24 tests ✅

**Total Phase 8 Code**: ~2,600 lines across 10 files

**Files Created**:
- `gui/theme.py` (250 lines) - VS Code dark theme system
- `gui/main_window.py` (300+ lines) - Main application window
- `gui/menu_bar.py` (450 lines) - Complete menu system
- `gui/settings.py` (260 lines) - Persistent settings
- `gui/settings_dialog.py` (320+ lines) - Settings UI
- `app.py` (23 lines) - Application entry point
- `testing/test_gui_window.py` (225 lines) - Window/theme tests
- `testing/test_gui_menu.py` (330 lines) - Menu system tests
- `testing/test_gui_settings.py` (300 lines) - Settings tests

---

### 8.1 Application Window and Theme
**Objective**: Create the main application window with dark VS Code-style theme.

**Tasks**:
- Create `gui/` module structure
- Implement `gui/theme.py`:
  - VS Code color palette (background, foreground, accent colors)
  - Font definitions (sizes for UI elements, canvas labels)
  - Padding and spacing constants
  - ttk.Style configuration for widgets
- Implement `gui/main_window.py`:
  - MainWindow class with tkinter.Tk root
  - Window title: "Relay Simulator III"
  - Default size: 1280x720
  - Window icon (if available)
  - Menu bar placeholder
  - Status bar placeholder
- Basic window lifecycle (open, close, exit confirmation)

**Deliverables**:
- Dark-themed empty window opens and closes
- Theme constants accessible to all GUI components
- Window handles Ctrl+Q to quit

**Tests**:
- Window opens with correct title and size
- Theme colors applied correctly
- Window closes gracefully

---

### 8.2 Menu System
**Objective**: Implement complete menu bar with all specified menus and items.

**Tasks**:
- Implement `gui/menu_bar.py`:
  - MenuBar class managing all menus
  - **File Menu**:
    - New (Ctrl+N)
    - Open (Ctrl+O)
    - Save (Ctrl+S)
    - Save As (Ctrl+Shift+S)
    - Settings
    - Recent Documents (submenu, dynamic)
    - Clear Recent Documents
    - Exit (Ctrl+Q)
  - **Edit Menu**:
    - Select All (Ctrl+A)
    - Cut (Ctrl+X)
    - Copy (Ctrl+C)
    - Paste (Ctrl+V)
  - **Simulation Menu**:
    - Start Simulation (F5)
    - Stop Simulation (Shift+F5)
  - **View Menu**:
    - Zoom In (Ctrl++)
    - Zoom Out (Ctrl+-)
    - Reset Zoom (Ctrl+0)
- Menu item state management (enabled/disabled based on context)
- Keyboard accelerator support

**Deliverables**:
- Complete menu bar with all items
- Keyboard shortcuts functional
- Menu items can be enabled/disabled programmatically

**Tests**:
- All menu items present
- Keyboard shortcuts trigger correct actions
- Menu state updates correctly

---

### 8.3 Settings System ✅ COMPLETE
**Objective**: Implement persistent settings storage and settings dialog.

**Tasks**:
- ✅ Implement `gui/settings.py`:
  - Settings class with JSON file storage (~/.relay_simulator/settings.json)
  - Default settings:
    - Recent documents list (max 10)
    - Simulation threading: "single" (options: "single", "multi")
    - Default canvas size: 3000x3000
    - Canvas grid size: 20px
    - Canvas snap size: 10px
  - load_settings() / save_settings() methods
  - get(key, default) / set(key, value) methods
- ✅ Implement `gui/settings_dialog.py`:
  - SettingsDialog modal window (500x400px)
  - Simulation threading radio buttons
  - Canvas size spinboxes (width, height)
  - Grid/snap size spinboxes with validation
  - Scrollable content with fixed OK/Cancel/Reset buttons
  - Input validation with error messages

**Deliverables**:
- ✅ Settings persist across application runs
- ✅ Settings dialog allows modification with validation
- ✅ Recent documents list maintained (max 10, no duplicates)
- ✅ Scrollable dialog layout with fixed action buttons

**Tests**: 24/24 passing ✅
- Settings save and load correctly
- Settings dialog updates settings
- Default values applied on first run
- Validation for threading mode and positive integers
- Dialog layout with scrollable content

**Implementation Notes**:
- Settings stored at ~/.relay_simulator/settings.json
- Dialog uses Canvas + Scrollbar for scrollable content
- Buttons fixed at bottom (always visible)
- Integration with MainWindow and MenuBar
- Recent documents synced between Settings and MenuBar

---

## Phase 9: File and Document Management

### 9.1 File Tab System ✅ COMPLETE
**Objective**: Multi-document support with file tabs.

**Tasks**:
- ✅ Implement `gui/file_tabs.py`:
  - FileTab class for individual tab state
  - FileTabBar class (notebook-style tabs)
  - Tab display: filename, close button (×)
  - Active tab highlighting (VS Code theme colors)
  - Tab switching (blocked during simulation)
  - Tab close confirmation (via callback)
  - New document creates "Untitled-N" tab (auto-incrementing)
- ✅ Integrate with Document from Phase 1
- ✅ Track document state (modified/saved with * indicator)
- ✅ Update MainWindow with file tab bar
- ✅ Update File > New menu to create new tabs

**Deliverables**:
- ✅ Multiple documents can be open simultaneously
- ✅ Tab switching works correctly
- ✅ Unsaved changes tracked with * indicator
- ✅ Cannot switch tabs during simulation
- ✅ Window title shows active tab name
- ✅ Tab close callbacks with unsaved changes confirmation

**Tests**: 25/25 passing ✅
- FileTab class tests (5 tests)
- FileTabBar functionality tests (18 tests)
- Integration with Document (2 tests)
- Tab switching, closing, modified state tracking
- Simulation state blocking

**Implementation Notes**:
- FileTabBar creates visual tabs with VS Code theme
- Tab switching blocked when `is_simulation_running` is True
- Initial untitled document created on startup
- Window title format: "filename - Relay Simulator III" or "*filename - Relay Simulator III"
- Callbacks: on_tab_switch, on_tab_close, on_tab_modified

---

### 9.2 Page Tab System ✅ COMPLETE
**Objective**: Multi-page support within each document with page tabs.

**Tasks**:
- ✅ Implement `gui/page_tabs.py`:
  - PageTabBar class (sits below file tabs, above canvas)
  - Tab display: page name, close button (for extra pages)
  - Active page highlighting
  - Add new page button (+)
  - Page renaming (double-click on tab)
  - Page deletion (with confirmation)
  - First page cannot be deleted
- ✅ Integrate with Document/Page classes
- ✅ Canvas position/zoom per page (stored in .rsim)
- ✅ Page switching saves/restores canvas state

**Deliverables**:
- ✅ Multiple pages per document
- ✅ Page renaming functional (double-click)
- ✅ Canvas state per page preserved
- ✅ Add page button creates new pages
- ✅ First page protected from deletion
- ✅ Page tabs update on document switch

**Tests**: 20/20 passing ✅
- PageTabBar functionality (17 tests)
- Integration scenarios (3 tests)
- Page switching, adding, renaming
- Document switching with page state

**Implementation Notes**:
- PageTabBar displays tabs for all pages in active document
- Page tabs sit between file tabs and canvas
- Canvas state (position + zoom) saved per page
- Double-click on tab to rename page
- Add page button (+) on right side
- First page cannot be deleted (no close button)
- Page switching triggers canvas state save/restore
- Integration with MainWindow callbacks for modified state

---

### 9.3 File Operations ✅ COMPLETE
**Objective**: Complete file operations (New, Open, Save, Save As).

**Tasks**:
- ✅ Implement file operations in MainWindow:
  - File > New: Creates new untitled document (already working from 9.1)
  - File > Open: File dialog with .rsim filter, DocumentLoader.load_from_file()
  - File > Save: Saves to current filepath, or Save As if untitled
  - File > Save As: File dialog to choose new path
  - Unsaved changes prompts on tab close and window close
  - Recent documents updated automatically
- ✅ File dialog filters: "Relay Simulator Files (*.rsim)"
- ✅ Integration with file tab system and DocumentLoader
- ✅ Error handling for file operations

**Deliverables**:
- ✅ New/Open/Save/Save As fully functional with file dialogs
- ✅ Unsaved changes prompt on close (per-tab and on exit)
- ✅ Recent documents updated automatically
- ✅ Prevent opening same file twice (switches to existing tab)
- ✅ Save modified indicator cleared after successful save
- ✅ Window title updates with filename

**Implementation Notes**:
- File operations integrated directly into MainWindow (no separate file_operations.py)
- Uses tkinter.filedialog for Open and Save As dialogs
- DocumentLoader from Phase 7 handles actual file I/O
- Recent documents synced to Settings and MenuBar
- Tab close callback saves file if user chooses "Yes"
- Window close saves all modified tabs if user chooses "Yes"
- Error dialogs shown for file not found or save failures
- Save and Save As operations
- Unsaved changes prompt works

---

## Phase 10: Canvas Implementation ✅ COMPLETE

**Status**: All Phase 10 subsections complete
- Phase 10.1: Canvas Foundation - 24 tests ✅
- Phase 10.2: Canvas State Management - 14 tests ✅
- Phase 10.3: Component Rendering - 30 tests ✅
- Phase 10.4: Wire Rendering ✅

**Total Phase 10 Code**: ~2,000 lines across 14 files

### 10.1 Canvas Foundation ✅ COMPLETE
**Objective**: Scrollable canvas with grid, zoom, and pan support.

**Tasks**:
- ✅ Implement `gui/canvas.py`:
  - DesignCanvas class (wraps tkinter.Canvas)
  - Canvas size: 3000x3000 (configurable from settings)
  - Horizontal and vertical scrollbars
  - Grid rendering:
    - Grid size: 20px (from settings)
    - Grid color: subtle dark gray (#2d2d2d)
    - Grid drawn with create_line() in background
    - Grid tagged and kept in background layer
  - Coordinate system helpers (canvas coords vs screen coords)
- ✅ Implement zoom:
  - Mouse wheel: zoom in/out (centered on cursor)
  - Zoom levels: 0.1x to 5.0x (clamped)
  - Scale all canvas items on zoom
  - Update grid on zoom (grid hidden if too dense)
  - Update scroll region on zoom
- ✅ Implement pan:
  - Right-click + drag: pan canvas
  - Cursor changes to "fleur" during pan
  - Update scrollbars during pan
- ✅ Integrate into MainWindow
- ✅ Connect View menu zoom commands to canvas

**Deliverables**:
- ✅ 3000x3000 scrollable canvas with grid
- ✅ Mouse wheel zoom functional (Ctrl++ / Ctrl+- also work via menu)
- ✅ Right-click pan functional
- ✅ Grid scales correctly with zoom
- ✅ Canvas loads size from settings

**Tests**: 24/24 passing ✅
- Canvas creation and initialization (5 tests)
- Zoom functionality (7 tests)
- Pan functionality (3 tests)
- Grid management (2 tests)
- Coordinate conversion (2 tests)
- Canvas clearing (2 tests)
- Integration tests (3 tests)

**Implementation Notes**:
- DesignCanvas is a wrapper around tk.Canvas for easier management
- Grid lines tagged with "grid" and kept in background
- Zoom uses canvas.scale() to transform all items
- Pan uses canvas.scan_mark/scan_dragto for smooth scrolling
- Zoom centered on mouse position for intuitive navigation
- Grid drawing skipped when zoomed out (effective grid < 5px)
- Status bar shows zoom level when zooming

---

### 10.2 Canvas State Management ✅ COMPLETE
**Objective**: Per-page canvas position and zoom persistence.

**Tasks**:
- ✅ Extend Page class with canvas state:
  - Add `canvas_x: float = 0.0`
  - Add `canvas_y: float = 0.0`
  - Add `canvas_zoom: float = 1.0`
  - Update to_dict() / from_dict() for serialization
- ✅ Implement canvas state save/restore:
  - When switching pages: save current canvas state to Page object
  - When switching pages: restore canvas state from new Page object
  - On document save: canvas state persisted to .rsim file
  - On document load: canvas state restored from .rsim file
- ✅ Integration with file tabs and page tabs

**Deliverables**:
- ✅ Canvas position/zoom persists per page
- ✅ Canvas state saved to .rsim files
- ✅ Switching pages restores canvas state
- ✅ Switching file tabs restores canvas state
- ✅ Backward compatible with older .rsim files

**Tests**: 14/14 passing ✅
- Page canvas state fields (7 tests)
- Canvas save/restore methods (3 tests)
- File persistence (3 tests)
- Integration with document serialization (1 test)

**Implementation Notes**:
- Page class extended with canvas_x, canvas_y, canvas_zoom fields
- DesignCanvas has save_canvas_state() and restore_canvas_state() methods
- MainWindow saves canvas state on file operations and tab/page switching
- Canvas state persists across file save/load cycles
- Each page maintains independent canvas state
- Backward compatible: older files without canvas state use defaults (0, 0, 1.0)
- State management integrated with both file tabs and page tabs

---

### 10.3 Component Rendering ✅ COMPLETE
**Objective**: Render all components on canvas with correct appearance.

**Tasks**:
- ✅ Implement `gui/renderers/` module:
  - ✅ `base_renderer.py`: ComponentRenderer base class
  - ✅ `switch_renderer.py`: Render Switch component
  - ✅ `indicator_renderer.py`: Render Indicator component
  - ✅ `relay_renderer.py`: Render DPDTRelay component
  - ✅ `vcc_renderer.py`: Render VCC component
  - ✅ `renderer_factory.py`: Factory for creating renderers
- ✅ Rendering features:
  - ✅ Draw component body (circle/rectangle)
  - ✅ Draw component label (name/id)
  - ✅ Draw pins/tabs at correct positions
  - ✅ Handle rotation (0, 90, 180, 270 degrees)
  - ✅ Scale with zoom level
  - ✅ Highlight on selection (blue outline)
  - ✅ Color changes for powered state (simulation mode)
  - ✅ Support for all component types
- ✅ Component appearance constants in theme.py
- ✅ Canvas integration (set_page, render_components, etc.)
- ✅ MainWindow integration (tab/page switching)

**Deliverables**:
- ✅ All 4 component types render correctly
- ✅ Components rotate properly
- ✅ Components scale with zoom
- ✅ Visual feedback for selection
- ✅ Visual feedback for powered/unpowered state
- ✅ Components render when switching tabs/pages

**Tests**: 30/30 passing ✅
- Renderer factory (5 tests)
- Base renderer functionality (5 tests)
- Switch renderer (4 tests)
- Indicator renderer (2 tests)
- Relay renderer (2 tests)
- VCC renderer (2 tests)
- Canvas integration (7 tests)
- Zoom and rotation handling (3 tests)

**Implementation Notes**:
- Base renderer provides common functionality (rotation, drawing primitives, tab rendering)
- Each component has dedicated renderer class for specific appearance
- Factory pattern maps component types to renderer classes
- Renderers manage their own canvas items for clean lifecycle
- Selection state: blue outline when selected
- Powered state: color changes (bright when powered, dim when unpowered)
- Rotation: All drawing rotated around component center using trigonometry
- Zoom: All dimensions scale with zoom factor (40px * zoom)
- Tab rendering: Draws connection points for all component pins
- Canvas integration: renderers dict tracks all active renderers
- Page switching: triggers full component re-render
- Zoom changes: automatically re-renders all components at new scale

**Files Created** (~900 lines total):
- `gui/renderers/__init__.py` (17 lines) - Package exports
- `gui/renderers/base_renderer.py` (302 lines) - Abstract base class
- `gui/renderers/switch_renderer.py` (75 lines) - Switch renderer (40px circle)
- `gui/renderers/indicator_renderer.py` (75 lines) - Indicator renderer (30px LED)
- `gui/renderers/relay_renderer.py` (110 lines) - Relay renderer (80x60px rect)
- `gui/renderers/vcc_renderer.py` (80 lines) - VCC renderer (30px + symbol)
- `gui/renderers/renderer_factory.py` (75 lines) - Factory pattern
- `testing/test_component_rendering.py` (475 lines) - Complete test suite

**Files Modified**:
- `gui/theme.py` (+28 lines) - Component rendering constants
- `gui/canvas.py` (+80 lines) - Component rendering methods
- `gui/main_window.py` (updated) - Tab/page switching integration

---

### 10.4 Wire Rendering ✅ COMPLETE
**Objective**: Render wires, waypoints, and junctions on canvas.

**Tasks**:
- ✅ Implement `gui/renderers/wire_renderer.py`:
  - ✅ WireRenderer class
  - ✅ Render wire segments (lines between waypoints)
  - ✅ Render waypoints (small squares)
  - ✅ Render junctions (circles at junction points)
  - ✅ Wire color: different for powered/unpowered (simulation mode)
  - ✅ Wire selection highlight
  - ✅ Scale with zoom
  - ✅ Handle tab-to-tab vs tab-to-waypoint connections
- ✅ Canvas integration:
  - ✅ Wire renderers dictionary
  - ✅ render_wires() method
  - ✅ Wire state management (selection, powered)
  - ✅ Zoom integration for wires

**Deliverables**:
- ✅ Wires render as connected line segments
- ✅ Waypoints visible (4px squares)
- ✅ Junctions visible (5px circles)
- ✅ Wire color changes based on power state
- ✅ Wires scale with zoom
- ✅ Support for complex wire paths with waypoints
- ✅ Support for junction-based branching

**Implementation Notes**:
- WireRenderer follows same pattern as ComponentRenderer
- Tab position lookup via component/pin hierarchy
- Wire path: start_tab → waypoints → end_tab/junction
- Recursive rendering for junction child wires
- Colors: Gray (unpowered), Green (powered), Blue (selected)
- Waypoint markers: Small squares at each waypoint
- Junction markers: Circles where wires branch
- Full zoom support: line width and marker sizes scale
- Wire segments drawn as canvas lines between points
- Tab positions calculated from component position + relative offset

**Files Created**:
- `gui/renderers/wire_renderer.py` (265 lines) - Complete wire renderer

**Files Modified**:
- `gui/canvas.py` (+60 lines) - Wire rendering methods
- `gui/renderers/__init__.py` (+1 line) - Export WireRenderer

---

## Phase 11: Component Toolbox ✅ COMPLETE

**Status**: Component toolbox and placement fully functional
- Phase 11.1: Toolbox Panel ✅
- Phase 11.2: Component Placement ✅

**Total Phase 11 Code**: ~250 lines

### 11.1 Toolbox Panel ✅ COMPLETE
**Objective**: Left sidebar with component toolbox.

**Tasks**:
- ✅ Implement `gui/toolbox.py`:
  - ✅ ToolboxPanel class (left sidebar frame)
  - ✅ Scrollable list of component types
  - ✅ Component types: Switch, Indicator, DPDTRelay, VCC
  - ✅ Each component type as button with label
  - ✅ Selected component highlighted
  - ✅ "Select" tool (default, for moving components)
- ✅ Component buttons with hover effects
- ✅ VS Code dark theme styling

**Deliverables**:
- ✅ Toolbox visible on left side (200px width)
- ✅ All 4 component types listed
- ✅ Clicking component selects it for placement
- ✅ Select tool deselects component placement mode
- ✅ Visual feedback for selected component

**Implementation Notes**:
- ComponentButton class for individual component buttons
- Selection state with visual highlighting (BG_SELECTED color)
- Hover effects for better UX
- Auto-scrolling if many components (future extensibility)
- Integrated with MainWindow via callback

**Files Created**:
- `gui/toolbox.py` (250 lines) - Complete toolbox implementation

---

### 11.2 Component Placement ✅ COMPLETE
**Objective**: Place components from toolbox onto canvas.

**Tasks**:
- ✅ Implement component placement interaction:
  - ✅ When component selected in toolbox:
    - ✅ Cursor changes to crosshair
    - ✅ Left-click on canvas places component
    - ✅ Snap to grid (10px snap - half of 20px grid)
    - ✅ Assign unique component ID via IDManager
    - ✅ Add to current Page
  - ✅ After placement:
    - ✅ Component rendered on canvas
    - ✅ Toolbox returns to "Select" tool
    - ✅ Document marked as modified

**Deliverables**:
- ✅ All 4 component types can be placed on canvas
- ✅ Grid snapping works (10px increments)
- ✅ Component added to document and persists
- ✅ Component immediately visible after placement
- ✅ Cursor feedback during placement mode
- ✅ Status bar shows placement instructions

**Implementation Notes**:
- Canvas click handler in MainWindow (_on_canvas_click)
- Component selection callback (_on_component_selected)
- Grid snapping using snap_size = grid_size // 2
- Canvas coordinates conversion (canvasx/canvasy)
- Component creation using component classes directly
- Automatic return to Select tool after placement
- Document modification tracking triggers
- Full integration with rendering system

**Files Modified**:
- `gui/main_window.py` (+100 lines) - Placement logic and toolbox integration

---

## Phase 12: Properties Panel

### 12.1 Properties Panel Framework
**Objective**: Right sidebar with VS Code-style grouped properties.

**Tasks**:
- Implement `gui/properties_panel.py`:
  - PropertiesPanel class (right sidebar frame)
  - Grouped sections (collapsible):
    - **Component** section (id, type, position, rotation)
    - **Properties** section (component-specific properties)
    - **Advanced** section (additional settings)
  - Section headers with expand/collapse arrows
  - Property editors:
    - Text entry (for strings, numbers)
    - Dropdowns (for enums)
    - Checkboxes (for bools)
  - Apply button (or auto-apply on change)

**Deliverables**:
- Properties panel visible on right side
- Grouped sections collapsible
- Property editors functional

**Tests**:
- Panel displays selected component properties
- Editing properties updates component
- Collapsing sections works

---

### 12.2 Component Property Editors
**Objective**: Component-specific property editing.

**Tasks**:
- Implement property editors for each component:
  - Switch: normally_open (bool)
  - Indicator: color (dropdown)
  - DPDTRelay: coil_resistance (float)
  - VCC: voltage (float)
- Position editing (x, y with snap-to-grid button)
- Rotation editing (dropdown: 0, 90, 180, 270)
- ID editing (with validation for uniqueness)

**Deliverables**:
- All component properties editable
- Changes reflected immediately on canvas
- ID uniqueness enforced

**Tests**:
- Edit each property type
- Verify canvas updates
- Verify invalid IDs rejected

---

## Phase 13: Selection and Editing

### 13.1 Component Selection
**Objective**: Select components and wires on canvas.

**Tasks**:
- Implement selection system:
  - Left-click on component: select (deselect others)
  - Left-click on empty canvas: deselect all
  - Ctrl+Left-click: add to selection
  - Bounding box selection:
    - Left-click + drag on empty canvas: draw selection rectangle
    - All components/wires inside rectangle selected
  - Selected items highlighted (border color change)
  - Properties panel shows selected item properties
  - Multi-selection shows "(Multiple Items Selected)"

**Deliverables**:
- Single and multi-selection working
- Bounding box selection working
- Properties panel reflects selection

**Tests**:
- Select single component
- Multi-select with Ctrl+click
- Bounding box selection
- Properties panel updates

---

### 13.2 Component Movement
**Objective**: Move selected components on canvas.

**Tasks**:
- Implement component dragging:
  - Left-click on selected component + drag: move component(s)
  - Snap to grid during drag
  - Update component position in model
  - Redraw wires connected to moved components
  - Undo dragging on Escape key
- Arrow key movement:
  - Arrow keys: move selected components by grid size
  - Shift+Arrow: move by 1px (fine adjustment)

**Deliverables**:
- Components draggable with mouse
- Grid snapping during drag
- Arrow key movement
- Connected wires update

**Tests**:
- Drag component with mouse
- Move with arrow keys
- Verify grid snapping
- Verify wires follow component

---

### 13.3 Cut, Copy, Paste
**Objective**: Clipboard operations for components and wires.

**Tasks**:
- Implement clipboard system:
  - Copy (Ctrl+C): Serialize selected items to clipboard
  - Cut (Ctrl+X): Copy + delete selected items
  - Paste (Ctrl+V): Deserialize from clipboard, place at cursor position
  - Assign new unique IDs on paste
  - Paste offset: slightly offset from original position
- Clipboard format: JSON serialization of selected components/wires
- Context menu (right-click): Cut, Copy, Paste options

**Deliverables**:
- Copy/Cut/Paste functional
- New IDs assigned on paste
- Context menu works

**Tests**:
- Copy and paste component
- Cut component
- Paste multiple times (unique IDs)
- Context menu operations

---

### 13.4 Component Deletion
**Objective**: Delete components and wires.

**Tasks**:
- Implement deletion:
  - Delete/Backspace key: delete selected items
  - Context menu: Delete option
  - Confirmation dialog for deletion
  - Delete wires connected to deleted components
  - Remove from Page.components / Page.wires

**Deliverables**:
- Delete key removes selected items
- Connected wires removed
- Confirmation dialog

**Tests**:
- Delete component
- Delete wire
- Verify connected wires removed
- Deletion confirmation

---

## Phase 14: Wiring Interface

### 14.1 Wire Creation (Tab-to-Tab)
**Objective**: Create wires by connecting component tabs.

**Tasks**:
- Implement wire creation:
  - Left-click on tab: start wire
  - Visual feedback: line from tab to cursor
  - Left-click on another tab: complete wire
  - Escape: cancel wire creation
  - Wire added to Page.wires
  - Auto-routing: straight line initially
  - Tab highlight when hovering (valid connection)

**Deliverables**:
- Tab-to-tab wiring functional
- Visual feedback during creation
- Wires added to document

**Tests**:
- Create wire between two tabs
- Cancel wire creation
- Verify wire added to Page.wires

---

### 14.2 Wire Editing (Waypoints)
**Objective**: Add waypoints to route wires.

**Tasks**:
- Implement waypoint editing:
  - Left-click on wire segment: add waypoint
  - Waypoint appears at click position
  - Drag waypoint to reposition
  - Right-click waypoint: delete waypoint
  - Snap waypoints to grid
  - Update Wire.waypoints list

**Deliverables**:
- Waypoints can be added to wires
- Waypoints draggable
- Waypoints deletable
- Grid snapping

**Tests**:
- Add waypoint to wire
- Drag waypoint
- Delete waypoint
- Verify Wire.waypoints updated

---

### 14.3 Junction Support
**Objective**: Create junctions for wire branching.

**Tasks**:
- Implement junction creation:
  - When wire crosses another wire:
    - Auto-detect intersection point
    - Prompt: "Create junction?"
    - Create Junction object at intersection
  - Junction rendered as circle
  - Junction acts as connection point
  - Wires reference junction in waypoints

**Deliverables**:
- Junctions created at wire intersections
- Junctions connect multiple wires
- Junction rendering

**Tests**:
- Create junction at wire intersection
- Verify multiple wires connected
- Verify Junction added to Page

---

## Phase 15: Mode Switching and Simulation Integration

### 15.1 Design Mode
**Objective**: Full editing mode with toolbox visible.

**Tasks**:
- Implement Design Mode:
  - Toolbox visible
  - All editing operations enabled
  - Simulation controls disabled
  - Components non-interactive (can't toggle switches)
  - Menu: Simulation → Start Simulation (F5)

**Deliverables**:
- Design mode as default state
- All editing features work
- Simulation disabled

**Tests**:
- Verify toolbox visible
- Verify editing works
- Verify simulation controls disabled

---

### 15.2 Simulation Mode
**Objective**: Simulation mode with component interaction.

**Tasks**:
- Implement Simulation Mode:
  - Hide toolbox
  - Disable editing operations (can't move, delete, add components)
  - Enable component interaction:
    - Left-click on Switch: toggle state
    - Component visual feedback (powered/unpowered)
    - Wire color changes (powered/unpowered)
  - Integrate with SimulationEngine:
    - Start simulation on mode switch
    - Continuous simulation updates
    - Stop simulation on mode exit
  - Menu: Simulation → Stop Simulation (Shift+F5)

**Deliverables**:
- Simulation mode functional
- Component interaction works
- Visual feedback for power state
- SimulationEngine integration

**Tests**:
- Start simulation mode
- Toggle switch component
- Verify LED lights up
- Stop simulation mode

---

### 15.3 Simulation Controls
**Objective**: Top toolbar with simulation controls.

**Tasks**:
- Implement `gui/simulation_toolbar.py`:
  - SimulationToolbar class (top toolbar)
  - Buttons:
    - Start Simulation (F5, green play icon)
    - Stop Simulation (Shift+F5, red stop icon)
    - Pause Simulation (yellow pause icon)
  - Button states (enabled/disabled based on mode)
  - Integration with mode switching

**Deliverables**:
- Simulation toolbar visible
- Start/Stop/Pause buttons functional
- Button states update correctly

**Tests**:
- Click Start Simulation
- Click Stop Simulation
- Click Pause Simulation
- Verify mode changes

---

### 15.4 Status Bar
**Objective**: Bottom status bar with zoom level and mode indicator.

**Tasks**:
- Implement `gui/status_bar.py`:
  - StatusBar class (bottom frame)
  - Display current zoom level (e.g., "Zoom: 100%")
  - Display current mode ("Design Mode" / "Simulation Mode")
  - Update on zoom changes
  - Update on mode changes

**Deliverables**:
- Status bar visible
- Zoom level displayed
- Mode displayed
- Updates in real-time

**Tests**:
- Zoom in/out, verify status updates
- Switch modes, verify status updates

---

## Phase 16: Polish and Testing

### 16.1 UI Testing
**Objective**: Comprehensive testing of all UI components.

**Tasks**:
- Create test suite for GUI:
  - `testing/test_gui_window.py`: Window and theme tests
  - `testing/test_gui_canvas.py`: Canvas, zoom, pan tests
  - `testing/test_gui_components.py`: Component rendering, placement tests
  - `testing/test_gui_wiring.py`: Wire creation, editing tests
  - `testing/test_gui_selection.py`: Selection, movement tests
  - `testing/test_gui_clipboard.py`: Copy/paste tests
  - `testing/test_gui_modes.py`: Design/Simulation mode tests
- Manual testing checklist:
  - All menu items work
  - All keyboard shortcuts work
  - All mouse interactions work
  - File operations work
  - Simulation integration works

**Deliverables**:
- Comprehensive GUI test suite
- All tests passing
- Manual testing checklist completed

**Tests**:
- 50+ GUI tests covering all features

---

### 16.2 Performance Optimization
**Objective**: Ensure smooth performance with large circuits.

**Tasks**:
- Profile rendering performance:
  - Measure FPS during zoom/pan
  - Identify rendering bottlenecks
  - Optimize grid rendering (only draw visible grid)
  - Optimize component rendering (cache rendered components)
  - Optimize wire rendering (simplify when zoomed out)
- Test with large circuits:
  - 100+ components
  - 200+ wires
  - Verify acceptable performance

**Deliverables**:
- Smooth zoom/pan performance
- Large circuits render quickly
- No UI lag during simulation

**Tests**:
- Performance benchmarks
- Large circuit tests

---

### 16.3 User Experience Refinements
**Objective**: Polish UI for professional appearance.

**Tasks**:
- UI refinements:
  - Tooltips for all buttons and menu items
  - Cursor changes for different tools (pointer, crosshair, move)
  - Smooth animations for zoom (optional)
  - Consistent spacing and alignment
  - Error message dialogs for invalid operations
  - Loading indicator for large files
- Keyboard shortcuts help dialog (F1)
- About dialog (Help → About)

**Deliverables**:
- Professional, polished UI
- Tooltips everywhere
- Help documentation

**Tests**:
- Manual UX review
- User testing (if available)

---

### 16.4 Documentation
**Objective**: Complete documentation for UI usage.

**Tasks**:
- Create `docs/UserGuide.md`:
  - Getting started
  - Creating a circuit (step-by-step)
  - Component placement
  - Wiring
  - Simulation
  - File operations
  - Keyboard shortcuts reference
  - FAQ
- Create `docs/DeveloperGuide.md`:
  - GUI architecture overview
  - Adding new component renderers
  - Extending the UI
  - Testing guidelines

**Deliverables**:
- Complete user guide
- Developer documentation

---

## Implementation Strategy

### Phase Ordering
The phases are designed to be implemented sequentially, with each phase building on the previous ones:

1. **Phase 8**: Window framework provides foundation
2. **Phase 9**: File management enables document operations
3. **Phase 10**: Canvas enables visualization
4. **Phase 11**: Toolbox enables component placement
5. **Phase 12**: Properties enable component editing
6. **Phase 13**: Selection/editing enable full design workflow
7. **Phase 14**: Wiring enables circuit creation
8. **Phase 15**: Mode switching enables simulation
9. **Phase 16**: Polish and finalize

### Testing Strategy
- Unit tests for non-GUI logic (settings, file operations)
- Integration tests for GUI components (where possible with tkinter testing)
- Manual testing checklist for UI interactions
- Example circuit tests (load and render example .rsim files)

### Integration Points
The UI integrates with existing backend:
- **Document/Page/Component classes**: Direct usage for data model
- **ComponentFactory**: Dynamic component loading
- **DocumentLoader**: File I/O operations
- **SimulationEngine**: Simulation execution
- **VnetBuilder**: Network building for simulation

---

## Success Criteria

### Phase 8 Complete When:
- [ ] Window opens with dark theme
- [ ] All menus present and functional
- [ ] Settings persist correctly
- [ ] 15+ tests passing

### Phase 9 Complete When:
- [ ] Multiple files can be open
- [ ] Multiple pages per file
- [ ] File operations work (New, Open, Save, Save As)
- [ ] Recent documents tracked
- [ ] 20+ tests passing

### Phase 10 Complete When:
- [ ] Canvas renders with grid
- [ ] Zoom/pan functional
- [ ] Components render correctly
- [ ] Wires render correctly
- [ ] Canvas state persists per page
- [ ] 25+ tests passing

### Phase 11 Complete When:
- [ ] Toolbox displays all components
- [ ] Components can be placed on canvas
- [ ] Grid snapping works
- [ ] 10+ tests passing

### Phase 12 Complete When:
- [ ] Properties panel shows component properties
- [ ] Properties can be edited
- [ ] Changes reflected on canvas
- [ ] 15+ tests passing

### Phase 13 Complete When:
- [ ] Selection works (single and multi)
- [ ] Components can be moved
- [ ] Copy/paste functional
- [ ] Deletion works
- [ ] 20+ tests passing

### Phase 14 Complete When:
- [ ] Wires can be created
- [ ] Waypoints can be added/edited
- [ ] Junctions can be created
- [ ] 15+ tests passing

### Phase 15 Complete When:
- [ ] Design mode fully functional
- [ ] Simulation mode functional
- [ ] Component interaction works (toggle switches)
- [ ] Visual feedback for power state
- [ ] SimulationEngine integrated
- [ ] 20+ tests passing

### Phase 16 Complete When:
- [ ] All UI tests passing (50+)
- [ ] Performance acceptable with large circuits
- [ ] User guide complete
- [ ] Developer guide complete
- [ ] Application ready for release

---

## Total Estimated Test Count
- Phase 8: 79 tests ✅ (Window, Menu, Settings)
- Phase 9: 45 tests ✅ (File Tabs, Page Tabs, File Operations)
- Phase 10: 68 tests ✅ (Canvas Foundation, State Management, Component Rendering, Wire Rendering)
  - Phase 10.1: 24 tests ✅
  - Phase 10.2: 14 tests ✅
  - Phase 10.3: 30 tests ✅
  - Phase 10.4: Manual testing ✅ (Wire rendering functional)
- Phase 11: Manual testing ✅ (Toolbox and Component Placement - fully functional)
- Phase 12: ~15 tests (Properties Panel)
- Phase 13: ~20 tests (Selection and Editing)
- Phase 14: ~15 tests (Wire Editing - wire creation UI)
- Phase 15: ~20 tests (Simulation Mode)
- Phase 16: ~50 tests (Polish and Integration)

**Current Progress: 192/~320 GUI tests complete (60%)**
**Completed Phases: 8, 9.1, 9.2, 9.3, 10.1, 10.2, 10.3, 10.4, 11.1, 11.2**
**Next: Phase 12 (Properties Panel), Phase 13 (Selection), or Phase 14 (Wire Editing)**

---

## Timeline Estimate
- Phase 8: 1-2 days (foundation)
- Phase 9: 2-3 days (file management complexity)
- Phase 10: 3-4 days (canvas complexity)
- Phase 11: 1 day (toolbox)
- Phase 12: 2 days (properties panel)
- Phase 13: 2-3 days (selection and editing)
- Phase 14: 2-3 days (wiring complexity)
- Phase 15: 2-3 days (simulation integration)
- Phase 16: 2-3 days (testing and polish)

**Total: ~17-26 days** (individual developer working full-time)

---

## Risk Assessment

### High-Risk Areas
1. **tkinter Canvas Performance**: Large circuits may cause lag
   - Mitigation: Implement canvas caching, draw only visible area
2. **Simulation Integration**: UI update rate during simulation
   - Mitigation: Use threading, throttle UI updates
3. **Multi-Document State**: Complex state management
   - Mitigation: Clear state separation, document-centric design

### Medium-Risk Areas
1. **Wire Routing**: Complex waypoint editing
   - Mitigation: Start with simple implementation, iterate
2. **Zoom/Scale**: Components and wires must scale correctly
   - Mitigation: Comprehensive testing at various zoom levels

### Low-Risk Areas
1. **Theme Application**: Well-defined color palette
2. **Menu System**: Standard tkinter menus
3. **File Operations**: Already implemented in backend

---

## Future Enhancements (Post-Phase 16)
- Undo/Redo system
- Component library browser
- Circuit validation (detect shorts, open circuits)
- Auto-routing for wires
- Circuit simulation visualization (animated current flow)
- Export circuit as image (PNG, SVG)
- Print circuit diagrams
- Multi-user collaboration (network sync)

---

**End of Frontend Implementation Plan**
