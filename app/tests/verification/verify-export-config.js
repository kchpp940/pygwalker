
const fs = require('fs');
const path = require('path');

let passed = 0;
let failed = 0;

const assert = (condition, message) => {
    if (!condition) {
        throw new Error(message || 'Assertion failed');
    }
};

const assertContains = (str, substr, message) => {
    const parts = substr.split(/\\n/);
    let matched = true;
    for (let i = 0; i < parts.length; i++) {
        if (!str.includes(parts[i])) {
            matched = false;
            break;
        }
    }
    if (!matched) {
        throw new Error(message || `Expected string to contain pattern derived from: "${substr}"`);
    }
};

const assertNotContains = (str, substr, message) => {
    if (str.includes(substr)) {
        throw new Error(message || `Expected string NOT to contain "${substr}"`);
    }
};

const runTest = (name, testFn) => {
    try {
        testFn();
        console.log(`  ✓ ${name}`);
        passed++;
    } catch (e) {
        console.log(`  ✗ ${name}`);
        console.log(`    Error: ${e.message}`);
        failed++;
    }
};

console.log('\n╔═══════════════════════════════════════════════════════════════╗');
console.log('║      Export Configuration Flow REAL Branch Verification      ║');
console.log('╚═══════════════════════════════════════════════════════════════╝\n');

const appRoot = path.join(__dirname, '..', '..', 'src');
const exportConfigPath = path.join(appRoot, 'components', 'exportConfigModal', 'index.tsx');
const exportConfigContent = fs.readFileSync(exportConfigPath, 'utf-8');

console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('1. SVG REAL Output Verification (NOT just PNG renamed)');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

runTest('SVG export passes mode="svg" to exportChart', () => {
    assertContains(exportConfigContent,
        'const gwMode: "data-url" | "svg" = exportFormat === "svg" ? "svg" : "data-url";',
        'SVG mode should dynamically select "svg" mode'
    );
});

runTest('SVG export checks startsWith("<svg") to confirm real SVG', () => {
    assertContains(exportConfigContent,
        'if (svgContent.startsWith("<svg"))',
        'Should verify SVG content starts with <svg'
    );
});

runTest('SVG export adds XML declaration for valid SVG file', () => {
    assertContains(exportConfigContent,
        '<?xml version="1.0" encoding="UTF-8"?>',
        'Should add XML declaration to SVG'
    );
});

runTest('SVG export uses image/svg+xml MIME type and .svg extension', () => {
    assertContains(exportConfigContent,
        'download(url, `${spec?.name || "chart"}.svg`, "image/svg+xml")',
        'Should download as .svg with image/svg+xml MIME'
    );
});

runTest('SVG export does NOT call scaleImage or addTitle (SVG only)', () => {
    const svgExportBlock = exportConfigContent.match(/if \(format === "svg"\) \{[\s\S]*?return;/)?.[0] || '';
    assertNotContains(svgExportBlock, 'scaleImage', 'SVG export should not call scaleImage');
    assertNotContains(svgExportBlock, 'addTitleAndDescriptionToImage', 'SVG export should not call addTitleAndDescriptionToImage');
});

runTest('exportChartList also receives correct gwMode parameter', () => {
    assertContains(exportConfigContent,
        'for await (const chart of gwRef.current.exportChartList(gwMode))',
        'exportChartList should receive gwMode parameter'
    );
});

console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('2. PNG Scale REAL Branch Verification');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

runTest('Scale state has type definition: 1 | 2 | 3 | 4', () => {
    assertContains(exportConfigContent,
        'type ImageScale = 1 | 2 | 3 | 4;',
        'ImageScale type should define 1-4'
    );
});

runTest('scaleImage function really scales canvas dimensions', () => {
    assertContains(exportConfigContent,
        'canvas.width = img.width * scale;',
        'Canvas width multiplied by scale'
    );
    assertContains(exportConfigContent,
        'canvas.height = img.height * scale;',
        'Canvas height multiplied by scale'
    );
    assertContains(exportConfigContent,
        'ctx.scale(scale, scale);',
        'Context is scaled'
    );
});

runTest('Scale 1x optimization returns original dataUrl (REAL branch)', () => {
    assertContains(exportConfigContent,
        'if (scale === 1) return dataUrl;',
        'Scale 1 should return original without processing'
    );
});

runTest('Scale UI only shown when exportFormat === "png"', () => {
    assertContains(exportConfigContent,
        '{exportFormat === "png" && (',
        'Scale options conditional on PNG format'
    );
});

console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('3. Title AND Description REAL Branch Verification');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

runTest('Has separate state for includeTitle AND includeDescription', () => {
    assertContains(exportConfigContent,
        'const [includeTitle, setIncludeTitle] = useState(true);',
        'Has includeTitle state'
    );
    assertContains(exportConfigContent,
        'const [includeDescription, setIncludeDescription] = useState(true);',
        'Has includeDescription state'
    );
});

runTest('Early return when BOTH title AND description disabled (REAL branch)', () => {
    assertContains(exportConfigContent,
        'if (!includeTitle && !includeDescription) return dataUrl;',
        'Should return early when neither is enabled'
    );
});

runTest('Title height calculated dynamically based on includeTitle state', () => {
    assertContains(exportConfigContent,
        'const titleHeight = includeTitle ? 40 * scale : 0;',
        'Title height conditional on includeTitle'
    );
});

runTest('Description height calculated dynamically based on includeDescription state', () => {
    assertContains(exportConfigContent,
        'const descHeight = includeDescription && description ? 50 * scale : 0;',
        'Description height conditional on includeDescription AND description value'
    );
});

runTest('Canvas height increased for title+description REAL effect', () => {
    assertContains(exportConfigContent,
        'canvas.height = img.height + topPadding;',
        'Canvas height increased by topPadding'
    );
    assertContains(exportConfigContent,
        'const topPadding = titleHeight + descHeight + padding;',
        'topPadding includes both title and description heights'
    );
});

runTest('Image drawn BELOW title/description REAL effect', () => {
    assertContains(exportConfigContent,
        'ctx.drawImage(img, 0, topPadding);',
        'Image drawn at y=topPadding (below title/desc)'
    );
});

runTest('Title uses spec.name REAL data binding', () => {
    assertContains(exportConfigContent,
        'ctx.fillText(title, canvas.width / 2, 30 * scale);',
        'Title text is drawn on canvas'
    );
});

runTest('Description does word wrapping REAL implementation', () => {
    assertContains(exportConfigContent,
        'const maxWidth = canvas.width - 40 * scale;',
        'Has max width for description'
    );
    assertContains(exportConfigContent,
        'for (const word of words)',
        'Loops through words'
    );
    assertContains(exportConfigContent,
        'const metrics = ctx.measureText(testLine);',
        'Measures text for wrapping'
    );
});

runTest('Title & Description UI only shown for PNG/SVG', () => {
    assertContains(exportConfigContent,
        'const showTitleDescOption = exportFormat === "png" || exportFormat === "svg";',
        'Title/desc UI conditional check'
    );
    assertContains(exportConfigContent,
        '{showTitleDescOption && (',
        'Title/desc section wrapped in showTitleDescOption check'
    );
});

console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('4. Export Content (Filtered vs Unfiltered) REAL Branch Verification');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

runTest('Has ExportContent type: "filtered" | "unfiltered"', () => {
    assertContains(exportConfigContent,
        'type ExportContent = "filtered" | "unfiltered";',
        'Has ExportContent type'
    );
});

runTest('exportContent state with onChange binding (REAL interaction)', () => {
    assertContains(exportConfigContent,
        'const [exportContent, setExportContent] = useState<ExportContent>("filtered");',
        'Has exportContent state'
    );
    assertContains(exportConfigContent,
        'onValueChange={(value) => setExportContent(value as ExportContent)}',
        'has setExportContent binding'
    );
});

runTest('UI shows "filtered" option', () => {
    assertContains(exportConfigContent,
        'value="filtered"',
        'Has filtered option value'
    );
    assertContains(exportConfigContent,
        'Current Filtered Results',
        'Has filtered option label'
    );
});

runTest('UI shows "unfiltered" option', () => {
    assertContains(exportConfigContent,
        'value="unfiltered"',
        'Has unfiltered option value'
    );
    assertContains(exportConfigContent,
        'Unfiltered Full Dataset',
        'Has unfiltered option label'
    );
});

runTest('UI uses filterStore.hasActiveFilters REAL state', () => {
    assertContains(exportConfigContent,
        'const hasActiveFilters = filterStore.hasActiveFilters;',
        'Reads hasActiveFilters from filterStore'
    );
    assertContains(exportConfigContent,
        'filterStore.enabledConditions.length',
        'Uses enabledConditions count'
    );
});

runTest('buildSpecWithContentPreference early returns for filtered', () => {
    assertContains(exportConfigContent,
        'if (exportContent === "filtered" || !spec) return spec;',
        'Early return for filtered content'
    );
});

runTest('Unfiltered branch DEEP CLONES spec to avoid mutation', () => {
    assertContains(exportConfigContent,
        'const clonedSpec = JSON.parse(JSON.stringify(spec));',
        'Clones spec before modification'
    );
});

runTest('Unfiltered branch REMOVES filters from config.filter', () => {
    assertContains(exportConfigContent,
        'if (clonedSpec.config?.filter || clonedSpec.filter)',
        'Checks for config.filter and spec.filter'
    );
    assertContains(exportConfigContent,
        'delete clonedSpec.config?.filter;',
        'Deletes config.filter'
    );
    assertContains(exportConfigContent,
        'delete clonedSpec.filter;',
        'Deletes spec.filter'
    );
});

runTest('Unfiltered branch CLEARS encodings.filter array', () => {
    assertContains(exportConfigContent,
        'if (clonedSpec.encodings?.filter?.length > 0)',
        'Checks encodings.filter length'
    );
    assertContains(exportConfigContent,
        'clonedSpec.encodings.filter = [];',
        'Clears encodings.filter array'
    );
});

runTest('Unfiltered branch FILTERS OUT filter workflow steps', () => {
    assertContains(exportConfigContent,
        'if (clonedSpec.config?.workflow)',
        'Checks for workflow'
    );
    assertContains(exportConfigContent,
        'clonedSpec.config.workflow = clonedSpec.config.workflow.filter',
        'Filters workflow'
    );
    assertContains(exportConfigContent,
        'step.type !== "filter"',
        'Filters out filter steps'
    );
});

runTest('exportJson calls buildSpecWithContentPreference REAL branch', () => {
    assertContains(exportConfigContent,
        'if (exportContent === "unfiltered")',
        'exportJson checks for unfiltered'
    );
    assertContains(exportConfigContent,
        'spec = spec.map(s => buildSpecWithContentPreference(s));',
        'exportJson calls buildSpecWithContentPreference'
    );
});

runTest('exportPythonCode also calls buildSpecWithContentPreference REAL branch', () => {
    assertContains(exportConfigContent,
        'spec = spec.map(s => buildSpecWithContentPreference(s));',
        'exportPythonCode calls buildSpecWithContentPreference'
    );
});

runTest('PNG/SVG shows read-only info (no Select) - not fake switch', () => {
    assertContains(exportConfigContent,
        '{exportFormat === "png" || exportFormat === "svg" ? (',
        'PNG/SVG uses ternary for different UI'
    );
    assertContains(exportConfigContent,
        'Images are rendered from the current screen state.',
        'Explains images use current screen state'
    );
    assertContains(exportConfigContent,
        'To export unfiltered data, use JSON or Code format.',
        'Tells user to use JSON/Code for unfiltered'
    );
});

runTest('JSON/Code shows Select (can change) - REAL switch', () => {
    assertContains(exportConfigContent,
        ') : (\\n                            <Select ',
        'JSON/Code uses Select in else branch'
    );
});

runTest('useEffect auto-resets PNG/SVG to "filtered" (state enforcement)', () => {
    assertContains(exportConfigContent,
        'useEffect(() => {\\n        if ((exportFormat === "png" || exportFormat === "svg") && exportContent === "unfiltered") {\\n            setExportContent("filtered");\\n        }\\n    }, [exportFormat, exportContent]);',
        'Has useEffect that resets to filtered for PNG/SVG'
    );
});

console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('5. Multiple Charts (ZIP) REAL Branch Verification');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

runTest('Imports JSZip REAL dependency', () => {
    assertContains(exportConfigContent,
        'import JSZip from "jszip";',
        'Imports JSZip'
    );
});

runTest('exportMultipleCharts state with onCheckedChange', () => {
    assertContains(exportConfigContent,
        'const [exportMultipleCharts, setExportMultipleCharts] = useState(false);',
        'Has exportMultipleCharts state'
    );
    assertContains(exportConfigContent,
        'onCheckedChange={(checked) => setExportMultipleCharts(checked as boolean)}',
        'has setExportMultipleCharts binding'
    );
});

runTest('hasMultipleCharts condition calculated from visSpec count', () => {
    assertContains(exportConfigContent,
        'const visSpecCount = visSpec.length;',
        'Calculates visSpecCount'
    );
    assertContains(exportConfigContent,
        'const hasMultipleCharts = visSpecCount > 1;',
        'hasMultipleCharts is visSpecCount > 1'
    );
    assertContains(exportConfigContent,
        '{hasMultipleCharts && (',
        'UI only shown when hasMultipleCharts'
    );
});

runTest('REAL branch: if (exportMultipleCharts) uses exportChartList', () => {
    assertContains(exportConfigContent,
        'if (exportMultipleCharts && gwRef.current.exportChartList)',
        'exportMultipleCharts=true branch check'
    );
    assertContains(exportConfigContent,
        'for await (const chart of gwRef.current.exportChartList(gwMode))',
        'Uses exportChartList in multi-chart mode'
    );
});

runTest('REAL branch: else uses single exportChart', () => {
    assertContains(exportConfigContent,
        '} else {',
        'Has else branch'
    );
    assertContains(exportConfigContent,
        'const chartData = await gwRef.current.exportChart!(gwMode);',
        'else branch uses single exportChart'
    );
});

runTest('REAL branch: single chart falls through to exportSingleImage (no ZIP)', () => {
    assertContains(exportConfigContent,
        'if (allCharts.length === 1)',
        'Checks for single chart'
    );
    assertContains(exportConfigContent,
        'await exportSingleImage(format, allCharts[0], spec);',
        'Single chart calls exportSingleImage'
    );
    assertContains(exportConfigContent,
        'return;',
        'Single chart returns early (no ZIP)'
    );
});

runTest('REAL branch: multiple charts create JSZip instance', () => {
    assertContains(exportConfigContent,
        'const zip = new JSZip();',
        'Creates new JSZip instance'
    );
});

runTest('REAL branch: PNG base64 encoded for ZIP', () => {
    assertContains(exportConfigContent,
        'const base64Data = imageData.split(",")[1];',
        'Extracts base64 part'
    );
    assertContains(exportConfigContent,
        'zip.file(',
        'Calls zip.file'
    );
    assertContains(exportConfigContent,
        '{ base64: true }',
        'Uses base64 encoding'
    );
});

runTest('ZIP respects format: SVG adds raw SVG, PNG adds base64 PNG', () => {
    assertContains(exportConfigContent,
        'if (format === "svg") {',
        'Checks format for SVG path'
    );
    assertContains(exportConfigContent,
        'zip.file(`${spec?.name || `chart_${i + 1}`}.svg`, svgContent);',
        'SVG adds raw SVG content to zip'
    );
    assertContains(exportConfigContent,
        'zip.file(`${spec?.name || `chart_${i + 1}`}.png`, base64Data, { base64: true });',
        'PNG adds base64 PNG to zip'
    );
});

runTest('gwMode passed to exportChartList for correct format in ZIP', () => {
    assertContains(exportConfigContent,
        'for await (const chart of gwRef.current.exportChartList(gwMode))',
        'exportChartList receives gwMode'
    );
    assertContains(exportConfigContent,
        'const gwMode: "data-url" | "svg" = exportFormat === "svg" ? "svg" : "data-url";',
        'gwMode derived from exportFormat'
    );
});

runTest('REAL branch: generateAsync + download as ZIP', () => {
    assertContains(exportConfigContent,
        'const content = await zip.generateAsync({ type: "blob" });',
        'Generates zip as blob'
    );
    assertContains(exportConfigContent,
        'download(url, `charts_${Date.now()}.zip`, "application/zip");',
        'Downloads as .zip'
    );
});

console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('6. getCurrentVisSpec REAL Branch Verification');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

runTest('REAL branch: exportMultipleCharts=false returns ONLY current visIndex', () => {
    assertContains(exportConfigContent,
        'if (!exportMultipleCharts && storeRef.current.visIndex !== undefined)',
        'Single chart mode check'
    );
    assertContains(exportConfigContent,
        'return [allSpec[storeRef.current.visIndex]];',
        'Single chart mode returns only visIndex spec'
    );
});

runTest('REAL branch: exportMultipleCharts=true returns ALL specs', () => {
    assertContains(exportConfigContent,
        'return allSpec;',
        'Multi-chart mode returns all specs'
    );
});

runTest('useEffect updates visSpec when modal opens (fresh data)', () => {
    assertContains(exportConfigContent,
        'useEffect(',
        'Has useEffect'
    );
    assertContains(exportConfigContent,
        'if (open && storeRef.current)',
        'Checks open and storeRef.current'
    );
    assertContains(exportConfigContent,
        'const spec = storeRef.current.exportCode();',
        'Calls exportCode'
    );
    assertContains(exportConfigContent,
        'setVisSpec(spec);',
        'Sets visSpec'
    );
    assertContains(exportConfigContent,
        '[open]',
        'Depends on open'
    );
});

console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('7. handleExport Routing REAL Branch Verification');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

runTest('REAL branch: PNG/SVG -> exportImages()', () => {
    assertContains(exportConfigContent,
        'if (exportFormat === "png" || exportFormat === "svg")',
        'PNG/SVG condition'
    );
    assertContains(exportConfigContent,
        'await exportImages();',
        'Calls exportImages for PNG/SVG'
    );
});

runTest('REAL branch: JSON -> exportJson()', () => {
    assertContains(exportConfigContent,
        'else if (exportFormat === "json")',
        'JSON condition'
    );
    assertContains(exportConfigContent,
        'await exportJson();',
        'Calls exportJson for JSON'
    );
});

runTest('REAL branch: Code -> exportPythonCode()', () => {
    assertContains(exportConfigContent,
        'else if (exportFormat === "code")',
        'Code condition'
    );
    assertContains(exportConfigContent,
        'await exportPythonCode();',
        'Calls exportPythonCode for Code'
    );
});

console.log('\n╔═══════════════════════════════════════════════════════════════╗');
console.log(`║              Test Results: ${passed.toString().padStart(2)} passed, ${failed.toString().padStart(2)} failed                   ║`);
console.log('╚═══════════════════════════════════════════════════════════════╝\n');

if (failed > 0) {
    process.exit(1);
}
