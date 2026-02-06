# Sub-Circuit Implementation - Phase 1 Summary

## ✅ Completed Tasks

### 1. SubCircuit Component Class
**File**: `relay_simulator/components/sub_circuit.py`

- Created `SubCircuit` component inheriting from `Component`
- Properties:
  - `sub_circuit_id`: References embedded definition in `Document.sub_circuits`
  - `instance_id`: Unique identifier per instance
  - `sub_circuit_name`: Display name
  - Dynamic pins/tabs based on FOOTPRINT Links
- Methods:
  - `simulate_logic()`: Passive - internal components handle logic
  - `sim_start()`: Creates bridges between external/internal Links (stub for Phase 3)
  - `add_pin_from_link()`: Builds component interface from FOOTPRINT
  - `to_dict()` / `from_dict()`: Serialization support
- Registered in `ComponentFactory`

### 2. Schema Extensions
**File**: `relay_simulator/fileio/rsim_schema.py`

Added three new schema definitions:
- `SUB_CIRCUIT_INSTANCE_SCHEMA`: Instance metadata (page mapping, parent reference)
- `SUB_CIRCUIT_DEFINITION_SCHEMA`: Template + instances structure
- Updated `DOCUMENT_SCHEMA`: Added optional `sub_circuits` field

### 3. .rsub File Loader
**File**: `relay_simulator/fileio/sub_circuit_loader.py`

Created `SubCircuitLoader` class:
- `load_from_file()`: Loads .rsub templates with validation
- `load_from_string()`: Loads from JSON string
- **Validation**:
  - Ensures FOOTPRINT page exists (case-sensitive)
  - Validates Link components have `link_name` set
  - Extracts interface definition
- `SubCircuitTemplate` class: Holds parsed template data

### 4. Document Structure Updates
**File**: `relay_simulator/core/document.py`

Added three new classes and document extensions:

**New Classes**:
1. `SubCircuitInstance`: Maps template pages to instance page IDs
2. `SubCircuitDefinition`: Embedded template + instances
   - Template pages (including FOOTPRINT)
   - Instance tracking
   - Serialization/deserialization

**Document Updates**:
- Added `sub_circuits` dictionary: `{sub_circuit_id -> SubCircuitDefinition}`
- New methods:
  - `add_sub_circuit_definition()`
  - `get_sub_circuit_definition()`
  - `remove_sub_circuit_definition()`
- Updated `to_dict()` / `from_dict()` to handle sub-circuits

### 5. Test Suite
**File**: `relay_simulator/testing/test_sub_circuit_phase1.py`

Comprehensive tests covering:
- ✅ Load Latch.rsub template (2 pages, 2 interface Links)
- ✅ SubCircuitDefinition serialization round-trip
- ✅ Document with embedded sub-circuits
- **All tests pass!**

---

## 📋 Data Model Overview

```
Document
├── pages[]                    # Main document pages
└── sub_circuits{}             # Embedded sub-circuit definitions
    └── {sub_circuit_id}
        ├── name                      # "Latch"
        ├── source_file               # "Latch.rsub"
        ├── template_pages[]          # Original template pages
        │   ├── FOOTPRINT page        # Interface definition
        │   └── Internal pages        # Circuit logic
        └── instances{}               # Instance tracking
            └── {instance_id}
                ├── parent_page_id    # Where SubCircuit component lives
                ├── component_id      # SubCircuit component ID
                └── page_id_map{}     # template_page_id -> instance_page_id
```

---

## 🔄 How It Works (Current State)

1. **Template Loading** (.rsub → SubCircuitTemplate)
   - Loader validates FOOTPRINT page exists
   - Extracts Link components as interface definition
   - Returns parsed template data

2. **Document Embedding** (Phase 2+)
   - Template will be embedded as `SubCircuitDefinition`
   - Each drag-and-drop creates new `SubCircuitInstance`
   - Instance pages are deep-copied with new IDs

3. **Component Interface** (Phase 2+)
   - SubCircuit component created on main page
   - Pins/tabs generated from FOOTPRINT Links
   - Link names map external connections to internal circuit

4. **Simulation** (Phase 3+)
   - Bridges connect SubCircuit tabs to FOOTPRINT Link tabs
   - FOOTPRINT Links bridge to internal page Links
   - All instance pages participate in VNET building

---

## 🚀 Next Steps: Phase 2 (Instantiation)

**Goals**: Create instances from templates, manage IDs, handle page copies

### Remaining Tasks:
1. **Sub-circuit instantiation logic**
   - Deep copy template pages with new IDs (8-char UUIDs)
   - Create SubCircuitInstance and update Document
   - Build SubCircuit component with pins from FOOTPRINT

2. **ID generation for instances**
   - Regenerate all IDs: page_id, component_id, pin_id, tab_id, wire_id
   - Maintain internal references (wire connections, etc.)
   - Update IDManager to track all IDs

3. **Page management**
   - Add `is_sub_circuit_page` flag to Page class
   - Add `parent_instance_id` to track instance ownership
   - Filter sub-circuit pages from GUI page tabs

4. **Bounding box calculation**
   - Calculate FOOTPRINT dimensions from Box/components
   - Set SubCircuit width/height for rendering

### Key Files to Modify:
- `core/page.py`: Add instance tracking fields
- `core/id_manager.py`: ID regeneration utilities
- New: `core/sub_circuit_instantiator.py`: Instantiation logic

---

## 📊 Test Results

```
Phase 1 Sub-Circuit Implementation Tests
============================================================

Test 1: Load Latch.rsub                              ✅ PASS
  - Loaded template: Latch
  - Pages: 2 (FOOTPRINT + Latching Relay)
  - Interface links: 2 (SUB_IN, SUB_OUT)

Test 2: SubCircuitDefinition Serialization           ✅ PASS
  - Serialization successful
  - Deserialization successful
  - Data integrity verified

Test 3: Document with Sub-Circuits                   ✅ PASS
  - Document creation successful
  - Sub-circuit embedding successful
  - Serialization/deserialization verified

All Phase 1 tests completed successfully!
```

---

## 🎯 Architecture Highlights

### Design Principles Applied:
✅ **Separation of Concerns**: SubCircuit component has no GUI dependencies  
✅ **Schema Compatibility**: Extensions are optional, backward-compatible  
✅ **8-Char UUID System**: All IDs follow existing convention  
✅ **Factory Pattern**: SubCircuit registered in ComponentFactory  
✅ **File Size Limit**: All new files under 300 lines  

### Key Decisions:
- **Embedded Model**: Sub-circuits stored in document (not external references)
  - Ensures portability
  - Simplifies versioning
  - Each instance gets full page copies

- **FOOTPRINT as Interface**: Visual + functional definition
  - Links define pins/tabs on SubCircuit component
  - Link names enable internal mapping

- **Instance Isolation**: Each instance has separate page copies
  - No shared state between instances
  - VNETs built per-instance

---

## 📁 Files Created/Modified

### Created:
- `relay_simulator/components/sub_circuit.py` (210 lines)
- `relay_simulator/fileio/sub_circuit_loader.py` (229 lines)
- `relay_simulator/testing/test_sub_circuit_phase1.py` (130 lines)

### Modified:
- `relay_simulator/components/factory.py` (2 additions)
- `relay_simulator/fileio/rsim_schema.py` (64 additions)
- `relay_simulator/core/document.py` (145 additions)

### Total New Code: ~569 lines
### All files under 300 lines ✅
