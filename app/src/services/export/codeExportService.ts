import { chartToWorkflow } from "@kanaries/graphic-walker/utils/workflow";
import type { IChart } from "@kanaries/graphic-walker/interfaces";
import type { CodeExportData, ExportResult, ExportOptions } from './types';
import { fileDownloadService } from './fileDownloadService';

export const codeExportService = {
    generatePygConfig(visSpec: IChart[], version: string): string {
        const config = {
            config: visSpec,
            chart_map: {},
            workflow_list: visSpec.map((spec) => chartToWorkflow(spec)),
            version
        };
        return JSON.stringify(config);
    },

    generatePythonCode(sourceCode: string, visSpec: IChart[], version: string): string {
        const pygConfig = this.generatePygConfig(visSpec, version);
        const preCode = sourceCode.replace("'____pyg_walker_spec_params____'", "vis_spec");
        return `vis_spec = r"""${pygConfig}"""\n${preCode}`;
    },

    generateJsonCode(visSpec: IChart[]): string {
        return JSON.stringify(visSpec, null, 2);
    },

    buildCodeExportData(
        sourceCode: string,
        visSpec: IChart[],
        version: string
    ): CodeExportData {
        return {
            python: this.generatePythonCode(sourceCode, visSpec, version),
            json: this.generateJsonCode(visSpec),
            visSpec
        };
    },

    async exportPythonCode(
        sourceCode: string,
        visSpec: IChart[],
        version: string,
        options: ExportOptions = {}
    ): Promise<ExportResult> {
        const pythonCode = this.generatePythonCode(sourceCode, visSpec, version);
        const filename = options.filename || 
            `pygwalker_code_${fileDownloadService.generateTimestamp()}.py`;
        
        return fileDownloadService.downloadText(
            pythonCode,
            filename,
            'text/plain;charset=utf-8'
        );
    },

    async exportJsonCode(
        visSpec: IChart[],
        options: ExportOptions = {}
    ): Promise<ExportResult> {
        const jsonCode = this.generateJsonCode(visSpec);
        const filename = options.filename || 
            `pygwalker_spec_${fileDownloadService.generateTimestamp()}.json`;
        
        return fileDownloadService.downloadText(
            jsonCode,
            filename,
            'application/json;charset=utf-8'
        );
    },

    async copyToClipboard(content: string): Promise<boolean> {
        try {
            await navigator.clipboard.writeText(content);
            return true;
        } catch (e) {
            return false;
        }
    },

    async copyPythonCode(
        sourceCode: string,
        visSpec: IChart[],
        version: string
    ): Promise<boolean> {
        const code = this.generatePythonCode(sourceCode, visSpec, version);
        return this.copyToClipboard(code);
    },

    async copyJsonCode(visSpec: IChart[]): Promise<boolean> {
        const code = this.generateJsonCode(visSpec);
        return this.copyToClipboard(code);
    }
};

export type CodeExportService = typeof codeExportService;
