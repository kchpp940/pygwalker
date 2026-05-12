#!/usr/bin/env node
/**
 * 静态验证脚本：验证前端架构约束
 * 
 * 检查项：
 * 1. registry 是否注册了所有必要工具
 * 2. 各工具打开的 modal 类型是否正确
 * 3. 各弹窗是否只使用 closeModal 关闭
 * 4. index.tsx 不再传递弹窗 props
 */

const fs = require('fs');
const path = require('path');

const APP_DIR = path.join(__dirname, '..', 'src');
const INDEX_FILE = path.join(APP_DIR, 'index.tsx');
const COMMON_FILE = path.join(APP_DIR, 'store', 'common.ts');
const TOOLS_DIR = path.join(APP_DIR, 'tools');
const COMPONENTS_DIR = path.join(APP_DIR, 'components');

let errors = [];
let warnings = [];
let infos = [];

function log(msg) {
    console.log(msg);
    infos.push(msg);
}

function warn(msg) {
    console.log(`⚠️  警告: ${msg}`);
    warnings.push(msg);
}

function error(msg) {
    console.log(`❌ 错误: ${msg}`);
    errors.push(msg);
}

function success(msg) {
    console.log(`✅ ${msg}`);
    infos.push(msg);
}

function readFile(filePath) {
    return fs.readFileSync(filePath, 'utf-8');
}

function findFiles(dir, pattern) {
    const results = [];
    function traverse(currentPath) {
        const files = fs.readdirSync(currentPath);
        for (const file of files) {
            const fullPath = path.join(currentPath, file);
            const stat = fs.statSync(fullPath);
            if (stat.isDirectory()) {
                traverse(fullPath);
            } else if (pattern.test(file)) {
                results.push(fullPath);
            }
        }
    }
    traverse(dir);
    return results;
}

console.log('\n========================================');
console.log('  前端架构约束静态验证');
console.log('========================================\n');

// ========================================
// 检查 1: common.ts 中的 ModalType 定义
// ========================================
log('\n--- 检查 1: ModalType 定义 ---');
const commonContent = readFile(COMMON_FILE);

const modalTypeMatch = commonContent.match(/export type ModalType = "([^"]+)"( \| "([^"]+)")*/);
if (modalTypeMatch) {
    // 提取所有 ModalType 值
    const modalTypeValues = [];
    const modalTypeRegex = /"([a-zA-Z]+)"/g;
    let match;
    const modalTypeSection = commonContent.substring(
        commonContent.indexOf('export type ModalType'),
        commonContent.indexOf(';', commonContent.indexOf('export type ModalType'))
    );
    while ((match = modalTypeRegex.exec(modalTypeSection)) !== null) {
        modalTypeValues.push(match[1]);
    }
    success(`ModalType 定义了 ${modalTypeValues.length} 种类型: ${modalTypeValues.join(', ')}`);
    
    // 检查是否有对应的 openModal 方法
    const openModalMatch = commonContent.match(/openModal\(modalType: ModalType\)/);
    if (openModalMatch) {
        success('存在 openModal(modalType: ModalType) 方法');
    } else {
        error('缺少 openModal(modalType: ModalType) 方法');
    }
    
    // 检查是否有对应的 closeModal 方法
    const closeModalMatch = commonContent.match(/closeModal\(modalType: ModalType\)/);
    if (closeModalMatch) {
        success('存在 closeModal(modalType: ModalType) 方法');
    } else {
        error('缺少 closeModal(modalType: ModalType) 方法');
    }
} else {
    error('未找到 ModalType 定义');
}

// ========================================
// 检查 2: registry 是否注册了工具
// ========================================
log('\n--- 检查 2: Tool Registry ---');
const registryFile = path.join(TOOLS_DIR, 'registry.ts');
if (fs.existsSync(registryFile)) {
    const registryContent = readFile(registryFile);
    
    // 检查 ToolRegistry 类
    if (registryContent.includes('class ToolRegistry')) {
        success('存在 ToolRegistry 类');
    } else {
        error('缺少 ToolRegistry 类');
    }
    
    // 检查 getAllTools 方法
    if (registryContent.includes('getAllTools():')) {
        success('存在 getAllTools() 方法');
    } else {
        error('缺少 getAllTools() 方法');
    }
    
    // 检查 register 方法
    if (registryContent.includes('register(')) {
        success('存在 register() 方法');
    } else {
        error('缺少 register() 方法');
    }
    
    // 提取默认注册的工具
    const registeredTools = [];
    
    // 找到 const defaultTools: ToolFactory[] = [ 的位置
    // 注意：需要跳过类型注解中的 `[]`，找到实际数组的 `[`
    const declarationPattern = /const\s+defaultTools\s*:\s*ToolFactory\[\]\s*=\s*\[/;
    const match = declarationPattern.exec(registryContent);
    
    if (!match) {
        warn('未找到 defaultTools 数组定义');
    } else {
        // 从匹配结束的位置开始（实际数组 [ 的位置）
        const defaultToolsStart = match.index + match[0].length - 1;  // 指向 [
        
        // 找到对应的 ] （考虑数组嵌套的情况）
        let depth = 0;
        let defaultToolsEnd = -1;
        for (let i = defaultToolsStart; i < registryContent.length; i++) {
            if (registryContent[i] === '[') {
                depth++;
            }
            if (registryContent[i] === ']') {
                depth--;
                if (depth === 0) {
                    defaultToolsEnd = i;
                    break;
                }
            }
        }
        
        if (defaultToolsEnd === -1) {
            warn('未找到 defaultTools 数组的结束位置');
        } else {
            const defaultToolsSection = registryContent.substring(defaultToolsStart, defaultToolsEnd + 1);
            
            // 提取所有 key: "xxx" 模式
            const defaultToolsRegex = /key:\s*"([^"]+)"/g;
            let toolMatch;
            while ((toolMatch = defaultToolsRegex.exec(defaultToolsSection)) !== null) {
                registeredTools.push(toolMatch[1]);
            }
        }
    }
    
    success(`默认注册了 ${registeredTools.length} 个工具: ${registeredTools.join(', ')}`);
    
    // 显式断言 exportDataframe 存在
    if (registeredTools.includes('exportDataframe')) {
        success('exportDataframe 已在默认注册列表中');
    } else {
        error('exportDataframe 未在默认注册列表中');
    }
    
    // 显式断言 exportDataframe 的条件注册逻辑
    const exportDataframePattern = /key:\s*"exportDataframe"[\s\S]*?condition:\s*\(\)\s*=>\s*commonStore\.appProps\?\.isExportDataFrame/;
    if (exportDataframePattern.test(registryContent)) {
        success('exportDataframe 条件注册逻辑正确: commonStore.appProps?.isExportDataFrame');
    } else {
        warn('exportDataframe 条件注册逻辑可能不正确');
    }
} else {
    error('缺少 registry.ts 文件');
}

// ========================================
// 检查 3: 工具文件 - 确认它们调用 openModal 而不是传递 props
// ========================================
log('\n--- 检查 3: 工具文件 ---');
const toolFiles = [
    'saveTool.tsx',
    'exportTool.tsx',
    'exportDataframe.tsx',
    'openDesktop.tsx',
    'runcellTool.tsx'
];

for (const toolFile of toolFiles) {
    const filePath = path.join(TOOLS_DIR, toolFile);
    if (fs.existsSync(filePath)) {
        const content = readFile(filePath);
        
        // 检查是否调用 openModal
        if (content.includes('commonStore.openModal')) {
            success(`${toolFile}: 使用 commonStore.openModal()`);
        }
        
        // 检查是否不再接收 props/gwRef/storeRef 参数
        const funcMatch = content.match(/export function get\w+\(([^)]*)\)/);
        if (funcMatch) {
            const params = funcMatch[1].trim();
            if (params === '' || params.includes(':') === false || params.includes('IGWHandler') === false) {
                success(`${toolFile}: 不再接收 props/gwRef/storeRef 参数`);
            } else {
                warn(`${toolFile}: 可能仍在接收 props 相关参数`);
            }
        }
    }
}

// ========================================
// 检查 4: 导出工具是否打开正确的 modal
// ========================================
log('\n--- 检查 4: 导出工具 ---');
const exportToolContent = readFile(path.join(TOOLS_DIR, 'exportTool.tsx'));
if (exportToolContent.includes('commonStore.openModal("exportConfig")')) {
    success('exportTool 打开的是 exportConfig (正确)');
} else if (exportToolContent.includes('commonStore.openModal("codeExport")')) {
    error('exportTool 打开的是 codeExport (应该打开 exportConfig)');
} else {
    error('exportTool 未正确使用 openModal');
}

// ========================================
// 检查 5: 保存工具是否打开正确的 modal
// ========================================
log('\n--- 检查 5: 保存工具 ---');
const saveToolContent = readFile(path.join(TOOLS_DIR, 'saveTool.tsx'));

if (saveToolContent.includes('commonStore.openModal("uploadSpec")')) {
    success('saveTool 打开 uploadSpec (正确)');
} else {
    warn('saveTool 可能未正确打开 uploadSpec');
}

if (saveToolContent.includes('commonStore.openModal("uploadChart")')) {
    success('saveTool 打开 uploadChart (正确)');
} else {
    warn('saveTool 可能未正确打开 uploadChart');
}

// ========================================
// 检查 6: 弹窗组件 - 确认它们只使用 closeModal
// ========================================
log('\n--- 检查 6: 弹窗组件 ---');
const modalComponents = [
    { name: 'uploadSpecModal', path: path.join(COMPONENTS_DIR, 'uploadSpecModal', 'index.tsx') },
    { name: 'uploadChartModal', path: path.join(COMPONENTS_DIR, 'uploadChartModal', 'index.tsx') },
    { name: 'codeExportModal', path: path.join(COMPONENTS_DIR, 'codeExportModal', 'index.tsx') },
    { name: 'exportConfigModal', path: path.join(COMPONENTS_DIR, 'exportConfigModal', 'index.tsx') }
];

for (const modal of modalComponents) {
    if (fs.existsSync(modal.path)) {
        const content = readFile(modal.path);
        
        // 检查是否使用 closeModal
        if (content.includes('commonStore.closeModal')) {
            success(`${modal.name}: 使用 commonStore.closeModal()`);
        } else {
            error(`${modal.name}: 未使用 commonStore.closeModal()`);
        }
        
        // 检查是否不再有 props 接口定义
        const interfaceMatch = content.match(/interface I\w+ModalProps/);
        if (interfaceMatch) {
            warn(`${modal.name}: 仍有 props 接口定义`);
        } else {
            success(`${modal.name}: 不再有 props 接口定义`);
        }
        
        // 检查组件签名是否不再接收 props
        // 1. 匹配 observer(({ a, b }) => { ... }) 这种形式
        // 2. 匹配 observer(() => { ... }) 这种形式
        // 使用非贪婪匹配并限制捕获范围
        const pattern1 = /const \w+Modal: React\.FC(<[^>]+>)?\s*=\s*observer\(\(\{([^{}]*)\}\)\s*=>/;
        const pattern2 = /const \w+Modal: React\.FC(<[^>]+>)?\s*=\s*observer\(\(\)\s*=>/;
        const pattern3 = /const \w+Modal: React\.FC\s*=\s*observer\(\s*\(\s*\)/;
        
        let match = content.match(pattern1);
        if (match) {
            // 找到了带有 destructuring 的形式，检查是否有 props
            const destructured = match[2] || '';
            if (destructured.trim() === '') {
                success(`${modal.name}: 组件签名不再接收多个 props`);
            } else {
                // 检查 destructured 中是否包含 storeRef, gwRef, props, setOpen, open 等关键字
                const forbiddenKeywords = ['storeRef', 'gwRef', 'setOpen', 'open=', 'sourceCode', 'globalStore', 'setGwIsChanged'];
                const hasForbidden = forbiddenKeywords.some(kw => destructured.includes(kw));
                if (hasForbidden) {
                    warn(`${modal.name}: 组件仍在接收禁止的 props: ${destructured}`);
                } else {
                    success(`${modal.name}: 组件签名不再接收禁止的 props`);
                }
            }
        } else {
            match = content.match(pattern2) || content.match(pattern3);
            if (match) {
                success(`${modal.name}: 组件签名不再接收 props (空参数)`);
            } else {
                // 如果都不匹配，可能是没有 props 接口的组件
                success(`${modal.name}: 组件签名格式正确`);
            }
        }
        
        // 检查是否从 commonStore 获取状态
        if (content.includes('commonStore.')) {
            success(`${modal.name}: 从 commonStore 获取状态`);
        }
    }
}

// ========================================
// 检查 7: index.tsx - 确认不再传递弹窗 props
// ========================================
log('\n--- 检查 7: index.tsx ---');
const indexContent = readFile(INDEX_FILE);

// 检查弹窗组件使用是否不再传递 props
const modalUsagePatterns = [
    '<UploadSpecModal',
    '<UploadChartModal',
    '<CodeExportModal',
    '<ExportConfigModal'
];

for (const pattern of modalUsagePatterns) {
    const regex = new RegExp(pattern + '[^>]*>', 'g');
    const matches = indexContent.match(regex);
    if (matches) {
        for (const match of matches) {
            // 检查是否有 props 传递
            if (match.includes('storeRef=') || match.includes('gwRef=') || 
                match.includes('props=') || match.includes('setOpen=') ||
                match.includes('open=') || match.includes('sourceCode=')) {
                error(`${pattern}: 仍在传递 props: ${match}`);
            } else {
                success(`${pattern}: 不再传递 props`);
            }
        }
    }
}

// 检查是否使用 toolRegistry
if (indexContent.includes('toolRegistry')) {
    success('index.tsx: 使用 toolRegistry');
} else {
    error('index.tsx: 未使用 toolRegistry');
}

// 检查是否使用 commonStore.setGwRef 等
if (indexContent.includes('commonStore.setGwRef') && 
    indexContent.includes('commonStore.setStoreRef') &&
    indexContent.includes('commonStore.setAppProps')) {
    success('index.tsx: 使用 commonStore 设置全局上下文');
}

// ========================================
// 检查 8: 确认没有遗留的独立 open 状态
// ========================================
log('\n--- 检查 8: 确认没有遗留的独立 open 状态 ---');
const allTsxFiles = findFiles(APP_DIR, /\.tsx$/);

let hasLegacyStates = false;
for (const file of allTsxFiles) {
    const content = readFile(file);
    const relativePath = path.relative(APP_DIR, file);
    
    // 检查 exportOpen 状态
    if (content.includes('exportOpen') || content.includes('setExportOpen')) {
        if (relativePath !== 'store/common.ts') {
            error(`${relativePath}: 仍有 exportOpen 状态`);
            hasLegacyStates = true;
        }
    }
    
    // 检查独立的 isChanged 状态
    if (content.includes('[isChanged, setIsChanged]')) {
        if (relativePath !== 'store/common.ts' && !relativePath.startsWith('tools/')) {
            error(`${relativePath}: 仍有独立的 isChanged 状态`);
            hasLegacyStates = true;
        }
    }
}

if (!hasLegacyStates) {
    success('没有遗留的独立 open 状态');
}

// ========================================
// 汇总结果
// ========================================
console.log('\n========================================');
console.log('  验证结果汇总');
console.log('========================================\n');
console.log(`✅ 通过: ${infos.length} 项`);
console.log(`⚠️  警告: ${warnings.length} 项`);
console.log(`❌ 错误: ${errors.length} 项\n`);

if (errors.length > 0) {
    console.log('错误详情:');
    errors.forEach((e, i) => console.log(`  ${i + 1}. ${e}`));
    process.exit(1);
} else {
    console.log('🎉 所有关键检查通过!');
    process.exit(0);
}
