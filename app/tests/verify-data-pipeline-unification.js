#!/usr/bin/env node
/**
 * Data Pipeline Unification Verification Script
 * 
 * 验证目标：
 * 1. 客户端过滤：filterRows 使用 FilterStage.execute()
 * 2. 服务端 Computation：_get_datas / _get_datas_by_payload 使用 DataPipeline.execute()
 * 3. 预览渲染：get_single_chart_html_by_spec / _get_gw_preview_html 使用 DataPipeline
 * 4. 导出数据：exportUnified / _export_dataframe_by_payload 使用 DataPipeline
 */

const fs = require('fs');
const path = require('path');

const appRoot = path.join(__dirname, '..', 'src');
const pygRoot = path.join(__dirname, '..', '..', 'pygwalker');

const passed = [];
const failed = [];
const failures = [];

const assert = (condition, message) => {
    if (!condition) {
        throw new Error(message || 'Assertion failed');
    }
};

const runTest = (name, testFn) => {
    try {
        testFn();
        console.log(`  ✓ ${name}`);
        passed.push(name);
    } catch (e) {
        console.log(`  ✗ ${name}`);
        console.log(`    Error: ${e.message}`);
        failed.push(name);
        failures.push({ test: name, error: e.message });
    }
};

const readSource = (relativePath, isPyg = false) => {
    const fullPath = isPyg 
        ? path.join(pygRoot, relativePath)
        : path.join(appRoot, relativePath);
    return fs.readFileSync(fullPath, 'utf-8');
};

console.log('\n╔═══════════════════════════════════════════════════════════════╗');
console.log('║         Data Pipeline Unification Verification               ║');
console.log('╚═══════════════════════════════════════════════════════════════╝\n');

// ========== 1. 读取所有需要验证的源码 ==========
const filterTsSource = readSource('utils/filter.ts');
const exportDataframeTsSource = readSource('tools/exportDataframe.tsx');
const dataPipelineTsSource = readSource('dataSource/dataPipeline.ts');

const pygwalkerPySource = readSource('api/pygwalker.py', true);
const dataPipelinePySource = readSource('services/data_pipeline.py', true);

// ========== 2. 前端 TypeScript 管道验证 ==========
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('1. 前端 TypeScript: 数据管道定义验证');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

runTest('DataPipeline 类存在', () => {
    assert(dataPipelineTsSource.includes('export class DataPipeline'),
        '应该导出 DataPipeline 类');
});

runTest('FilterStage 类存在', () => {
    assert(dataPipelineTsSource.includes('export class FilterStage'),
        '应该导出 FilterStage 类');
});

runTest('SamplingStage 类存在', () => {
    assert(dataPipelineTsSource.includes('export class SamplingStage'),
        '应该导出 SamplingStage 类');
});

runTest('PipelineBuilder 类存在', () => {
    assert(dataPipelineTsSource.includes('export class PipelineBuilder'),
        '应该导出 PipelineBuilder 类');
});

runTest('createPipelineBuilder 便捷函数存在', () => {
    assert(dataPipelineTsSource.includes('export function createPipelineBuilder'),
        '应该导出 createPipelineBuilder 便捷函数');
});

runTest('createClientPipeline 便捷函数存在', () => {
    assert(dataPipelineTsSource.includes('export function createClientPipeline'),
        '应该导出 createClientPipeline 便捷函数');
});

runTest('createServerPipeline 便捷函数存在', () => {
    assert(dataPipelineTsSource.includes('export function createServerPipeline'),
        '应该导出 createServerPipeline 便捷函数');
});

runTest('DataPipeline.execute 方法存在', () => {
    assert(dataPipelineTsSource.includes('async execute('),
        'DataPipeline 应该有 execute 方法');
});

runTest('DataPipeline.executeBatch 方法存在', () => {
    assert(dataPipelineTsSource.includes('async executeBatch('),
        'DataPipeline 应该有 executeBatch 方法');
});

// ========== 3. 客户端过滤验证 ==========
console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('2. 客户端过滤: filterRows 验证');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

runTest('filter.ts 导入 FilterStage', () => {
    assert(filterTsSource.includes("import { FilterStage"),
        '应该导入 FilterStage 类');
});

runTest('filter.ts 创建 filterStage 实例', () => {
    assert(filterTsSource.includes('const filterStage = new FilterStage()'),
        '应该创建 FilterStage 实例');
});

runTest('filterRows 使用 FilterStage.execute', () => {
    assert(filterTsSource.includes('return filterStage.execute('),
        'filterRows 应该调用 FilterStage.execute()');
});

runTest('filterRows 不再手动过滤（验证：无直接 Array.filter 逻辑）', () => {
    const filterRowsBody = filterTsSource.substring(
        filterTsSource.indexOf('export const filterRows'),
        filterTsSource.indexOf('export const estimateFilteredCount')
    );
    assert(!filterRowsBody.includes('.filter(row =>'),
        'filterRows 不应该手动使用 Array.filter 进行条件过滤');
});

runTest('filterRows 仍然导出 matchCondition（向后兼容）', () => {
    assert(filterTsSource.includes('export const matchCondition'),
        '应该导出 matchCondition 函数以保持向后兼容');
});

// ========== 4. 导出数据验证（前端） ==========
console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('3. 导出数据: exportDataframe 验证');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

runTest('exportDataframe 导入 dataPipeline', () => {
    assert(exportDataframeTsSource.includes("import { createPipelineBuilder"),
        '应该导入 createPipelineBuilder');
    assert(exportDataframeTsSource.includes("createClientPipeline"),
        '应该导入 createClientPipeline');
    assert(exportDataframeTsSource.includes("createServerPipeline"),
        '应该导入 createServerPipeline');
});

runTest('exportDataframe 有 buildServerDataSource 函数', () => {
    assert(exportDataframeTsSource.includes('const buildServerDataSource = (): DataSource =>'),
        '应该有 buildServerDataSource 函数');
});

runTest('exportDataframe 有 exportUnified 函数', () => {
    assert(exportDataframeTsSource.includes('const exportUnified = async () =>'),
        '应该有 exportUnified 统一导出函数');
});

runTest('客户端模式使用 createClientPipeline', () => {
    const exportUnifiedBody = exportDataframeTsSource.substring(
        exportDataframeTsSource.indexOf('const exportUnified = async () =>'),
        exportDataframeTsSource.indexOf('await communicationStore')
    );
    assert(exportUnifiedBody.includes('createClientPipeline('),
        '客户端模式应该调用 createClientPipeline');
    assert(exportUnifiedBody.includes('pipeline.execute()'),
        '应该调用 pipeline.execute()');
});

runTest('服务端模式使用 PipelineBuilder', () => {
    const exportUnifiedBody = exportDataframeTsSource.substring(
        exportDataframeTsSource.indexOf('const exportUnified = async () =>'),
        exportDataframeTsSource.indexOf('await communicationStore')
    );
    assert(exportUnifiedBody.includes('createPipelineBuilder({'),
        '服务端模式应该调用 createPipelineBuilder');
    assert(exportUnifiedBody.includes('builder.withFilter('),
        '应该调用 builder.withFilter()');
    assert(exportUnifiedBody.includes('builder.build()'),
        '应该调用 builder.build()');
});

runTest('导出统一使用 export_dataframe_by_data', () => {
    assert(exportDataframeTsSource.includes('exportUnified'),
        '应该有 exportUnified 函数');
    assert(exportDataframeTsSource.includes('onClick: onClick'),
        'onClick 应该使用统一的 onClick 函数');
    assert(!exportDataframeTsSource.includes('communicationStore.comm?.sendMsg("export_dataframe_by_payload"'),
        '不应该直接调用 export_dataframe_by_payload（应通过管道统一处理）');
    assert(!exportDataframeTsSource.includes('communicationStore.comm?.sendMsg("export_dataframe_by_sql"'),
        '不应该直接调用 export_dataframe_by_sql（应通过管道统一处理）');
});

// ========== 5. 后端 Python 管道验证 ==========
console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('4. 后端 Python: 数据管道定义验证');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

runTest('DataPipeline 类存在 (Python)', () => {
    assert(dataPipelinePySource.includes('class DataPipeline:'),
        '应该有 DataPipeline 类');
});

runTest('FilterStage 类存在 (Python)', () => {
    assert(dataPipelinePySource.includes('class FilterStage(PipelineStage):'),
        '应该有 FilterStage 类');
});

runTest('SamplingStage 类存在 (Python)', () => {
    assert(dataPipelinePySource.includes('class SamplingStage(PipelineStage):'),
        '应该有 SamplingStage 类');
});

runTest('PipelineBuilder 类存在 (Python)', () => {
    assert(dataPipelinePySource.includes('class PipelineBuilder:'),
        '应该有 PipelineBuilder 类');
});

runTest('create_pipeline_builder 便捷函数存在 (Python)', () => {
    assert(dataPipelinePySource.includes('def create_pipeline_builder'),
        '应该有 create_pipeline_builder 便捷函数');
});

// ========== 6. 服务端 Computation 回调验证 ==========
console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('5. 服务端 Computation: 回调函数验证');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

runTest('pygwalker.py 导入 data_pipeline', () => {
    assert(pygwalkerPySource.includes('from pygwalker.services.data_pipeline import create_pipeline_builder'),
        '应该导入 create_pipeline_builder');
});

runTest('有 _create_pipeline_with_filters 函数', () => {
    assert(pygwalkerPySource.includes('def _create_pipeline_with_filters'),
        '应该有 _create_pipeline_with_filters 辅助函数');
});

runTest('_get_datas 使用 DataPipeline.execute', () => {
    const getDatasBody = pygwalkerPySource.substring(
        pygwalkerPySource.indexOf('def _get_datas(data: Dict[str, Any]):'),
        pygwalkerPySource.indexOf('def _get_datas_by_payload')
    );
    assert(getDatasBody.includes('pipeline.execute(sql=sql)'),
        '_get_datas 应该调用 pipeline.execute(sql=sql)');
    assert(!getDatasBody.includes('self.data_parser.get_datas_by_sql(sql)'),
        '_get_datas 不应该直接调用 data_parser.get_datas_by_sql');
});

runTest('_get_datas_by_payload 使用 DataPipeline.execute', () => {
    const getDatasBody = pygwalkerPySource.substring(
        pygwalkerPySource.indexOf('def _get_datas_by_payload(data: Dict[str, Any]):'),
        pygwalkerPySource.indexOf('def _batch_get_datas_by_sql')
    );
    assert(getDatasBody.includes('pipeline.execute(payload=data["payload"])'),
        '_get_datas_by_payload 应该调用 pipeline.execute(payload=...)');
    assert(!getDatasBody.includes('self.data_parser.get_datas_by_payload'),
        '_get_datas_by_payload 不应该直接调用 data_parser.get_datas_by_payload');
});

runTest('_batch_get_datas_by_sql 使用 DataPipeline.executeBatch', () => {
    const getDatasBody = pygwalkerPySource.substring(
        pygwalkerPySource.indexOf('def _batch_get_datas_by_sql'),
        pygwalkerPySource.indexOf('def _batch_get_datas_by_payload')
    );
    assert(getDatasBody.includes('pipeline.execute_batch'),
        '_batch_get_datas_by_sql 应该调用 pipeline.execute_batch');
});

runTest('_batch_get_datas_by_payload 使用 DataPipeline.executeBatch', () => {
    const getDatasBody = pygwalkerPySource.substring(
        pygwalkerPySource.indexOf('def _batch_get_datas_by_payload'),
        pygwalkerPySource.indexOf('def _export_dataframe_by_payload')
    );
    assert(getDatasBody.includes('pipeline.execute_batch'),
        '_batch_get_datas_by_payload 应该调用 pipeline.execute_batch');
});

// ========== 7. 预览渲染验证 ==========
console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('6. 预览渲染: 预览 HTML 生成验证');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

runTest('get_single_chart_html_by_spec 使用 PipelineBuilder', () => {
    const funcBody = pygwalkerPySource.substring(
        pygwalkerPySource.indexOf('def get_single_chart_html_by_spec'),
        pygwalkerPySource.indexOf('return render_gw_chart_preview_html')
    );
    assert(funcBody.includes('create_pipeline_builder(self.data_parser)'),
        '应该使用 create_pipeline_builder');
    assert(funcBody.includes('builder.with_filter('),
        '应该调用 builder.with_filter()');
    assert(funcBody.includes('builder.with_scatter_sampling()'),
        '应该调用 builder.with_scatter_sampling()');
    assert(funcBody.includes('pipeline.execute(payload=workflow)'),
        '应该调用 pipeline.execute()');
});

runTest('get_single_chart_html_by_spec 新增 filters 参数', () => {
    const funcBody = pygwalkerPySource.substring(
        pygwalkerPySource.indexOf('def get_single_chart_html_by_spec'),
        pygwalkerPySource.indexOf('return render_gw_chart_preview_html')
    );
    assert(funcBody.includes('filters'),
        '应该有 filters 参数');
    assert(funcBody.includes('filter_logic'),
        '应该有 filter_logic 参数');
    assert(funcBody.includes('builder.with_filter(filters, filter_logic)'),
        '应该调用 builder.with_filter(filters, filter_logic)');
});

runTest('_get_gw_preview_html 使用 PipelineBuilder', () => {
    const funcBody = pygwalkerPySource.substring(
        pygwalkerPySource.indexOf('def _get_gw_preview_html'),
        pygwalkerPySource.indexOf('html = render_gw_preview_html')
    );
    assert(funcBody.includes('create_pipeline_builder(self.data_parser)'),
        '应该使用 create_pipeline_builder');
    assert(funcBody.includes('is_scatter_plot_spec(spec)'),
        '应该检查散点图');
    assert(funcBody.includes('builder.with_scatter_sampling()'),
        '应该调用 builder.with_scatter_sampling()');
    assert(funcBody.includes('pipeline.execute(payload=workflow)'),
        '应该调用 pipeline.execute()');
});

runTest('_get_gw_chart_preview_html 使用 PipelineBuilder', () => {
    const funcBody = pygwalkerPySource.substring(
        pygwalkerPySource.indexOf('def _get_gw_chart_preview_html'),
        pygwalkerPySource.indexOf('return render_gw_chart_preview_html')
    );
    assert(funcBody.includes('create_pipeline_builder(self.data_parser)'),
        '应该使用 create_pipeline_builder');
    assert(funcBody.includes('builder.with_scatter_sampling()'),
        '应该调用 builder.with_scatter_sampling()');
    assert(funcBody.includes('pipeline.execute(payload='),
        '应该调用 pipeline.execute()');
});

// ========== 8. 导出数据验证（后端） ==========
console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('7. 导出数据: 后端导出函数验证');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

runTest('_export_dataframe_by_payload 使用 DataPipeline', () => {
    const funcBody = pygwalkerPySource.substring(
        pygwalkerPySource.indexOf('def _export_dataframe_by_payload'),
        pygwalkerPySource.indexOf('def _export_dataframe_by_sql')
    );
    assert(funcBody.includes('_create_pipeline_with_filters(data)'),
        '应该调用 _create_pipeline_with_filters');
    assert(funcBody.includes('pipeline.execute(payload=data["payload"])'),
        '应该调用 pipeline.execute(payload=...)');
    assert(!funcBody.includes('self.data_parser.get_datas_by_payload(data["payload"])'),
        '不应该直接调用 data_parser.get_datas_by_payload');
});

runTest('_export_dataframe_by_sql 使用 DataPipeline', () => {
    const funcBody = pygwalkerPySource.substring(
        pygwalkerPySource.indexOf('def _export_dataframe_by_sql'),
        pygwalkerPySource.indexOf('def _export_dataframe_by_data')
    );
    assert(funcBody.includes('_create_pipeline_with_filters(data)'),
        '应该调用 _create_pipeline_with_filters');
    assert(funcBody.includes('pipeline.execute(sql=sql)'),
        '应该调用 pipeline.execute(sql=sql)');
    assert(!funcBody.includes('self.data_parser.get_datas_by_sql(sql)'),
        '不应该直接调用 data_parser.get_datas_by_sql');
});

// ========== 9. 统一入口验证 ==========
console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('8. 统一入口: 所有场景调用同一管道验证');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

const pipelineExecutions = [
    { name: '前端过滤', source: filterTsSource, pattern: 'filterStage.execute(' },
    { name: '前端导出', source: exportDataframeTsSource, pattern: 'pipeline.execute(' },
    { name: '服务端 Computation (SQL)', source: pygwalkerPySource, pattern: 'pipeline.execute(sql=' },
    { name: '服务端 Computation (Payload)', source: pygwalkerPySource, pattern: 'pipeline.execute(payload=' },
    { name: '服务端预览', source: pygwalkerPySource, pattern: 'pipeline.execute(payload=workflow)' },
    { name: '服务端导出', source: pygwalkerPySource, pattern: 'pipeline.execute(payload=data["payload"])' },
];

for (const item of pipelineExecutions) {
    runTest(`${item.name}: 使用 pipeline.execute()`, () => {
        assert(item.source.includes(item.pattern),
            `${item.name} 应该调用 ${item.pattern}`);
    });
}

// ========== 10. 前后端一致性验证 ==========
console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('9. 前后端一致性: 过滤逻辑验证');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

const filterConditions = [
    { ts: "case 'range':", py: 'if condition_type == "range":' },
    { ts: "case 'temporal range':", py: 'elif condition_type == "temporal range":' },
    { ts: "case 'one of':", py: 'elif condition_type == "one of":' },
    { ts: "case 'not in':", py: 'elif condition_type == "not in":' },
    { ts: "case 'contains':", py: 'elif condition_type == "contains":' },
    { ts: "case 'equals':", py: 'elif condition_type == "equals":' },
    { ts: "case 'greater than':", py: 'elif condition_type == "greater than":' },
    { ts: "case 'less than':", py: 'elif condition_type == "less than":' },
];

for (const cond of filterConditions) {
    runTest(`过滤条件 ${cond.ts.replace("case '", "").replace("':", "")} 前后端都支持`, () => {
        assert(dataPipelineTsSource.includes(cond.ts),
            `TypeScript 应该支持 ${cond.ts}`);
        assert(dataPipelinePySource.includes(cond.py),
            `Python 应该支持 ${cond.py}`);
    });
}

// ========== 结果输出 ==========
console.log('\n╔═══════════════════════════════════════════════════════════════╗');
console.log(`║              Test Results: ${passed.length.toString().padStart(2)} passed, ${failed.length.toString().padStart(2)} failed                   ║`);
console.log('╚═══════════════════════════════════════════════════════════════╝\n');

if (failed.length > 0) {
    console.log('Failed tests:');
    failures.forEach(f => {
        console.log(`  ✗ ${f.test}`);
        console.log(`    Error: ${f.error}`);
    });
    process.exit(1);
}

console.log('✅ All data pipeline unification verifications passed!');
console.log('');
console.log('总结: 以下所有场景都已统一使用 DataPipeline 入口:');
console.log('  ┌─────────────────────────────────────────────────────────────┐');
console.log('  │  1. 客户端过滤: filterRows → FilterStage.execute()          │');
console.log('  │  2. 服务端 Computation: _get_datas → DataPipeline.execute() │');
console.log('  │  3. 预览渲染: get_single_chart_html_by_spec → Pipeline      │');
console.log('  │  4. 导出数据: exportUnified / _export_dataframe_by_payload  │');
console.log('  │     → DataPipeline.execute()                               │');
console.log('  └─────────────────────────────────────────────────────────────┘');

process.exit(0);
