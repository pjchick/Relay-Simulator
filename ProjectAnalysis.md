# Relay Logic Simulator - Project Analysis & Notes

## Executive Summary
Building a multi-threaded relay logic simulator with a focus on the simulation engine first, followed by a front-end designer later. The engine will be controlled via a telnet/terminal interface for development and debugging.

---

## 1. CORE ARCHITECTURE DECISIONS

### 1.1 Technology Stack (TO BE DECIDED)
- **Language**: Python. Eventually I will have a tkInter front end.
- **Threading Model**: With 100's of components to be processed I suggest that we allocate an initial 4 threads to the component logic and maybe 2 threads to the vnet engine. The faster we van process VNETS and components the better. Multi threading should massively help performance.
- **File Format**: .json based with .rsim extension.
- **Interface**: Telnet/Terminal server for remote control. I will also enventially have other apps (like a simulated logic analyser connected to the Engine. So we need a robust mechanism to allow the designer and the engine to interact bit share common code and classes for the component re-draws as an example. WE may need to dicuss this further.)
- **Components**: Plugin/modular architecture for component classes. Components will be self contained in their own python class files. NO Component code should be in the main engine. All components will be kept in a subfolder called .\components. Ideally these will be dynamically loaded on startup.

### 1.2 Initial Scope
- **Components**: 
  - Toggle Switch
  - Indicator (LED)
  - DPDT Relay (Double Pole Double Throw)
  - VCC Power

### 1.3 Performance Requirements
- Must handle 100s of components efficiently
- Multi-threaded VNET processing
- Multi-threaded Component processing
- Dirty-flag optimization for stable circuits

---

## 2. ID SYSTEM & HIERARCHY

### 2.1 ID Generation
- **Format**: First 8 characters of UUID
- **Uniqueness**: Global across entire document
- **Hierarchical**: Dot-separated (PageId.ComponentId.PinId.TabId)

### 2.2 Copy/Paste Behavior
| Operation | Same Page | Different Page |
|-----------|-----------|----------------|
| COPY | Generate all new IDs | Generate all new IDs |
| CUT | Keep all IDs | Keep all except PageId |

### 2.3 Implementation Notes
- Need UUID generation library
- Need ID validation on document load
- Need ID regeneration utilities for copy/paste
- Consider ID lookup tables for performance. We can Hash the ID's when loading the file into the simulator engine and just refer to the hashes internally. Need to discuss other approaches.

---

## 3. ELECTRICAL MODEL

### 3.1 Signal States (Not HIGH/LOW, but HIGH/FLOAT)
- **FLOAT**: No signal (default state)
- **HIGH**: Active signal
- **Logic**: HIGH OR FLOAT = HIGH (HIGH always wins)
- **Bidirectional**: All pins and tabs are bidirectional

### 3.2 Pin-Tab Relationship
```
Component
  └─ Pin (logical electrical connection)
      ├─ Tab (physical connection point at 12 o'clock)
      ├─ Tab (physical connection point at 3 o'clock)
      ├─ Tab (physical connection point at 6 o'clock)
      └─ Tab (physical connection point at 9 o'clock)
```

**Key Rules**:
- Multiple tabs per pin (e.g., Indicator has 1 pin, 4 tabs)
- Any tab goes HIGH → All tabs HIGH → Pin HIGH
- Pin goes HIGH → All tabs HIGH
- State is read from PIN, not individual tabs

### 3.3 Implementation Considerations
- Need Pin class with tab collection
- Need state propagation logic (tab→pin, pin→tab)
- Need position data for each tab on component

---

## 4. WIRING SYSTEM

### 4.1 Wire Structure
```
Wire
  ├─ TabId (start point)
  ├─ Waypoint (visual only, no electrical effect)
  ├─ Waypoint (visual only)
  ├─ Junction
  │   ├─ Wire → Waypoint → TabId (branch 1)
  │   └─ Wire → Waypoint → TabId (branch 2)
  └─ TabId (end point)
```

### 4.2 Junctions
- Connect multiple wires electrically
- Create branching points
- Nested wire structure for hierarchical representation

### 4.3 Implementation Notes
- Wire class needs hierarchical structure
- Waypoints only for visual routing (front-end concern)
- Junction class links multiple wires
- Consider wire deletion/modification algorithms

---

## 5. VNET (VIRTUAL NETWORK) SYSTEM

### 5.1 Purpose
Convert complex wire/junction structures into simplified electrical networks for simulation.

### 5.2 VNET Contents
```
VnetId
  ├─ TabId (Component_A.Pin.Tab)
  ├─ TabId (Component_B.Pin.Tab)
  ├─ TabId (Component_C.Pin.Tab)
  ├─ Link ("LinkName") - optional
  └─ Bridge (bridgeId) - runtime only
```

### 5.3 VNET Building Rules
- **Scope**: Single page only (use PageId to determine boundaries)
- **Process**: Trace all wires/junctions, collect connected tabs
- **Links**: Cross-page connections by name
- **Bridges**: Runtime dynamic connections (relays)

### 5.4 VNET State Processing
1. Check if VNET is marked "Dirty"
2. If dirty, evaluate all connected tabs
3. Apply HIGH OR FLOAT logic
4. Update VNET state
5. Propagate state to all tabs in VNET
6. Trigger component logic updates (async via thread pool)
7. Clear dirty flag

### 5.5 Dirty Flag System
**VNET marked dirty when**:
- Component changes pin state differently from current VNET state
- Link connected to VNET changes state
- Bridge added/removed from VNET

**Stability**:
- Simulation stable when NO dirty VNETs exist
- Only then can front-end redraw
- Front-end blocked during unstable periods

### 5.6 Implementation Considerations
- VNET builder algorithm (graph traversal)
- Efficient dirty flag tracking
- VNET state evaluation engine
- State propagation system
- Stability detection
- Thread-safe VNET access

---

## 6. LINKS SYSTEM

### 6.1 Purpose
Virtual wires connecting VNETs across pages without physical wire representation.

### 6.2 Characteristics
- **Name-based**: Components have "Link Name" property
- **Cross-page**: Can connect different pages
- **Same-page**: Can also work on same page
- **Virtual**: No wire visualization needed

### 6.3 Link in VNET
```
VnetId
  ├─ TabId (Component_A)
  ├─ TabId (Component_B)
  └─ Link("TestLink")

VnetId (different page)
  ├─ TabId (Component_X)
  └─ Link("TestLink")
```

### 6.4 Implementation Notes
- Link registry (name → list of VNETs)
- Link state synchronization across VNETs
- Component property: LinkName (optional)

---

## 7. BRIDGE SYSTEM

### 7.1 Purpose
Dynamic runtime connections within components (e.g., relay contacts).

### 7.2 Characteristics
- **Runtime only**: Created at SimStart, NOT saved to .rsim file
- **Dynamic**: Can be added/removed during simulation
- **Component-controlled**: Components manage their own bridges

### 7.3 Example: DPDT Relay
**Relay not energized (NC connected)**:
```
COM.Vnet
  ├─ Tabs...
  └─ BRIDGE(bridge_id)

NC.Vnet
  ├─ Tabs...
  └─ BRIDGE(bridge_id)

NO.Vnet
  └─ Tabs... (no bridge)
```

**Relay energized (NO connected)**:
```
COM.Vnet
  ├─ Tabs...
  └─ BRIDGE(bridge_id)

NC.Vnet
  └─ Tabs... (bridge removed)

NO.Vnet
  ├─ Tabs...
  └─ BRIDGE(bridge_id) (bridge moved here)
```

### 7.4 Bridge Operations
- Add bridge between two VNETs
- Remove bridge from VNETs
- Mark both VNETs dirty after modification
- Thread-safe bridge modifications

### 7.5 Implementation Notes
- Bridge ID allocation system (runtime)
- Bridge registry (bridgeId → [VnetId1, VnetId2])
- Bridge add/remove API for components
- VNET dirty marking on bridge changes

---

## 8. COMPONENT ARCHITECTURE

### 8.1 Component Class Requirements
**Each component must implement**:

#### 8.1.1 Component Logic
- Read current state of all component PINs
- Calculate new state based on component behavior
- Update PIN states
- Mark VNETs as dirty if state changed

#### 8.1.2 Update Code (Front-end)
- Redraw component based on internal state
- Only needed if component on visible page
- Defer to phase 2 (front-end development)

#### 8.1.3 Interaction Code
- Handle user interactions (button press, switch toggle)
- Can be triggered from canvas OR API/terminal
- Update PIN states accordingly
- Remote control capability

#### 8.1.4 SimStart
- Initialize component to default state
- Create any necessary BRIDGEs

  At Sim start the component must be able to read what VNETS are connected to it's TABS / PINS.

- Set up initial PIN states

#### 8.1.5 SimStop
- Clear internal state
- Clean up resources
- Remove bridges (handled by engine?) Bridge removal shoud be handled by the engine.

### 8.2 Component Properties
- Position (X, Y coordinates)

We will be eventuially using a tkInter front end with a canvas size of 3000x3000px per page (This may change at a later date).

- Rotation/orientation (if applicable). Only Some components will need to be flipped or rotated, not all.
- LinkName (optional, for cross-page connections)
- Component-specific properties
- All properties must be copyable

All proerties must be saved to the .rsim file.

### 8.3 Component Isolation
- Component-specific code in separate class files
- NO component logic in main application
- Plugin/modular architecture
- Component base class or interface

### 8.4 Initial Components to Implement

#### Toggle Switch
- 1 Pin with four tabs. at 3.6.9 and 12 o'clock positions,
- Circular design.
- The swit has it's own Internal Power
- States: ON (HIGH), OFF (FLOAT)
- Interaction: Toggle between states
- SimStart: Default to OFF

#### Indicator (LED)
- 1 pin, 4 tabs (12, 3, 6, 9 o'clock positions)
- Visual state: ON when pin is HIGH
- No interaction (passive component)
- SimStart: FLOAT (off)

#### DPDT Relay
- Need to clarify: 
  - Coil: 1 pin. Ground not required.
  - Contacts: 2 poles × 3 positions (COM, NO, NC) = 6 pins
- States: Energized, De-energized
- SimStart: Create bridges COM→NC for both poles
- Logic: When coil HIGH, move bridges COM→NO
- Coil will respond to HIGH or FLOAT
- Coil will have a delay time of 20ms (user adjustable). When the coil is set HIGH this will start a timer for that instance of relay. So on the first processing loop the relay will not change it's state. Once the timer completes then the Change over logic will run. In real life a relay does not change over instantly. The contacts will normally take a number of milli seconds to change over. This must be modelled.

#### VCC
Simple power component single pin, single tag.
Used to connect permanent VCC supply (HIGH) to a circuit.
Only High on SIM Start.

---

## 9. TERMINAL/TELNET INTERFACE

### 9.1 Requirements
- Standard telnet protocol
- Terminal-based control and debugging
- Enabled by default during development
- Command-line interface for simulator

### 9.2 Commands Needed (To Be Defined)
- Load .rsim file
- Start/stop simulation
- List components
- Get component state
- Set component state (toggle switch, etc.)
- Get VNET information
- List dirty VNETs
- Show simulation statistics
- Debug commands

### 9.3 Implementation Considerations
- TCP socket server
- Command parser
- Help system
- Command history? Would be a nice feature.
- Output formatting
- Multi-client support Yes.

---

## 10. MULTI-THREADING ARCHITECTURE

### 10.1 Thread Pool Model
- **VNET Processing Thread Pool**: Process dirty VNETs
- **Component Logic Thread Pool**: Execute component logic updates

### 10.2 Concurrency Concerns
- VNET state access (read/write locks?)
- Dirty flag modifications (atomic operations?)
- Bridge add/remove operations (locks)
- Component state updates (thread-safe)
- Link state synchronization

### 10.3 Processing Flow
```
Main Loop (single thread):
  └─ Iterate all VNETs
      └─ If VNET dirty:
          ├─ Evaluate VNET state
          └─ Queue component updates to thread pool

Component Thread Pool:
  └─ Execute component logic
      └─ May mark VNETs dirty
          └─ Triggers next main loop iteration

Loop until stable (no dirty VNETs)
```

### 10.4 Implementation Considerations
- Choose threading library
- Thread pool sizing
- Work queue management
- Deadlock prevention
- Performance monitoring

---

## 11. FILE FORMAT (.rsim)

### 11.1 Structure
- Multiple pages per document
- Hierarchical storage matching ID structure
- Must preserve all component properties
- Must preserve wire routing (waypoints, junctions)

### 11.2 What NOT to Store
- VNETs (rebuilt at simulation start)
- Bridges (created at SimStart)
- Runtime state (unless "save state" feature added) Save State not required.

### 11.3 What TO Store
```
Document
  ├─ Metadata (version, author, etc.)
  ├─ Page
  │   ├─ PageId
  │   ├─ Components
  │   │   └─ Component
  │   │       ├─ ComponentId
  │   │       ├─ Type (ToggleSwitch, Indicator, Relay)
  │   │       ├─ Position (X, Y)
  │   │       ├─ Properties
  │   │       └─ Pins
  │   │           └─ Pin
  │   │               ├─ PinId
  │   │               └─ Tabs
  │   │                   └─ Tab
  │   │                       ├─ TabId
  │   │                       └─ Position (relative to component)
  │   └─ Wires
  │       └─ Wire
  │           ├─ WireId
  │           ├─ StartTabId
  │           ├─ Waypoints
  │           ├─ Junctions
  │           └─ EndTabId
  └─ Page
      └─ ...
```

### 11.4 Format Choice
- **JSON**: Modern, less verbose, easy to parse


---

## 12. SIMULATION LIFECYCLE

### 12.1 Initialization
1. Load .rsim file
2. Parse document structure
3. Create component instances
4. Build VNET structures (per page) - VNET Should only be created in SIM START and rebuilt every time.
5. Process Links (cross-page VNETs)
6. Call SimStart on all components
7. Mark all VNETs dirty
8. Initial stabilization

### 12.2 Running Simulation
```
While simulation running:
  For each VNET:
    If dirty:
      Evaluate VNET state
      Propagate to all tabs
      Queue component logic updates (async)
  
  Wait for component processing to complete
  
  If no dirty VNETs:
    Mark simulation stable
    Signal front-end for redraw
  
  Handle user interactions
  Handle API commands
```

### 12.3 Shutdown
1. Call SimStop on all components
2. Clear VNETs
3. Clear bridges
4. Save state? Not Required.

---

## 13. KEY ALGORITHMS NEEDED

### 13.1 VNET Builder
- **Input**: Page with components, wires, junctions
- **Process**: 
  - Start from each tab
  - Traverse wires and junctions
  - Collect all connected tabs
  - Create VNET with collected tabs
  - Handle already-processed tabs (skip)
- **Output**: Set of VNETs for page

### 13.2 Link Resolver
- **Input**: All VNETs, component link names
- **Process**:
  - Build link name → VNETs mapping
  - Connect VNETs with same link name
- **Output**: Updated VNETs with link references

### 13.3 VNET State Evaluator
- **Input**: VNET with multiple tabs
- **Process**:
  - Read each tab state
  - Apply HIGH OR FLOAT logic
  - Determine VNET state
- **Output**: VNET state (HIGH or FLOAT)

### 13.4 State Propagation
- **Input**: VNET with new state
- **Process**:
  - Update all tabs in VNET to new state
  - Update pins associated with tabs
- **Output**: Updated component pin states

### 13.5 Dirty Detection
- **Input**: Component wants to change pin state
- **Process**:
  - Compare new state with current VNET state
  - If different, mark VNET dirty
- **Output**: Dirty flag set or not

### 13.6 Stability Detection
- **Input**: All VNETs
- **Process**: Check if any VNET is dirty
- **Output**: Boolean (stable or not)

---

## 14. TESTING STRATEGY

### 14.1 Unit Tests Needed
- ID generation and uniqueness
- Pin-Tab state propagation
- VNET state evaluation (HIGH OR FLOAT logic)
- VNET builder algorithm
- Link resolution
- Bridge add/remove
- Each component logic
- Copy/paste ID generation

### 14.2 Integration Tests Needed
- Load .rsim file
- Build VNETs from complex wire structures
- Simulation stability convergence
- Multi-threaded safety
- Terminal command processing

### 14.3 Test Circuits
- Simple: Switch → LED
- Medium: Switch → Relay → LED
- Complex: Multiple relays with feedback loops
- Cross-page: Components with links
- Performance: 100+ components

---

## 15. POTENTIAL CHALLENGES

### 15.1 Technical Challenges
1. **Oscillation**: Circuit designs that never stabilize
   - Need oscillation detection - Agreed!
   - Need iteration limit or timeout - Add iteration limit (user adjustable)
   
2. **Race Conditions**: Multi-threaded access to VNETs
   - Need proper locking strategy
   - Need atomic operations
   
3. **Performance**: 100s of components, continuous evaluation
   - Dirty flag optimization crucial
   - Thread pool tuning important
   
4. **Bridge Management**: Dynamic VNET connections
   - Complex state management
   - Thread-safety critical

5. **VNET Merging**: When bridges connect VNETs
   - Do we merge VNETs or just connect them? WE connect them only as we might have to disconnect them later.
   - Performance implications

### 15.2 Design Decisions Needed
1. **Programming Language**: Python
2. **File Format**: JSON
3. **Threading Library**: Platform-specific or cross-platform Ideally cross platform but Windows platform specific if that's not possible.
4. **Component Count**: Is 4 components correct I have added the missing component VCC Power.
5. **Relay Details**: Exact pin configuration for DPDT
6. **Oscillation Handling**: Max iterations - 50 for now? Watchdog timer to terminate sim if no processing loop has completed after 10 seconds?
7. **State Persistence**: Save simulation state in .rsim. No do not save state.
8. **Multi-client**: Allow multiple telnet connections Ideally Yes.

### 15.3 Clarifications Needed
- DPDT Relay pin/tab configuration COIL, COM1, NC1, NC2, COM2, NC2, NO2
- Initial component states on load All relays to start with the coil off and COM connected to NC
- Oscillation detection strategy. count how many times the same vnet has been dirty in each processing cycle. If it's over 50 chances are it's oscillating.
- Performance targets (updates per second?) the designer refresh will be dependent on the engine cycle performance as the designer will only be able to update at the end of every sim cycle when all 'dirty' nets are resolved.

- Error handling for invalid circuits. If a user wires somthing incorrectly don't worry. If the engine has issues compiling VNETS or processing then we need to know.

---

## 16. DEVELOPMENT PHASES

### Phase 1: Core Engine Foundation
- ID system implementation
- Pin/Tab classes
- Component base class
- VNET basic structure
- File format definition

### Phase 2: VNET Builder
- Wire/Junction parsing
- VNET construction algorithm
- Link resolution
- Bridge system

### Phase 3: Component Implementation
- Toggle Switch
- Indicator (LED)
- DPDT Relay
- Component logic implementation

### Phase 4: Simulation Engine
- VNET state evaluator
- Dirty flag system
- Stability detection
- Main simulation loop

### Phase 5: Multi-threading
- Thread pool setup
- Concurrent VNET processing
- Component logic threading
- Thread safety

### Phase 6: Terminal Interface
- Telnet server
- Command parser
- Debug commands
- Status reporting

### Phase 7: Testing & Optimization
- Unit tests
- Integration tests
- Performance tuning
- Bug fixes

### Phase 8: Documentation
- API documentation
- User guide
- Circuit examples
- .rsim format specification

---

## 17. OPEN QUESTIONS

1.  Do we need a scripting interface for automated testing? YES

---

## 18. ESTIMATED COMPLEXITY

### Core Components (by complexity)
1. **ID System**: Low
2. **Pin/Tab**: Low-Medium
3. **Wire/Junction**: Medium
4. **VNET Builder**: High (graph algorithm)
5. **VNET State Engine**: Medium
6. **Dirty Flag System**: Medium
7. **Link System**: Medium
8. **Bridge System**: High (dynamic, thread-safe)
9. **Component Logic**: Medium per component
10. **Multi-threading**: High (concurrency, safety)
11. **Terminal Interface**: Low-Medium
12. **File I/O**: Medium
13. **Testing**: High (comprehensive coverage)

### Overall Project Complexity: **HIGH**
- Estimated development time: **3-6 months** (single developer)
- Lines of code estimate: **5,000-10,000** (excluding tests)

---

## 19. RECOMMENDED NEXT STEPS

1. **Decide on technology stack** (language, frameworks)
2. **Create detailed component specifications** (pin counts, behaviors)
3. **Design class hierarchy** (UML diagrams)
4. **Define .rsim file format** (schema/specification)
5. **Create project structure** (folders, modules)
6. **Implement Phase 1** (Foundation classes)
7. **Build simple test case** (Switch → LED)
8. **Iterate and expand**

---

## 20. SUCCESS CRITERIA

### Minimum Viable Product (MVP)
- Load .rsim file with 3 components
- Build VNETs correctly
- Simulate simple circuits (Switch → LED)
- Achieve stability
- Control via telnet
- Handle 10+ components without issues

### Full Success
- All component types working
- Links across pages functional
- Bridges working (relay contacts)
- Multi-threaded performance with 100+ components
- Stable simulation convergence
- Comprehensive terminal interface
- Well-tested and documented
- Ready for front-end integration

---

*End of Analysis*
