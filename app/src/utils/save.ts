import { imageExportService, fileDownloadService } from '../services/export';
import type { IChartExportResult } from '@kanaries/graphic-walker/interfaces';

export function download(data: string, filename: string, type: string) {
    fileDownloadService.triggerDownload(
        fileDownloadService.createBlob(data, type),
        filename
    );
}

export async function formatExportedChartDatas(chartData: IChartExportResult) {
    return imageExportService.formatChartData(chartData);
}

export function getTimezoneOffsetSeconds(): number {
    return -new Date().getTimezoneOffset() * 60;
}
