import type { IRow, IDataQueryPayload } from '@kanaries/graphic-walker/interfaces';
import type { IFilterCondition, FilterLogic } from '../interfaces/filter';

export enum DataPipelineStage {
    SOURCE = "source",
    FILTER = "filter",
    TRANSFORM = "transform",
    SAMPLE = "sample",
    AGGREGATE = "aggregate",
    OUTPUT = "output"
}

export interface PipelineContext {
    sourceType: 'client' | 'server';
    payload?: IDataQueryPayload;
    sql?: string;
    filters: IFilterCondition[];
    filterLogic: FilterLogic;
    samplingStrategy?: 'smart' | 'random' | 'byte_limit' | 'scatter';
    sampleSize?: number;
    byteLimit?: number;
    preserveBoundaries: boolean;
    metadata: Record<string, any>;
}

export interface DataSource {
    getDatasByPayload(payload: IDataQueryPayload): Promise<IRow[]>;
    getDatasBySql(sql: string): Promise<IRow[]>;
    batchGetDatasByPayload(payloadList: IDataQueryPayload[]): Promise<IRow[][]>;
    batchGetDatasBySql(sqlList: string[]): Promise<IRow[][]>;
}

export interface LocalDataSource {
    data: IRow[];
}

export type PipelineExecutor = 
    | { type: 'client'; source: LocalDataSource }
    | { type: 'server'; source: DataSource };

export class PipelineStage {
    name: string;
    
    constructor(name: string) {
        this.name = name;
    }
    
    execute(data: IRow[], context: PipelineContext): IRow[] {
        return data;
    }
}

export class FilterStage extends PipelineStage {
    constructor() {
        super('filter');
    }
    
    execute(data: IRow[], context: PipelineContext): IRow[] {
        if (!context.filters || context.filters.length === 0) {
            return data;
        }
        
        const enabledFilters = context.filters.filter(c => c.enabled);
        if (enabledFilters.length === 0) {
            return data;
        }
        
        return data.filter(row => {
            if (context.filterLogic === "AND") {
                return enabledFilters.every(filter => this.matchCondition(row, filter));
            } else {
                return enabledFilters.some(filter => this.matchCondition(row, filter));
            }
        });
    }
    
    private matchCondition(row: IRow, condition: IFilterCondition): boolean {
        const value = row[condition.fid];
        
        switch (condition.conditionType) {
            case 'range':
                return this.matchRange(value, condition.value);
            case 'temporal range':
                return this.matchTemporalRange(value, condition.value);
            case 'one of':
                return this.matchOneOf(value, condition.value);
            case 'not in':
                return !this.matchOneOf(value, condition.value);
            case 'contains':
                return this.matchContains(value, condition.value);
            case 'equals':
                return value === condition.value;
            case 'greater than':
                return this.matchGreaterThan(value, condition.value);
            case 'less than':
                return this.matchLessThan(value, condition.value);
            default:
                return true;
        }
    }
    
    private matchRange(value: any, rangeValue: [number | null, number | null]): boolean {
        if (!Array.isArray(rangeValue) || rangeValue.length !== 2) {
            return true;
        }
        const [min, max] = rangeValue;
        if (typeof value !== 'number') return false;
        const aboveMin = min === null || value >= min;
        const belowMax = max === null || value <= max;
        return aboveMin && belowMax;
    }
    
    private matchTemporalRange(value: any, rangeValue: [number | null, number | null]): boolean {
        if (!Array.isArray(rangeValue) || rangeValue.length !== 2) {
            return true;
        }
        const [min, max] = rangeValue;
        
        let timestamp: number;
        if (value instanceof Date) {
            timestamp = value.getTime();
        } else if (typeof value === 'string') {
            timestamp = new Date(value).getTime();
        } else if (typeof value === 'number') {
            timestamp = value;
        } else {
            return false;
        }
        
        if (isNaN(timestamp)) return false;
        
        const aboveMin = min === null || timestamp >= min;
        const belowMax = max === null || timestamp <= max;
        return aboveMin && belowMax;
    }
    
    private matchOneOf(value: any, values: any[]): boolean {
        if (!Array.isArray(values)) {
            return true;
        }
        return values.includes(value);
    }
    
    private matchContains(value: any, substring: string): boolean {
        if (typeof value !== 'string' || typeof substring !== 'string') {
            return false;
        }
        return value.toLowerCase().includes(substring.toLowerCase());
    }
    
    private matchGreaterThan(value: any, threshold: number): boolean {
        if (threshold === null || threshold === undefined) {
            return true;
        }
        if (typeof value !== 'number' || typeof threshold !== 'number') {
            return false;
        }
        return value > threshold;
    }
    
    private matchLessThan(value: any, threshold: number): boolean {
        if (threshold === null || threshold === undefined) {
            return true;
        }
        if (typeof value !== 'number' || typeof threshold !== 'number') {
            return false;
        }
        return value < threshold;
    }
}

export class SamplingStage extends PipelineStage {
    constructor() {
        super('sample');
    }
    
    execute(data: IRow[], context: PipelineContext): IRow[] {
        if (!context.samplingStrategy === undefined) {
            return data;
        }
        
        switch (context.samplingStrategy) {
            case 'smart':
                return this.smartSample(data, context);
            case 'random':
                return this.randomSample(data, context);
            case 'scatter':
                return this.scatterSample(data, context);
            default:
                return data;
        }
    }
    
    private smartSample(data: IRow[], context: PipelineContext): IRow[] {
        if (context.sampleSize === undefined || data.length <= context.sampleSize) {
            return data;
        }
        
        const n = data.length;
        const sampleSize = context.sampleSize;
        
        if (context.preserveBoundaries && sampleSize >= 2) {
            const boundaryCount = Math.min(2, sampleSize);
            const middleCount = sampleSize - boundaryCount;
            const middleData = boundaryCount === 2 
                ? data.slice(boundaryCount, -boundaryCount) 
                : data.slice(1);
            
            let sampled: IRow[];
            if (middleData.length <= middleCount) {
                sampled = middleData;
            } else {
                const step = middleData.length / middleCount;
                sampled = [];
                for (let i = 0; i < middleCount; i++) {
                    sampled.push(middleData[Math.floor(i * step)]);
                }
            }
            
            if (boundaryCount === 2) {
                return [data[0], ...sampled, data[data.length - 1]];
            } else {
                return [data[0], ...sampled];
            }
        }
        
        const step = n / sampleSize;
        const result: IRow[] = [];
        for (let i = 0; i < sampleSize; i++) {
            result.push(data[Math.floor(i * step)]);
        }
        return result;
    }
    
    private randomSample(data: IRow[], context: PipelineContext): IRow[] {
        if (context.sampleSize === undefined || data.length <= context.sampleSize) {
            return data;
        }
        
        const indices = new Set<number>();
        while (indices.size < context.sampleSize) {
            indices.add(Math.floor(Math.random() * data.length));
        }
        return Array.from(indices).sort((a, b) => a - b).map(i => data[i]);
    }
    
    private scatterSample(data: IRow[], context: PipelineContext): IRow[] {
        const SCATTER_PLOT_LARGE_DATA_THRESHOLD = 10000;
        const SCATTER_PLOT_SAMPLE_LIMIT = 5000;
        
        const n = data.length;
        
        if (n <= SCATTER_PLOT_LARGE_DATA_THRESHOLD) {
            return data;
        }
        
        const sampleSize = Math.min(SCATTER_PLOT_SAMPLE_LIMIT, Math.floor(SCATTER_PLOT_LARGE_DATA_THRESHOLD / 2));
        
        return this.smartSample(data, {
            ...context,
            sampleSize,
            preserveBoundaries: true
        });
    }
}

export class DataPipeline {
    executor: PipelineExecutor;
    stages: PipelineStage[];
    context: PipelineContext;
    
    constructor(
        executor: PipelineExecutor,
        stages?: PipelineStage[],
        context?: Partial<PipelineContext>
    ) {
        this.executor = executor;
        this.stages = stages || [new FilterStage(), new SamplingStage()];
        this.context = {
            sourceType: executor.type,
            filters: [],
            filterLogic: 'AND',
            preserveBoundaries: false,
            metadata: {},
            ...context
        };
    }
    
    static create(
        executor: PipelineExecutor,
        context?: Partial<PipelineContext>
    ): DataPipeline {
        return new DataPipeline(executor, undefined, context);
    }
    
    configure(updates: Partial<PipelineContext>): DataPipeline {
        this.context = { ...this.context, ...updates };
        return this;
    }
    
    addStage(stage: PipelineStage): DataPipeline {
        this.stages.push(stage);
        return this;
    }
    
    private async fetchData(): Promise<IRow[]> {
        if (this.executor.type === 'client') {
            return [...this.executor.source.data];
        }
        
        if (this.context.payload !== undefined) {
            return this.executor.source.getDatasByPayload(this.context.payload);
        }
        
        if (this.context.sql !== undefined) {
            return this.executor.source.getDatasBySql(this.context.sql);
        }
        
        throw new Error('Either payload or sql must be provided in context');
    }
    
    async execute(
        payload?: IDataQueryPayload,
        sql?: string,
        updates?: Partial<PipelineContext>
    ): Promise<IRow[]> {
        if (payload !== undefined) {
            this.context.payload = payload;
        }
        if (sql !== undefined) {
            this.context.sql = sql;
        }
        if (updates !== undefined) {
            this.configure(updates);
        }
        
        let data = await this.fetchData();
        
        for (const stage of this.stages) {
            data = stage.execute(data, this.context);
        }
        
        return data;
    }
    
    async executeBatch(
        payloadList?: IDataQueryPayload[],
        sqlList?: string[],
        updates?: Partial<PipelineContext>
    ): Promise<IRow[][]> {
        if (updates !== undefined) {
            this.configure(updates);
        }
        
        let rawDatas: IRow[][];
        const executor = this.executor;
        
        if (executor.type === 'client') {
            rawDatas = payloadList?.map(() => [...executor.source.data]) ?? [];
        } else if (payloadList !== undefined) {
            rawDatas = await executor.source.batchGetDatasByPayload(payloadList);
        } else if (sqlList !== undefined) {
            rawDatas = await executor.source.batchGetDatasBySql(sqlList);
        } else {
            throw new Error('Either payloadList or sqlList must be provided');
        }
        
        const results: IRow[][] = [];
        for (const data of rawDatas) {
            let processedData = data;
            for (const stage of this.stages) {
                processedData = stage.execute(processedData, this.context);
            }
            results.push(processedData);
        }
        
        return results;
    }
}

export class PipelineBuilder {
    executor: PipelineExecutor;
    stages: PipelineStage[] = [];
    contextUpdates: Partial<PipelineContext> = {};
    
    constructor(executor: PipelineExecutor) {
        this.executor = executor;
    }
    
    withFilter(filters: IFilterCondition[], logic: FilterLogic = 'AND'): PipelineBuilder {
        if (filters.length > 0) {
            this.stages.push(new FilterStage());
            this.contextUpdates.filters = filters;
            this.contextUpdates.filterLogic = logic;
        }
        return this;
    }
    
    withSampling(
        strategy: 'smart' | 'random' | 'scatter',
        sampleSize?: number,
        preserveBoundaries: boolean = false
    ): PipelineBuilder {
        this.stages.push(new SamplingStage());
        this.contextUpdates.samplingStrategy = strategy;
        if (sampleSize !== undefined) {
            this.contextUpdates.sampleSize = sampleSize;
        }
        this.contextUpdates.preserveBoundaries = preserveBoundaries;
        return this;
    }
    
    withScatterSampling(): PipelineBuilder {
        return this.withSampling('scatter');
    }
    
    withSmartSampling(sampleSize: number, preserveBoundaries: boolean = true): PipelineBuilder {
        return this.withSampling('smart', sampleSize, preserveBoundaries);
    }
    
    withMetadata(metadata: Record<string, any>): PipelineBuilder {
        this.contextUpdates.metadata = {
            ...this.contextUpdates.metadata,
            ...metadata
        };
        return this;
    }
    
    build(): DataPipeline {
        return new DataPipeline(
            this.executor,
            this.stages,
            this.contextUpdates
        );
    }
}

export function createPipelineBuilder(executor: PipelineExecutor): PipelineBuilder {
    return new PipelineBuilder(executor);
}

export function createClientPipeline(
    data: IRow[],
    filters?: IFilterCondition[],
    filterLogic?: FilterLogic
): DataPipeline {
    const builder = createPipelineBuilder({
        type: 'client',
        source: { data }
    });
    
    if (filters && filters.length > 0) {
        builder.withFilter(filters, filterLogic);
    }
    
    return builder.build();
}

export function createServerPipeline(
    source: DataSource,
    filters?: IFilterCondition[],
    filterLogic?: FilterLogic
): DataPipeline {
    const builder = createPipelineBuilder({
        type: 'server',
        source
    });
    
    if (filters && filters.length > 0) {
        builder.withFilter(filters, filterLogic);
    }
    
    return builder.build();
}
