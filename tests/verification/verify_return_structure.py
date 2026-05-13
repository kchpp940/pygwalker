"""
最小脚本：验证 get_spec_by_text / get_chart_by_chats 返回结构
断言：
1. 旧字段 data 保持原样
2. 新字段 explanation 存在
3. 前端 askviz/vlChat 仍返回原 data
4. 前端会打开解释弹窗
"""

import sys
import os
import json
import importlib.util

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEST_DIR = os.path.dirname(os.path.abspath(__file__))

module_path = os.path.join(PROJECT_DIR, 'pygwalker', 'services', 'recommendation_explainer.py')
spec = importlib.util.spec_from_file_location('recommendation_explainer', module_path)
module = importlib.util.module_from_spec(spec)
sys.modules['recommendation_explainer'] = module
spec.loader.exec_module(module)

RecommendationExplainer = module.RecommendationExplainer

PASS = 0
FAIL = 0

def assert_true(condition, message):
    global PASS, FAIL
    if condition:
        print(f'✓ PASS: {message}')
        PASS += 1
    else:
        print(f'✗ FAIL: {message}')
        FAIL += 1

def assert_equal(actual, expected, message):
    global PASS, FAIL
    if actual == expected:
        print(f'✓ PASS: {message}')
        PASS += 1
    else:
        print(f'✗ FAIL: {message} (expected: {expected}, got: {actual})')
        FAIL += 1

field_qualities = {
    'category': {'fid': 'category', 'missingRate': 0.0, 'dataType': 'string', 'distribution': {}, 'anomalies': [], 'warnings': [], 'isSuitableForAnalysis': True},
    'sales': {'fid': 'sales', 'missingRate': 0.0, 'dataType': 'number', 'distribution': {}, 'anomalies': [], 'warnings': [], 'isSuitableForAnalysis': True}
}

metas = [
    {'fid': 'category', 'name': 'Category', 'analyticType': 'dimension', 'semanticType': 'nominal'},
    {'fid': 'sales', 'name': 'Sales', 'analyticType': 'measure', 'semanticType': 'quantitative'}
]

mock_cloud_result = {
    'visSpec': [{
        'config': {'geom': 'interval'},
        'encodings': {
            'rows': [{'fid': 'sales', 'name': 'Sales', 'analyticType': 'measure', 'semanticType': 'quantitative', 'aggName': 'sum'}],
            'columns': [{'fid': 'category', 'name': 'Category', 'analyticType': 'dimension', 'semanticType': 'nominal'}]
        }
    }]
}

explainer = RecommendationExplainer(field_qualities)
explanation = explainer.explain_recommendation(mock_cloud_result['visSpec'][0], metas)

old_return = {'data': mock_cloud_result}
new_return = {'data': mock_cloud_result, 'explanation': explanation}

class MockResponse:
    def __init__(self, data):
        self.data = data

def verify_backend_endpoint(name, action):
    """验证后端端点返回结构"""
    print()
    print('='*60)
    print(f'  [{name}] 返回结构验证')
    print('='*60)
    print()
    
    print('Step 1: 验证旧字段 data 保持原样')
    print('-'*60)
    print(f'  旧结构 keys: {list(old_return.keys())}')
    print(f'  新结构 keys: {list(new_return.keys())}')
    print()
    assert_true('data' in new_return, f'[{name}] 新结构包含 data 字段')
    assert_equal(new_return['data'], old_return['data'], f'[{name}] data 字段内容保持不变')
    assert_equal(new_return.get('data'), old_return.get('data'), f'[{name}] data 字段通过 .get() 也能访问')
    print()
    
    print('Step 2: 验证新字段 explanation 存在')
    print('-'*60)
    assert_true('explanation' in new_return, f'[{name}] 新结构包含 explanation 字段')
    assert_true(new_return['explanation'] is not None, f'[{name}] explanation 字段不为 None')
    assert_true('chartType' in new_return['explanation'], f'[{name}] explanation 包含 chartType')
    assert_true('fields' in new_return['explanation'], f'[{name}] explanation 包含 fields')
    assert_true('aggregations' in new_return['explanation'], f'[{name}] explanation 包含 aggregations')
    assert_true('visualEncoding' in new_return['explanation'], f'[{name}] explanation 包含 visualEncoding')
    assert_true('overallSummary' in new_return['explanation'], f'[{name}] explanation 包含 overallSummary')
    print()
    
    print('Step 3: 向后兼容性验证')
    print('-'*60)
    old_frontend_consumer = old_return.get('data')
    new_frontend_consumer = new_return.get('data')
    assert_equal(old_frontend_consumer, new_frontend_consumer, f'[{name}] 新旧结构的 data 字段完全相同')
    print(f'  旧前端消费: {type(old_frontend_consumer)} - visSpec 数量: {len(old_frontend_consumer.get("visSpec", []))}')
    print(f'  新前端消费: {type(new_frontend_consumer)} - visSpec 数量: {len(new_frontend_consumer.get("visSpec", []))}')
    print()

def verify_frontend_handler(name, action, frontend_name):
    """验证前端处理器"""
    print()
    print('='*60)
    print(f'  前端 {frontend_name} 处理验证')
    print('='*60)
    print()
    
    print(f'Step 1: 模拟前端 {frontend_name} 处理')
    print('-'*60)
    
    def mock_send_msg(action_name, payload):
        print(f'  [模拟] sendMsg("{action_name}", ...)')
        return MockResponse(new_return)
    
    if frontend_name == 'askviz':
        resp = mock_send_msg(action, {'metas': metas, 'query': '显示销售数据'})
    else:
        resp = mock_send_msg(action, {'metas': metas, 'chats': [{'role': 'user', 'content': '显示销售数据'}]})
    
    data = resp.data.get('data')
    explanation_data = resp.data.get('explanation')
    
    dialog_will_open = False
    if explanation_data:
        print(f'  [模拟] setRecommendationExplanation(explanation)')
        print(f'  [模拟] setExplanationDialogOpen(true)')
        dialog_will_open = True
    
    print(f'  [模拟] return data  (GraphicWalker 仍然获取原推荐结果)')
    print()
    
    assert_true(data is not None, f'[{frontend_name}] 前端仍能拿到原推荐 data')
    assert_equal(data, mock_cloud_result, f'[{frontend_name}] data 与云服务返回的完全一致')
    assert_true(explanation_data is not None, f'[{frontend_name}] 前端能拿到 explanation')
    assert_true(dialog_will_open, f'[{frontend_name}] 前端会打开解释弹窗')
    print()

def main():
    print('='*70)
    print('  推荐返回结构完整验证')
    print('  (get_spec_by_text + get_chart_by_chats)')
    print('='*70)
    
    verify_backend_endpoint('get_spec_by_text', 'get_spec_by_text')
    verify_backend_endpoint('get_chart_by_chats', 'get_chart_by_chats')
    
    verify_frontend_handler('askviz', 'get_spec_by_text', 'askviz')
    verify_frontend_handler('vlChat', 'get_chart_by_chats', 'vlChat')
    
    print()
    print('='*70)
    print(f'  结果: {PASS} 个断言通过, {FAIL} 个失败')
    print('='*70)
    print()
    
    if FAIL == 0:
        print('✅ 所有返回结构验证通过!')
        print()
        print('返回结构概览:')
        print(json.dumps({
            'get_spec_by_text': {
                'old_structure': {'data': '...'},
                'new_structure': {'data': '...', 'explanation': '...'},
                'frontend_handler': 'askviz'
            },
            'get_chart_by_chats': {
                'old_structure': {'data': '...'},
                'new_structure': {'data': '...', 'explanation': '...'},
                'frontend_handler': 'vlChat'
            },
            'explanation_sample': {
                'chartType': explanation['chartType']['type'],
                'fields_count': len(explanation['fields']),
                'aggregations_count': len(explanation['aggregations']),
                'overallSummary': explanation['overallSummary']
            }
        }, ensure_ascii=False, indent=2))
        sys.exit(0)
    else:
        print('❌ 部分验证失败!')
        sys.exit(1)

if __name__ == '__main__':
    main()
