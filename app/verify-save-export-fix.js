/**
 * 静态验证脚本：验证 formatExportedChartDatas 修复
 * 
 * 通过读取真实源码 app/src/utils/save.ts 做静态断言，确认：
 * 1. 存在优先路径：charts.length === 1 && ... startsWith("data:image/")
 * 2. 命中后直接返回 singleChart: chartData.charts[0].data
 * 3. 回退路径仍调用 htmlToImage.toPng
 */

const fs = require('fs');
const path = require('path');

function runVerify() {
  const sourcePath = path.join(__dirname, 'src/utils/save.ts');
  const source = fs.readFileSync(sourcePath, 'utf-8');
  
  const results = [];
  let allPassed = true;
  
  // 找到 formatExportedChartDatas 函数体
  const fnStart = source.indexOf('export async function formatExportedChartDatas');
  if (fnStart === -1) {
    console.error('❌ 未找到 formatExportedChartDatas 函数');
    process.exit(1);
  }
  
  // 简单提取函数体（基于大括号匹配）
  let depth = 0;
  let inFn = false;
  let fnEnd = source.length;
  for (let i = fnStart; i < source.length; i++) {
    if (source[i] === '{') {
      depth++;
      inFn = true;
    } else if (source[i] === '}') {
      depth--;
      if (inFn && depth === 0) {
        fnEnd = i + 1;
        break;
      }
    }
  }
  const fnBody = source.slice(fnStart, fnEnd);
  
  // 断言 1：存在 charts.length === 1 的判断
  const hasChartsLengthCheck = /charts\.length\s*===\s*1/.test(fnBody);
  results.push({
    assert: '源码中存在 charts.length === 1 的判断',
    passed: hasChartsLengthCheck,
    actual: hasChartsLengthCheck ? '存在' : '不存在'
  });
  if (!hasChartsLengthCheck) allPassed = false;
  
  // 断言 2：存在 startsWith("data:image/") 的判断
  const hasStartsWithCheck = /startsWith\(\s*["']data:image\//.test(fnBody);
  results.push({
    assert: '源码中存在 startsWith("data:image/") 的判断',
    passed: hasStartsWithCheck,
    actual: hasStartsWithCheck ? '存在' : '不存在'
  });
  if (!hasStartsWithCheck) allPassed = false;
  
  // 断言 3：命中后返回 singleChart: chartData.charts[0].data
  // 检查在 if (charts.length === 1 ...) 块内是否有 singleChart: chartData.charts[0].data
  const ifBlockStart = fnBody.indexOf('charts.length === 1');
  const ifBlockEnd = findIfBlockEnd(fnBody, ifBlockStart);
  const ifBlock = fnBody.slice(ifBlockStart, ifBlockEnd);
  
  const hasDirectReturn = /singleChart\s*:\s*chartData\.charts\[0\]\.data/.test(ifBlock);
  results.push({
    assert: '在优先路径 if 块内直接返回 singleChart: chartData.charts[0].data',
    passed: hasDirectReturn,
    actual: hasDirectReturn ? '存在' : '不存在'
  });
  if (!hasDirectReturn) allPassed = false;
  
  // 断言 4：仍保留 htmlToImage.toPng 调用作为回退
  const hasHtmlToImageFallback = /htmlToImage\.toPng/.test(fnBody);
  results.push({
    assert: '源码中仍保留 htmlToImage.toPng 作为回退',
    passed: hasHtmlToImageFallback,
    actual: hasHtmlToImageFallback ? '存在' : '不存在'
  });
  if (!hasHtmlToImageFallback) allPassed = false;
  
  // 断言 5：优先路径的 return 在 htmlToImage.toPng 调用之前
  const directReturnPos = fnBody.indexOf('chartData.charts[0].data');
  const htmlToImagePos = fnBody.indexOf('htmlToImage.toPng');
  const hasCorrectOrder = directReturnPos !== -1 && htmlToImagePos !== -1 && directReturnPos < htmlToImagePos;
  results.push({
    assert: '优先路径的 return 在 htmlToImage.toPng 调用之前（先检查优先路径）',
    passed: hasCorrectOrder,
    actual: hasCorrectOrder ? `顺序正确（return 在 ${directReturnPos}，toPng 在 ${htmlToImagePos}）` : 
            directReturnPos === -1 ? '缺少直接 return' : 
            htmlToImagePos === -1 ? '缺少 htmlToImage.toPng' : '顺序错误'
  });
  if (!hasCorrectOrder) allPassed = false;
  
  // 输出结果
  console.log('\n========== formatExportedChartDatas 静态源码验证 ==========\n');
  console.log(`源码路径: ${sourcePath}\n`);
  
  results.forEach((r, i) => {
    console.log(`${r.passed ? '✅' : '❌'} 断言 ${i + 1}: ${r.assert}`);
    console.log(`   实际: ${r.actual}`);
  });
  
  console.log(`\n${allPassed ? '✅' : '❌'} 结果: ${allPassed ? '所有断言通过' : '存在失败断言'}`);
  console.log('\n============================================================\n');
  
  process.exit(allPassed ? 0 : 1);
}

// 简单的 if 块结束定位（找到匹配的 }）
function findIfBlockEnd(source, startPos) {
  // 找到 if 后的 {
  let braceStart = source.indexOf('{', startPos);
  if (braceStart === -1) return source.length;
  
  let depth = 0;
  for (let i = braceStart; i < source.length; i++) {
    if (source[i] === '{') depth++;
    else if (source[i] === '}') {
      depth--;
      if (depth === 0) return i + 1;
    }
  }
  return source.length;
}

runVerify();
