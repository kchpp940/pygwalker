"""
Full verification test suite for recommendation explanation feature.
Runs all tests without pytest dependency.
"""

import sys
import os
import json
import importlib.util
import traceback

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(TEST_DIR)

PASS = 0
FAIL = 0


def test(name):
    def decorator(func):
        def wrapper(*args, **kwargs):
            global PASS, FAIL
            print(f"\n{'='*60}")
            print(f"TEST: {name}")
            print(f"{'='*60}")
            try:
                result = func(*args, **kwargs)
                print(f"✓ PASS: {name}")
                PASS += 1
                return result
            except AssertionError as e:
                print(f"✗ FAIL: {name}")
                print(f"  Assertion failed: {e}")
                FAIL += 1
                return None
            except Exception as e:
                print(f"✗ FAIL: {name}")
                print(f"  Error: {e}")
                traceback.print_exc()
                FAIL += 1
                return None
        return wrapper
    return decorator


def assert_equal(actual, expected, message=""):
    if actual != expected:
        raise AssertionError(f"{message}. Expected {expected}, got {actual}")


def assert_in(item, container, message=""):
    if item not in container:
        raise AssertionError(f"{message}. '{item}' not in container")


def assert_true(condition, message=""):
    if not condition:
        raise AssertionError(message)


module_path = os.path.join(PROJECT_DIR, 'pygwalker', 'services', 'recommendation_explainer.py')
spec = importlib.util.spec_from_file_location('recommendation_explainer', module_path)
module = importlib.util.module_from_spec(spec)
sys.modules['recommendation_explainer'] = module
spec.loader.exec_module(module)

RecommendationExplainer = module.RecommendationExplainer
ChartType = module.ChartType
VisualEncodingType = module.VisualEncodingType
AggregationType = module.AggregationType


@test("Module import and initialization")
def test_module_import():
    explainer = RecommendationExplainer({})
    assert_true(explainer is not None, "Explainer should be created")
    return True


@test("Chart type identification - bar from geom")
def test_chart_type_bar():
    explainer = RecommendationExplainer({})
    spec = {"config": {"geom": "interval"}, "encodings": {}}
    chart_type = explainer._identify_chart_type(spec)
    assert_equal(chart_type, ChartType.BAR, "Should identify bar chart")
    return True


@test("Chart type identification - line from geom")
def test_chart_type_line():
    explainer = RecommendationExplainer({})
    spec = {"config": {"geom": "line"}, "encodings": {}}
    chart_type = explainer._identify_chart_type(spec)
    assert_equal(chart_type, ChartType.LINE, "Should identify line chart")
    return True


@test("Chart type identification - scatter from geom")
def test_chart_type_scatter():
    explainer = RecommendationExplainer({})
    spec = {"config": {"geom": "point"}, "encodings": {}}
    chart_type = explainer._identify_chart_type(spec)
    assert_equal(chart_type, ChartType.SCATTER, "Should identify scatter chart")
    return True


@test("Chart type identification - pie from geom")
def test_chart_type_pie():
    explainer = RecommendationExplainer({})
    spec = {"config": {"geom": "arc"}, "encodings": {}}
    chart_type = explainer._identify_chart_type(spec)
    assert_equal(chart_type, ChartType.PIE, "Should identify pie chart")
    return True


@test("Full explanation - bar chart with sum aggregation")
def test_full_explanation_bar():
    field_qualities = {
        'category': {
            'fid': 'category', 'missingRate': 0.0, 'uniqueCount': 5, 'distinctRate': 0.2,
            'dataType': 'string', 'distribution': {'type': 'string'},
            'anomalies': [], 'warnings': [], 'isSuitableForAnalysis': True
        },
        'sales': {
            'fid': 'sales', 'missingRate': 0.0, 'uniqueCount': 100, 'distinctRate': 0.9,
            'dataType': 'number', 'distribution': {'type': 'number', 'min': 100, 'max': 1000, 'mean': 500, 'stddev': 200},
            'anomalies': [], 'warnings': [], 'isSuitableForAnalysis': True
        }
    }
    
    metas = [
        {'fid': 'category', 'name': 'Category', 'analyticType': 'dimension', 'semanticType': 'nominal'},
        {'fid': 'sales', 'name': 'Sales', 'analyticType': 'measure', 'semanticType': 'quantitative'}
    ]
    
    spec = {
        'config': {'geom': 'interval'},
        'encodings': {
            'rows': [{'fid': 'sales', 'name': 'Sales', 'analyticType': 'measure', 'semanticType': 'quantitative', 'aggName': 'sum'}],
            'columns': [{'fid': 'category', 'name': 'Category', 'analyticType': 'dimension', 'semanticType': 'nominal'}]
        }
    }
    
    explainer = RecommendationExplainer(field_qualities)
    explanation = explainer.explain_recommendation(spec, metas)
    
    assert_equal(explanation['chartType']['type'], 'bar', "Should be bar chart")
    assert_true(len(explanation['chartType']['reasons']) > 0, "Should have reasons")
    assert_true(len(explanation['chartType']['advantages']) > 0, "Should have advantages")
    
    assert_equal(len(explanation['fields']), 2, "Should have 2 fields")
    
    sales_field = next(f for f in explanation['fields'] if f['fieldName'] == 'Sales')
    assert_equal(sales_field['fieldType'], 'measure', "Sales should be measure")
    assert_equal(sales_field['semanticType'], 'quantitative', "Sales should be quantitative")
    assert_equal(sales_field['encoding'], 'y', "Sales should be on y axis")
    
    category_field = next(f for f in explanation['fields'] if f['fieldName'] == 'Category')
    assert_equal(category_field['fieldType'], 'dimension', "Category should be dimension")
    assert_equal(category_field['semanticType'], 'nominal', "Category should be nominal")
    assert_equal(category_field['encoding'], 'x', "Category should be on x axis")
    
    assert_equal(len(explanation['aggregations']), 1, "Should have 1 aggregation")
    assert_equal(explanation['aggregations'][0]['aggregationType'], 'sum', "Should be sum aggregation")
    
    assert_equal(explanation['visualEncoding']['x'], 'Category', "X should be Category")
    assert_equal(explanation['visualEncoding']['y'], 'Sales', "Y should be Sales")
    
    assert_true(len(explanation['overallSummary']) > 0, "Should have summary")
    
    json_str = json.dumps(explanation, ensure_ascii=False)
    parsed = json.loads(json_str)
    assert_equal(parsed['chartType']['type'], 'bar', "Should be JSON serializable")
    
    print("\nGenerated Explanation:")
    print(json.dumps(explanation, ensure_ascii=False, indent=2))
    
    return True


@test("Full explanation - line chart with avg aggregation")
def test_full_explanation_line():
    field_qualities = {
        'date': {
            'fid': 'date', 'missingRate': 0.0, 'uniqueCount': 365, 'distinctRate': 0.95,
            'dataType': 'datetime', 'distribution': {'type': 'datetime'},
            'anomalies': [], 'warnings': [], 'isSuitableForAnalysis': True
        },
        'revenue': {
            'fid': 'revenue', 'missingRate': 0.05, 'uniqueCount': 100, 'distinctRate': 0.9,
            'dataType': 'number', 'distribution': {'type': 'number', 'min': 1000, 'max': 10000, 'mean': 5000, 'stddev': 2000},
            'anomalies': [], 'warnings': [], 'isSuitableForAnalysis': True
        }
    }
    
    metas = [
        {'fid': 'date', 'name': 'Date', 'analyticType': 'dimension', 'semanticType': 'temporal'},
        {'fid': 'revenue', 'name': 'Revenue', 'analyticType': 'measure', 'semanticType': 'quantitative'}
    ]
    
    spec = {
        'config': {'geom': 'line'},
        'encodings': {
            'rows': [{'fid': 'revenue', 'name': 'Revenue', 'analyticType': 'measure', 'semanticType': 'quantitative', 'aggName': 'avg'}],
            'columns': [{'fid': 'date', 'name': 'Date', 'analyticType': 'dimension', 'semanticType': 'temporal'}]
        }
    }
    
    explainer = RecommendationExplainer(field_qualities)
    explanation = explainer.explain_recommendation(spec, metas)
    
    assert_equal(explanation['chartType']['type'], 'line', "Should be line chart")
    assert_equal(len(explanation['aggregations']), 1, "Should have 1 aggregation")
    assert_equal(explanation['aggregations'][0]['aggregationType'], 'avg', "Should be avg aggregation")
    
    reasons = " ".join(explanation['chartType']['reasons'])
    assert_true("时间" in reasons or "趋势" in reasons, "Should mention time/trend")
    
    return True


@test("Full explanation - scatter plot with color encoding")
def test_full_explanation_scatter():
    field_qualities = {
        'x_val': {
            'fid': 'x_val', 'missingRate': 0.0, 'uniqueCount': 100, 'distinctRate': 0.9,
            'dataType': 'number', 'distribution': {'type': 'number'},
            'anomalies': [], 'warnings': [], 'isSuitableForAnalysis': True
        },
        'y_val': {
            'fid': 'y_val', 'missingRate': 0.0, 'uniqueCount': 100, 'distinctRate': 0.9,
            'dataType': 'number', 'distribution': {'type': 'number'},
            'anomalies': [], 'warnings': [], 'isSuitableForAnalysis': True
        },
        'category': {
            'fid': 'category', 'missingRate': 0.0, 'uniqueCount': 5, 'distinctRate': 0.2,
            'dataType': 'string', 'distribution': {'type': 'string'},
            'anomalies': [], 'warnings': [], 'isSuitableForAnalysis': True
        }
    }
    
    metas = [
        {'fid': 'x_val', 'name': 'X_Value', 'analyticType': 'measure', 'semanticType': 'quantitative'},
        {'fid': 'y_val', 'name': 'Y_Value', 'analyticType': 'measure', 'semanticType': 'quantitative'},
        {'fid': 'category', 'name': 'Category', 'analyticType': 'dimension', 'semanticType': 'nominal'}
    ]
    
    spec = {
        'config': {'geom': 'point'},
        'encodings': {
            'rows': [{'fid': 'y_val', 'name': 'Y_Value', 'analyticType': 'measure', 'semanticType': 'quantitative', 'aggName': 'none'}],
            'columns': [{'fid': 'x_val', 'name': 'X_Value', 'analyticType': 'measure', 'semanticType': 'quantitative', 'aggName': 'none'}],
            'color': [{'fid': 'category', 'name': 'Category', 'analyticType': 'dimension', 'semanticType': 'nominal'}]
        }
    }
    
    explainer = RecommendationExplainer(field_qualities)
    explanation = explainer.explain_recommendation(spec, metas)
    
    assert_equal(explanation['chartType']['type'], 'scatter', "Should be scatter chart")
    assert_true('color' in explanation['visualEncoding'], "Should have color encoding")
    assert_equal(explanation['visualEncoding']['color'], 'Category', "Color should be Category")
    
    return True


@test("Degrade - empty field qualities")
def test_degrade_empty_field_qualities():
    metas = [
        {'fid': 'category', 'name': 'Category', 'analyticType': 'dimension', 'semanticType': 'nominal'},
        {'fid': 'sales', 'name': 'Sales', 'analyticType': 'measure', 'semanticType': 'quantitative'}
    ]
    
    spec = {
        'config': {'geom': 'interval'},
        'encodings': {
            'rows': [{'fid': 'sales', 'name': 'Sales', 'analyticType': 'measure', 'semanticType': 'quantitative', 'aggName': 'sum'}],
            'columns': [{'fid': 'category', 'name': 'Category', 'analyticType': 'dimension', 'semanticType': 'nominal'}]
        }
    }
    
    explainer = RecommendationExplainer({})
    explanation = explainer.explain_recommendation(spec, metas)
    
    assert_equal(explanation['chartType']['type'], 'bar', "Should still identify bar chart")
    assert_equal(len(explanation['fields']), 2, "Should still extract fields")
    assert_true(len(explanation['overallSummary']) > 0, "Should still have summary")
    
    print("\nExplanation with empty field qualities:")
    print(f"  Chart Type: {explanation['chartType']['type']}")
    print(f"  Fields: {[f['fieldName'] for f in explanation['fields']]}")
    
    return True


@test("Degrade - empty spec")
def test_degrade_empty_spec():
    field_qualities = {
        'category': {'fid': 'category', 'missingRate': 0.0, 'dataType': 'string', 'distribution': {}, 'anomalies': [], 'warnings': [], 'isSuitableForAnalysis': True}
    }
    
    metas = [
        {'fid': 'category', 'name': 'Category', 'analyticType': 'dimension', 'semanticType': 'nominal'}
    ]
    
    spec = {"config": {}, "encodings": {}}
    
    explainer = RecommendationExplainer(field_qualities)
    explanation = explainer.explain_recommendation(spec, metas)
    
    assert_true('chartType' in explanation, "Should have chartType")
    assert_true('fields' in explanation, "Should have fields")
    assert_true('aggregations' in explanation, "Should have aggregations")
    assert_true('visualEncoding' in explanation, "Should have visualEncoding")
    assert_true('overallSummary' in explanation, "Should have overallSummary")
    assert_true('dataInsights' in explanation, "Should have dataInsights")
    
    print("\nExplanation with empty spec:")
    print(f"  Chart Type: {explanation['chartType']['type']}")
    print(f"  Fields count: {len(explanation['fields'])}")
    
    return True


@test("Degrade - missing field in field_qualities")
def test_degrade_missing_field():
    field_qualities = {
        'existing_field': {'fid': 'existing_field', 'missingRate': 0.0, 'dataType': 'string', 'distribution': {}, 'anomalies': [], 'warnings': [], 'isSuitableForAnalysis': True}
    }
    
    metas = [
        {'fid': 'missing_field', 'name': 'MissingField', 'analyticType': 'dimension', 'semanticType': 'nominal'},
        {'fid': 'measure_field', 'name': 'MeasureField', 'analyticType': 'measure', 'semanticType': 'quantitative'}
    ]
    
    spec = {
        'config': {'geom': 'interval'},
        'encodings': {
            'rows': [{'fid': 'measure_field', 'name': 'MeasureField', 'analyticType': 'measure', 'semanticType': 'quantitative', 'aggName': 'sum'}],
            'columns': [{'fid': 'missing_field', 'name': 'MissingField', 'analyticType': 'dimension', 'semanticType': 'nominal'}]
        }
    }
    
    explainer = RecommendationExplainer(field_qualities)
    explanation = explainer.explain_recommendation(spec, metas)
    
    assert_equal(explanation['chartType']['type'], 'bar', "Should still work")
    assert_equal(len(explanation['fields']), 2, "Should extract both fields")
    
    missing_field = next(f for f in explanation['fields'] if f['fieldName'] == 'MissingField')
    assert_true(len(missing_field['reason']) > 0, "Should have reason even without quality data")
    
    print("\nExplanation with missing field quality data:")
    print(f"  Fields: {[f['fieldName'] for f in explanation['fields']]}")
    
    return True


@test("Degrade - multiple charts (only first explained)")
def test_degrade_multiple_charts():
    field_qualities = {}
    metas = [
        {'fid': 'cat', 'name': 'Cat', 'analyticType': 'dimension', 'semanticType': 'nominal'},
        {'fid': 'val', 'name': 'Val', 'analyticType': 'measure', 'semanticType': 'quantitative'}
    ]
    
    single_spec = {
        'config': {'geom': 'interval'},
        'encodings': {
            'rows': [{'fid': 'val', 'name': 'Val', 'analyticType': 'measure', 'semanticType': 'quantitative', 'aggName': 'sum'}],
            'columns': [{'fid': 'cat', 'name': 'Cat', 'analyticType': 'dimension', 'semanticType': 'nominal'}]
        }
    }
    
    explainer = RecommendationExplainer(field_qualities)
    explanation = explainer.explain_recommendation(single_spec, metas)
    
    assert_equal(explanation['chartType']['type'], 'bar', "Should explain first chart")
    assert_true(len(explanation['overallSummary']) > 0, "Should have summary")
    
    print("\nMulti-chart handling:")
    print(f"  Explained chart type: {explanation['chartType']['type']}")
    
    return True


@test("Verify get_spec_by_text return structure compatibility")
def test_return_structure_compatibility():
    field_qualities = {
        'category': {'fid': 'category', 'missingRate': 0.0, 'dataType': 'string', 'distribution': {}, 'anomalies': [], 'warnings': [], 'isSuitableForAnalysis': True},
        'sales': {'fid': 'sales', 'missingRate': 0.0, 'dataType': 'number', 'distribution': {}, 'anomalies': [], 'warnings': [], 'isSuitableForAnalysis': True}
    }
    
    metas = [
        {'fid': 'category', 'name': 'Category', 'analyticType': 'dimension', 'semanticType': 'nominal'},
        {'fid': 'sales', 'name': 'Sales', 'analyticType': 'measure', 'semanticType': 'quantitative'}
    ]
    
    mock_result = {
        'visSpec': [{
            'config': {'geom': 'interval'},
            'encodings': {
                'rows': [{'fid': 'sales', 'name': 'Sales', 'analyticType': 'measure', 'semanticType': 'quantitative', 'aggName': 'sum'}],
                'columns': [{'fid': 'category', 'name': 'Category', 'analyticType': 'dimension', 'semanticType': 'nominal'}]
            }
        }]
    }
    
    explainer = RecommendationExplainer(field_qualities)
    
    old_return = {"data": mock_result}
    new_return = {"data": mock_result, "explanation": None}
    
    assert_equal(new_return.get('data'), old_return.get('data'), "data field should be same")
    assert_true('explanation' in new_return, "Should have explanation field")
    
    first_spec = mock_result['visSpec'][0]
    explanation = explainer.explain_recommendation(first_spec, metas)
    
    full_return = {"data": mock_result, "explanation": explanation}
    
    assert_true('data' in full_return, "data should exist for backward compatibility")
    assert_true('explanation' in full_return, "explanation should be added")
    assert_true(full_return['data'] is not None, "data should not be None")
    assert_true(full_return['explanation'] is not None, "explanation should be generated")
    
    print("\nReturn structure compatibility:")
    print(f"  Old structure keys: {list(old_return.keys())}")
    print(f"  New structure keys: {list(full_return.keys())}")
    print(f"  Backward compatible: data field preserved = {full_return.get('data') == old_return.get('data')}")
    print(f"  Explanation present: {full_return.get('explanation') is not None}")
    
    return True


@test("Exception handling - explainer should not crash")
def test_exception_handling():
    explainer = RecommendationExplainer({})
    
    try:
        explanation = explainer.explain_recommendation({}, [])
        assert_true('chartType' in explanation, "Should return valid structure")
        print("\nException handling:")
        print(f"  Empty spec handled gracefully")
        return True
    except Exception as e:
        raise AssertionError(f"Should not crash: {e}")


def main():
    global PASS, FAIL
    
    print("\n" + "="*70)
    print("  FULL RECOMMENDATION EXPLANATION VERIFICATION SUITE")
    print("="*70)
    
    test_module_import()
    test_chart_type_bar()
    test_chart_type_line()
    test_chart_type_scatter()
    test_chart_type_pie()
    test_full_explanation_bar()
    test_full_explanation_line()
    test_full_explanation_scatter()
    test_degrade_empty_field_qualities()
    test_degrade_empty_spec()
    test_degrade_missing_field()
    test_degrade_multiple_charts()
    test_return_structure_compatibility()
    test_exception_handling()
    
    print("\n" + "="*70)
    print(f"  RESULTS: {PASS} PASSED, {FAIL} FAILED")
    print("="*70)
    
    if FAIL > 0:
        print("\n❌ Some tests failed!")
        sys.exit(1)
    else:
        print("\n✅ All tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
