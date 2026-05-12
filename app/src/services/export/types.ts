import type { IChartExportResult, IChart } from '@kanaries/graphic-walker/interfaces';

export type ExportFormat = 'png' | 'svg' | 'json' | 'code';

export interface ExportOptions {
    filename?: string;
    includeAllCharts?: boolean;
    compress?: boolean;
}

export interface ChartImageData {
    dataUrl: string;
    width: number;
    height: number;
    chartIndex: number;
}

export interface FormattedChartData extends IChartExportResult {
    singleChart: string;
}

export interface SpecExportData {
    config: IChart[];
    chart_map: Record<string, any>;
    workflow_list: any[];
    version: string;
}

export interface CodeExportData {
    python: string;
    json: string;
    visSpec: IChart[];
}

export interface DownloadOptions {
    filename: string;
    data: string | Blob;
    type: string;
}

export interface ZipEntry {
    filename: string;
    content: string | Blob;
    compress?: boolean;
}

export interface ExportResult {
    success: boolean;
    error?: string;
    filename?: string;
}
