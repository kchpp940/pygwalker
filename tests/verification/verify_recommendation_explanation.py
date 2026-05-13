"""
Backend verification script for recommendation explanation feature.
Verifies py_compile and runs comprehensive tests.
"""

import sys
import os
import py_compile
import traceback

PYGWALKER_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PYGWALKER_PATH)

def test_py_compile(file_path):
    """Test that a Python file compiles without syntax errors."""
    try:
        py_compile.compile(file_path, doraise=True)
        print(f"PASS: py_compile successful for {os.path.basename(file_path)}")
        return True
    except py_compile.PyCompileError as e:
        print(f"FAIL: py_compile failed for {os.path.basename(file_path)}")
        print(f"Error: {e}")
        return False

def test_import():
    """Test that the module can be imported."""
    try:
        import importlib.util
        import sys
        
        module_path = os.path.join(PYGWALKER_PATH, "pygwalker", "services", "recommendation_explainer.py")
        spec = importlib.util.spec_from_file_location("recommendation_explainer", module_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules["recommendation_explainer"] = module
        spec.loader.exec_module(module)
        
        RecommendationExplainer = module.RecommendationExplainer
        ChartType = module.ChartType
        VisualEncodingType = module.VisualEncodingType
        AggregationType = module.AggregationType
        
        print("PASS: Import successful")
        
        explainer = RecommendationExplainer({})
        print("PASS: RecommendationExplainer instantiation successful")
        
        return True, module
    except Exception as e:
        print(f"FAIL: Import failed")
        print(f"Error: {e}")
        traceback.print_exc()
        return False, None

def test_explain_recommendation(module):
    """Test the main explain_recommendation method."""
    try:
        RecommendationExplainer = module.RecommendationExplainer
        
        field_qualities = {
            "category": {
                "fid": "category",
                "missingRate": 0.0,
                "uniqueCount": 5,
                "distinctRate": 0.2,
                "dataType": "string",
                "distribution": {"type": "string"},
                "anomalies": [],
                "warnings": [],
                "isSuitableForAnalysis": True
            },
            "sales": {
                "fid": "sales",
                "missingRate": 0.0,
                "uniqueCount": 100,
                "distinctRate": 0.9,
                "dataType": "number",
                "distribution": {"type": "number", "min": 100, "max": 1000, "mean": 500, "stddev": 200},
                "anomalies": [],
                "warnings": [],
                "isSuitableForAnalysis": True
            }
        }
        
        metas = [
            {"fid": "category", "name": "Category", "analyticType": "dimension", "semanticType": "nominal"},
            {"fid": "sales", "name": "Sales", "analyticType": "measure", "semanticType": "quantitative"}
        ]
        
        spec = {
            "config": {"geom": "interval"},
            "encodings": {
                "rows": [{"fid": "sales", "name": "Sales", "analyticType": "measure", "semanticType": "quantitative", "aggName": "sum"}],
                "columns": [{"fid": "category", "name": "Category", "analyticType": "dimension", "semanticType": "nominal"}]
            }
        }
        
        explainer = RecommendationExplainer(field_qualities)
        explanation = explainer.explain_recommendation(spec, metas)
        
        assert "chartType" in explanation, "Missing chartType"
        assert explanation["chartType"]["type"] == "bar", f"Expected 'bar', got {explanation['chartType']['type']}"
        print("PASS: Chart type explanation - bar chart detected")
        
        assert "fields" in explanation, "Missing fields"
        assert len(explanation["fields"]) == 2, f"Expected 2 fields, got {len(explanation['fields'])}"
        print("PASS: Field type explanation - 2 fields extracted")
        
        assert "aggregations" in explanation, "Missing aggregations"
        assert len(explanation["aggregations"]) == 1, f"Expected 1 aggregation, got {len(explanation['aggregations'])}"
        assert explanation["aggregations"][0]["aggregationType"] == "sum", "Expected 'sum' aggregation"
        print("PASS: Aggregation explanation - sum aggregation detected")
        
        assert "visualEncoding" in explanation, "Missing visualEncoding"
        assert "x" in explanation["visualEncoding"], "Missing x encoding"
        assert "y" in explanation["visualEncoding"], "Missing y encoding"
        print("PASS: Visual encoding explanation - x/y encodings extracted")
        
        assert "overallSummary" in explanation, "Missing overallSummary"
        assert len(explanation["overallSummary"]) > 0, "Overall summary is empty"
        print("PASS: Overall summary generated")
        
        assert "dataInsights" in explanation, "Missing dataInsights"
        print("PASS: Data insights section present")
        
        import json
        json_str = json.dumps(explanation, ensure_ascii=False)
        parsed = json.loads(json_str)
        assert parsed["chartType"]["type"] == "bar", "JSON serialization failed"
        print("PASS: Explanation is JSON serializable")
        
        print("\n--- Generated Explanation Preview ---")
        print(f"Chart Type: {explanation['chartType']['type']}")
        print(f"Reasons: {explanation['chartType']['reasons']}")
        print(f"Advantages: {explanation['chartType']['advantages']}")
        print(f"Overall Summary: {explanation['overallSummary']}")
        print(f"Fields: {[f['fieldName'] for f in explanation['fields']]}")
        print(f"Aggregations: {[(a['fieldName'], a['aggregationType']) for a in explanation['aggregations']]}")
        print(f"Visual Encoding: {explanation['visualEncoding']}")
        
        return True
        
    except Exception as e:
        print(f"FAIL: explain_recommendation test failed")
        print(f"Error: {e}")
        traceback.print_exc()
        return False

def test_pygwalker_integration():
    """Test that pygwalker.py has the new functions registered."""
    try:
        import ast
        
        pygwalker_path = os.path.join(PYGWALKER_PATH, "pygwalker", "api", "pygwalker.py")
        with open(pygwalker_path, "r") as f:
            content = f.read()
        
        checks = [
            ("RecommendationExplainer import", "from pygwalker.services.recommendation_explainer import RecommendationExplainer"),
            ("get_spec_by_text returns explanation", '"explanation": explanation'),
            ("get_chart_by_chats returns explanation", '"explanation": explanation'),
            ("_get_recommendation_explanation function", "def _get_recommendation_explanation"),
            ("get_recommendation_explanation registration", 'comm.register("get_recommendation_explanation"')
        ]
        
        all_passed = True
        for check_name, check_string in checks:
            if check_string in content:
                print(f"PASS: {check_name}")
            else:
                print(f"FAIL: {check_name}")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"FAIL: pygwalker integration test failed")
        print(f"Error: {e}")
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("Backend Verification: Recommendation Explanation")
    print("=" * 60)
    print()
    
    files_to_compile = [
        os.path.join(PYGWALKER_PATH, "pygwalker", "services", "recommendation_explainer.py"),
        os.path.join(PYGWALKER_PATH, "pygwalker", "api", "pygwalker.py"),
    ]
    
    print("Step 1: py_compile verification")
    print("-" * 40)
    compile_passed = all([test_py_compile(f) for f in files_to_compile])
    print()
    
    if not compile_passed:
        print("\npy_compile failed, aborting further tests.")
        sys.exit(1)
    
    print("Step 2: Import test")
    print("-" * 40)
    import_passed, module = test_import()
    print()
    
    if not import_passed or module is None:
        print("\nImport test failed.")
        sys.exit(1)
    
    print("Step 3: explain_recommendation functional test")
    print("-" * 40)
    func_passed = test_explain_recommendation(module)
    print()
    
    print("Step 4: pygwalker integration test")
    print("-" * 40)
    integration_passed = test_pygwalker_integration()
    print()
    
    print("=" * 60)
    all_passed = compile_passed and import_passed and func_passed and integration_passed
    if all_passed:
        print("ALL BACKEND VERIFICATION TESTS PASSED!")
    else:
        print("SOME TESTS FAILED")
        sys.exit(1)
    print("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
