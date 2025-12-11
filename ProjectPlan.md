# Relay Logic Simulator - Project Plan & Todo Lists

## Project Overview
Development of a multi-threaded relay logic simulation engine with terminal interface, designed to handle 100+ components efficiently using a dirty-flag optimization strategy.

---

## PHASE 0: PROJECT SETUP & DECISIONS

### Technology Stack Decisions
- [ ] Choose primary programming language
  - [ ] Python - Rapid development, but performance concerns

  
- [ ] Select file format for .rsim files
  - [ ] JSON (recommended - modern, readable, easy parsing)
  
- [ ] Choose threading library/approach
  - [ ] Language built-in (preferred)
  
- [ ] Select testing framework
  - [ ] Integration testing approach
  
- [ ] Choose UUID library
  - [ ] Built-in UUID support

### Project Structure Setup
- [ ] Create project folders - YES
  - [ ] `/src` - Source code
  - [ ] `/src/core` - Core engine
  - [ ] `/src/components` - Component implementations
  - [ ] `/src/networking` - Terminal/telnet interface
  - [ ] `/src/fileio` - File loading/saving
  - [ ] `/tests` - Unit and integration tests
  - [ ] `/docs` - Documentation
  - [ ] `/examples` - Example .rsim files

  Split Classes into separate files whenever possible I dont want 5000 line .py files if I can avoid it
  
- [ ] Initialize version control (Git) - YES
- [ ] Create README.md - YES
- [ ] Set up build system - YES
- [ ] Configure IDE/editor - YES
---

## PHASE 1: CORE FOUNDATION CLASSES

### 1.1 ID Management System
- [*] Implement UUID generation utility
  - [*] Generate full UUID
  - [*] Truncate to first 8 characters
  - [*] Ensure uniqueness within document
  
- [*] Create ID validation system
  - [*] Check for duplicates
  - [*] Validate hierarchical format
  - [*] Parse hierarchical IDs (split by dots)
  
- [*] Implement ID regeneration for copy/paste
  - [*] Copy: Generate all new IDs
  - [*] Cut same page: Keep IDs
  - [*] Cut different page: Regenerate PageID only
  
- [ ] Create ID registry/lookup system
  - [ ] Fast lookups by ID
  - [ ] Support hierarchical queries

**Tests:**
- [*] Test UUID generation uniqueness
- [*] Test ID validation
- [*] Test copy/paste ID regeneration
- [*] Test hierarchical ID parsing

---

### 1.2 Signal State System
- [*] Define PinState enumeration
  - [*] FLOAT state
  - [*] HIGH state
  
- [*] Implement state logic functions
  - [*] OR logic: HIGH + FLOAT = HIGH
  - [*] OR logic: FLOAT + FLOAT = FLOAT
  - [*] OR logic: HIGH + HIGH = HIGH
  
- [*] Create state comparison utilities
  - [*] Detect state changes
  - [*] State equality checking

**Tests:**
- [*] Test all state combinations
- [*] Test state change detection

---

### 1.3 Tab Class
- [*] Define Tab class
  - [*] TabId (string, 8 char UUID)
  - [*] Position (relative to component)
  - [*] Current state (PinState)
  - [*] Parent pin reference
  
- [*] Implement tab state management
  - [*] Get state
  - [*] Set state (propagate to pin)
  
- [*] Add serialization support
  - [*] Serialize to file format
  - [*] Deserialize from file format

**Tests:**
- [*] Test tab creation
- [*] Test state management
- [*] Test serialization/deserialization

---

### 1.4 Pin Class
- [*] Define Pin class
  - [*] PinId (string, 8 char UUID)
  - [*] Collection of Tabs
  - [*] Current state (PinState)
  - [*] Parent component reference
  
- [*] Implement pin-tab state synchronization
  - [*] Tab state change → Pin state update
  - [*] Pin state change → All tabs update
  - [*] HIGH OR logic across all tabs
  
- [*] Add tab management
  - [*] Add tab
  - [*] Remove tab
  - [*] Get all tabs
  
- [*] Add serialization support

**Tests:**
- [*] Test pin-tab state propagation
- [*] Test multiple tabs on one pin
- [*] Test HIGH OR logic with multiple tabs
- [*] Test serialization

---

### 1.5 Component Base Class/Interface
- [*] Define IComponent interface or Component base class
  - [*] ComponentId (string)
  - [*] ComponentType (enum or string)
  - [*] Position (X, Y)
  - [*] Rotation (if needed)
  - [*] LinkName (optional string)
  - [*] Collection of Pins
  - [*] Custom properties dictionary
  
- [*] Define required methods
  - [*] `ComponentLogic()` - Calculate new states
  - [*] `UpdateVisual()` - Redraw (stub for now)
  - [*] `HandleInteraction(interactionType)` - User input
  - [*] `SimStart()` - Initialize on simulation start
  - [*] `SimStop()` - Cleanup on simulation stop
  
- [*] Add pin management
  - [*] Add pin
  - [*] Get pin by ID
  - [*] Get all pins
  
- [*] Add property management
  - [*] Get property
  - [*] Set property
  - [*] Clone properties (for copy)
  
- [*] Add serialization support

**Tests:**
- [*] Test component creation
- [*] Test pin management
- [*] Test property management
- [*] Test serialization

---

### 1.6 Page Class
- [*] Define Page class
  - [*] PageId (string, 8 char UUID)
  - [*] Name/Title (string)
  - [*] Collection of Components
  - [*] Collection of Wires
  
- [*] Implement component management
  - [*] Add component
  - [*] Remove component
  - [*] Get component by ID
  - [*] Get all components
  
- [*] Implement wire management (basic for now)
  - [*] Add wire
  - [*] Remove wire
  - [*] Get wire by ID
  
- [*] Add serialization support

**Tests:**
- [*] Test page creation
- [*] Test component management
- [*] Test serialization

---

### 1.7 Document Class
- [*] Define Document class
  - [*] Document metadata
  - [*] Collection of Pages
  
- [*] Implement page management
  - [*] Add page
  - [*] Remove page
  - [*] Get page by ID
  - [*] Get all pages
  
- [*] Implement document-wide operations
  - [*] Validate all IDs unique
  - [*] Get all components across pages
  
- [*] Add serialization support
  - [*] Save to .rsim file
  - [*] Load from .rsim file

**Tests:**
- [*] Test document creation
- [*] Test page management
- [*] Test ID uniqueness validation
- [*] Test file save/load

---

## PHASE 2: WIRE & VNET SYSTEM

### 2.1 Wire Structure Classes
- [*] Define Waypoint class
  - [*] WaypointId (string)
  - [*] Position (X, Y)
  
- [*] Define Junction class
  - [*] JunctionId (string)
  - [*] Position (X, Y)
  - [*] Collection of child Wires
  
- [*] Define Wire class
  - [*] WireId (string)
  - [*] StartTabId (reference)
  - [*] EndTabId (reference, can be null if junction)
  - [*] Collection of Waypoints
  - [*] Collection of Junctions
  - [*] Parent wire (if nested)
  
- [*] Implement wire hierarchy
  - [*] Nested wire structure
  - [*] Navigate parent/child relationships
  
- [*] Add serialization support

**Tests:**
- [*] Test wire creation
- [*] Test wire hierarchy
- [*] Test junction connections
- [*] Test junction deletions
- [*] Test serialization

---

### 2.2 VNET Class
- [*] Define VNET class
  - [*] VnetId (string, 8 char UUID)
  - [*] Collection of TabIds
  - [*] Collection of LinkNames
  - [*] Collection of BridgeIds
  - [*] Current state (PinState)
  - [*] Dirty flag (boolean)
  - [*] PageId (for single-page VNETs)
  
- [*] Implement VNET operations
  - [*] Add tab
  - [*] Remove tab
  - [*] Add link
  - [*] Remove link
  - [*] Add bridge
  - [*] Remove bridge
  
- [*] Implement state management
  - [*] Evaluate VNET state (HIGH OR FLOAT)
  - [*] Mark dirty
  - [*] Clear dirty
  - [*] Check if dirty
  
- [*] Thread-safety
  - [*] Add locking for state changes
  - [*] Add locking for dirty flag

**Tests:**
- [*] Test VNET creation
- [*] Test tab management
- [*] Test state evaluation
- [*] Test dirty flag
- [*] Test thread-safety

---

### 2.3 VNET Builder Algorithm
- [*] Implement graph traversal algorithm
  - [*] Follow wire to connected tabs
  - [*] Handle junctions (multiple branches)
  - [*] Mark tabs as processed
  - [*] Create VNET with all connected tabs
  
- [*] Handle edge cases
  - [*] Disconnected tabs (single-tab VNETs)
  - [*] Complex junction networks
  - [*] Circular wire paths
  
- [*] Optimize for performance
  - [*] Efficient data structures
  - [*] Avoid redundant processing
  
- [*] Create VnetBuilder class/module
  - [*] `BuildVnetsForPage(page)` - Main entry point
  - [*] Returns collection of VNETs

**Tests:**
- [*] Test simple wire (2 tabs)
- [*] Test junction (3+ tabs)
- [*] Test complex network
- [*] Test disconnected components
- [*] Test nested junctions

---

### 2.4 Link Resolution System
- [*] Implement link resolver
  - [*] Scan all components for LinkName property
  - [*] Build link name → components map
  - [*] Find VNETs containing linked component tabs
  - [*] Add link name to those VNETs
  
- [*] Create LinkResolver class
  - [*] `ResolveLinks(document, vnets)` - Main entry point
  
- [*] Handle cross-page links
  - [*] Link VNETs from different pages
  
- [*] Validate links
  - [*] Warn about unconnected links
  - [*] Detect link name conflicts

**Tests:**
- [*] Test same-page links
- [*] Test cross-page links
- [*] Test multiple components same link name
- [*] Test unconnected links

---

### 2.5 Bridge System
- [*] Define Bridge class
  - [*] BridgeId (string, runtime only)
  - [*] VnetId1 (first connected VNET)
  - [*] VnetId2 (second connected VNET)
  - [*] Owner component (reference)
  
- [*] Implement BridgeManager class
  - [*] Create bridge between two VNETs
  - [*] Remove bridge from VNETs
  - [*] Get bridge by ID
  - [*] Mark connected VNETs dirty
  
- [*] Add bridge operations to VNET
  - [*] Add bridge reference
  - [*] Remove bridge reference
  - [*] Get connected VNETs via bridges
  
- [*] Thread-safety
  - [*] Lock during bridge add/remove

**Tests:**
- [*] Test bridge creation
- [*] Test bridge removal
- [*] Test VNET dirty marking
- [*] Test thread-safety
- [*] Test multiple bridges on same VNET

---

## PHASE 3: COMPONENT IMPLEMENTATIONS

The properties panel will have consistant sections for easier navigation

Ive added the section name before the property to add.

General > ID means the ID field will be in the General section etc

### 3.1 Switch Component
- [*] Define Switch class (extends Component)
  - [*] Pin configuration: 1 pin 4 tags at 3,6,9 and 12 o'clock positions
  - [*] Circular 40px diameter
  - [*] State: ON/OFF (boolean)
  
- [*] Implement ComponentLogic()
  - [*] If ON: Set output pin to HIGH
  - [*] If OFF: Set output pin to FLOAT
  - [*] Mark VNET dirty if state changed
  
- [*] Implement HandleInteraction()
  - [*] Toggle: ON ↔ OFF
  - [*] Pushbutton Mode: Pressed = ON Released = OFF
  - [*] Update pin state
  
- [*] Implement SimStart()
  - [*] Default to OFF state
  - [*] Set initial pin states
  
- [*] Implement SimStop()
  - [*] Clear state (optional)
  
- [*] Add visual properties
  - [*] General > ID (readonly)
  - [*] General >Label (optional)
  - [*] General >Label position (Top, bottom left or right)
  - [*] Format > Mode Pushbutton or Toggle
  - [*] Format > Color
                    Drop down combo box with basic colors.
                    If Red is selected set the On color to Bright red and the Off color to a dull red.

**Tests:**
- [*] Test switch creation
- [*] Test toggle interaction in both Modes
- [*] Test pin state updates
- [*] Test VNET dirty marking
- [*] Test SimStart initialization

---

### 3.2 Indicator (LED) Component [*]
- [*] Define Indicator class (extends Component)
  - [*] Pin configuration: 1 pin, 4 tabs (12, 3, 6, 9 o'clock)
  - [*] Visual state: ON/OFF (derived from pin state)
  
- [*] Implement ComponentLogic()
  - [*] Read pin state (passive component)
  - [*] No state changes (read-only)
  
- [*] Implement HandleInteraction()
  - [*] No interaction (passive component)
  
- [*] Implement SimStart()
  - [*] Initialize pin to FLOAT
  - [*] Position tabs at clock positions
  
- [*] Implement SimStop()
  - [*] No cleanup needed
  
- [*] Add visual properties
  - [*] General > ID (readonly)
  - [*] General >Label (optional)
  - [*] General >Label position (Top, bottom left or right)
  - [*] Format > Color
                    Drop down combo box with basic colors.
                    If Red is selected set the On color to Bright red and the Off color to a dull red.

**Tests:**
- [*] Test indicator creation
- [*] Test pin state reading
- [*] Test 4 tabs on 1 pin
- [*] Test visual state (HIGH → ON)

---

### 3.3 DPDT Relay Component [*]
- [*] **FIRST: Define exact pin configuration**
  - [*] Coil: 1 pins (COIL)
  - [*] Pole 1: COM1, NO1, NC1 (3 pins)
  - [*] Pole 2: COM2, NO2, NC2 (3 pins)
  - [*] Total: 7 pins
  
- [*] Define DPDTRelay class (extends Component)
  - [*] Pin references for all 7 pins
  - [*] State: Energized/De-energized (boolean)
  - [*] Bridge IDs for both poles
  - [*] Coil threshold: HIGH = energized
  
- [*] Implement ComponentLogic()
  - [*] Read coil pin states
  - [*] If coil HIGH → Start internal 10ms timer 
  - [*] If coil FLOAT → Start internal 10ms timer
  - [*] Once timer completes then energise or de-energize coil.
  - [*] Timer is non blocking
  - [*] If timer completes:
    - [*] Move bridges (see below)
    - [*] Mark affected VNETs dirty
  
- [*] Implement Bridge Management
  - [*] Create 2 bridges at SimStart
  - [*] De-energized: COM1→NC1, COM2→NC2
  - [*] Energized: COM1→NO1, COM2→NO2
  - [*] Remove from old VNETs, add to new VNETs
  
- [*] Implement SimStart()
  - [*] Create bridges for both poles
  - [*] Connect COM→NC (de-energized state)
  - [*] Initialize coil to FLOAT
  
- [*] Implement SimStop()
  - [*] Bridges removed by engine (or explicitly here?)
  
- [*] Add visual properties
  - [*] General > ID (readonly)
  - [*] General > Label (optional)
  - [*] General > Label position (Top, bottom left or right)
  - [*] Format > Color
                    Drop down combo box with basic colors.
                    If Red is selected set the On color to Bright red and the Off color to a dull red.
  - [*] Format > Rotation 0, 90, 180,270 degrees
  - [*] Format > Flip Horizontal
  - [*] Format > Flip Vertical

**Tests:**
- [*] Test relay creation
- [*] Test coil energization
- [*] Test Timer and delayed switching
- [*] Test bridge switching (NC→NO)
- [*] Test dual-pole independence
- [*] Test VNET dirty marking
- [*] Test bridge cleanup

---
### 3.3.5 VCC [*]
- [*] Define Indicator class (extends Component)
  - [*] Pin configuration: 1 pin, 1 tab
  - [*] Visual state: Always ON
  
- [*] Implement ComponentLogic()
  - None
  
- [*] Implement HandleInteraction()
  - None
  
- [*] Implement SimStart()
  - [*] Initialize pin to HIGH

  
- [*] Implement SimStop()
  - [*] Set pin to HIGH
  - [*] No cleanup needed
  
- [*] Add visual properties
  - [*] General > ID (readonly)

**Tests:**
- [*] Test goes HIGH on Sim Start
- [*] Test goes FLOAT on Sim Stop

---

### 3.4 Component Factory/Registry [*]
- [*] Create ComponentFactory class
  - [*] Register component types
  - [*] Create component by type string
  - [*] List available component types
  
- [*] Register all components
  - [*] ToggleSwitch
  - [*] Indicator
  - [*] DPDTRelay
  - [*] VCC
  
- [*] Support deserialization
  - [*] Create component from file data
  - [*] Restore all properties

**Tests:**
- [*] Test component creation by type
- [*] Test component registration
- [*] Test deserialization

---

## PHASE 4: SIMULATION ENGINE

### 4.1 VNET State Evaluator [*]
- [*] Create VnetEvaluator class
  - [*] `EvaluateVnetState(vnet)` - Main method
  
- [*] Implement evaluation logic
  - [*] Read all tab states in VNET
  - [*] Apply HIGH OR FLOAT logic
  - [*] Determine final VNET state
  - [*] Return computed state
  
- [*] Handle links
  - [*] Get state from linked VNETs
  - [*] Include in OR evaluation
  
- [*] Handle bridges
  - [*] Get state from bridged VNETs
  - [*] Include in OR evaluation

**Tests:**
- [*] Test with all FLOAT tabs
- [*] Test with one HIGH tab
- [*] Test with multiple HIGH tabs
- [*] Test with links
- [*] Test with bridges

---

### 4.2 State Propagation System [*]
- [*] Create StatePropagator class
  - [*] `PropagateVnetState(vnet, newState)`
  
- [*] Implement propagation logic
  - [*] Update VNET state
  - [*] Update all tab states in VNET
  - [*] Update pins associated with tabs
  - [*] Propagate to linked VNETs
  - [*] Propagate to bridged VNETs
  
- [*] Handle link propagation
  - [*] Find all VNETs with same link name
  - [*] Propagate state to those VNETs
  - [*] Avoid infinite loops
  
- [*] Handle bridge propagation
  - [*] Find connected VNETs via bridges
  - [*] Propagate state
  - [*] Avoid infinite loops

**Tests:**
- [*] Test basic propagation
- [*] Test pin-tab update
- [*] Test link propagation
- [*] Test bridge propagation
- [*] Test circular link detection

---

### 4.3 Dirty Flag Manager [*]
- [*] Create DirtyFlagManager class
  - [*] Track all VNETs
  - [*] Mark VNET dirty
  - [*] Clear VNET dirty
  - [*] Get all dirty VNETs
  - [*] Check if any VNETs dirty
  
- [*] Implement dirty detection
  - [*] Component requests pin state change
  - [*] Compare with current VNET state
  - [*] If different → mark dirty
  
- [*] Thread-safety
  - [*] Lock when marking/clearing dirty
  - [*] Atomic dirty flag operations

**Tests:**
- [*] Test marking dirty
- [*] Test clearing dirty
- [*] Test getting dirty VNETs
- [*] Test stability detection
- [*] Test thread-safety

---

### 4.4 Component Update Coordinator [*]
- [*] Create ComponentUpdateCoordinator class
  - [*] Queue component logic updates
  - [*] Track pending updates
  - [*] Wait for completion
  
- [*] Implement update queueing
  - [*] Get all components connected to dirty VNET
  - [*] Queue their ComponentLogic() calls
  - [*] Avoid duplicate queues
  
- [*] Implement completion tracking
  - [*] Count pending updates
  - [*] Wait for all to complete
  - [*] Timeout handling

**Tests:**
- [*] Test update queueing
- [*] Test completion waiting
- [*] Test timeout handling

---

### 4.5 Main Simulation Loop [*]
- [*] Create SimulationEngine class
  - [*] Document reference
  - [*] Collection of VNETs
  - [*] Running state (boolean)
  - [*] Statistics (iterations, time, etc.)
  
- [*] Implement initialization
  - [*] Load document
  - [*] Build VNETs for all pages
  - [*] Resolve links
  - [*] Call SimStart on all components
  - [*] Mark all VNETs dirty
  
- [*] Implement main loop
  ```
  While running:
    For each VNET:
      If dirty:
        Evaluate VNET state
        Propagate to tabs/pins
        Queue component updates
    
    Wait for component updates to complete
    
    If no dirty VNETs:
      Mark stable
      Notify observers (for front-end)
    Else:
      Continue loop
    
    Check for max iterations (oscillation detection)
    Check for user commands
  ```
  
- [*] Implement shutdown
  - [*] Set running = false
  - [*] Call SimStop on all components
  - [*] Clear VNETs
  - [*] Clear bridges
  
- [*] Add oscillation detection
  - [*] Max iterations limit
  - [*] Timeout limit
  - [*] Report oscillation error
  
- [*] Add statistics tracking
  - [*] Iterations count
  - [*] Time to stability
  - [*] Components updated

**Tests:**
- [*] Test simple circuit (Switch → LED)
- [*] Test stability detection
- [*] Test oscillation detection
- [*] Test SimStart/SimStop calls
- [*] Test statistics

---

## PHASE 5: MULTI-THREADING

### 5.1 Thread Pool Setup [*]
- [*] Choose thread pool implementation
  - [*] Language built-in (preferred)
  - [*] Custom implementation
  
- [*] Create ThreadPool wrapper class
  - [*] Initialize with thread count
  - [*] Submit work items
  - [*] Wait for completion
  - [*] Shutdown pool
  
- [*] Determine optimal thread count
  - [*] CPU core count based?
  - [*] Configurable?

**Tests:**
- [*] Test pool initialization
- [*] Test work submission
- [*] Test completion waiting
- [*] Test shutdown

---

### 5.2 Concurrent VNET Processing [*]
- [*] Modify SimulationEngine for threading
  - [*] Process multiple VNETs in parallel
  - [*] Thread-safe VNET access
  - [*] Lock strategies
  
- [*] Implement VNET work items
  - [*] Evaluate VNET task
  - [*] Propagate state task
  - [*] Queue component updates task
  
- [*] Add synchronization
  - [*] Read/write locks on VNETs
  - [*] Dirty flag atomic operations
  - [*] Thread-safe collections

**Tests:**
- [*] Test parallel VNET processing
- [*] Test thread-safety under load
- [*] Test deadlock prevention
- [*] Test performance vs single-threaded

---

### 5.3 Component Logic Threading [*]
- [*] Modify component logic execution
  - [*] Submit to thread pool
  - [*] Track completion
  - [*] Handle errors
  
- [*] Add component-level thread-safety
  - [*] Lock component state during logic
  - [*] Thread-safe pin access
  
- [*] Implement work coordinator
  - [*] Queue component logic calls
  - [*] Wait for all completions
  - [*] Collect errors

**Tests:**
- [*] Test parallel component execution
- [*] Test component state consistency
- [*] Test error handling
- [*] Test performance improvement

---

### 5.4 Performance Optimization [*]
- [*] Profile execution
  - [*] Identify bottlenecks (threading_overhead_profiler.py)
  - [*] Measure lock contention (1.45x slowdown)
  - [*] Measure thread pool overhead (19.5µs per task)
  - [*] Measure synchronization barriers (60% overhead)
  - [*] Analyze work unit granularity
  
- [*] Document findings
  - [*] Created THREADING_BOTTLENECK_ANALYSIS.md (comprehensive report)
  - [*] Identified 4 primary bottlenecks
  - [*] Provided optimization recommendations
  
- [*] Implement single-threaded by default
  - [*] Created SimulationEngineFactory
  - [*] Created EngineConfig for mode selection
  - [*] AUTO mode: <2000 components = single, ≥2000 = multi
  - [*] Option to override: 'single', 'multi', or 'auto'
  - [*] 26 tests passing

**Findings:**
- Multi-threaded is 2x SLOWER for typical circuits (<500 components)
- Threading overhead exceeds parallelism benefit
- Synchronization barriers: 60% overhead (1.60x slowdown)
- Thread pool overhead: 19.5µs per task vs 2-15µs work time
- Lock contention: 1.45x slowdown
- Crossover point: ~2000-5000 components

**Implementation:**
- Default: AUTO mode (single-threaded for <2000, multi for ≥2000)
- Factory pattern for engine selection
- Convenience functions for explicit mode selection
- Performance recommendations based on component count

**Tests:**
- [*] Benchmark with 10, 50, 100, 500 components
- [*] Thread scaling test (1, 2, 4, 8, 16 threads)
- [*] Circuit complexity test
- [*] Lock contention profiling
- [*] Thread pool overhead measurement
- [*] Work unit granularity analysis
- [*] Synchronization barrier analysis
- [*] Engine factory unit tests (26 tests)

---

## PHASE 6: TERMINAL INTERFACE

### 6.1 Telnet Server [*]
- [*] Implement TCP socket server
  - [*] Listen on configurable port (default: 5000)
  - [*] Accept client connections
  - [*] Handle multiple clients (up to configurable max)
  
- [*] Implement basic telnet protocol
  - [*] Character-by-character input
  - [*] Line buffering
  - [*] Echo handling (configurable on/off)
  - [*] Control characters (Ctrl+C, Ctrl+D, Backspace)
  
- [*] Create TerminalServer class
  - [*] Start server
  - [*] Stop server
  - [*] Handle client connections (threaded per-client)
  - [*] Send/receive text
  - [*] Command callback system
  - [*] Broadcast to all clients
  - [*] Status reporting
  
- [*] Additional features
  - [*] Built-in commands (quit, exit, bye)
  - [*] Welcome message
  - [*] Prompt display (relay>)
  - [*] Client connection tracking
  - [*] Maximum client limit
  - [*] Graceful shutdown
  - [*] Thread-safe client management

**Tests:**
- [*] Test server start/stop (passing)
- [*] Test client connection (passing)
- [*] Test text send/receive (passing)
- [*] Test multiple clients (passing)
- [*] Test max clients limit (passing)
- [*] Test command processing (passing)
- [*] Test backspace handling (passing)
- [*] Test Ctrl+C handling (passing)
- [*] Test quit command (passing)
- [*] Test broadcast (passing)
- [*] Test echo on/off (passing)
- [*] Test status reporting (passing)
- [*] 15 tests passing

---

### 6.2 Command Parser
- [*] Create CommandParser class
  - [*] Parse command line
  - [*] Split into command + arguments
  - [*] Validate arguments
  
- [*] Define command structure
  - [*] Command name
  - [*] Argument list
  - [*] Options/flags
  
- [*] Implement command registry
  - [*] Register command handlers
  - [*] Dispatch to handlers
  - [*] Return results

**Tests:**
- [*] Test command parsing (14 tests)
- [*] Test argument validation (11 tests)
- [*] Test option validation (6 tests)
- [*] Test Command class (6 tests)
- [*] Test CommandRegistry (16 tests)
- [*] Test integration (2 tests)
- [*] Test convenience functions (1 test)
- [*] Total: 57 tests passing

**Additional Features Implemented:**
- ArgumentType enum with 7 types (STRING, INTEGER, FLOAT, BOOLEAN, COMPONENT_ID, VNET_ID, FILENAME)
- ArgumentSpec with validation (required, default, choices, help_text)
- OptionSpec for flags and options (short/long form, values, defaults)
- ParsedCommand dataclass for structured parsing results
- Quote handling (single and double quotes)
- Escape sequence support
- Option formats: -v, --verbose, --key=value
- Command aliases
- Automatic help text generation (brief and verbose)
- Usage string generation
- Error messages with context
- Type conversion and validation
- Case-insensitive command names

---

### 6.3 Core Commands ✅ COMPLETED
**Implementation:** `networking/simulator_commands.py` (650 lines), `networking/terminal_integration.py` (80 lines)
**Tests:** `testing/test_simulator_commands.py` (576 lines, 36 tests - 35 passing + 1 skipped)

Implemented complete command system with SimulatorContext and command handlers:

- [x] **File Commands:**
  - [x] `load <filename>` - Load .rsim file via JSON deserialization
  
- [x] **Simulation Commands:**
  - [x] `start [mode]` - Start simulation (mode: normal/fast/slow)
  - [x] `stop` - Stop simulation
  - [x] `status` - Show document/simulation/debug status
  - [x] `stats` - Display detailed simulation statistics
  
- [x] **Component Commands:**
  - [x] `list [--verbose]` - List all components
  - [x] `show <id>` - Show component details (type, position, pins, properties)
  - [x] `toggle <id>` - Toggle switch component state
  
- [x] **VNET Commands:**
  - [x] `vnets [--verbose]` - List all VNETs
  - [x] `vnet <id>` - Show VNET details (state, tabs, links, bridges)
  - [x] `dirty` - List dirty/unstable VNETs
  
- [x] **Debug Commands:**
  - [x] `debug <on|off>` - Toggle debug output mode
  - [x] `trace vnet <id>` - Enable VNET tracing
  - [x] `trace component <id>` - Enable component tracing
  
- [x] **Utility Commands:**
  - [x] `help [command]` - Show all commands or specific help
  - [x] `clear` - Clear screen (ANSI escape codes)
  - [x] Command aliases: `ls` (list), `?` (help), `cls` (clear)

**Architecture:**
- `SimulatorContext`: Shared state (document, engine, debug flags, trace sets)
- `SimulatorCommands`: Static methods for each command handler
- `register_all_commands()`: Registers all commands with ArgumentSpec/OptionSpec
- `command_callback_handler()`: Integration callback for terminal server
- `create_integrated_terminal_server()`: Factory function for integrated terminal

**Test Coverage (36 tests):**
- [x] SimulatorContext (3 tests): creation, has_document, is_simulating
- [x] File commands (2 tests): load valid/nonexistent files
- [x] Simulation commands (6 tests): start/stop/status/stats, error handling (1 skipped)
- [x] Component commands (8 tests): list/show/toggle, verbose mode, error handling
- [x] VNET commands (3 tests): list/show/dirty when not running
- [x] Debug commands (5 tests): debug on/off, trace vnet/component, invalid input
- [x] Utility commands (3 tests): help all/specific, clear screen
- [x] Command registration (2 tests): all commands registered, aliases work
- [x] Context creation (1 test): factory creates complete context
- [x] Integration (3 tests): full workflow, help system, error handling

**Notes:**
- Components don't auto-deserialize from JSON (Page.from_dict limitation) - requires component loader
- Simulation requires full VNET/tab/bridge building - integration test skipped
- All command handlers have comprehensive error handling
- Help system auto-generates from command specs

---

### 6.4 Output Formatting ✅ COMPLETED
**Implementation:** `networking/output_formatter.py` (550 lines)
**Tests:** `testing/test_output_formatter.py` (420 lines, 38 tests - all passing)

Implemented comprehensive output formatting system for terminal display:

- [x] **OutputFormatter class**
  - [x] Configurable terminal width (default: 80)
  - [x] ANSI color support (enabled/disabled)
  - [x] Unicode/ASCII box characters
  - [x] Text alignment (LEFT, RIGHT, CENTER)
  - [x] Text truncation with custom suffix
  
- [x] **Table formatting**
  - [x] Column headers with alignment
  - [x] Auto-calculated column widths
  - [x] Fixed column widths support
  - [x] Automatic width adjustment for terminal size
  - [x] Box drawing (ASCII or Unicode)
  - [x] Bold headers with ANSI codes
  
- [x] **List formatting**
  - [x] Bulleted lists (custom bullet character)
  - [x] Numbered lists (1. 2. 3...)
  - [x] Simple multi-line output
  
- [x] **Key-value formatting**
  - [x] Aligned key-value pairs
  - [x] Custom separator (default: ': ')
  - [x] Indentation support
  - [x] Color-coded keys (optional)
  
- [x] **Additional features**
  - [x] Section formatting with titles
  - [x] Word wrapping for long text
  - [x] ANSI color codes (20+ colors and styles)
  - [x] Color enable/disable toggle
  - [x] Convenience functions for component/VNET tables
  
**ANSI Color Support:**
- Text colors: Black, Red, Green, Yellow, Blue, Magenta, Cyan, White
- Bright variants: All colors have bright versions
- Text styles: Bold, Dim, Italic, Underline
- Auto-reset after colored text

**Box Drawing:**
- ASCII: +, -, | characters (universal compatibility)
- Unicode: ─, │, ┌, ┐, └, ┘, ├, ┤, ┬, ┴, ┼ (cleaner appearance)
- Configurable per formatter instance

**Test Coverage (38 tests):**
- [x] Alignment (6 tests): left/right/center, exact fit, overflow
- [x] Truncation (5 tests): long text, short text, custom suffix, edge cases
- [x] Colorization (3 tests): enabled/disabled, static method
- [x] Table formatting (7 tests): simple, alignments, widths, unicode, terminal fit
- [x] List formatting (4 tests): bulleted, numbered, custom bullet, empty
- [x] Key-value formatting (5 tests): simple, indent, separator, alignment, empty
- [x] Section formatting (2 tests): simple, colored title
- [x] Word wrap (3 tests): long text, short text, custom width
- [x] Convenience functions (2 tests): component table, VNET table
- [x] Integration (2 tests): complex output, all features combined

**Usage Examples:**
```python
formatter = OutputFormatter(terminal_width=80, use_colors=True, use_unicode=True)

# Table
table = formatter.format_table(
    headers=['ID', 'Type', 'State'],
    rows=[['SW1', 'Switch', 'ON'], ['LED1', 'Indicator', 'OFF']],
    alignments=[Alignment.LEFT, Alignment.LEFT, Alignment.CENTER]
)

# List
items = formatter.format_list(['Item 1', 'Item 2'], numbered=True)

# Key-value
details = formatter.format_key_value({'Name': 'SW1', 'Type': 'Switch'})

# Section
output = formatter.format_section("Components", table)
```

---

### 6.5 Interactive Features ✅ COMPLETED
**Implementation:** `networking/interactive_features.py` (580 lines)
**Tests:** `testing/test_interactive_features.py` (513 lines, 43 tests - all passing)

Implemented full readline-like interactive features for the terminal interface:

- [x] **Command History (CommandHistory class)**
  - [x] Up/down arrow navigation through history
  - [x] History buffer with configurable max size (default: 100)
  - [x] Automatic duplicate filtering (consecutive commands)
  - [x] Empty command filtering
  - [x] Temp command preservation during navigation
  - [x] History search functionality
  - [x] Clear and reset operations
  
- [x] **Tab Completion (TabCompleter class)**
  - [x] Command name completion
  - [x] Argument completion with custom providers
  - [x] Multiple completion candidates display
  - [x] Common prefix auto-completion
  - [x] Case-insensitive matching
  - [x] Custom completion provider registration
  
- [x] **Enhanced Prompts (PromptFormatter class)**
  - [x] Dynamic prompt templates
  - [x] Context placeholder substitution
  - [x] Multiple placeholder support
  - [x] Status information display (document, simulation state)
  
- [x] **Special Key Handling (KeyHandler class)**
  - [x] ANSI escape sequence parsing
  - [x] Arrow keys (up, down, left, right)
  - [x] Home/End keys
  - [x] Delete key
  - [x] Control characters (Ctrl+C, Ctrl+D, Ctrl+L)
  - [x] Tab key
  - [x] Backspace handling
  - [x] Escape sequence buffering and completion detection
  
- [x] **Interactive Line Editor (InteractiveLineEditor class)**
  - [x] Full line editing with cursor positioning
  - [x] Character insertion at cursor
  - [x] Backspace/Delete at cursor
  - [x] Cursor movement (arrows, Home, End)
  - [x] History integration with up/down arrows
  - [x] Tab completion integration
  - [x] Line submission and reset
  - [x] Ctrl+C to cancel current line
  - [x] Ctrl+D for EOF signal

**Key Features:**
- **Stateful Navigation:** Preserves current input when browsing history
- **Smart History:** Ignores empty commands and consecutive duplicates
- **Extensible Completion:** Custom providers for context-aware completion
- **Full ANSI Support:** Proper escape sequence handling for all special keys
- **Cursor Management:** Insert/delete at any position in line
- **Integration Ready:** Designed for easy integration with terminal server

**Test Coverage (43 tests):**
- [x] CommandHistory (10 tests): add, navigate, search, max size, duplicates
- [x] TabCompleter (8 tests): command/argument completion, providers, case-insensitive
- [x] PromptFormatter (4 tests): static/dynamic prompts, placeholders
- [x] KeyHandler (11 tests): regular chars, control chars, escape sequences, arrows
- [x] InteractiveLineEditor (8 tests): editing, navigation, history, special keys
- [x] Integration (2 tests): complete workflows, history with editing

**Usage Example:**
```python
# Create components
history = CommandHistory(max_size=100)
completer = TabCompleter()
completer.set_commands(['help', 'list', 'load', 'show', 'start'])

# Register custom completion provider
def component_id_provider(text, arg_index):
    # Return matching component IDs
    return [id for id in get_component_ids() if id.startswith(text.upper())]
completer.register_provider('show', component_id_provider)

# Create interactive editor
editor = InteractiveLineEditor(history, completer)

# Enhanced prompt
prompt_formatter = PromptFormatter("[{status}] relay> ")
prompt_formatter.set_context({'status': 'RUNNING'})

# Handle key input
key_handler = KeyHandler()
for char in input_stream:
    key_name = key_handler.process(char)
    if key_name:
        line, is_complete = editor.handle_key(key_name, char)
        if is_complete:
            command = editor.submit()
            execute_command(command)
```

**ANSI Escape Sequences Supported:**
- Arrow Up: `ESC[A`
- Arrow Down: `ESC[B`
- Arrow Left: `ESC[D`
- Arrow Right: `ESC[C`
- Home: `ESC[H`
- End: `ESC[F`
- Delete: `ESC[3~`

**Control Characters:**
- Ctrl+C (`\x03`): Cancel current line
- Ctrl+D (`\x04`): EOF/quit signal
- Ctrl+L (`\x0c`): Clear screen (external handling)
- Tab (`\t`): Trigger completion
- Backspace (`\x7f`): Delete previous char

---

## PHASE 7: FILE I/O

### 7.1 File Format Specification ✅ COMPLETED
**Implementation:** `fileio/rsim_schema.py` (390 lines), `docs/RSIM_FILE_FORMAT.md` (comprehensive spec)
**Examples:** `fileio/example_files.py` (550 lines, 5+ examples)

Implemented complete .rsim file format specification with JSON schema:

- [x] **Define .rsim format specification**
  - [x] JSON schema (structured as nested dictionaries)
  - [x] Document structure (Document → Pages → Components/Wires → Pins/Tabs)
  - [x] Version number (1.0.0 with compatibility checking)
  
- [x] **Document format documentation**
  - [x] Examples (5 complete circuits + 4 invalid examples)
  - [x] Field descriptions (all fields documented)
  - [x] Validation rules (types, ranges, references)

**Schema Components:**
- `SchemaVersion`: Version management with compatibility checking
- `FieldType`: Type enumeration (STRING, INTEGER, FLOAT, BOOLEAN, OBJECT, ARRAY, ENUM, UUID)
- `TAB_SCHEMA`: tab_id, position (x, y), state (runtime)
- `PIN_SCHEMA`: pin_id, tabs array, state (runtime)
- `COMPONENT_SCHEMA`: component_id, component_type, position, rotation, link_name, pins, properties
- `WAYPOINT_SCHEMA`: waypoint_id, position
- `JUNCTION_SCHEMA`: junction_id, position, child_wires (nested structure)
- `WIRE_SCHEMA`: wire_id, start_tab_id, end_tab_id, waypoints, junctions
- `PAGE_SCHEMA`: page_id, name, components, wires
- `DOCUMENT_SCHEMA`: version, metadata, pages

**Version Compatibility:**
- MAJOR.MINOR.PATCH format (e.g., "1.0.0")
- Major version must match (breaking changes)
- Minor version backward compatible (file ≤ app)
- Patch version always compatible (bug fixes)
- `is_compatible()` validates file can be loaded

**File Structure:**
```json
{
  "version": "1.0.0",
  "metadata": {
    "title": "Circuit Name",
    "author": "Author Name",
    "description": "Description",
    "created": "ISO 8601 datetime",
    "modified": "ISO 8601 datetime"
  },
  "pages": [...]
}
```

**Component Types Supported:**
- `ToggleSwitch`: 1 pin (4 tabs), properties: label, mode, color
- `Indicator`: 1 pin (4 tabs), properties: label, color
- `DPDTRelay`: 7 pins (coil + 2 poles × 3), properties: label, color, rotation, flip
- `VCC`: 1 pin (1 tab), no properties

**Wire Features:**
- Direct connections (tab → tab)
- Waypoints for routing (intermediate points)
- Junctions for branching (tree structure)
- Nested child wires from junctions

**Cross-Page Links:**
- `link_name` property on components
- Components with same link_name form virtual connections
- Enables multi-page circuits

**Validation Rules:**
- ID format: 8 lowercase hex characters `^[0-9a-f]{8}$`
- All IDs unique within document
- Referenced IDs must exist (start_tab_id, end_tab_id)
- Rotation: 0, 90, 180, or 270 degrees
- Version: matches `^\d+\.\d+\.\d+$` pattern
- Minimum items in arrays (pages ≥ 1, tabs ≥ 1, etc.)

**Example Files:**
1. **SIMPLE_SWITCH_LED**: Switch → LED (basic circuit)
2. **RELAY_CIRCUIT**: Switch → Relay → LED (with VCC)
3. **CROSS_PAGE_LINKS**: Multi-page with link connections
4. **WIRE_WITH_JUNCTION**: Junction branching to 3 LEDs
5. **COMPLEX_CIRCUIT**: Multiple relays, interlocking logic

**Invalid Examples (for testing):**
- INVALID_VERSION: Malformed version string
- INVALID_MISSING_REQUIRED: Missing required fields
- INVALID_ID_FORMAT: Wrong ID format
- INVALID_ROTATION: Invalid rotation value

**Documentation (RSIM_FILE_FORMAT.md):**
- Complete specification with all field definitions
- Validation rules and error handling
- Migration guide for future versions
- Common error messages and solutions
- Extensibility guidelines

**Helper Functions:**
- `get_schema_for_type(type_name)`: Get schema by type name
- `get_required_fields(schema)`: Extract required field names
- `get_default_value(field_def)`: Get default value if defined
- `SchemaVersion.is_compatible(file_version)`: Check version compatibility

---

### 7.2 Serialization Implementation ✅ COMPLETED
**Implementation:** Updated `to_dict()`/`from_dict()` methods across 6 core files
**Tests:** `testing/test_serialization.py` (654 lines, 37 tests - all passing)

Implemented schema-compliant serialization for all core classes:

- [x] **Implement Tab serialization**
  - [x] position as {x: float, y: float} object (not tuple)
  - [x] tab_id field
  - [x] Round-trip parsing from {x, y} to (x, y) tuple

- [x] **Implement Pin serialization**
  - [x] tabs as array (not dict) for schema compliance
  - [x] pin_id field
  - [x] Each tab serialized with position object

- [x] **Implement Component serialization**
  - [x] Base properties (component_id, component_type, position)
  - [x] Optional fields only when non-default (rotation, link_name, properties)
  - [x] Type-specific properties (all components inherit base serialization)
  - [x] Pin hierarchy (pins as array of pin objects)
  - [x] position as {x: float, y: float} object
  - [x] component_type field (not "type")
  
- [x] **Implement Wire serialization**
  - [x] Waypoint serialization (waypoint_id, position {x, y})
  - [x] Junction serialization (junction_id, position {x, y}, child_wires array)
  - [x] Nested wire structure (Junction → child_wires[])
  - [x] Optional fields (end_tab_id, waypoints, junctions)
  - [x] Arrays for collections (waypoints[], junctions[], child_wires[])
  
- [x] **Implement Page serialization**
  - [x] Components as array (not dict)
  - [x] Wires as array (not dict)
  - [x] Optional components/wires (not included if empty)
  - [x] page_id and name fields
  
- [x] **Implement Document serialization**
  - [x] version field (always "1.0.0")
  - [x] Version validation on load (throws ValueError for incompatible)
  - [x] Metadata optional (not included if None)
  - [x] All pages as array

**Schema Compliance Achieved:**
- Position fields: Always {x: float, y: float} objects (never tuples or [x,y])
- Collections: Arrays not dicts (tabs[], pins[], components[], wires[], waypoints[], junctions[], child_wires[], pages[])
- Optional fields: Only included when non-default values
- Field naming: component_type (not type), component_id (not id)
- Version validation: Document.from_dict() checks compatibility

**Implementation Details:**

`core/tab.py`:
- `to_dict()`: Returns `{'tab_id': str, 'position': {'x': float, 'y': float}}`
- `from_dict()`: Parses position from {x, y} object to (x, y) tuple for internal storage

`core/pin.py`:
- `to_dict()`: Returns `{'pin_id': str, 'tabs': [tab.to_dict(), ...]}`
- `from_dict()`: Parses tabs from array (not dict)

`components/base.py`:
- `to_dict()`: Returns component_type (not type), position as {x,y}, pins as array
- Optional fields only included if non-default: rotation, link_name, properties
- All component types (Switch, Indicator, DPDTRelay, VCC) inherit this

`core/wire.py` (Waypoint, Junction, Wire):
- `Waypoint.to_dict()`: position as {x, y}
- `Junction.to_dict()`: position as {x, y}, child_wires as array
- `Wire.to_dict()`: Optional end_tab_id/waypoints/junctions, all as arrays
- All `from_dict()` methods parse arrays not dicts

`core/page.py`:
- `to_dict()`: components/wires as arrays, optional (not included if empty)
- `from_dict()`: Parses wires from array, notes components require ComponentFactory

`core/document.py`:
- `to_dict()`: Includes version field (1.0.0), pages as array, metadata optional
- `from_dict()`: Validates version compatibility using SchemaVersion.is_compatible()
- Throws ValueError if file version incompatible with current version
- Parses pages from array

**Test Coverage (37 tests):**

`TestTabSerialization` (3 tests):
- to_dict format, from_dict parsing, round-trip

`TestPinSerialization` (3 tests):
- to_dict format, from_dict parsing, round-trip

`TestWaypointSerialization` (3 tests):
- to_dict format, from_dict parsing, round-trip

`TestJunctionSerialization` (4 tests):
- to_dict no children, to_dict with children, from_dict, round-trip

`TestWireSerialization` (5 tests):
- Simple wire, with waypoints, with junction, from_dict, round-trip

`TestComponentSerialization` (8 tests):
- Switch to_dict, Indicator to_dict, DPDTRelay to_dict, VCC to_dict
- Component with link_name, optional fields handling

`TestPageSerialization` (5 tests):
- Empty page, with components, with wires, from_dict, round-trip

`TestDocumentSerialization` (5 tests):
- Minimal document, with metadata, from_dict, version validation, round-trip

`TestCompleteCircuitSerialization` (3 tests):
- Switch→LED circuit, cross-page links, JSON compatibility

**Round-Trip Verified:**
All tests prove: Object → to_dict() → JSON → from_dict() → Object preserves data

**JSON Compatibility:**
Serialized data is valid JSON (tested with json.dumps()/json.loads())

**Version Validation:**
Document.from_dict() validates version compatibility and throws ValueError for incompatible versions

---

### 7.3 Deserialization Implementation
- [*] Implement document loading
  - [*] Parse file format
  - [*] Validate structure
  - [*] Handle errors
  
- [*] Implement object reconstruction
  - [*] Create components by type
  - [*] Restore properties
  - [*] Restore pins/tabs
  - [*] Restore wires
  
- [*] Implement ID validation
  - [*] Check for duplicates
  - [*] Validate hierarchy
  
- [*] Implement version compatibility
  - [*] Handle older versions
  - [*] Migration if needed

**Tests:**
- [*] Test loading valid files
- [*] Test loading invalid files
- [*] Test error handling
- [*] Test version compatibility

---

### 7.4 Example Files
- [ ] Create example .rsim files
  - [ ] Simple: Switch → LED
  - [ ] Medium: Switch → Relay → LED
  - [ ] Complex: Multiple relays
  - [ ] Cross-page: Links example
  
- [ ] Validate examples
  - [ ] Load successfully
  - [ ] Simulate correctly

---

## PHASE 8: TESTING & QUALITY

### 8.1 Unit Tests
- [ ] Write tests for all core classes
  - [ ] ID system
  - [ ] Pin/Tab
  - [ ] Component base
  - [ ] VNET
  - [ ] Bridge
  
- [ ] Write tests for algorithms
  - [ ] VNET builder
  - [ ] Link resolver
  - [ ] State evaluator
  - [ ] State propagator
  
- [ ] Write tests for components
  - [ ] Toggle switch
  - [ ] Indicator
  - [ ] DPDT relay
  
- [ ] Achieve >80% code coverage

---

### 8.2 Integration Tests
- [ ] Test complete simulation
  - [ ] Load file
  - [ ] Build VNETs
  - [ ] Run simulation
  - [ ] Verify results
  
- [ ] Test example circuits
  - [ ] Switch → LED
  - [ ] Switch → Relay → LED
  - [ ] Complex circuits
  
- [ ] Test edge cases
  - [ ] Disconnected components
  - [ ] Oscillating circuits
  - [ ] Large circuits (100+ components)
  
- [ ] Test thread safety
  - [ ] Concurrent access
  - [ ] Race conditions
  - [ ] Deadlock prevention

---

### 8.3 Performance Testing
- [ ] Benchmark scenarios
  - [ ] 10 components
  - [ ] 100 components
  - [ ] 1000 components
  
- [ ] Measure metrics
  - [ ] Time to stability
  - [ ] Iterations per second
  - [ ] Memory usage
  - [ ] Thread utilization
  
- [ ] Compare single vs multi-threaded
- [ ] Identify bottlenecks
- [ ] Optimize as needed

---

### 8.4 Bug Fixing
- [ ] Track bugs in issue tracker
- [ ] Prioritize by severity
- [ ] Fix critical bugs first
- [ ] Write tests for bug fixes
- [ ] Regression testing

---

## PHASE 9: DOCUMENTATION

### 9.1 Code Documentation
- [ ] Add inline comments
  - [ ] Complex algorithms
  - [ ] Non-obvious code
  
- [ ] Add API documentation
  - [ ] Class descriptions
  - [ ] Method descriptions
  - [ ] Parameter descriptions
  - [ ] Return value descriptions
  
- [ ] Generate API docs
  - [ ] Use documentation tool (Doxygen, Javadoc, etc.)

---

### 9.2 User Documentation
- [ ] Write user guide
  - [ ] Getting started
  - [ ] Terminal commands
  - [ ] Creating circuits
  - [ ] Component reference
  
- [ ] Write examples/tutorials
  - [ ] Basic circuit
  - [ ] Relay circuit
  - [ ] Cross-page links
  
- [ ] Document file format
  - [ ] .rsim structure
  - [ ] Schema reference
  - [ ] Examples

---

### 9.3 Developer Documentation
- [ ] Architecture overview
- [ ] Component development guide
- [ ] Build instructions
- [ ] Testing guide
- [ ] Contributing guidelines

---

## PHASE 10: FUTURE ENHANCEMENTS (Post-MVP)

### 10.1 Additional Components
- [ ] SPDT Relay (Single Pole)
- [ ] Push Button (momentary)
- [ ] Timer
- [ ] Counter
- [ ] Logic Gates (AND, OR, NOT)
- [ ] Custom components

---

### 10.2 Advanced Features
- [ ] State persistence (save runtime state)
- [ ] Breakpoints/stepping
- [ ] Signal tracing/waveforms
- [ ] Performance profiling
- [ ] Remote API (REST/WebSocket)
- [ ] Scripting support

---

### 10.3 Front-End Application
- [ ] Schematic designer
- [ ] Component library
- [ ] Wire routing tools
- [ ] Real-time visualization
- [ ] Interactive debugging
- [ ] Multiple document tabs

---

## MILESTONES & DELIVERABLES

### Milestone 1: Foundation Complete (End of Phase 1)
- Core classes implemented
- Basic serialization working
- Unit tests passing

### Milestone 2: Wiring & VNETs Complete (End of Phase 2)
- VNET builder working
- Links and bridges functional
- Wire structures complete

### Milestone 3: Components Complete (End of Phase 3)
- All 3 initial components working
- Component logic tested
- Bridge management functional

### Milestone 4: Simulation Engine Complete (End of Phase 4)
- Main loop working
- Stability detection working
- Oscillation detection working
- Simple circuits simulating correctly

### Milestone 5: Multi-threading Complete (End of Phase 5)
- Thread pool working
- Performance improved
- Thread-safety verified
- Large circuits (100+) working

### Milestone 6: Terminal Interface Complete (End of Phase 6)
- Telnet server working
- All commands implemented
- Help system complete
- User can control simulator remotely

### Milestone 7: File I/O Complete (End of Phase 7)
- .rsim format defined
- Save/load working
- Example files created
- Validation working

---

## PHASE 8: GRAPHICAL USER INTERFACE

### 8.1 Application Window and Theme ✓ COMPLETE
**Status**: COMPLETE - 20 tests passing

**Objective**: Create the main application window with dark VS Code-style theme.

- [x] **Create gui/ module structure**
  - [x] gui/__init__.py
  - [x] Module organization

- [x] **Implement gui/theme.py**
  - [x] VS Code color palette (background, foreground, accent colors)
  - [x] Font definitions (sizes for UI elements, canvas labels)
  - [x] Padding and spacing constants
  - [x] ttk.Style configuration for widgets
  - [x] Color constants: BG_PRIMARY, BG_SECONDARY, BG_TERTIARY
  - [x] Accent colors: ACCENT_BLUE, ACCENT_GREEN, ACCENT_ORANGE, ACCENT_RED
  - [x] Canvas colors: CANVAS_BG, CANVAS_GRID
  - [x] Component colors: COMPONENT_FILL, WIRE_POWERED, WIRE_UNPOWERED
  - [x] Font sizes: SMALL (9), NORMAL (10), MEDIUM (11), LARGE (12)
  - [x] Widget sizes: TOOLBAR_HEIGHT, STATUSBAR_HEIGHT, TOOLBOX_WIDTH
  
- [x] **Implement gui/main_window.py**
  - [x] MainWindow class with tkinter.Tk root
  - [x] Window title: "Relay Simulator III"
  - [x] Default size: 1280x720
  - [x] Theme application on startup
  - [x] Menu bar placeholder
  - [x] Status bar with message display
  - [x] Content frame for future components
  - [x] Unsaved changes tracking
  - [x] Window close handler with confirmation
  - [x] Ctrl+Q keyboard shortcut to quit

- [x] **Create application entry point**
  - [x] app.py file for launching GUI
  - [x] main() function
  - [x] Proper module imports

- [x] **Create tests for Phase 8.1**
  - [x] testing/test_gui_window.py (20 tests)
  - [x] TestVSCodeTheme: 10 tests (color constants, fonts, spacing)
  - [x] TestMainWindow: 8 tests (window creation, title, size, status)
  - [x] TestThemeApplication: 2 tests (theme applied correctly)

**Implementation Files**:
- `gui/__init__.py`: Module initialization
- `gui/theme.py`: VSCodeTheme class with color palette and styling (250 lines)
- `gui/main_window.py`: MainWindow class (180 lines)
- `app.py`: Application entry point
- `testing/test_gui_window.py`: 20 tests

**Test Results**: All 20 tests passing
- Theme constants validated
- Font system working
- Window creation successful
- Theme application verified
- Status bar functional
- Unsaved changes tracking working

**Features Delivered**:
- Professional dark theme matching VS Code
- Properly centered window (1280x720)
- Status bar with message display
- Unsaved changes indication in title (*)
- Keyboard shortcut support (Ctrl+Q)
- Proper window close handling
- Foundation for future GUI components

---

### 8.2 Menu System ✓ COMPLETE
**Status**: COMPLETE - 35 tests passing

**Objective**: Implement complete menu bar with all specified menus and keyboard shortcuts.

- [x] **Implement gui/menu_bar.py**
  - [x] MenuBar class managing all menus
  - [x] Recent documents tracking (max 10, no duplicates)
  - [x] Callback system for menu actions
  - [x] Menu state management (enable/disable items)
  
- [x] **File Menu**
  - [x] New (Ctrl+N)
  - [x] Open (Ctrl+O)
  - [x] Save (Ctrl+S)
  - [x] Save As (Ctrl+Shift+S)
  - [x] Settings
  - [x] Recent Documents (submenu, dynamic)
  - [x] Clear Recent Documents
  - [x] Exit (Ctrl+Q)
  
- [x] **Edit Menu**
  - [x] Select All (Ctrl+A)
  - [x] Cut (Ctrl+X)
  - [x] Copy (Ctrl+C)
  - [x] Paste (Ctrl+V)
  - [x] State management (Cut/Copy disabled when no selection)
  
- [x] **Simulation Menu**
  - [x] Start Simulation (F5)
  - [x] Stop Simulation (Shift+F5)
  - [x] State management (Start/Stop toggle based on running state)
  
- [x] **View Menu**
  - [x] Zoom In (Ctrl++)
  - [x] Zoom Out (Ctrl+-)
  - [x] Reset Zoom (Ctrl+0)
  
- [x] **Keyboard Shortcuts**
  - [x] All shortcuts bound to root window
  - [x] Case-insensitive (Ctrl+N and Ctrl+n both work)
  - [x] Ctrl+= also triggers zoom in (same key as +)
  
- [x] **Menu Item State Management**
  - [x] enable_edit_menu(has_selection) - enables/disables Cut/Copy
  - [x] enable_simulation_controls(is_running) - toggles Start/Stop
  - [x] set_menu_state(menu, item, enabled) - general state setter
  
- [x] **Integration with MainWindow**
  - [x] Menu bar created before window components
  - [x] All callbacks connected to MainWindow methods
  - [x] Status bar updates when menu items triggered
  - [x] Placeholder implementations (marked with TODO for future phases)
  
- [x] **Create tests for Phase 8.2**
  - [x] testing/test_gui_menu.py (35 tests)
  - [x] TestMenuBar: 17 tests (menu creation, callbacks, recent docs, state management)
  - [x] TestMenuBarIntegration: 7 tests (MainWindow integration, status updates)
  - [x] TestKeyboardShortcuts: 11 tests (all keyboard bindings verified)

**Implementation Files**:
- `gui/menu_bar.py`: MenuBar class with all menus (450 lines)
- `gui/main_window.py`: Updated with menu integration and callbacks (320 lines)
- `testing/test_gui_menu.py`: 35 comprehensive tests (330 lines)

**Test Results**: All 35 tests passing
- Menu bar creation verified
- All menus present (File, Edit, Simulation, View)
- Recent documents list management working
- Callbacks execute correctly
- Menu state management functional
- Edit menu enables/disables based on selection
- Simulation menu toggles Start/Stop correctly
- All keyboard shortcuts bound
- MainWindow integration complete

**Features Delivered**:
- Complete menu system with all specified menus
- 15 menu commands with keyboard shortcuts
- Recent documents submenu (max 10, dynamic)
- Menu state management (enable/disable items)
- Status bar updates on menu actions
- Professional menu organization
- All shortcuts work (Ctrl+N, Ctrl+S, F5, etc.)
- Placeholder implementations for future phases

**Keyboard Shortcuts Working**:
- File: Ctrl+N, Ctrl+O, Ctrl+S, Ctrl+Shift+S, Ctrl+Q
- Edit: Ctrl+A, Ctrl+X, Ctrl+C, Ctrl+V
- Simulation: F5, Shift+F5
- View: Ctrl++, Ctrl+-, Ctrl+0

---

### 8.3 Settings System ✓ COMPLETE
**Status**: COMPLETE - 24 tests passing

**Objective**: Implement persistent settings storage and settings dialog.

- [x] **Implement gui/settings.py**
  - [x] Settings class with JSON file storage (~/.relay_simulator/settings.json)
  - [x] Default settings:
    - recent_documents: [] (max 10)
    - simulation_threading: "single" (options: "single", "multi")
    - default_canvas_width: 3000
    - default_canvas_height: 3000
    - canvas_grid_size: 20
    - canvas_snap_size: 10
  - [x] load() / save() methods with error handling
  - [x] get() / set() generic methods
  - [x] Helper methods:
    - get_recent_documents() / add_recent_document() / remove_recent_document() / clear_recent_documents()
    - get_simulation_threading() / set_simulation_threading()
    - get_canvas_size() / set_canvas_size()
    - get_grid_size() / set_grid_size()
    - get_snap_size() / set_snap_size()
    - reset_to_defaults()
  - [x] Input validation (positive values for sizes, valid threading mode)
  
- [x] **Implement gui/settings_dialog.py**
  - [x] SettingsDialog class (modal dialog)
  - [x] Professional VS Code-styled UI
  - [x] Form fields:
    - Simulation Threading (radio buttons: Single/Multi)
    - Canvas Size (width/height spinboxes)
    - Grid Size (spinbox)
    - Snap Size (spinbox)
  - [x] Buttons:
    - OK (saves and closes)
    - Cancel (discards changes)
    - Reset to Defaults (restores default values)
  - [x] Input validation with error messages
  - [x] show() method returns True if saved, False if cancelled
  
- [x] **Integration with MainWindow**
  - [x] Settings instance created on startup
  - [x] Settings menu callback connected
  - [x] Recent documents synced from settings to menu on startup
  - [x] Recent documents saved to settings when added
  - [x] Status bar updates on settings save/cancel
  
- [x] **Create tests for Phase 8.3**
  - [x] testing/test_gui_settings.py (24 tests)
  - [x] TestSettings: 17 tests (defaults, get/set, save/load, recent docs, validation)
  - [x] TestSettingsDialog: 4 tests (creation, initialization, reset, cancel)
  - [x] TestMainWindowSettingsIntegration: 3 tests (settings instance, menu sync, callback)

**Implementation Files**:
- `gui/settings.py`: Settings class with JSON persistence (260 lines)
- `gui/settings_dialog.py`: SettingsDialog with professional UI (320 lines)
- `gui/main_window.py`: Updated with settings integration (300 lines)
- `testing/test_gui_settings.py`: 24 comprehensive tests (300 lines)

**Test Results**: All 24 tests passing
- Default settings initialized correctly
- Get/set methods working
- Save/load persistence verified
- Recent documents management (add, remove, clear, limit, no duplicates)
- Validation working (positive sizes, valid threading modes)
- Dialog creation and initialization
- Reset to defaults functional
- Cancel doesn't save changes
- MainWindow integration complete

**Features Delivered**:
- Persistent settings storage in user's home directory
- Professional settings dialog with VS Code styling
- All settings editable via GUI
- Input validation with error messages
- Recent documents automatically tracked
- Settings survive application restarts
- Reset to defaults button
- Cancel discards changes
- Proper error handling for corrupted settings files

**Settings Dialog Features**:
- Centered on parent window
- Modal (blocks main window)
- Dark theme matching application
- Organized sections (Threading, Canvas, Grid/Snap)
- Spinboxes for numeric inputs
- Radio buttons for threading mode
- Visual separators between sections
- Three-button layout (Reset, Cancel, OK)

---

## PHASE 9: FILE AND DOCUMENT MANAGEMENT

### 9.1 File Tab System
- [ ] Implement gui/file_tabs.py
- [ ] FileTabBar class (notebook-style tabs)
- [ ] Multiple documents support
- [ ] Tab switching (blocked during simulation)
- [ ] Tab close confirmation (if unsaved)
- [ ] New document creates "Untitled-N" tab

### Milestone 8: MVP Complete (End of Phase 8)
- All tests passing
- Performance acceptable
- Known bugs fixed
- Basic documentation complete

### Milestone 9: Release Ready (End of Phase 9)
- Full documentation
- Examples and tutorials
- Clean, maintainable code
- Ready for front-end development

---

## ESTIMATED TIMELINE (Single Developer)

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 0: Setup | 1 week | None |
| Phase 1: Foundation | 2 weeks | Phase 0 |
| Phase 2: Wire/VNET | 2 weeks | Phase 1 |
| Phase 3: Components | 2 weeks | Phase 1, 2 |
| Phase 4: Sim Engine | 2 weeks | Phase 1, 2, 3 |
| Phase 5: Threading | 1 week | Phase 4 |
| Phase 6: Terminal | 2 weeks | Phase 4 |
| Phase 7: File I/O | 1 week | Phase 1 |
| Phase 8: Testing | 2 weeks | All previous |
| Phase 9: Documentation | 1 week | All previous |
| **Total** | **16 weeks** (4 months) | |

Note: This is an aggressive timeline. More realistic estimate: **6-9 months** with buffer for unforeseen issues, learning, and iteration.

---

## RISK FACTORS

### High Risk
- Multi-threading complexity and bugs
- Oscillation handling
- Bridge system complexity
- Performance with large circuits

### Medium Risk
- VNET builder algorithm correctness
- File format changes during development
- Component interaction complexity
- Terminal protocol issues

### Low Risk
- Basic classes and structures
- Serialization
- Simple components
- Documentation

---

## SUCCESS METRICS

### MVP Success
- ✅ All 3 components working correctly
- ✅ Simple circuits simulate correctly
- ✅ Stability achieved in <1 second
- ✅ 100 components handled efficiently
- ✅ Terminal interface fully functional
- ✅ Load/save .rsim files
- ✅ No critical bugs

### Quality Success
- ✅ >80% test coverage
- ✅ No memory leaks
- ✅ No race conditions/deadlocks
- ✅ Clean, maintainable code
- ✅ Comprehensive documentation

### Performance Success
- ✅ 100 component circuit: <100ms to stability
- ✅ 1000 component circuit: <1s to stability
- ✅ Multi-threaded 2-5x faster than single-threaded
- ✅ Memory usage <100MB for typical circuits

---

*End of Project Plan*
