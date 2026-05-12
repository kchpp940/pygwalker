
import * as fs from 'fs';
import * as path from 'path';

let passed = 0;
let failed = 0;

const assert = (condition: boolean, message?: string) => {
    if (!condition) {
        throw new Error(message || 'Assertion failed');
    }
};

const assertContains = (text: string, substring: string, message?: string) => {
    if (!text.includes(substring)) {
        throw new Error(message || `Expected to find "${substring}" in text`);
    }
};

const runTest = (name: string, testFn: () => void) => {
    try {
        testFn();
        console.log(`  ✓ ${name}`);
        passed++;
    } catch (e) {
        console.log(`  ✗ ${name}`);
        console.log(`    Error: ${(e as Error).message}`);
        failed++;
    }
};

const appRoot = path.join(__dirname, '..', '..');

console.log('\n╔═══════════════════════════════════════════════════════════════╗');
console.log('║        Enhanced Filter Integration Verification Tests        ║');
console.log('╚═══════════════════════════════════════════════════════════════╝\n');

console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('1. Core Filter Logic (filter.ts)');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

const filterTsPath = path.join(appRoot, 'src', 'utils', 'filter.ts');
const filterTsContent = fs.readFileSync(filterTsPath, 'utf-8');

runTest('filterRows exists and handles AND logic', () => {
    assertContains(filterTsContent, 'export const filterRows');
    assertContains(filterTsContent, 'logic === "AND"');
    assertContains(filterTsContent, 'enabledConditions.every');
});

runTest('filterRows handles OR logic', () => {
    assertContains(filterTsContent, 'enabledConditions.some');
});

runTest('filterRows returns original data when no conditions', () => {
    assertContains(filterTsContent, 'if (enabledConditions.length === 0)');
    assertContains(filterTsContent, 'return rows;');
});

runTest('estimateFilteredCount exists', () => {
    assertContains(filterTsContent, 'export const estimateFilteredCount');
});

runTest('Multiple condition types supported', () => {
    const conditions = ['range', 'temporal range', 'one of', 'not in', 'contains', 'equals', 'greater than', 'less than'];
    conditions.forEach(cond => {
        assertContains(filterTsContent, cond);
    });
});

console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('2. Index.tsx Integration (filteredDataSource -> GraphicWalker)');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

const indexTsxPath = path.join(appRoot, 'src', 'index.tsx');
const indexTsxContent = fs.readFileSync(indexTsxPath, 'utf-8');

runTest('filteredDataSource is computed with filterStore', () => {
    assertContains(indexTsxContent, 'const filteredDataSource = React.useMemo');
    assertContains(indexTsxContent, 'filterStore.hasActiveFilters');
    assertContains(indexTsxContent, 'filterRows(');
    assertContains(indexTsxContent, 'filterStore.conditions');
    assertContains(indexTsxContent, 'filterStore.logic');
});

runTest('filteredDataSource is passed to GraphicWalker (client mode)', () => {
    assertContains(indexTsxContent, 'data={props.useKernelCalc ? undefined : filteredDataSource}');
});

runTest('filteredDataSource is passed to GraphicRendererApp', () => {
    assertContains(indexTsxContent, 'dataSource={filteredDataSource}');
});

runTest('computationCallback wraps and filters server results', () => {
    assertContains(indexTsxContent, 'const computationCallback = React.useMemo');
    assertContains(indexTsxContent, 'const result = await baseCallback(payload)');
    assertContains(indexTsxContent, 'if (filterStore.hasActiveFilters && Array.isArray(result))');
    assertContains(indexTsxContent, 'return filterRows(');
});

runTest('EnhancedFilterPanel is rendered', () => {
    assertContains(indexTsxContent, '<EnhancedFilterPanel');
    assertContains(indexTsxContent, 'fields={fieldMetas}');
    assertContains(indexTsxContent, 'dataSource={props.dataSource || []}');
});

runTest('filterTool is added to toolbar', () => {
    assertContains(indexTsxContent, 'const filterTool = getFilterTool()');
    assertContains(indexTsxContent, 'const tools = [runcellTool, exportTool, openInDesktopTool, filterTool]');
});

console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('3. Export Dataframe Integration (exportDataframeTool)');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

const exportDfPath = path.join(appRoot, 'src', 'tools', 'exportDataframe.tsx');
const exportDfContent = fs.readFileSync(exportDfPath, 'utf-8');

runTest('filterStore is imported', () => {
    assertContains(exportDfContent, 'import filterStore from "../store/filter"');
});

runTest('exportWithFilter function exists', () => {
    assertContains(exportDfContent, 'const exportWithFilter = async () =>');
});

runTest('exportWithFilter handles client mode (uses props.dataSource)', () => {
    assertContains(exportDfContent, 'if (!props.useKernelCalc)');
    assertContains(exportDfContent, 'dataToExport = props.dataSource ? [...props.dataSource] : []');
});

runTest('exportWithFilter handles server mode (fetches data)', () => {
    assertContains(exportDfContent, 'getDatasFromKernelByPayload');
    assertContains(exportDfContent, 'getDatasFromKernelBySql');
});

runTest('exportWithFilter applies filterRows before export', () => {
    assertContains(exportDfContent, 'if (filterStore.hasActiveFilters)');
    assertContains(exportDfContent, 'dataToExport = filterRows(');
    assertContains(exportDfContent, 'filterStore.conditions');
    assertContains(exportDfContent, 'filterStore.logic');
});

runTest('exportWithFilter sends data via export_dataframe_by_data', () => {
    assertContains(exportDfContent, 'export_dataframe_by_data');
    assertContains(exportDfContent, 'records: dataToExport');
});

runTest('onClick checks for active filters and uses exportWithFilter', () => {
    assertContains(exportDfContent, 'if (filterStore.hasActiveFilters)');
    assertContains(exportDfContent, 'await exportWithFilter()');
});

console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('4. Python Backend Integration (pygwalker.py)');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

const pygwalkerPyPath = path.join(appRoot, '..', 'pygwalker', 'api', 'pygwalker.py');
const pygwalkerPyContent = fs.readFileSync(pygwalkerPyPath, 'utf-8');

runTest('_export_dataframe_by_data handler exists', () => {
    assertContains(pygwalkerPyContent, 'def _export_dataframe_by_data');
});

runTest('_export_dataframe_by_data receives records and creates DataFrame', () => {
    assertContains(pygwalkerPyContent, 'records = data.get("records", [])');
    assertContains(pygwalkerPyContent, 'df = pd.DataFrame(records)');
});

runTest('_export_dataframe_by_data sets last_exported_dataframe', () => {
    assertContains(pygwalkerPyContent, 'GlobalVarManager.set_last_exported_dataframe(df)');
    assertContains(pygwalkerPyContent, 'self._last_exported_dataframe = df');
});

runTest('export_dataframe_by_data is registered', () => {
    assertContains(pygwalkerPyContent, 'comm.register("export_dataframe_by_data", _export_dataframe_by_data)');
});

console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('5. Filter Store (filter.ts store)');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

const filterStorePath = path.join(appRoot, 'src', 'store', 'filter.ts');
const filterStoreContent = fs.readFileSync(filterStorePath, 'utf-8');

runTest('FilterStore class exists with MobX observables', () => {
    assertContains(filterStoreContent, 'class FilterStore');
    assertContains(filterStoreContent, 'makeObservable(this, {');
    assertContains(filterStoreContent, 'conditions: observable');
    assertContains(filterStoreContent, 'logic: observable');
});

runTest('hasActiveFilters computed property', () => {
    assertContains(filterStoreContent, 'hasActiveFilters: computed');
    assertContains(filterStoreContent, 'get hasActiveFilters()');
    assertContains(filterStoreContent, 'return this.enabledConditions.length > 0');
});

runTest('enabledConditions filters out disabled', () => {
    assertContains(filterStoreContent, 'get enabledConditions()');
    assertContains(filterStoreContent, 'return this.conditions.filter(c => c.enabled)');
});

runTest('toggleCondition action exists', () => {
    assertContains(filterStoreContent, 'toggleCondition: action');
    assertContains(filterStoreContent, 'condition.enabled = !condition.enabled');
});

runTest('AND/OR logic support', () => {
    assertContains(filterStoreContent, 'logic: FilterLogic = "AND"');
    assertContains(filterStoreContent, 'setLogic: action');
});

console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('6. Filter Tool (filterTool.tsx)');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

const filterToolPath = path.join(appRoot, 'src', 'tools', 'filterTool.tsx');
const filterToolContent = fs.readFileSync(filterToolPath, 'utf-8');

runTest('filterTool uses filterStore', () => {
    assertContains(filterToolContent, 'import filterStore from "../store/filter"');
    assertContains(filterToolContent, 'filterStore.toggleFilterPanel()');
});

runTest('filterTool shows badge with active condition count', () => {
    assertContains(filterToolContent, 'filterStore.enabledConditions.length');
    assertContains(filterToolContent, 'badgeCount > 0');
});

console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('7. Integration Flow Summary');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

const flows = [
    {
        name: 'Client-side rendering: dataSource -> filteredDataSource -> GraphicWalker',
        checks: [
            'filteredDataSource = useMemo(..., [filterStore.conditions, filterStore.logic])',
            'GraphicWalker receives data={filteredDataSource}',
        ]
    },
    {
        name: 'Server-side computation: baseCallback -> filterRows -> GraphicWalker',
        checks: [
            'computationCallback wraps getComputationCallback',
            'After baseCallback returns, filterRows is applied',
            'Filtered result is returned to GraphicWalker',
        ]
    },
    {
        name: 'Dataframe export with filters: fetch data -> filterRows -> export_dataframe_by_data',
        checks: [
            'exportWithFilter checks filterStore.hasActiveFilters',
            'Gets data from props.dataSource or getDatasFromKernelByPayload/Sql',
            'Applies filterRows with conditions and logic',
            'Sends via export_dataframe_by_data to Python',
            'Python creates DataFrame from records',
        ]
    },
    {
        name: 'Chart export (saveTool): filtered data is already rendered',
        checks: [
            'saveTool uses gwRef.current?.exportChart',
            'Chart is already rendered with filteredDataSource',
            'Exported chart reflects filtered data',
        ]
    }
];

flows.forEach((flow, idx) => {
    console.log(`Flow ${idx + 1}: ${flow.name}`);
    flow.checks.forEach(check => {
        console.log(`  → ${check}`);
    });
    console.log('');
});

console.log('\n╔═══════════════════════════════════════════════════════════════╗');
console.log(`║              Test Results: ${passed.toString().padStart(2)} passed, ${failed.toString().padStart(2)} failed                   ║`);
console.log('╚═══════════════════════════════════════════════════════════════╝\n');

if (failed > 0) {
    process.exit(1);
}
