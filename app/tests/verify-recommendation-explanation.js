const fs = require('fs');
const path = require('path');

const APP_PATH = path.resolve(__dirname, '..', 'src');

function readFile(filePath) {
    return fs.readFileSync(filePath, 'utf-8');
}

function assert(condition, message) {
    if (!condition) {
        console.error('FAIL: ' + message);
        process.exit(1);
    }
    console.log('PASS: ' + message);
}

function assertContains(content, substring, message) {
    assert(content.includes(substring), message);
}

console.log('============================================================');
console.log('Frontend Static Verification: Recommendation Explanation');
console.log('============================================================');
console.log('');

const indexTsxContent = readFile(path.join(APP_PATH, 'index.tsx'));
const explanationComponentContent = readFile(path.join(APP_PATH, 'components', 'recommendationExplanation', 'index.tsx'));

console.log('Verifying index.tsx...');
console.log('');

assertContains(indexTsxContent, 'import RecommendationExplanation', 'index.tsx imports RecommendationExplanation');

assertContains(indexTsxContent, 'getRecommendationExplanation', 'enhanceAPI contains getRecommendationExplanation');

assertContains(indexTsxContent, 'get_recommendation_explanation', 'calls get_recommendation_explanation via sendMsg');

assertContains(indexTsxContent, 'resp?.data.explanation', 'askviz accesses explanation from response');

assertContains(indexTsxContent, 'setRecommendationExplanation', 'state is updated with explanation');

assertContains(indexTsxContent, '<RecommendationExplanation', 'RecommendationExplanation component is rendered');

assertContains(indexTsxContent, 'explanation={recommendationExplanation', 'explanation prop is passed to component');

console.log('');
console.log('Verifying RecommendationExplanation component...');
console.log('');

assertContains(explanationComponentContent, 'export interface RecommendationExplanationData', 'has RecommendationExplanationData interface');

assertContains(explanationComponentContent, '图表类型', 'has chart type tab');

assertContains(explanationComponentContent, '字段选择', 'has fields tab');

assertContains(explanationComponentContent, '聚合方式', 'has aggregation tab');

assertContains(explanationComponentContent, '数据洞察', 'has insights tab');

assertContains(explanationComponentContent, '总体摘要', 'has overall summary section');

assertContains(explanationComponentContent, '可视编码', 'has visual encoding section');

assertContains(explanationComponentContent, 'explanation.chartType', 'uses explanation.chartType');

assertContains(explanationComponentContent, 'explanation.fields', 'uses explanation.fields');

assertContains(explanationComponentContent, 'explanation.aggregations', 'uses explanation.aggregations');

assertContains(explanationComponentContent, 'explanation.visualEncoding', 'uses explanation.visualEncoding');

assertContains(explanationComponentContent, 'explanation.overallSummary', 'uses explanation.overallSummary');

assertContains(explanationComponentContent, 'explanation.dataInsights', 'uses explanation.dataInsights');

console.log('');
console.log('============================================================');
console.log('All frontend static verification passed!');
console.log('============================================================');
console.log('');
