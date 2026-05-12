import { chartToWorkflow } from "@kanaries/graphic-walker/utils/workflow";
import type { IChart } from "@kanaries/graphic-walker/interfaces";
import type { SpecExportData, ExportResult, ExportOptions } from './types';
import { fileDownloadService } from './fileDownloadService';

export const jsonExportService = {
    buildSpecData(
        visSpec: IChart[],
        version: string
    ): SpecExportData {
        return {
            config: visSpec,
            chart_map: {},
            workflow_list: visSpec.map(spec => chartToWorkflow(spec)),
            version
        };
    },

    serializeSpecData(data: SpecExportData): string {
        return JSON.stringify(data, null, 2);
    },

    parseSpecData(jsonStr: string): SpecExportData {
        return JSON.parse(jsonStr);
    },

    async exportSpec(
        visSpec: IChart[],
        version: string,
        options: ExportOptions = {}
    ): Promise<ExportResult> {
        const specData = this.buildSpecData(visSpec, version);
        const jsonStr = this.serializeSpecData(specData);
        
        const filename = options.filename || 
            `pygwalker_spec_${fileDownloadService.generateTimestamp()}.json`;
        
        return fileDownloadService.downloadText(
            jsonStr,
            filename,
            'application/json;charset=utf-8'
        );
    },

    exportSpecToBlob(
        visSpec: IChart[],
        version: string
    ): Blob {
        const specData = this.buildSpecData(visSpec, version);
        const jsonStr = this.serializeSpecData(specData);
        return new Blob([jsonStr], { type: 'application/json;charset=utf-8' });
    },

    getWorkflowFromSpec(visSpec: IChart[]) {
        return visSpec.map(spec => chartToWorkflow(spec));
    },

    validateSpecData(data: any): data is SpecExportData {
        return (
            Array.isArray(data.config) &&
            typeof data.chart_map === 'object' &&
            Array.isArray(data.workflow_list) &&
            typeof data.version === 'string'
        );
    }
};

export type JsonExportService = typeof jsonExportService;
