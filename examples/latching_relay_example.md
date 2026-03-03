# Latching Relay Component

## Overview
The latching relay is a bistable relay with two coils (SET and RESET) and two poles with DPDT contacts.

## Features
- **Two Coils**: COIL_SET and COIL_RESET
- **Bistable Operation**: Maintains its state after coil de-energization
- **Visual**: 60px wide × 240px tall (taller than standard DPDT to accommodate second coil)
- **Switching Delay**: 10ms realistic timing
- **Grid Spacing**: 
  - Coils positioned 3 grid squares (60px) from nearest COM pins
  - COM1 to COM2 spacing: 4 grid squares (80px)
- **Margins**: 20px top and bottom around pins

## Pin Configuration

### Left Side (Input)
- **COIL_SET** (top, y=-100): When HIGH, switches relay to SET state (COM → NO)
- **COM1** (y=-40): Common terminal for pole 1
- **COM2** (y=+40): Common terminal for pole 2
- **COIL_RESET** (bottom, y=+100): When HIGH, switches relay to RESET state (COM → NC)

### Right Side (Output)
- **NO1** (y=-60): Normally-open contact for pole 1
- **NC1** (y=-20): Normally-closed contact for pole 1
- **NO2** (y=+20): Normally-open contact for pole 2
- **NC2** (y=+60): Normally-closed contact for pole 2

## Operation

### SET State (Energized)
1. Apply HIGH to COIL_SET (while COIL_RESET is LOW)
2. After 10ms delay: COM1 connects to NO1, COM2 connects to NO2
3. State is maintained even when COIL_SET goes LOW

### RESET State (De-energized)
1. Apply HIGH to COIL_RESET (while COIL_SET is LOW)
2. After 10ms delay: COM1 connects to NC1, COM2 connects to NC2
3. State is maintained even when COIL_RESET goes LOW

### Both Coils Energized
1. If both COIL_SET and COIL_RESET are HIGH simultaneously
2. Relay maintains its current state (no switching occurs)
3. This prevents undefined behavior and contact bounce

## Example Use Cases
- **Memory Elements**: Store 1-bit state in relay circuits
- **Toggle Circuits**: Create flip-flop behavior
- **Power-On Reset**: Initialize circuits to known state
- **Debouncing**: Mechanical switch debouncing with latching behavior

## Differences from Standard DPDT Relay
| Feature | DPDT Relay | Latching Relay |
|---------|-----------|----------------|
| Coils | 1 | 2 (SET/RESET) |
| State | Returns to NC when de-energized | Maintains last state |
| Height | 200px | 240px |
| Pins | 7 | 8 |
| Power | Requires continuous power | Only needs pulse to change |
| COM Spacing | N/A | 4 grid squares (80px) |
| Coil Spacing | 1 coil at top | 3 grid squares from COM pins |

## Example Circuit
```
VCC ──┬─── Switch1 ─── COIL_SET
      │
      └─── Switch2 ─── COIL_RESET

               COM1 ──── (Output)
```

When Switch1 is pressed: Output goes HIGH (if VCC connected to COM1 and Output to NO1)
When Switch2 is pressed: Output goes LOW (if Output to NC1 connected to GND)
The relay maintains its state between switch presses!
