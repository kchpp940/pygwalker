import type { IFilterCondition, FilterConditionType } from '../interfaces/filter';
import type { IRow } from '@kanaries/graphic-walker/interfaces';
import { FilterStage, type PipelineContext } from '../dataSource/dataPipeline';

const filterStage = new FilterStage();

export const getConditionTypeByFieldType = (semanticType: string): FilterConditionType[] => {
    switch (semanticType) {
        case "quantitative":
            return ["range", "equals", "greater than", "less than"];
        case "temporal":
            return ["temporal range"];
        case "nominal":
        case "ordinal":
        default:
            return ["one of", "not in", "contains", "equals"];
    }
};

export const getDefaultValueForConditionType = (conditionType: FilterConditionType): any => {
    switch (conditionType) {
        case "range":
        case "temporal range":
            return [null, null];
        case "one of":
        case "not in":
            return [];
        case "contains":
        case "equals":
            return "";
        case "greater than":
        case "less than":
            return null;
        default:
            return null;
    }
};

export const matchCondition = (row: IRow, condition: IFilterCondition): boolean => {
    const value = row[condition.fid];
    
    switch (condition.conditionType) {
        case "range": {
            const [min, max] = condition.value;
            if (typeof value !== 'number') return false;
            const aboveMin = min === null || value >= min;
            const belowMax = max === null || value <= max;
            return aboveMin && belowMax;
        }
        case "temporal range": {
            const [min, max] = condition.value;
            const dateValue = value instanceof Date ? value.getTime() : new Date(value).getTime();
            if (isNaN(dateValue)) return false;
            const aboveMin = min === null || dateValue >= min;
            const belowMax = max === null || dateValue <= max;
            return aboveMin && belowMax;
        }
        case "one of": {
            return condition.value.includes(value);
        }
        case "not in": {
            return !condition.value.includes(value);
        }
        case "contains": {
            if (typeof value !== 'string') return false;
            return value.toLowerCase().includes(condition.value.toLowerCase());
        }
        case "equals": {
            return value === condition.value;
        }
        case "greater than": {
            if (typeof value !== 'number' || condition.value === null) return false;
            return value > condition.value;
        }
        case "less than": {
            if (typeof value !== 'number' || condition.value === null) return false;
            return value < condition.value;
        }
        default:
            return true;
    }
};

export const filterRows = (
    rows: IRow[],
    conditions: IFilterCondition[],
    logic: "AND" | "OR"
): IRow[] => {
    const context: PipelineContext = {
        sourceType: 'client',
        filters: conditions,
        filterLogic: logic,
        preserveBoundaries: false,
        metadata: {}
    };
    
    return filterStage.execute(rows, context);
};

export const estimateFilteredCount = (
    rows: IRow[],
    conditions: IFilterCondition[],
    logic: "AND" | "OR"
): number => {
    return filterRows(rows, conditions, logic).length;
};

export const convertConditionToGraphicWalkerFilter = (condition: IFilterCondition) => {
    switch (condition.conditionType) {
        case "range":
            return {
                fid: condition.fid,
                rule: {
                    type: "range" as const,
                    value: condition.value
                }
            };
        case "temporal range":
            return {
                fid: condition.fid,
                rule: {
                    type: "temporal range" as const,
                    value: condition.value
                }
            };
        case "one of":
            return {
                fid: condition.fid,
                rule: {
                    type: "one of" as const,
                    value: condition.value
                }
            };
        case "not in":
            return {
                fid: condition.fid,
                rule: {
                    type: "not in" as const,
                    value: condition.value
                }
            };
        default:
            return null;
    }
};

export const generateEnhancedFilterPayload = (
    conditions: IFilterCondition[],
    logic: "AND" | "OR"
) => {
    const enabledConditions = conditions.filter(c => c.enabled);
    if (enabledConditions.length === 0) {
        return null;
    }

    const gwFilters = enabledConditions
        .map(convertConditionToGraphicWalkerFilter)
        .filter(Boolean);

    return {
        type: "filter" as const,
        filters: gwFilters,
        enhancedLogic: logic
    };
};

export const getFieldUniqueValues = (
    rows: IRow[],
    fid: string,
    limit: number = 100
): any[] => {
    const values = new Set<any>();
    for (const row of rows) {
        if (values.size >= limit) break;
        const value = row[fid];
        if (value !== null && value !== undefined) {
            values.add(value);
        }
    }
    return Array.from(values);
};

export const getFieldRange = (rows: IRow[], fid: string): [number, number] | null => {
    let min: number | null = null;
    let max: number | null = null;
    
    for (const row of rows) {
        const value = row[fid];
        if (typeof value === 'number') {
            min = min === null ? value : Math.min(min, value);
            max = max === null ? value : Math.max(max, value);
        }
    }
    
    if (min === null || max === null) return null;
    return [min, max];
};
