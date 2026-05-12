import type { IChartExportResult, IChart } from '@kanaries/graphic-walker/interfaces';
import type { ExportFormat, ExportOptions, ExportResult, FormattedChartData, SpecExportData } from './types';
import { imageExportService } from './imageExportService';
import { jsonExportService } from './jsonExportService';
import { codeExportService } from './codeExportService';
import { fileDownloadService } from './fileDownloadService';
import { zipService } from './zipService';
import { notificationService } from './notificationService';

export interface ExportPngOptions extends ExportOptions {
    chartData: IChartExportResult;
}

export interface ExportJsonOptions extends ExportOptions {
    visSpec: IChart[];
    version: string;
}

export interface ExportCodeOptions extends ExportOptions {
    visSpec: IChart[];
    version: string;
    sourceCode?: string;
    codeType: 'python' | 'json';
}

export interface ExportAllOptions extends ExportOptions {
    chartData?: IChartExportResult;
    visSpec: IChart[];
    version: string;
    formats: ExportFormat[];
    sourceCode?: string;
}

export const exportService = {
    async exportPng(options: ExportPngOptions): Promise<ExportResult> {
        return imageExportService.exportPng(options.chartData, options);
    },

    async formatChartData(chartData: IChartExportResult): Promise<FormattedChartData> {
        return imageExportService.formatChartData(chartData);
    },

    async exportJson(options: ExportJsonOptions): Promise<ExportResult> {
        return jsonExportService.exportSpec(options.visSpec, options.version, options);
    },

    buildSpecData(visSpec: IChart[], version: string): SpecExportData {
        return jsonExportService.buildSpecData(visSpec, version);
    },

    async exportCode(options: ExportCodeOptions): Promise<ExportResult> {
        if (options.codeType === 'python' && options.sourceCode) {
            return codeExportService.exportPythonCode(
                options.sourceCode,
                options.visSpec,
                options.version,
                options
            );
        }
        return codeExportService.exportJsonCode(options.visSpec, options);
    },

    async copyPythonCode(sourceCode: string, visSpec: IChart[], version: string): Promise<boolean> {
        return codeExportService.copyPythonCode(sourceCode, visSpec, version);
    },

    async copyJsonCode(visSpec: IChart[]): Promise<boolean> {
        return codeExportService.copyJsonCode(visSpec);
    },

    generatePythonCode(sourceCode: string, visSpec: IChart[], version: string): string {
        return codeExportService.generatePythonCode(sourceCode, visSpec, version);
    },

    generateJsonCode(visSpec: IChart[]): string {
        return codeExportService.generateJsonCode(visSpec);
    },

    async exportAll(options: ExportAllOptions): Promise<ExportResult> {
        const entries: Array<{ filename: string; content: string | Blob; compress?: boolean }> = [];
        const timestamp = fileDownloadService.generateTimestamp();

        if (options.formats.includes('png') && options.chartData) {
            const formattedData = await this.formatChartData(options.chartData);
            if (formattedData.singleChart) {
                const blob = fileDownloadService.dataUrlToBlob(formattedData.singleChart);
                entries.push({
                    filename: `chart_${timestamp}.png`,
                    content: blob,
                    compress: false
                });
            }
        }

        if (options.formats.includes('json')) {
            const specData = this.buildSpecData(options.visSpec, options.version);
            entries.push({
                filename: `spec_${timestamp}.json`,
                content: JSON.stringify(specData, null, 2),
                compress: true
            });
        }

        if (options.formats.includes('code') && options.sourceCode) {
            const pythonCode = this.generatePythonCode(
                options.sourceCode,
                options.visSpec,
                options.version
            );
            entries.push({
                filename: `pygwalker_code_${timestamp}.py`,
                content: pythonCode,
                compress: true
            });
        }

        if (entries.length === 0) {
            return {
                success: false,
                error: 'No valid export formats selected'
            };
        }

        if (entries.length === 1) {
            const entry = entries[0];
            return fileDownloadService.download({
                filename: options.filename || entry.filename,
                data: entry.content,
                type: this.getMimeType(entry.filename)
            });
        }

        return zipService.exportZip(entries, {
            filename: options.filename || `pygwalker_export_${timestamp}.zip`
        });
    },

    getMimeType(filename: string): string {
        if (filename.endsWith('.png')) return 'image/png';
        if (filename.endsWith('.json')) return 'application/json;charset=utf-8';
        if (filename.endsWith('.py')) return 'text/plain;charset=utf-8';
        return 'application/octet-stream';
    },

    notify: notificationService
};

export type ExportService = typeof exportService;
