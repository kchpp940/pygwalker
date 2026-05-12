import { v4 as uuidv4 } from 'uuid';

interface ITestChart {
    name: string;
    visId: string;
    index: number;
}

interface IBatchManageState {
    spec: ITestChart[];
    isChanged: boolean;
}

function createTestSpec(): ITestChart[] {
    return [
        { name: "Sales Overview", visId: "chart-abc123", index: 0 },
        { name: "Monthly Trends", visId: "chart-def456", index: 1 },
        { name: "Regional Analysis", visId: "chart-ghi789", index: 2 },
        { name: "Customer Segments", visId: "chart-jkl012", index: 3 },
    ];
}

function assert(condition: boolean, message: string): void {
    if (!condition) {
        throw new Error(`Assertion failed: ${message}`);
    }
}

function testBatchRename(): void {
    console.log("\n=== Test: Batch Rename ===");
    
    let state: IBatchManageState = {
        spec: createTestSpec(),
        isChanged: false
    };
    
    const selectedIndices = new Set([1, 2]);
    const sortedIndices = Array.from(selectedIndices).sort((a, b) => a - b);
    
    const newSpec = [...state.spec];
    sortedIndices.forEach((idx, i) => {
        newSpec[idx] = {
            ...newSpec[idx],
            name: `Report ${i + 1}`
        };
    });
    
    state.spec = newSpec;
    state.isChanged = true;
    
    assert(state.isChanged === true, "isChanged should be true after rename");
    assert(state.spec[1].name === "Report 1", "Chart at index 1 should be renamed to 'Report 1'");
    assert(state.spec[2].name === "Report 2", "Chart at index 2 should be renamed to 'Report 2'");
    assert(state.spec[0].name === "Sales Overview", "Unselected chart should remain unchanged");
    
    console.log("✓ Batch rename test passed");
}

function testBatchCopyVisIdUnique(): void {
    console.log("\n=== Test: Batch Copy - visId Uniqueness ===");
    
    let state: IBatchManageState = {
        spec: createTestSpec(),
        isChanged: false
    };
    
    const selectedIndices = new Set([0, 2]);
    const sortedIndices = Array.from(selectedIndices).sort((a, b) => a - b);
    
    const originalVisIds = new Set(state.spec.map(c => c.visId));
    const newCharts: ITestChart[] = [];
    
    sortedIndices.forEach(idx => {
        const chart = JSON.parse(JSON.stringify(state.spec[idx]));
        chart.name = `${chart.name} Copy`;
        chart.visId = `chart-${uuidv4().slice(0, 8)}`;
        newCharts.push(chart);
    });
    
    const lastIdx = sortedIndices[sortedIndices.length - 1];
    state.spec = [
        ...state.spec.slice(0, lastIdx + 1),
        ...newCharts,
        ...state.spec.slice(lastIdx + 1)
    ];
    state.isChanged = true;
    
    assert(state.isChanged === true, "isChanged should be true after copy");
    assert(state.spec.length === 6, "Should have 6 charts after copying 2");
    
    const allVisIds = state.spec.map(c => c.visId);
    const uniqueVisIds = new Set(allVisIds);
    assert(uniqueVisIds.size === allVisIds.length, "All visIds should be unique");
    
    const originalWithCopySuffix = state.spec.filter(c => c.name.includes("Copy"));
    assert(originalWithCopySuffix.length === 2, "Should have 2 charts with 'Copy' suffix");
    
    newCharts.forEach(newChart => {
        assert(!originalVisIds.has(newChart.visId), `New visId ${newChart.visId} should not exist in original`);
    });
    
    console.log("✓ Batch copy visId uniqueness test passed");
}

function testBatchSorting(): void {
    console.log("\n=== Test: Batch Sorting/Move ===");
    
    let state: IBatchManageState = {
        spec: createTestSpec(),
        isChanged: false
    };
    
    const selectedIndices = new Set([2, 3]);
    const selectedItems = Array.from(selectedIndices)
        .sort((a, b) => a - b)
        .map(i => state.spec[i]);
    
    const remaining = state.spec.filter((_, i) => !selectedIndices.has(i));
    
    const newSpec = [...selectedItems, ...remaining];
    state.spec = newSpec;
    state.isChanged = true;
    
    assert(state.isChanged === true, "isChanged should be true after move");
    assert(state.spec[0].visId === "chart-ghi789", "Chart 'Regional Analysis' should be at index 0");
    assert(state.spec[1].visId === "chart-jkl012", "Chart 'Customer Segments' should be at index 1");
    assert(state.spec[2].visId === "chart-abc123", "Chart 'Sales Overview' should be at index 2");
    assert(state.spec[3].visId === "chart-def456", "Chart 'Monthly Trends' should be at index 3");
    
    console.log("✓ Batch sorting test passed");
}

function testBatchGroupAndRestore(): void {
    console.log("\n=== Test: Batch Group and Restore ===");
    
    let state: IBatchManageState = {
        spec: createTestSpec(),
        isChanged: false
    };
    
    const groupName = "Sales Reports";
    const selectedIndices = new Set([0, 1]);
    
    const newSpec = [...state.spec];
    selectedIndices.forEach(idx => {
        newSpec[idx] = {
            ...newSpec[idx],
            name: `[${groupName}] ${newSpec[idx].name}`
        };
    });
    state.spec = newSpec;
    state.isChanged = true;
    
    assert(state.isChanged === true, "isChanged should be true after grouping");
    assert(state.spec[0].name.startsWith(`[${groupName}]`), "Chart 0 should have group prefix");
    assert(state.spec[1].name.startsWith(`[${groupName}]`), "Chart 1 should have group prefix");
    
    const groupedCharts = state.spec.filter(c => c.name.startsWith(`[${groupName}]`));
    assert(groupedCharts.length === 2, "Should have 2 grouped charts");
    
    const restoreSpec = state.spec.map(chart => ({
        ...chart,
        name: chart.name.replace(/^\[.*?\]\s*/, "")
    }));
    
    assert(restoreSpec[0].name === "Sales Overview", "Should be able to restore original name");
    assert(restoreSpec[1].name === "Monthly Trends", "Should be able to restore original name");
    
    console.log("✓ Batch group and restore test passed");
}

function testBatchDelete(): void {
    console.log("\n=== Test: Batch Delete ===");
    
    let state: IBatchManageState = {
        spec: createTestSpec(),
        isChanged: false
    };
    
    const selectedIndices = new Set([1, 3]);
    const originalLength = state.spec.length;
    
    const newSpec = state.spec.filter((_, i) => !selectedIndices.has(i));
    state.spec = newSpec;
    state.isChanged = true;
    
    assert(state.isChanged === true, "isChanged should be true after delete");
    assert(state.spec.length === originalLength - 2, "Should have 2 fewer charts");
    
    const remainingNames = state.spec.map(c => c.name);
    assert(!remainingNames.includes("Monthly Trends"), "Deleted chart should not be in spec");
    assert(!remainingNames.includes("Customer Segments"), "Deleted chart should not be in spec");
    assert(remainingNames.includes("Sales Overview"), "Undeleted chart should remain");
    assert(remainingNames.includes("Regional Analysis"), "Undeleted chart should remain");
    
    console.log("✓ Batch delete test passed");
}

function testSpecPersistenceAndReload(): void {
    console.log("\n=== Test: Spec Persistence and Reload ===");
    
    let state: IBatchManageState = {
        spec: createTestSpec(),
        isChanged: false
    };
    
    const selectedIndices = new Set([2, 3]);
    const sortedIndices = Array.from(selectedIndices).sort((a, b) => a - b);
    const selectedItems = sortedIndices.map(i => state.spec[i]);
    const remaining = state.spec.filter((_, i) => !selectedIndices.has(i));
    
    const movedSpec = [...selectedItems, ...remaining];
    state.spec = movedSpec;
    state.isChanged = true;
    
    const savedSpec = JSON.parse(JSON.stringify(state.spec));
    
    const reloadedSpec = savedSpec;
    
    assert(reloadedSpec[0].visId === "chart-ghi789", "After reload, chart 0 should be 'Regional Analysis'");
    assert(reloadedSpec[1].visId === "chart-jkl012", "After reload, chart 1 should be 'Customer Segments'");
    assert(reloadedSpec[2].visId === "chart-abc123", "After reload, chart 2 should be 'Sales Overview'");
    assert(reloadedSpec[3].visId === "chart-def456", "After reload, chart 3 should be 'Monthly Trends'");
    
    assert(reloadedSpec.length === movedSpec.length, "Reloaded spec should have same length");
    reloadedSpec.forEach((chart: ITestChart, idx: number) => {
        assert(chart.visId === movedSpec[idx].visId, `Chart at index ${idx} should match`);
        assert(chart.name === movedSpec[idx].name, `Chart name at index ${idx} should match`);
    });
    
    console.log("✓ Spec persistence and reload test passed");
}

function runAllTests(): void {
    console.log("=" .repeat(50));
    console.log("Batch Management Validation Tests");
    console.log("=" .repeat(50));
    
    try {
        testBatchRename();
        testBatchCopyVisIdUnique();
        testBatchSorting();
        testBatchGroupAndRestore();
        testBatchDelete();
        testSpecPersistenceAndReload();
        
        console.log("\n" + "=" .repeat(50));
        console.log("✓ All tests passed!");
        console.log("=" .repeat(50));
    } catch (error) {
        console.error("\n✗ Test failed:", (error as Error).message);
        console.error("Stack:", (error as Error).stack);
        process.exit(1);
    }
}

runAllTests();
