# .rsim File Format Specification

**Version:** 1.0.0  
**Status:** Draft  
**Last Updated:** December 10, 2025

---

## Overview

The `.rsim` file format is a JSON-based format for storing relay logic circuit designs. It uses a hierarchical structure to represent documents, pages, components, wires, and their connections.

### Design Principles

- **Human-readable:** JSON format for easy debugging and manual editing
- **Hierarchical:** Clear parent-child relationships (Document → Pages → Components/Wires → Pins/Tabs)
- **UUID-based:** All entities have unique 8-character identifiers
- **Version-controlled:** Schema versioning for backward compatibility
- **Extensible:** Custom properties support for component-specific data

---

## File Structure

```json
{
  "version": "1.0.0",
  "metadata": {
    "title": "My Circuit",
    "author": "User Name",
    "description": "Description of circuit",
    "created": "2025-12-10T10:30:00Z",
    "modified": "2025-12-10T14:45:00Z"
  },
  "pages": [...]
}
```

### Top-Level Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `version` | string | Yes | Schema version (e.g., "1.0.0") |
| `metadata` | object | No | Document metadata |
| `pages` | array | Yes | Array of page objects (min 1) |

---

## Version Compatibility

### Version String Format
`MAJOR.MINOR.PATCH` (e.g., "1.0.0")

### Compatibility Rules

- **Major version:** Must match exactly (breaking changes)
- **Minor version:** File version ≤ Application version (new features)
- **Patch version:** Any (bug fixes only)

**Examples:**
- Application 1.0.0 can read file 1.0.0 ✓
- Application 1.1.0 can read file 1.0.0 ✓
- Application 1.0.0 cannot read file 1.1.0 ✗
- Application 2.0.0 cannot read file 1.0.0 ✗

---

## Metadata Object

Optional metadata about the document.

```json
{
  "title": "Switch and LED Test",
  "author": "John Doe",
  "description": "Simple circuit to test basic switch and indicator",
  "created": "2025-12-10T10:30:00Z",
  "modified": "2025-12-10T14:45:00Z"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | No | Document title |
| `author` | string | No | Author name |
| `description` | string | No | Circuit description |
| `created` | string | No | ISO 8601 creation datetime |
| `modified` | string | No | ISO 8601 last modified datetime |

---

## Page Object

Represents a single page/sheet in the document.

```json
{
  "page_id": "a1b2c3d4",
  "name": "Main Page",
  "components": [...],
  "wires": [...]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `page_id` | string | Yes | Unique 8-char UUID |
| `name` | string | Yes | Display name of page |
| `components` | array | No | Array of component objects (default: []) |
| `wires` | array | No | Array of wire objects (default: []) |

---

## Component Object

Represents a component on a page.

```json
{
  "component_id": "e5f6g7h8",
  "component_type": "ToggleSwitch",
  "position": {"x": 100.0, "y": 200.0},
  "rotation": 0,
  "link_name": null,
  "pins": [...],
  "properties": {
    "label": "SW1",
    "label_position": "top",
    "mode": "toggle",
    "color": "red"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `component_id` | string | Yes | Unique 8-char UUID |
| `component_type` | string | Yes | Component type name |
| `position` | object | Yes | {x: float, y: float} position on canvas |
| `rotation` | integer | No | Rotation in degrees (0, 90, 180, 270) |
| `link_name` | string | No | Link name for cross-page connections |
| `pins` | array | Yes | Array of pin objects (min 1) |
| `properties` | object | No | Component-specific properties |

### Component Types

| Type | Description | Pin Count |
|------|-------------|-----------|
| `ToggleSwitch` | Toggle or pushbutton switch | 1 pin (4 tabs) |
| `Indicator` | LED indicator (passive) | 1 pin (4 tabs) |
| `DPDTRelay` | Double-pole double-throw relay | 7 pins (coil + 2 poles) |
| `VCC` | Voltage source (always HIGH) | 1 pin (1 tab) |

### Common Properties

| Property | Type | Components | Description |
|----------|------|------------|-------------|
| `label` | string | All | Display label |
| `label_position` | string | Switch, Indicator | "top", "bottom", "left", "right" |
| `mode` | string | Switch | "toggle" or "pushbutton" |
| `color` | string | Switch, Indicator | "red", "green", "yellow", "blue", etc. |
| `flip_horizontal` | boolean | Relay | Mirror horizontally |
| `flip_vertical` | boolean | Relay | Mirror vertically |

---

## Pin Object

Represents a pin on a component with one or more tabs.

```json
{
  "pin_id": "i9j0k1l2",
  "tabs": [...]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `pin_id` | string | Yes | Unique 8-char UUID |
| `tabs` | array | Yes | Array of tab objects (min 1) |

**Note:** Pin state is runtime-only and not saved to file.

---

## Tab Object

Represents a connection point on a pin.

```json
{
  "tab_id": "m3n4o5p6",
  "position": {"x": 10.0, "y": 0.0}
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `tab_id` | string | Yes | Unique 8-char UUID |
| `position` | object | Yes | {x: float, y: float} relative to component |

**Note:** Tab state is runtime-only and not saved to file.

---

## Wire Object

Represents a wire connecting tabs, with optional waypoints and junctions.

```json
{
  "wire_id": "q7r8s9t0",
  "start_tab_id": "m3n4o5p6",
  "end_tab_id": "u1v2w3x4",
  "waypoints": [...],
  "junctions": [...]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `wire_id` | string | Yes | Unique 8-char UUID |
| `start_tab_id` | string | Yes | ID of starting tab |
| `end_tab_id` | string | No | ID of ending tab (null if ends at junction) |
| `waypoints` | array | No | Array of waypoint objects (default: []) |
| `junctions` | array | No | Array of junction objects (default: []) |

### Wire Routing

- **Simple wire:** `start_tab_id` → `end_tab_id` (direct connection)
- **Wire with waypoints:** `start_tab_id` → waypoint1 → waypoint2 → `end_tab_id`
- **Wire with junction:** `start_tab_id` → junction → multiple child wires

---

## Waypoint Object

Represents an intermediate routing point on a wire.

```json
{
  "waypoint_id": "y5z6a7b8",
  "position": {"x": 150.0, "y": 250.0}
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `waypoint_id` | string | Yes | Unique 8-char UUID |
| `position` | object | Yes | {x: float, y: float} on canvas |

---

## Junction Object

Represents a branching point where multiple wires meet.

```json
{
  "junction_id": "c9d0e1f2",
  "position": {"x": 200.0, "y": 300.0},
  "child_wires": [...]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `junction_id` | string | Yes | Unique 8-char UUID |
| `position` | object | Yes | {x: float, y: float} on canvas |
| `child_wires` | array | Yes | Array of wire objects branching from junction (min 1) |

### Junction Hierarchy

Junctions create a tree structure of nested wires:

```
Wire 1: TabA → Junction1
  ├─ Wire 2: Junction1 → TabB
  ├─ Wire 3: Junction1 → TabC
  └─ Wire 4: Junction1 → Junction2
      ├─ Wire 5: Junction2 → TabD
      └─ Wire 6: Junction2 → TabE
```

---

## ID Requirements

### UUID Format

- **Length:** Exactly 8 characters
- **Character set:** Lowercase hexadecimal (0-9, a-f)
- **Generation:** First 8 characters of full UUID

### Uniqueness

All IDs must be unique within the document:
- Component IDs
- Page IDs
- Wire IDs
- Junction IDs
- Waypoint IDs
- Pin IDs
- Tab IDs

### Hierarchical IDs

For runtime identification, IDs may be combined hierarchically:
- `component_id.pin_id.tab_id` (e.g., "e5f6g7h8.i9j0k1l2.m3n4o5p6")
- This is for internal use only and not stored in the file

---

## Validation Rules

### Required Field Validation

All required fields must be present with correct types.

### ID Validation

- All IDs must match pattern: `^[0-9a-f]{8}$`
- All IDs must be unique within document
- Referenced IDs must exist (e.g., `start_tab_id` must reference an existing tab)

### Value Validation

- `rotation`: Must be 0, 90, 180, or 270
- `version`: Must match pattern: `^\d+\.\d+\.\d+$`
- Arrays with `min_items`: Must have at least that many items

### Reference Validation

- `start_tab_id` and `end_tab_id`: Must reference existing tabs on same page
- `link_name`: Components with same link name form cross-page connections
- Junction `child_wires`: Each child wire must have valid structure

---

## Example Files

### Example 1: Simple Switch and LED

```json
{
  "version": "1.0.0",
  "metadata": {
    "title": "Switch and LED",
    "description": "Simple test circuit"
  },
  "pages": [
    {
      "page_id": "page0001",
      "name": "Main",
      "components": [
        {
          "component_id": "comp0001",
          "component_type": "ToggleSwitch",
          "position": {"x": 100.0, "y": 100.0},
          "rotation": 0,
          "pins": [
            {
              "pin_id": "pin00001",
              "tabs": [
                {"tab_id": "tab00001", "position": {"x": 0.0, "y": -20.0}},
                {"tab_id": "tab00002", "position": {"x": 20.0, "y": 0.0}},
                {"tab_id": "tab00003", "position": {"x": 0.0, "y": 20.0}},
                {"tab_id": "tab00004", "position": {"x": -20.0, "y": 0.0}}
              ]
            }
          ],
          "properties": {
            "label": "SW1",
            "mode": "toggle",
            "color": "red"
          }
        },
        {
          "component_id": "comp0002",
          "component_type": "Indicator",
          "position": {"x": 300.0, "y": 100.0},
          "rotation": 0,
          "pins": [
            {
              "pin_id": "pin00002",
              "tabs": [
                {"tab_id": "tab00005", "position": {"x": 0.0, "y": -20.0}},
                {"tab_id": "tab00006", "position": {"x": 20.0, "y": 0.0}},
                {"tab_id": "tab00007", "position": {"x": 0.0, "y": 20.0}},
                {"tab_id": "tab00008", "position": {"x": -20.0, "y": 0.0}}
              ]
            }
          ],
          "properties": {
            "label": "LED1",
            "color": "green"
          }
        }
      ],
      "wires": [
        {
          "wire_id": "wire0001",
          "start_tab_id": "tab00002",
          "end_tab_id": "tab00008",
          "waypoints": []
        }
      ]
    }
  ]
}
```

### Example 2: Cross-Page Links

```json
{
  "version": "1.0.0",
  "pages": [
    {
      "page_id": "page0001",
      "name": "Input Page",
      "components": [
        {
          "component_id": "comp0001",
          "component_type": "ToggleSwitch",
          "position": {"x": 100.0, "y": 100.0},
          "link_name": "SIGNAL_A",
          "pins": [...],
          "properties": {"label": "Input A"}
        }
      ]
    },
    {
      "page_id": "page0002",
      "name": "Output Page",
      "components": [
        {
          "component_id": "comp0002",
          "component_type": "Indicator",
          "position": {"x": 100.0, "y": 100.0},
          "link_name": "SIGNAL_A",
          "pins": [...],
          "properties": {"label": "Output A"}
        }
      ]
    }
  ]
}
```

Both components share `"link_name": "SIGNAL_A"`, creating a virtual connection between pages.

### Example 3: Wire with Junction

```json
{
  "wire_id": "wire0001",
  "start_tab_id": "tab00001",
  "end_tab_id": null,
  "waypoints": [
    {"waypoint_id": "wp000001", "position": {"x": 150.0, "y": 100.0}}
  ],
  "junctions": [
    {
      "junction_id": "junc0001",
      "position": {"x": 200.0, "y": 100.0},
      "child_wires": [
        {
          "wire_id": "wire0002",
          "start_tab_id": "junc0001",
          "end_tab_id": "tab00002",
          "waypoints": []
        },
        {
          "wire_id": "wire0003",
          "start_tab_id": "junc0001",
          "end_tab_id": "tab00003",
          "waypoints": []
        }
      ]
    }
  ]
}
```

This creates a Y-shaped connection from tab00001 to both tab00002 and tab00003.

---

## Migration Guide

### From Version 1.0.0 to Future Versions

When new schema versions are released:

1. **Check compatibility:** Use version validation before loading
2. **Handle missing fields:** Use default values for new optional fields
3. **Ignore unknown fields:** Forward compatibility for older applications
4. **Version-specific loaders:** Implement migration functions for breaking changes

### Best Practices

- Always include `version` field
- Use default values for optional fields when upgrading
- Preserve unknown fields when re-saving (don't strip future additions)
- Test with sample files from each version

---

## Error Handling

### Common Validation Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Invalid version | Version string malformed | Use "MAJOR.MINOR.PATCH" format |
| Incompatible version | Major version mismatch | Update application or downgrade file |
| Missing required field | Field not present | Add required field |
| Invalid ID format | ID not 8 hex chars | Generate proper UUID |
| Duplicate ID | Same ID used twice | Regenerate duplicate IDs |
| Invalid reference | Tab/pin ID doesn't exist | Fix reference or add missing entity |
| Invalid rotation | Not 0/90/180/270 | Use valid rotation value |

### Error Messages

Errors should include:
- File path
- Line number (if available)
- Field path (e.g., "pages[0].components[2].pins[1].tab_id")
- Expected vs actual value
- Suggested fix

**Example:**
```
Error in file "circuit.rsim":
  Path: pages[0].components[2].rotation
  Invalid value: 45
  Expected: One of [0, 90, 180, 270]
  Suggestion: Use valid rotation value (0, 90, 180, or 270)
```

---

## Future Extensions

### Planned Features (v1.1.0+)

- Custom component types with type definitions
- Grid snapping settings
- Canvas size and zoom level
- Component libraries and imports
- Annotations and comments
- Simulation settings (timeouts, max iterations)

### Extensibility

The `properties` object allows for component-specific extensions without breaking schema compatibility. Future versions may formalize common properties into the schema.

---

*End of Specification*
