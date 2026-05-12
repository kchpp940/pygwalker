export type FilterConditionType = "range" | "temporal range" | "one of" | "not in" | "contains" | "equals" | "greater than" | "less than";

export interface IFilterCondition {
    id: string;
    fid: string;
    fieldName: string;
    fieldType: "dimension" | "measure";
    conditionType: FilterConditionType;
    value: any;
    enabled: boolean;
}

export type FilterLogic = "AND" | "OR";

export interface IEnhancedFilterState {
    conditions: IFilterCondition[];
    logic: FilterLogic;
    estimatedCount: number | null;
}

export interface IFieldMeta {
    fid: string;
    name: string;
    semanticType: "nominal" | "ordinal" | "quantitative" | "temporal";
}

export interface IFilterValue {
    range?: [number, number];
    temporalRange?: [number, number];
    oneOf?: any[];
    notIn?: any[];
    contains?: string;
    equals?: any;
    greaterThan?: number;
    lessThan?: number;
}
