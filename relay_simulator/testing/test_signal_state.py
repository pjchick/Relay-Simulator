"""
Test suite for Signal State System (Phase 1.2)

Tests PinState enumeration, state logic functions, and state comparison utilities.
"""

import sys
import os

# Add parent directory to path to import relay_simulator
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.state import PinState, combine_states, has_state_changed, states_equal


def test_pinstate_enum():
    """Test PinState enumeration values."""
    print("\n=== Testing PinState Enumeration ===")
    
    # Test enum values
    assert PinState.FLOAT.value == 0, "FLOAT should have value 0"
    assert PinState.HIGH.value == 1, "HIGH should have value 1"
    
    # Test string representation
    assert str(PinState.FLOAT) == "FLOAT", f"String representation failed: {str(PinState.FLOAT)}"
    assert str(PinState.HIGH) == "HIGH", f"String representation failed: {str(PinState.HIGH)}"
    
    # Test repr
    assert repr(PinState.FLOAT) == "PinState.FLOAT"
    assert repr(PinState.HIGH) == "PinState.HIGH"
    
    print("✓ PinState enum values correct")
    print("✓ String representations correct")
    print("✓ PinState enumeration tests passed")


def test_combine_states_all_combinations():
    """Test combine_states with all possible combinations."""
    print("\n=== Testing State Combination Logic ===")
    
    # Test 1: FLOAT + FLOAT = FLOAT
    result = combine_states(PinState.FLOAT, PinState.FLOAT)
    assert result == PinState.FLOAT, f"FLOAT + FLOAT should = FLOAT, got {result}"
    print("✓ FLOAT + FLOAT = FLOAT")
    
    # Test 2: HIGH + FLOAT = HIGH
    result = combine_states(PinState.HIGH, PinState.FLOAT)
    assert result == PinState.HIGH, f"HIGH + FLOAT should = HIGH, got {result}"
    print("✓ HIGH + FLOAT = HIGH")
    
    # Test 3: FLOAT + HIGH = HIGH (order shouldn't matter)
    result = combine_states(PinState.FLOAT, PinState.HIGH)
    assert result == PinState.HIGH, f"FLOAT + HIGH should = HIGH, got {result}"
    print("✓ FLOAT + HIGH = HIGH")
    
    # Test 4: HIGH + HIGH = HIGH
    result = combine_states(PinState.HIGH, PinState.HIGH)
    assert result == PinState.HIGH, f"HIGH + HIGH should = HIGH, got {result}"
    print("✓ HIGH + HIGH = HIGH")
    
    print("✓ All 2-state combinations tested")


def test_combine_states_multiple():
    """Test combine_states with more than 2 states."""
    print("\n=== Testing Multiple State Combinations ===")
    
    # Test 1: All FLOAT
    result = combine_states(PinState.FLOAT, PinState.FLOAT, PinState.FLOAT, PinState.FLOAT)
    assert result == PinState.FLOAT, f"All FLOAT should = FLOAT, got {result}"
    print("✓ 4x FLOAT = FLOAT")
    
    # Test 2: One HIGH among FLOAT
    result = combine_states(PinState.FLOAT, PinState.FLOAT, PinState.HIGH, PinState.FLOAT)
    assert result == PinState.HIGH, f"One HIGH among FLOAT should = HIGH, got {result}"
    print("✓ FLOAT, FLOAT, HIGH, FLOAT = HIGH")
    
    # Test 3: Multiple HIGH
    result = combine_states(PinState.HIGH, PinState.FLOAT, PinState.HIGH, PinState.HIGH)
    assert result == PinState.HIGH, f"Multiple HIGH should = HIGH, got {result}"
    print("✓ Multiple HIGH = HIGH")
    
    # Test 4: All HIGH
    result = combine_states(PinState.HIGH, PinState.HIGH, PinState.HIGH)
    assert result == PinState.HIGH, f"All HIGH should = HIGH, got {result}"
    print("✓ All HIGH = HIGH")
    
    # Test 5: Single state
    result = combine_states(PinState.FLOAT)
    assert result == PinState.FLOAT, f"Single FLOAT should = FLOAT, got {result}"
    result = combine_states(PinState.HIGH)
    assert result == PinState.HIGH, f"Single HIGH should = HIGH, got {result}"
    print("✓ Single state combinations correct")
    
    # Test 6: Empty (edge case)
    result = combine_states()
    assert result == PinState.FLOAT, f"No states should = FLOAT, got {result}"
    print("✓ Empty combination = FLOAT")
    
    print("✓ Multiple state combinations tested")


def test_has_state_changed():
    """Test state change detection."""
    print("\n=== Testing State Change Detection ===")
    
    # Test 1: FLOAT -> HIGH (change)
    assert has_state_changed(PinState.FLOAT, PinState.HIGH) == True, "FLOAT -> HIGH should be detected"
    print("✓ FLOAT -> HIGH detected as change")
    
    # Test 2: HIGH -> FLOAT (change)
    assert has_state_changed(PinState.HIGH, PinState.FLOAT) == True, "HIGH -> FLOAT should be detected"
    print("✓ HIGH -> FLOAT detected as change")
    
    # Test 3: FLOAT -> FLOAT (no change)
    assert has_state_changed(PinState.FLOAT, PinState.FLOAT) == False, "FLOAT -> FLOAT should not be detected"
    print("✓ FLOAT -> FLOAT not detected as change")
    
    # Test 4: HIGH -> HIGH (no change)
    assert has_state_changed(PinState.HIGH, PinState.HIGH) == False, "HIGH -> HIGH should not be detected"
    print("✓ HIGH -> HIGH not detected as change")
    
    print("✓ State change detection tests passed")


def test_states_equal():
    """Test state equality checking."""
    print("\n=== Testing State Equality ===")
    
    # Test 1: FLOAT == FLOAT
    assert states_equal(PinState.FLOAT, PinState.FLOAT) == True, "FLOAT should equal FLOAT"
    print("✓ FLOAT == FLOAT")
    
    # Test 2: HIGH == HIGH
    assert states_equal(PinState.HIGH, PinState.HIGH) == True, "HIGH should equal HIGH"
    print("✓ HIGH == HIGH")
    
    # Test 3: FLOAT != HIGH
    assert states_equal(PinState.FLOAT, PinState.HIGH) == False, "FLOAT should not equal HIGH"
    print("✓ FLOAT != HIGH")
    
    # Test 4: HIGH != FLOAT
    assert states_equal(PinState.HIGH, PinState.FLOAT) == False, "HIGH should not equal FLOAT"
    print("✓ HIGH != FLOAT")
    
    print("✓ State equality tests passed")


def test_or_logic_principle():
    """Test that HIGH always wins (OR logic principle)."""
    print("\n=== Testing HIGH Always Wins Principle ===")
    
    # This is the core principle of the system
    test_cases = [
        ([PinState.HIGH], PinState.HIGH),
        ([PinState.FLOAT], PinState.FLOAT),
        ([PinState.HIGH, PinState.FLOAT], PinState.HIGH),
        ([PinState.FLOAT, PinState.HIGH], PinState.HIGH),
        ([PinState.FLOAT, PinState.FLOAT, PinState.FLOAT, PinState.HIGH], PinState.HIGH),
        ([PinState.HIGH, PinState.HIGH, PinState.HIGH], PinState.HIGH),
        ([PinState.FLOAT, PinState.FLOAT, PinState.FLOAT], PinState.FLOAT),
    ]
    
    for states, expected in test_cases:
        result = combine_states(*states)
        assert result == expected, f"States {states} should = {expected}, got {result}"
        state_str = " + ".join([s.name for s in states])
        print(f"✓ {state_str} = {expected.name}")
    
    print("✓ OR logic principle verified")


def run_all_tests():
    """Run all Signal State System tests."""
    print("=" * 60)
    print("SIGNAL STATE SYSTEM TEST SUITE")
    print("=" * 60)
    
    try:
        test_pinstate_enum()
        test_combine_states_all_combinations()
        test_combine_states_multiple()
        test_has_state_changed()
        test_states_equal()
        test_or_logic_principle()
        
        print("\n" + "=" * 60)
        print("✓ ALL SIGNAL STATE SYSTEM TESTS PASSED")
        print("=" * 60)
        return True
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
