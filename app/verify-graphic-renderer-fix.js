/**
 * 最小验证脚本：验证 GraphicRendererApp 筛选联动修复
 * 
 * 用法：node verify-graphic-renderer-fix.js
 * 
 * 断言：
 * 1. GraphicRendererApp 内没有 props.visSpec.map 包裹 GraphicRenderer
 * 2. 没有 chart={[chart]} 单个元素数组模式
 * 3. useKernelCalc 两个分支都是 chart={props.visSpec} 完整数组
 */

const fs = require('fs');
const path = require('path');

function runVerify() {
  const sourcePath = path.join(__dirname, 'src/index.tsx');
  const source = fs.readFileSync(sourcePath, 'utf-8');
  
  const fnStart = source.indexOf('function GraphicRendererApp');
  const fnEnd = findFunctionEnd(source, fnStart);
  const fnBody = source.slice(fnStart, fnEnd);
  
  const results = [];
  let allPassed = true;
  
  // 断言 1
  const hasMapRender = /props\.visSpec\.map[\s\S]*?<GraphicRenderer/.test(fnBody);
  results.push({
    assert: 'GraphicRendererApp 内没有 props.visSpec.map 包裹 GraphicRenderer',
    passed: !hasMapRender,
    actual: hasMapRender ? '存在' : '不存在'
  });
  if (hasMapRender) allPassed = false;
  
  // 断言 2
  const hasSingleChart = /chart=\{\[chart\]\}/.test(fnBody);
  results.push({
    assert: '没有 chart={[chart]} 单个元素数组模式',
    passed: !hasSingleChart,
    actual: hasSingleChart ? '存在' : '不存在'
  });
  if (hasSingleChart) allPassed = false;
  
  // 断言 3
  const fullVisSpecMatches = fnBody.match(/chart=\{props\.visSpec\}/g) || [];
  const hasFullVisSpec = fullVisSpecMatches.length === 2;
  results.push({
    assert: 'useKernelCalc 两个分支都是 chart={props.visSpec}',
    passed: hasFullVisSpec,
    actual: `出现 ${fullVisSpecMatches.length} 次`
  });
  if (!hasFullVisSpec) allPassed = false;
  
  // 输出
  console.log('\n========== GraphicRendererApp 筛选联动修复验证 ==========\n');
  
  results.forEach((r, i) => {
    console.log(`${r.passed ? '✅' : '❌'} 断言 ${i + 1}: ${r.assert}`);
    console.log(`   实际: ${r.actual}`);
  });
  
  console.log(`\n${allPassed ? '✅' : '❌'} 结果: ${allPassed ? '所有断言通过' : '存在失败断言'}`);
  console.log('\n========================================================\n');
  
  process.exit(allPassed ? 0 : 1);
}

function findFunctionEnd(source, start) {
  let depth = 0;
  let inFn = false;
  for (let i = start; i < source.length; i++) {
    if (source[i] === '{') {
      depth++;
      inFn = true;
    } else if (source[i] === '}') {
      depth--;
      if (inFn && depth === 0) return i + 1;
    }
  }
  return source.length;
}

runVerify();
