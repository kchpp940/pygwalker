
import { 
    matchCondition, 
    filterRows, 
    estimateFilteredCount,
    getConditionTypeByFieldType,
    getDefaultValueForConditionType
} from './filter';
import type { IFilterCondition } from '../interfaces/filter';
import type { IRow } from '@kanaries/graphic-walker/interfaces';

const mockData: IRow[] = [
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
console.log('║           Enhanced Filter Utils Verification Tests            ║');
console.log('╚═══════════════════════════════════════════════════════════════╝\n');

console.log('Test Data (6 rows):');
mockData.forEach(row => {
    console.log(`  ID:${row.id} ${row.name}, Age:${row.age}, City:${row.city}, Score:${row.score}`);
});
console.log('');

console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('1. Helper Functions');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

runTest('getConditionTypeByFieldType - quantitative', () => {
    const types = getConditionTypeByFieldType('quantitative');
    assertEqual(types, ['range', 'equals', 'greater than', 'less than']);
});

runTest('getConditionTypeByFieldType - temporal', () => {
    const types = getConditionTypeByFieldType('temporal');
    assertEqual(types, ['temporal range']);
});

runTest('getConditionTypeByFieldType - nominal', () => {
    const types = getConditionTypeByFieldType('nominal');
    assertEqual(types, ['one of', 'not in', 'contains', 'equals']);
});

runTest('getDefaultValueForConditionType - range', () => {
    assertEqual(getDefaultValueForConditionType('range'), [null, null]);
});

runTest('getDefaultValueForConditionType - one of', () => {
    assertEqual(getDefaultValueForConditionType('one of'), []);
});

console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('2. Single Condition Matching');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

runTest('Range [25, 35] - matches Alice(25), Bob(30), Charlie(35)', () => {
    const cond = createCondition({ fid: 'age', conditionType: 'range', value: [25, 35] });
    assert(matchCondition(mockData[0], cond) === true); // Alice 25
    assert(matchCondition(mockData[1], cond) === true); // Bob 30
    assert(matchCondition(mockData[2], cond) === true); // Charlie 35
    assert(matchCondition(mockData[4], cond) === false); // Eve 40
});

runTest('One of [New York, London] - matches 5 rows', () => {
    const cond = createCondition({ fid: 'city', conditionType: 'one of', value: ['New York', 'London'] });
    assert(matchCondition(mockData[0], cond) === true); // New York
    assert(matchCondition(mockData[3], cond) === false); // Paris
});

runTest('Not in [New York, London] - matches only Diana(Paris)', () => {
    const cond = createCondition({ fid: 'city', conditionType: 'not in', value: ['New York', 'London'] });
    assert(matchCondition(mockData[0], cond) === false); // New York
    assert(matchCondition(mockData[3], cond) === true); // Paris
});

runTest('Contains "ali" (case insensitive) - matches Alice', () => {
    const cond = createCondition({ fid: 'name', conditionType: 'contains', value: 'ali' });
    assert(matchCondition(mockData[0], cond) === true); // Alice
    assert(matchCondition(mockData[1], cond) === false); // Bob
});

runTest('Equals "Alice" - matches only Alice', () => {
    const cond = createCondition({ fid: 'name', conditionType: 'equals', value: 'Alice' });
    assert(matchCondition(mockData[0], cond) === true);
    assert(matchCondition(mockData[1], cond) === false);
});

runTest('Greater than 30 - matches Charlie(35), Eve(40)', () => {
    const cond = createCondition({ fid: 'age', conditionType: 'greater than', value: 30 });
    assert(matchCondition(mockData[1], cond) === false); // Bob 30
    assert(matchCondition(mockData[2], cond) === true); // Charlie 35
    assert(matchCondition(mockData[4], cond) === true); // Eve 40
});

runTest('Less than 30 - matches Alice(25), Diana(28), Frank(22)', () => {
    const cond = createCondition({ fid: 'age', conditionType: 'less than', value: 30 });
    assert(matchCondition(mockData[0], cond) === true); // Alice 25
    assert(matchCondition(mockData[1], cond) === false); // Bob 30
});

console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('3. AND Logic (All conditions must match)');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

runTest('No conditions - returns all 6 rows', () => {
    const result = filterRows(mockData, [], "AND");
    assertEqual(result.length, 6);
    assertEqual(result, mockData);
});

runTest('City=New York AND Age<30 - matches Alice(25), Frank(22)', () => {
    const conditions: IFilterCondition[] = [
        createCondition({ fid: 'city', conditionType: 'one of', value: ['New York'] }),
        createCondition({ fid: 'age', conditionType: 'less than', value: 30 })
    ];
    const result = filterRows(mockData, conditions, "AND");
    assertEqual(result.length, 2);
    const names = result.map(r => r.name);
    assert(names.includes('Alice'));
    assert(names.includes('Frank'));
});

runTest('Score>90 AND City in [New York, London] - matches only Alice', () => {
    const conditions: IFilterCondition[] = [
        createCondition({ fid: 'score', conditionType: 'greater than', value: 90 }),
        createCondition({ fid: 'city', conditionType: 'one of', value: ['New York', 'London'] })
    ];
    const result = filterRows(mockData, conditions, "AND");
    assertEqual(result.length, 1);
    assertEqual(result[0].name, 'Alice');
});

console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('4. OR Logic (Any condition matches)');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

runTest('Name=Alice OR City=Paris - matches Alice, Diana', () => {
    const conditions: IFilterCondition[] = [
        createCondition({ fid: 'name', conditionType: 'equals', value: 'Alice' }),
        createCondition({ fid: 'city', conditionType: 'one of', value: ['Paris'] })
    ];
    const result = filterRows(mockData, conditions, "OR");
    assertEqual(result.length, 2);
    const names = result.map(r => r.name);
    assert(names.includes('Alice'));
    assert(names.includes('Diana'));
});

runTest('Age>35 OR Score>90 - matches Eve(40), Alice(95.5)', () => {
    const conditions: IFilterCondition[] = [
        createCondition({ fid: 'age', conditionType: 'greater than', value: 35 }),
        createCondition({ fid: 'score', conditionType: 'greater than', value: 90 })
    ];
    const result = filterRows(mockData, conditions, "OR");
    assertEqual(result.length, 2);
    const names = result.map(r => r.name);
    assert(names.includes('Alice'));
    assert(names.includes('Eve'));
});

runTest('Complex OR: Paris OR Score>90 OR Age<25 - 3 matches', () => {
    const conditions: IFilterCondition[] = [
        createCondition({ fid: 'city', conditionType: 'one of', value: ['Paris'] }),
        createCondition({ fid: 'score', conditionType: 'greater than', value: 90 }),
        createCondition({ fid: 'age', conditionType: 'less than', value: 25 })
    ];
    const result = filterRows(mockData, conditions, "OR");
    assertEqual(result.length, 3);
    const names = result.map(r => r.name);
    assert(names.includes('Alice')); // score=95.5
    assert(names.includes('Diana')); // Paris
    assert(names.includes('Frank')); // age=22
});

console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('5. Condition Enable/Disable');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

runTest('Disabled condition is ignored - returns all 6 rows', () => {
    const conditions: IFilterCondition[] = [
        createCondition({ fid: 'age', conditionType: 'greater than', value: 100, enabled: false })
    ];
    const result = filterRows(mockData, conditions, "AND");
    assertEqual(result.length, 6);
});

runTest('Mixed enabled/disabled with AND - disabled is ignored', () => {
    const conditions: IFilterCondition[] = [
        createCondition({ fid: 'city', conditionType: 'one of', value: ['New York'] }),
        createCondition({ fid: 'age', conditionType: 'greater than', value: 100, enabled: false })
    ];
    const result = filterRows(mockData, conditions, "AND");
    assertEqual(result.length, 3); // Only the enabled condition applied
});

runTest('All disabled - returns all rows', () => {
    const conditions: IFilterCondition[] = [
        createCondition({ fid: 'city', conditionType: 'one of', value: ['New York'], enabled: false }),
        createCondition({ fid: 'age', conditionType: 'less than', value: 30, enabled: false })
    ];
    const result = filterRows(mockData, conditions, "AND");
    assertEqual(result.length, 6);
});

console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('6. Result Count Estimation');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

runTest('No conditions - estimate returns total (6)', () => {
    const count = estimateFilteredCount(mockData, [], "AND");
    assertEqual(count, 6);
});

runTest('City=New York - estimate returns 3', () => {
    const conditions: IFilterCondition[] = [
        createCondition({ fid: 'city', conditionType: 'one of', value: ['New York'] })
    ];
    const count = estimateFilteredCount(mockData, conditions, "AND");
    assertEqual(count, 3);
});

runTest('Complex AND - estimate matches actual count', () => {
    const conditions: IFilterCondition[] = [
        createCondition({ fid: 'city', conditionType: 'one of', value: ['New York'] }),
        createCondition({ fid: 'age', conditionType: 'less than', value: 30 })
    ];
    const actual = filterRows(mockData, conditions, "AND").length;
    const estimated = estimateFilteredCount(mockData, conditions, "AND");
    assertEqual(estimated, actual);
    assertEqual(estimated, 2);
});

runTest('Complex OR - estimate matches actual count', () => {
    const conditions: IFilterCondition[] = [
        createCondition({ fid: 'city', conditionType: 'one of', value: ['Paris'] }),
        createCondition({ fid: 'score', conditionType: 'greater than', value: 90 })
    ];
    const actual = filterRows(mockData, conditions, "OR").length;
    const estimated = estimateFilteredCount(mockData, conditions, "OR");
    assertEqual(estimated, actual);
});

console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('7. Edge Cases');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

runTest('Empty filter value - one of with empty array matches nothing', () => {
    const conditions: IFilterCondition[] = [
        createCondition({ fid: 'city', conditionType: 'one of', value: [] })
    ];
    const result = filterRows(mockData, conditions, "AND");
    assertEqual(result.length, 0);
});

runTest('Range with only min [30, null] - matches Bob+', () => {
    const conditions: IFilterCondition[] = [
        createCondition({ fid: 'age', conditionType: 'range', value: [30, null] })
    ];
    const result = filterRows(mockData, conditions, "AND");
    assertEqual(result.length, 3); // Bob(30), Charlie(35), Eve(40)
});

runTest('Range with only max [null, 28] - matches Alice, Diana, Frank', () => {
    const conditions: IFilterCondition[] = [
        createCondition({ fid: 'age', conditionType: 'range', value: [null, 28] })
    ];
    const result = filterRows(mockData, conditions, "AND");
    assertEqual(result.length, 3); // Alice(25), Diana(28), Frank(22)
});

console.log('\n╔═══════════════════════════════════════════════════════════════╗');
console.log(`║              Test Results: ${passed.toString().padStart(2)} passed, ${failed.toString().padStart(2)} failed                   ║`);
console.log('╚═══════════════════════════════════════════════════════════════╝\n');

if (failed > 0) {
    process.exit(1);
}
