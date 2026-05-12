import * as htmlToImage from 'html-to-image';
import type { IChartExportResult } from '@kanaries/graphic-walker/interfaces';
import type { FormattedChartData, ChartImageData, ExportResult, ExportOptions } from './types';
import { fileDownloadService } from './fileDownloadService';

export const imageExportService = {
    async formatChartData(chartData: IChartExportResult): Promise<FormattedChartData> {
        const chartDom = chartData.container();
        
        if (chartDom === null) {
            return {
                ...chartData,
                singleChart: ''
            };
        }

        if (chartData.charts.length === 0) {
            return {
                ...chartData,
                nCols: 1,
                nRows: 1,
                charts: [{
                    colIndex: 0,
                    rowIndex: 0,
                    width: chartDom.clientWidth,
                    height: chartDom.clientHeight,
                    canvasWidth: chartDom.clientWidth,
                    canvasHeight: chartDom.clientHeight,
                    data: '',
                    canvas: () => null
                }],
                singleChart: ''
            };
        }

        if (this.hasNativeVegaImage(chartData)) {
            return {
                ...chartData,
                singleChart: chartData.charts[0].data
            };
        }

        const singleChart = await this.captureWithHtmlToImage(chartDom);
        return {
            ...chartData,
            singleChart
        };
    },

    hasNativeVegaImage(chartData: IChartExportResult): boolean {
        return (
            chartData.charts.length === 1 &&
            !!chartData.charts[0].data &&
            chartData.charts[0].data.startsWith('data:image/')
        );
    },

    async captureWithHtmlToImage(element: HTMLElement): Promise<string> {
        return htmlToImage.toPng(element, {
            width: element.scrollWidth,
            height: element.scrollHeight
        });
    },

    async exportPng(
        chartData: IChartExportResult,
        options: ExportOptions = {}
    ): Promise<ExportResult> {
        const formattedData = await this.formatChartData(chartData);
        
        if (!formattedData.singleChart) {
            return {
                success: false,
                error: 'Failed to generate image data'
            };
        }

        const filename = options.filename || `chart_${fileDownloadService.generateTimestamp()}.png`;
        
        return fileDownloadService.downloadFromDataUrl(formattedData.singleChart, filename);
    },

    async exportMultiplePng(
        charts: Array<{ data: IChartExportResult; index: number }>,
        options: ExportOptions = {}
    ): Promise<ExportResult[]> {
        const results: ExportResult[] = [];
        
        for (const chart of charts) {
            const result = await this.exportPng(chart.data, {
                ...options,
                filename: options.filename ? 
                    `${options.filename.replace('.png', '')}_${chart.index + 1}.png` :
                    `chart_${chart.index + 1}_${fileDownloadService.generateTimestamp()}.png`
            });
            results.push(result);
        }
        
        return results;
    },

    extractImageData(chartData: IChartExportResult): ChartImageData[] {
        const chartDom = chartData.container();
        const width = chartDom?.clientWidth || 0;
        const height = chartDom?.clientHeight || 0;

        return chartData.charts.map((chart, index) => ({
            dataUrl: chart.data || '',
            width: chart.width || width,
            height: chart.height || height,
            chartIndex: index
        }));
    },

    getImageDimensions(chartData: IChartExportResult): { width: number; height: number } {
        const chartDom = chartData.container();
        return {
            width: chartDom?.scrollWidth || chartData.charts[0]?.canvasWidth || 0,
            height: chartDom?.scrollHeight || chartData.charts[0]?.canvasHeight || 0
        };
    },

    isGeoChart(chartData: IChartExportResult): boolean {
        return chartData.charts.length === 0;
    }
};

export type ImageExportService = typeof imageExportService;
