
import { filterRows } from './filter';
import type { IFilterCondition } from '../interfaces/filter';
import type { IRow } from '@kanaries/graphic-walker/interfaces';

let passed = 0;
let failed = 0;

const assert = (condition: boolean, message?: string) => {
    if (!condition) {
        throw new Error(message || 'Assertion failed');
    }
};

const assertEqual = (actual: any, expected: any, message?: string) => {
    const actualStr = JSON.stringify(actual);
    const expectedStr = JSON.stringify(expected);
    if (actualStr !== expectedStr) {
        throw new Error(message || `Expected ${expectedStr}, got ${actualStr}`);
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

console.log('\n╔═══════════════════════════════════════════════════════════════╗');
console.log('║        Export Dataframe Flow Verification Tests              ║');
console.log('╚═══════════════════════════════════════════════════════════════╝\n');

const mockDataSource: IRow[] = [
    { id: 1, name: 'Alice', age: 25, city: 'New York', score: 95.5, active: true },
    { id: 2, name: 'Bob', age: 30, city: 'London', score: 85.0, active: true },
    { id: 3, name: 'Charlie', age: 35, city: 'New York', score: 75.5, active: false },
    { id: 4, name: 'Diana', age: 28, city: 'Paris', score: 90.0, active: true },
    { id: 5, name: 'Eve', age: 40, city: 'London', score: 65.0, active: false },
    { id: 6, name: 'Frank', age: 22, city: 'New York', score: 88.5, active: true },
];

function createCondition(partial: Partial<IFilterCondition>): IFilterCondition {
    return {
        id: 'test-id',
        fid: 'id',
        fieldName: 'ID',
        fieldType: 'measure',
        conditionType: 'range',
        value: null,
        enabled: true,
        ...partial
    };
}

console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('1. Filter Logic for Export');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

runTest('Original data has 6 rows', () => {
    assertEqual(mockDataSource.length, 6);
});

runTest('filterRows with AND: city=New York AND age<30 -> 2 rows', () => {
    const conditions: IFilterCondition[] = [
        createCondition({ fid: 'city', conditionType: 'one of', value: ['New York'] }),
        createCondition({ fid: 'age', conditionType: 'less than', value: 30 })
    ];
    const filtered = filterRows(mockDataSource, conditions, "AND");
    assertEqual(filtered.length, 2);
    const names = filtered.map(r => r.name);
    assert(names.includes('Alice'));
    assert(names.includes('Frank'));
});

runTest('filterRows with OR: name=Alice OR city=Paris -> 2 rows', () => {
    const conditions: IFilterCondition[] = [
        createCondition({ fid: 'name', conditionType: 'equals', value: 'Alice' }),
        createCondition({ fid: 'city', conditionType: 'one of', value: ['Paris'] })
    ];
    const filtered = filterRows(mockDataSource, conditions, "OR");
    assertEqual(filtered.length, 2);
    const names = filtered.map(r => r.name);
    assert(names.includes('Alice'));
    assert(names.includes('Diana'));
});

runTest('Disabled condition is ignored for export', () => {
    const conditions: IFilterCondition[] = [
        createCondition({ fid: 'city', conditionType: 'one of', value: ['New York'] }),
        createCondition({ fid: 'age', conditionType: 'greater than', value: 100, enabled: false })
    ];
    const filtered = filterRows(mockDataSource, conditions, "AND");
    assertEqual(filtered.length, 3); // Only first condition applied
});

console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('2. Simulate export_dataframe_by_data Payload Construction');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

interface ExportPayload {
    records: IRow[];
    encodings?: any;
}

function buildExportPayload(
    dataSource: IRow[],
    conditions: IFilterCondition[],
    logic: "AND" | "OR",
    encodings?: any
): ExportPayload {
    let records = [...dataSource];
    
    const hasActiveFilters = conditions.filter(c => c.enabled).length > 0;
    if (hasActiveFilters) {
        records = filterRows(records, conditions, logic);
    }
    
    return {
        records,
        encodings
    };
}

runTest('Build payload without filters -> contains all 6 rows', () => {
    const payload = buildExportPayload(mockDataSource, [], "AND", {});
    assertEqual(payload.records.length, 6);
    assert(payload.encodings !== undefined);
});

runTest('Build payload with filters -> contains only filtered rows', () => {
    const conditions: IFilterCondition[] = [
        createCondition({ fid: 'city', conditionType: 'one of', value: ['New York'] }),
        createCondition({ fid: 'age', conditionType: 'less than', value: 30 })
    ];
    const payload = buildExportPayload(mockDataSource, conditions, "AND", { x: 'city' });
    assertEqual(payload.records.length, 2);
    const names = payload.records.map(r => r.name);
    assert(names.includes('Alice'));
    assert(names.includes('Frank'));
    assertEqual(payload.encodings, { x: 'city' });
});

runTest('Build payload with OR logic -> correct filtered rows', () => {
    const conditions: IFilterCondition[] = [
        createCondition({ fid: 'name', conditionType: 'equals', value: 'Alice' }),
        createCondition({ fid: 'city', conditionType: 'one of', value: ['Paris'] })
    ];
    const payload = buildExportPayload(mockDataSource, conditions, "OR");
    assertEqual(payload.records.length, 2);
    const names = payload.records.map(r => r.name);
    assert(names.includes('Alice'));
    assert(names.includes('Diana'));
});

console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('3. Verify Python Handler Signature Match');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

console.log('Python handler expects:');
console.log('  - data.get("records", []) -> List[Dict[str, Any]]');
console.log('  - df = pd.DataFrame(records)');
console.log('  - GlobalVarManager.set_last_exported_dataframe(df)');
console.log('');

runTest('Payload structure matches Python handler expectation', () => {
    const conditions: IFilterCondition[] = [
        createCondition({ fid: 'city', conditionType: 'one of', value: ['New York'] })
    ];
    const payload = buildExportPayload(mockDataSource, conditions, "AND");
    
    assert(payload.records !== undefined);
    assert(Array.isArray(payload.records));
    
    const firstRecord = payload.records[0];
    assert(firstRecord !== undefined);
    assert(typeof firstRecord === 'object');
    assert('id' in firstRecord);
    assert('name' in firstRecord);
});

console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('4. End-to-End Flow Simulation');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

console.log('Flow: filterStore.conditions -> filterRows -> export_dataframe_by_data payload');
console.log('');

function simulateExportWithFilterStore(
    dataSource: IRow[],
    conditions: IFilterCondition[],
    logic: "AND" | "OR"
): ExportPayload {
    const hasActiveFilters = conditions.filter(c => c.enabled).length > 0;
    
    console.log('  Step 1: Check filterStore.hasActiveFilters');
    console.log(`    → ${hasActiveFilters ? 'TRUE' : 'FALSE'}`);
    
    let records = [...dataSource];
    
    if (hasActiveFilters) {
        console.log('  Step 2: Apply filterRows with conditions and logic');
        console.log(`    → Conditions: ${conditions.filter(c => c.enabled).length} active`);
        console.log(`    → Logic: ${logic}`);
        records = filterRows(records, conditions, logic);
    }
    
    console.log('  Step 3: Build export_dataframe_by_data payload');
    console.log(`    → Records in payload: ${records.length}`);
    
    return { records };
}

runTest('End-to-end: No filters -> all 6 rows exported', () => {
    console.log('\n  [Scenario] No active filters');
    const payload = simulateExportWithFilterStore(mockDataSource, [], "AND");
    console.log(`  Result: ${payload.records.length} rows exported`);
    assertEqual(payload.records.length, 6);
});

runTest('End-to-end: With filters -> filtered rows exported', () => {
    console.log('\n  [Scenario] Active filters: city=New York AND age<30');
    const conditions: IFilterCondition[] = [
        createCondition({ fid: 'city', conditionType: 'one of', value: ['New York'] }),
        createCondition({ fid: 'age', conditionType: 'less than', value: 30 })
    ];
    const payload = simulateExportWithFilterStore(mockDataSource, conditions, "AND");
    console.log(`  Result: ${payload.records.length} rows exported (expected: 2)`);
    assertEqual(payload.records.length, 2);
    
    const names = payload.records.map(r => r.name);
    console.log(`  Exported names: ${names.join(', ')}`);
    assert(names.includes('Alice'));
    assert(names.includes('Frank'));
});

runTest('End-to-end: With disabled condition -> only active filters applied', () => {
    console.log('\n  [Scenario] Mixed: active + disabled filters');
    const conditions: IFilterCondition[] = [
        createCondition({ fid: 'city', conditionType: 'one of', value: ['New York'] }),
        createCondition({ fid: 'age', conditionType: 'greater than', value: 100, enabled: false })
    ];
    const payload = simulateExportWithFilterStore(mockDataSource, conditions, "AND");
    console.log(`  Result: ${payload.records.length} rows exported (expected: 3)`);
    assertEqual(payload.records.length, 3);
});

console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('5. Verify Code Integration Points');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

import * as fs from 'fs';
import * as path from 'path';

const appRoot = path.join(__dirname, '..', '..');

runTest('exportDataframeTool imports filterStore and filterRows', () => {
    const exportDfPath = path.join(appRoot, 'src', 'tools', 'exportDataframe.tsx');
    const content = fs.readFileSync(exportDfPath, 'utf-8');
    assert(content.includes('import filterStore from "../store/filter"'));
    assert(content.includes('import { filterRows } from "../utils/filter"'));
});

runTest('exportDataframeTool checks filterStore.hasActiveFilters', () => {
    const exportDfPath = path.join(appRoot, 'src', 'tools', 'exportDataframe.tsx');
    const content = fs.readFileSync(exportDfPath, 'utf-8');
    assert(content.includes('if (filterStore.hasActiveFilters)'));
});

runTest('exportDataframeTool uses export_dataframe_by_data message', () => {
    const exportDfPath = path.join(appRoot, 'src', 'tools', 'exportDataframe.tsx');
    const content = fs.readFileSync(exportDfPath, 'utf-8');
    assert(content.includes('export_dataframe_by_data'));
    assert(content.includes('records: dataToExport'));
});

runTest('Python registers export_dataframe_by_data handler', () => {
    const pygwalkerPath = path.join(appRoot, '..', 'pygwalker', 'api', 'pygwalker.py');
    const content = fs.readFileSync(pygwalkerPath, 'utf-8');
    assert(content.includes('def _export_dataframe_by_data'));
    assert(content.includes('comm.register("export_dataframe_by_data", _export_dataframe_by_data)'));
});

console.log('\n╔═══════════════════════════════════════════════════════════════╗');
console.log(`║              Test Results: ${passed.toString().padStart(2)} passed, ${failed.toString().padStart(2)} failed                   ║`);
console.log('╚═══════════════════════════════════════════════════════════════╝\n');

if (failed > 0) {
    process.exit(1);
}
