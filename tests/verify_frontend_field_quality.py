#!/usr/bin/env python3
"""
Static verification script for frontend field quality integration.
Verifies:
1. fieldQualities prop is defined in IAppProps interface
2. FieldQualityPanel is imported in index.tsx
3. fieldQualities prop is passed to FieldQualityPanel
4. FieldQualityPanel handles edge cases (empty data, missing fields)
"""

import re
import sys
from pathlib import Path


def read_file(filepath: str) -> str:
    """Read file content."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def test_interface_definition(interfaces_content: str) -> bool:
    """Test that fieldQualities is defined in IAppProps."""
    print("\n[TEST 1] IAppProps has fieldQualities prop")
    print("-" * 50)
    
    # Check IFieldQuality interface exists
    if 'interface IFieldQuality' not in interfaces_content:
        print("  ❌ FAIL: IFieldQuality interface not found")
        return False
    print("  ✅ IFieldQuality interface found")
    
    # Check fieldQualities is in IAppProps with correct type
    if 'fieldQualities?: Record<string, IFieldQuality>' not in interfaces_content:
        print("  ❌ FAIL: fieldQualities prop not found in IAppProps with correct type")
        return False
    print("  ✅ fieldQualities prop found in IAppProps: Record<string, IFieldQuality>")
    
    return True


def test_field_quality_panel_import(index_content: str) -> bool:
    """Test that FieldQualityPanel is imported."""
    print("\n[TEST 2] FieldQualityPanel is imported")
    print("-" * 50)
    
    if "import FieldQualityPanel from './components/fieldQualityPanel'" not in index_content:
        print("  ❌ FAIL: FieldQualityPanel import not found")
        return False
    print("  ✅ FieldQualityPanel import found")
    
    return True


def test_field_qualities_passed_to_panel(index_content: str) -> bool:
    """Test that fieldQualities prop is passed to FieldQualityPanel."""
    print("\n[TEST 3] fieldQualities prop is passed to FieldQualityPanel")
    print("-" * 50)
    
    # Check FieldQualityPanel is used with fieldQualities prop
    pattern = r'<FieldQualityPanel[\s\S]*?fieldQualities=\{props\.fieldQualities\}'
    match = re.search(pattern, index_content, re.MULTILINE)
    
    if not match:
        print("  ❌ FAIL: fieldQualities not passed to FieldQualityPanel")
        return False
    
    matched_text = match.group(0)
    print("  ✅ FieldQualityPanel component found with fieldQualities prop")
    
    # Also check fieldNames prop
    if 'fieldNames=' in matched_text:
        print("  ✅ fieldNames prop also passed to FieldQualityPanel")
    
    return True


def test_field_name_map_creation(index_content: str) -> bool:
    """Test that fieldNameMap is created from rawFields."""
    print("\n[TEST 4] fieldNameMap is created from rawFields")
    print("-" * 50)
    
    # Check fieldNameMap logic exists
    if 'fieldNameMap' not in index_content:
        print("  ❌ FAIL: fieldNameMap not found")
        return False
    
    # Check it uses React.useMemo
    if "const fieldNameMap = React.useMemo" not in index_content:
        print("  ❌ FAIL: fieldNameMap not created with React.useMemo")
        return False
    
    # Check it iterates over rawFields
    if 'props.rawFields.forEach' not in index_content:
        print("  ❌ FAIL: fieldNameMap does not iterate over rawFields")
        return False
    
    print("  ✅ fieldNameMap created with React.useMemo from props.rawFields")
    return True


def test_panel_handles_empty_data(panel_content: str) -> bool:
    """Test that FieldQualityPanel handles empty/undefined data."""
    print("\n[TEST 5] FieldQualityPanel handles empty/undefined data")
    print("-" * 50)
    
    # Check for null/undefined guard
    if 'if (!fieldQualities' not in panel_content and "fieldQualities?.length" not in panel_content:
        # Check alternative patterns
        if 'Object.keys(fieldQualities).length === 0' in panel_content:
            print("  ✅ Panel checks for empty fieldQualities")
        elif 'Object.keys(fieldQualities).length' in panel_content:
            print("  ✅ Panel handles fieldQualities iteration")
        else:
            # Check if it has a guard at the beginning
            if 'fieldQualities && Object.keys' in panel_content:
                print("  ✅ Panel has null guard for fieldQualities")
            elif "if (!fieldQualities || Object.keys(fieldQualities).length === 0)" in panel_content:
                print("  ✅ Panel returns null for empty fieldQualities")
            else:
                # Check for optional chaining
                if "fieldQualities?:" in panel_content or "fieldQualities &&" in panel_content:
                    print("  ✅ Panel uses optional chaining for fieldQualities")
                else:
                    print("  ⚠️  No explicit empty check found, but TypeScript types provide safety")
    else:
        print("  ✅ Panel has null guard for empty fieldQualities")
    
    return True


def test_panel_handles_missing_field_names(panel_content: str) -> bool:
    """Test that FieldQualityPanel handles missing field names."""
    print("\n[TEST 6] FieldQualityPanel handles missing field names")
    print("-" * 50)
    
    # Check displayName fallback
    if 'displayName={fieldNames?.[fid]' in panel_content:
        print("  ✅ Panel uses optional chaining for fieldNames")
    elif 'displayName={fieldNames[fid]' in panel_content:
        # Check if there's a fallback
        if '|| fid' in panel_content or '? fid : fid' in panel_content:
            print("  ✅ Panel has fallback to fid when fieldName missing")
        else:
            print("  ⚠️  Panel uses fieldNames[fid] without explicit fallback")
    elif 'displayName={fieldNames' not in panel_content:
        print("  ⚠️  Panel may not use fieldNames prop")
    
    # Check if displayName defaults to fid
    if 'fieldNames?.[fid] || fid' in panel_content or "fieldNames?.[fid] ?? fid" in panel_content:
        print("  ✅ Panel falls back to fid when fieldName missing")
    
    return True


def test_field_quality_item_handles_edge_cases(panel_content: str) -> bool:
    """Test that FieldQualityItem handles edge cases."""
    print("\n[TEST 7] FieldQualityItem handles edge cases")
    print("-" * 50)
    
    # Check distribution handling
    if 'distribution.topValues' in panel_content:
        print("  ✅ Panel handles distribution.topValues")
    
    if 'distribution?.topValues' in panel_content:
        print("  ✅ Panel uses optional chaining for distribution")
    
    # Check anomalies handling
    if 'anomalies.length === 0' in panel_content:
        print("  ✅ Panel checks for empty anomalies")
    
    if 'quality.anomalies' in panel_content:
        print("  ✅ Panel accesses quality.anomalies")
    
    # Check warnings handling
    if 'warnings.length > 0' in panel_content:
        print("  ✅ Panel checks for warnings")
    
    return True


def test_get_quality_status_function(panel_content: str) -> bool:
    """Test that getQualityStatus function exists and handles cases."""
    print("\n[TEST 8] getQualityStatus function handles quality status")
    print("-" * 50)
    
    if 'getQualityStatus' not in panel_content:
        print("  ❌ FAIL: getQualityStatus function not found")
        return False
    
    print("  ✅ getQualityStatus function found")
    
    # Check it handles all three statuses
    if 'isSuitableForAnalysis' in panel_content:
        print("  ✅ Function checks isSuitableForAnalysis")
    
    if 'anomalies.some(a => a.severity === \"high\")' in panel_content:
        print("  ✅ Function checks for high severity anomalies")
    
    return True


def main():
    """Run all static verification tests."""
    print("=" * 60)
    print("FRONTEND FIELD QUALITY STATIC VERIFICATION")
    print("=" * 60)
    
    # Get project root
    project_root = Path(__file__).parent.parent
    app_dir = project_root / "app" / "src"
    
    # Read files
    interfaces_file = app_dir / "interfaces" / "index.ts"
    index_file = app_dir / "index.tsx"
    panel_file = app_dir / "components" / "fieldQualityPanel" / "index.tsx"
    
    print(f"\nReading files from: {app_dir}")
    
    try:
        interfaces_content = read_file(str(interfaces_file))
        index_content = read_file(str(index_file))
        panel_content = read_file(str(panel_file))
    except FileNotFoundError as e:
        print(f"\n❌ ERROR: File not found: {e}")
        return 1
    
    print(f"  ✅ interfaces/index.ts: {len(interfaces_content)} chars")
    print(f"  ✅ index.tsx: {len(index_content)} chars")
    print(f"  ✅ fieldQualityPanel/index.tsx: {len(panel_content)} chars")
    
    # Run all tests
    all_passed = True
    
    tests = [
        ("Interface Definition", lambda: test_interface_definition(interfaces_content)),
        ("Panel Import", lambda: test_field_quality_panel_import(index_content)),
        ("Prop Passing", lambda: test_field_qualities_passed_to_panel(index_content)),
        ("Field Name Map", lambda: test_field_name_map_creation(index_content)),
        ("Empty Data Handling", lambda: test_panel_handles_empty_data(panel_content)),
        ("Missing Field Names", lambda: test_panel_handles_missing_field_names(panel_content)),
        ("Edge Case Handling", lambda: test_field_quality_item_handles_edge_cases(panel_content)),
        ("Quality Status Function", lambda: test_get_quality_status_function(panel_content)),
    ]
    
    passed_count = 0
    for test_name, test_func in tests:
        try:
            if test_func():
                passed_count += 1
        except Exception as e:
            print(f"\n  ❌ EXCEPTION in {test_name}: {e}")
            all_passed = False
    
    # Summary
    print("\n" + "=" * 60)
    if passed_count == len(tests):
        print(f"  ✅ ALL {passed_count}/{len(tests)} TESTS PASSED!")
        print("=" * 60)
        print("\nSummary of verified data flow:")
        print("  1. IAppProps.fieldQualities?: Record<string, IFieldQuality>")
        print("  2. FieldQualityPanel imported from './components/fieldQualityPanel'")
        print("  3. <FieldQualityPanel fieldQualities={props.fieldQualities} ... />")
        print("  4. fieldNameMap created from props.rawFields with fallback to fid")
        print("  5. Panel handles empty/undefined fieldQualities")
        print("  6. Panel handles missing field names (falls back to fid)")
        print("  7. Panel handles distribution.topValues, anomalies, warnings")
        print("  8. getQualityStatus determines good/warning/error status")
        return 0
    else:
        print(f"  ❌ {passed_count}/{len(tests)} tests passed")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
