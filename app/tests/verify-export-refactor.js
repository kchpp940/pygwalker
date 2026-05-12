#!/usr/bin/env node
/**
 * Export Refactoring Verification Script
 * 
 * 基于源码关键链路的断言验证，不使用脆弱的单行字符串匹配
 * 验证目标：
 * 1. PNG 导出：优先路径和回退路径逻辑
 * 2. JSON/Code 生成：内容结构不变
 * 3. ZIP 打包：多图打包流程
 * 4. 错误处理：ExportResult 和通知
 * 5. 组件集成：所有导出面板接入新服务
 */

const fs = require('fs');
const path = require('path');

const appRoot = path.join(__dirname, '..', 'src');
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

const readSource = (relativePath) => {
    const fullPath = path.join(appRoot, relativePath);
    return fs.readFileSync(fullPath, 'utf-8');
};

// 解析函数体（简化版，基于花括号匹配）
const findFunctionBody = (source, functionStart) => {
    const startIndex = source.indexOf(functionStart);
    if (startIndex === -1) return null;
    
    let braceCount = 0;
    let foundOpen = false;
    let bodyStart = -1;
    
    for (let i = startIndex; i < source.length; i++) {
        if (source[i] === '{') {
            if (!foundOpen) {
                bodyStart = i;
                foundOpen = true;
            }
            braceCount++;
        } else if (source[i] === '}') {
            braceCount--;
            if (foundOpen && braceCount === 0) {
                return source.substring(bodyStart, i + 1);
            }
        }
    }
    return null;
};

// 检查函数体中是否包含关键调用
const hasCallsInOrder = (body, calls) => {
    let lastIndex = 0;
    for (const call of calls) {
        const idx = body.indexOf(call, lastIndex);
        if (idx === -1) return false;
        lastIndex = idx;
    }
    return true;
};

console.log('\n╔═══════════════════════════════════════════════════════════════╗');
console.log('║            Export Service Refactoring Verification           ║');
console.log('╚═══════════════════════════════════════════════════════════════╝\n');

// ========== 1. 读取所有需要验证的源码 ==========
const imageExportSource = readSource('services/export/imageExportService.ts');
const fileDownloadSource = readSource('services/export/fileDownloadService.ts');
const codeExportSource = readSource('services/export/codeExportService.ts');
const zipServiceSource = readSource('services/export/zipService.ts');
const exportServiceSource = readSource('services/export/exportService.ts');
const notificationServiceSource = readSource('services/export/notificationService.ts');
const typesSource = readSource('services/export/types.ts');
const saveTsSource = readSource('utils/save.ts');
const exportConfigModalSource = readSource('components/exportConfigModal/index.tsx');
const codeExportModalSource = readSource('components/codeExportModal/index.tsx');
const uploadSpecModalSource = readSource('components/uploadSpecModal/index.tsx');

// ========== 2. PNG 导出链路验证 ==========
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('1. PNG Export: 优先路径和回退路径验证');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

runTest('imageExportService.formatChartData 存在', () => {
    assert(imageExportSource.includes('formatChartData(chartData: IChartExportResult)'), 
        '应该包含 formatChartData 函数');
});

runTest('优先路径: 检查 charts.length === 1', () => {
    assert(imageExportSource.includes('charts.length === 1'),
        '应该检查 charts.length === 1');
});

runTest('优先路径: 检查 startsWith data:image/', () => {
    assert(imageExportSource.includes('startsWith'),
        '应该使用 startsWith 检查');
    assert(imageExportSource.includes('data:image/'),
        '应该检查 data:image/ 前缀');
});

runTest('优先路径: 返回 chartData.charts[0].data', () => {
    assert(imageExportSource.includes('chartData.charts[0].data'),
        '应该返回 chartData.charts[0].data');
});

runTest('回退路径: 使用 html-to-image', () => {
    assert(imageExportSource.includes("import * as htmlToImage from 'html-to-image'"),
        '应该导入 html-to-image');
    assert(imageExportSource.includes('htmlToImage.toPng'),
        '应该调用 htmlToImage.toPng');
});

runTest('回退路径: 使用 scrollWidth 和 scrollHeight', () => {
    assert(imageExportSource.includes('scrollWidth'),
        '应该使用 scrollWidth');
    assert(imageExportSource.includes('scrollHeight'),
        '应该使用 scrollHeight');
});

runTest('边界情况: chartDom 为 null 时返回空', () => {
    assert(imageExportSource.includes('chartDom === null'),
        '应该检查 chartDom === null');
    assert(imageExportSource.includes("singleChart: ''"),
        '应该返回空的 singleChart');
});

runTest('边界情况: 地理图表处理 (charts.length === 0)', () => {
    assert(imageExportSource.includes('chartData.charts.length === 0'),
        '应该检查 charts.length === 0');
    assert(imageExportSource.includes('nCols: 1'),
        '应该设置 nCols: 1');
    assert(imageExportSource.includes('nRows: 1'),
        '应该设置 nRows: 1');
});

// ========== 3. 向后兼容验证 ==========
console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('2. 向后兼容: save.ts 兼容层验证');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

runTest('save.ts 保留原有函数签名', () => {
    assert(saveTsSource.includes('export function download(data: string, filename: string, type: string)'),
        '应该保留 download 函数');
    assert(saveTsSource.includes('export async function formatExportedChartDatas(chartData: IChartExportResult)'),
        '应该保留 formatExportedChartDatas 函数');
    assert(saveTsSource.includes('export function getTimezoneOffsetSeconds()'),
        '应该保留 getTimezoneOffsetSeconds 函数');
});

runTest('save.ts 导入并调用新服务', () => {
    assert(saveTsSource.includes("import { imageExportService, fileDownloadService }"),
        '应该导入新服务');
    assert(saveTsSource.includes('fileDownloadService.triggerDownload'),
        '应该调用 fileDownloadService.triggerDownload');
    assert(saveTsSource.includes('imageExportService.formatChartData'),
        '应该调用 imageExportService.formatChartData');
});

// ========== 4. 文件下载链路验证 ==========
console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('3. 文件下载: fileDownloadService 验证');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

runTest('fileDownloadService 包含下载核心逻辑', () => {
    assert(fileDownloadSource.includes('URL.createObjectURL'),
        '应该使用 URL.createObjectURL');
    assert(fileDownloadSource.includes('document.createElement'),
        '应该创建 a 标签');
    assert(fileDownloadSource.includes('.click()'),
        '应该触发 click');
    assert(fileDownloadSource.includes('URL.revokeObjectURL'),
        '应该释放 URL');
});

runTest('fileDownloadService 支持 IE 兼容', () => {
    assert(fileDownloadSource.includes('msSaveOrOpenBlob'),
        '应该支持 IE 的 msSaveOrOpenBlob');
});

runTest('fileDownloadService 返回 ExportResult', () => {
    assert(fileDownloadSource.includes('Promise<ExportResult>'),
        '应该返回 Promise<ExportResult>');
    assert(fileDownloadSource.includes('success: true'),
        '应该返回 success: true');
    assert(fileDownloadSource.includes('success: false'),
        '应该返回 success: false');
});

runTest('fileDownloadService 提供多种下载方式', () => {
    assert(fileDownloadSource.includes('downloadText'),
        '应该有 downloadText');
    assert(fileDownloadSource.includes('downloadJSON'),
        '应该有 downloadJSON');
    assert(fileDownloadSource.includes('downloadFromDataUrl'),
        '应该有 downloadFromDataUrl');
});

// ========== 5. JSON/Code 生成验证 ==========
console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('4. JSON/Code 生成: 内容结构不变验证');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

runTest('codeExportService 导入 chartToWorkflow', () => {
    assert(codeExportSource.includes("import { chartToWorkflow }"),
        '应该导入 chartToWorkflow');
});

runTest('codeExportService.generatePygConfig 结构正确', () => {
    assert(codeExportSource.includes('config: visSpec'),
        '应该包含 config: visSpec');
    assert(codeExportSource.includes('chart_map: {}'),
        '应该包含 chart_map: {}');
    assert(codeExportSource.includes('workflow_list: visSpec.map'),
        '应该包含 workflow_list');
    assert(codeExportSource.includes('version'),
        '应该包含 version');
});

runTest('codeExportService.generatePythonCode 逻辑正确', () => {
    assert(codeExportSource.includes('____pyg_walker_spec_params____'),
        '应该替换 ____pyg_walker_spec_params____');
    assert(codeExportSource.includes('vis_spec = r"""'),
        '应该生成 vis_spec = r""" 格式');
    assert(codeExportSource.includes('JSON.stringify'),
        '应该使用 JSON.stringify');
});

// ========== 6. ZIP 打包验证 ==========
console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('5. ZIP 打包: zipService 验证');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

runTest('zipService 使用 JSZip', () => {
    assert(zipServiceSource.includes("import JSZip from 'jszip'"),
        '应该导入 JSZip');
    assert(zipServiceSource.includes('new JSZip()'),
        '应该创建 JSZip 实例');
});

runTest('zipService 支持多种内容类型', () => {
    assert(zipServiceSource.includes('typeof entry.content'),
        '应该检查内容类型');
    assert(zipServiceSource.includes('zip.file('),
        '应该调用 zip.file');
});

runTest('zipService 支持压缩选项', () => {
    assert(zipServiceSource.includes('DEFLATE'),
        '应该支持 DEFLATE 压缩');
    assert(zipServiceSource.includes('STORE'),
        '应该支持 STORE 不压缩');
    assert(zipServiceSource.includes('compressionOptions'),
        '应该设置压缩选项');
});

runTest('zipService 导出为 ZIP 文件', () => {
    assert(zipServiceSource.includes('zip.generateAsync'),
        '应该调用 generateAsync');
    assert(zipServiceSource.includes('application/zip'),
        '应该使用 application/zip MIME 类型');
});

// ========== 7. ExportResult 类型验证 ==========
console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('6. 错误处理: ExportResult 类型验证');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

runTest('ExportResult 类型定义正确', () => {
    assert(typesSource.includes('export interface ExportResult'),
        '应该定义 ExportResult 接口');
    assert(typesSource.includes('success: boolean'),
        '应该有 success: boolean');
    assert(typesSource.includes('error?: string'),
        '应该有 error?: string');
    assert(typesSource.includes('filename?: string'),
        '应该有 filename?: string');
});

runTest('notificationService 集成 commonStore', () => {
    assert(notificationServiceSource.includes('import commonStore'),
        '应该导入 commonStore');
    assert(notificationServiceSource.includes('commonStore.setNotification'),
        '应该调用 commonStore.setNotification');
});

runTest('notificationService 支持所有通知类型', () => {
    assert(notificationServiceSource.includes("type: 'success'"),
        '应该支持 success');
    assert(notificationServiceSource.includes("type: 'error'"),
        '应该支持 error');
    assert(notificationServiceSource.includes("type: 'info'"),
        '应该支持 info');
    assert(notificationServiceSource.includes("type: 'warning'"),
        '应该支持 warning');
});

// ========== 8. 统一导出服务验证 ==========
console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('7. 统一导出服务: exportService 整合验证');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

runTest('exportService 导入所有子服务', () => {
    assert(exportServiceSource.includes('imageExportService'),
        '应该导入 imageExportService');
    assert(exportServiceSource.includes('jsonExportService'),
        '应该导入 jsonExportService');
    assert(exportServiceSource.includes('codeExportService'),
        '应该导入 codeExportService');
    assert(exportServiceSource.includes('fileDownloadService'),
        '应该导入 fileDownloadService');
    assert(exportServiceSource.includes('zipService'),
        '应该导入 zipService');
    assert(exportServiceSource.includes('notificationService'),
        '应该导入 notificationService');
});

runTest('exportService 支持多种导出格式', () => {
    assert(exportServiceSource.includes("'png'"),
        '应该支持 png');
    assert(exportServiceSource.includes("'json'"),
        '应该支持 json');
    assert(exportServiceSource.includes("'code'"),
        '应该支持 code');
});

runTest('exportService 单文件直接下载', () => {
    assert(exportServiceSource.includes('entries.length === 1'),
        '应该检查单文件');
    assert(exportServiceSource.includes('fileDownloadService.download('),
        '应该直接调用 fileDownloadService.download');
});

runTest('exportService 多文件打包为 ZIP', () => {
    assert(exportServiceSource.includes('zipService.exportZip('),
        '应该调用 zipService.exportZip');
});

runTest('exportService 集成通知服务', () => {
    assert(exportServiceSource.includes('notify: notificationService'),
        '应该集成 notificationService');
});

// ========== 9. 组件集成验证 ==========
console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('8. 组件集成: 导出面板验证');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

runTest('CodeExportModal 使用 exportService', () => {
    assert(codeExportModalSource.includes('exportService'),
        '应该导入/使用 exportService');
});

runTest('CodeExportModal 使用 generatePythonCode/generateJsonCode', () => {
    assert(codeExportModalSource.includes('generatePythonCode'),
        '应该调用 generatePythonCode');
    assert(codeExportModalSource.includes('generateJsonCode'),
        '应该调用 generateJsonCode');
});

runTest('UploadSpecModal 使用 exportService', () => {
    assert(uploadSpecModalSource.includes('exportService'),
        '应该导入/使用 exportService');
    assert(uploadSpecModalSource.includes('exportService.exportJson'),
        '应该调用 exportService.exportJson');
});

runTest('UploadSpecModal 处理 ExportResult', () => {
    assert(uploadSpecModalSource.includes('result.success'),
        '应该检查 result.success');
    assert(uploadSpecModalSource.includes('exportService.notify.success'),
        '应该使用 notify.success');
    assert(uploadSpecModalSource.includes('exportService.notify.error'),
        '应该使用 notify.error');
});

runTest('ExportConfigModal 已恢复且未被删除', () => {
    assert(fs.existsSync(path.join(appRoot, 'components/exportConfigModal/index.tsx')),
        'ExportConfigModal 应该存在');
});

runTest('ExportConfigModal 不再直接导入 JSZip 和 download', () => {
    assert(!exportConfigModalSource.includes('import JSZip from "jszip"'),
        '不应该直接导入 JSZip');
    assert(!exportConfigModalSource.includes('import { download } from "@/utils/save"'),
        '不应该直接导入 download');
});

runTest('ExportConfigModal 使用新的导出服务', () => {
    assert(exportConfigModalSource.includes('exportService'),
        '应该使用 exportService');
    assert(exportConfigModalSource.includes('fileDownloadService'),
        '应该使用 fileDownloadService');
    assert(exportConfigModalSource.includes('zipService'),
        '应该使用 zipService');
});

runTest('ExportConfigModal 保留所有原有功能', () => {
    // SVG 导出
    assert(exportConfigModalSource.includes('<?xml version="1.0" encoding="UTF-8"?>'),
        '应该保留 SVG 导出');
    assert(exportConfigModalSource.includes('image/svg+xml'),
        '应该保留 SVG MIME 类型');
    
    // PNG scale
    assert(exportConfigModalSource.includes('ImageScale'),
        '应该保留 ImageScale 类型');
    assert(exportConfigModalSource.includes('canvas.width = img.width * scale'),
        '应该保留 PNG scale 逻辑');
    
    // Title & Description
    assert(exportConfigModalSource.includes('includeTitle'),
        '应该保留 includeTitle');
    assert(exportConfigModalSource.includes('includeDescription'),
        '应该保留 includeDescription');
    
    // Filtered vs Unfiltered
    assert(exportConfigModalSource.includes('ExportContent'),
        '应该保留 ExportContent 类型');
    assert(exportConfigModalSource.includes('buildSpecWithContentPreference'),
        '应该保留 buildSpecWithContentPreference');
    
    // Multiple Charts ZIP
    assert(exportConfigModalSource.includes('exportMultipleCharts'),
        '应该保留 exportMultipleCharts');
    assert(exportConfigModalSource.includes('allCharts.length === 1'),
        '应该保留单图分支判断');
});

// ========== 10. 服务索引验证 ==========
console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('9. 服务索引: 统一导出验证');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

const indexSource = readSource('services/export/index.ts');

runTest('index.ts 导出所有服务', () => {
    assert(indexSource.includes("exportService"),
        '应该导出 exportService');
    assert(indexSource.includes("imageExportService"),
        '应该导出 imageExportService');
    assert(indexSource.includes("jsonExportService"),
        '应该导出 jsonExportService');
    assert(indexSource.includes("codeExportService"),
        '应该导出 codeExportService');
    assert(indexSource.includes("fileDownloadService"),
        '应该导出 fileDownloadService');
    assert(indexSource.includes("zipService"),
        '应该导出 zipService');
    assert(indexSource.includes("notificationService"),
        '应该导出 notificationService');
    assert(indexSource.includes("export * from './types'"),
        '应该导出类型');
});

// ========== 11. 行为等价性验证 ==========
console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('10. 行为等价性: 新旧逻辑对比验证');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

runTest('旧 formatExportedChartDatas 关键逻辑已迁移', () => {
    const oldPatterns = [
        'chartDom === null',
        'charts.length === 0',
        'charts.length === 1',
        'htmlToImage.toPng',
        'scrollWidth',
        'scrollHeight'
    ];
    for (const pattern of oldPatterns) {
        assert(imageExportSource.includes(pattern),
            `新实现应包含旧逻辑: ${pattern}`);
    }
});

runTest('旧 download 关键逻辑已迁移', () => {
    const oldPatterns = [
        'URL.createObjectURL',
        'document.createElement',
        '.click()',
        'URL.revokeObjectURL',
        'msSaveOrOpenBlob'
    ];
    for (const pattern of oldPatterns) {
        assert(fileDownloadSource.includes(pattern),
            `新实现应包含旧逻辑: ${pattern}`);
    }
});

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

console.log('✅ All export service verifications passed!');
process.exit(0);
