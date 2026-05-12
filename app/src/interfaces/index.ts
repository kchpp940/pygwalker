import type { IRow, IMutField } from '@kanaries/graphic-walker/interfaces'
import type { IDarkMode, IThemeKey, IComputationFunction } from '@kanaries/graphic-walker/interfaces';

export interface IFieldQuality {
    fid: string;
    missingRate: number;
    uniqueCount: number;
    distinctRate: number;
    dataType: string;
    distribution: IFieldDistribution;
    anomalies: IFieldAnomaly[];
    warnings: string[];
    isSuitableForAnalysis: boolean;
}

export interface IFieldDistribution {
    type: string;
    min?: number;
    max?: number;
    mean?: number;
    stddev?: number;
    variationRatio?: number;
    topValues?: ITopValue[];
    entropy?: number;
    minDate?: string;
    maxDate?: string;
    [key: string]: any;
}

export interface ITopValue {
    value: string;
    count: number;
}

export interface IFieldAnomaly {
    type: string;
    description: string;
    samples?: number[];
    value?: string;
    percentage?: number;
    severity: "low" | "medium" | "high";
}

export interface IAppProps {
    // graphic-walker props
    fieldkeyGuard: boolean;
    themeKey: IThemeKey;
    dark: IDarkMode;
    // pygwalker props
    dataSource: IRow[];
    rawFields: IMutField[];
    id: string;
    dataSourceProps: IDataSourceProps;
    version?: string;
    hashcode?: string;
    visSpec: any;
    userConfig?: IUserConfig;
    env?: string;
    needLoadDatas?: boolean;
    specType: string;
    showCloudTool: boolean;
    enableAskViz: boolean;
    enableVlChat: boolean;
    needInitChart: boolean;
    useKernelCalc: boolean;
    useSaveTool: boolean;
    parseDslType: "server" | "client";
    communicationUrl: string;
    gwMode: "explore" | "renderer" | "filter_renderer" | "table";
    needLoadLastSpec: boolean;
    extraConfig?: any;
    fieldMetas: any;
    fieldQualities?: Record<string, IFieldQuality>;
    isExportDataFrame: boolean;
    defaultTab: "data" | "vis";
}

export interface IDataSourceProps {
    tunnelId: string;
    dataSourceId: string;
}

export interface IUserConfig {
    [key: string]: any;
    privacy: 'events' | 'update-only' | 'offline';
}
