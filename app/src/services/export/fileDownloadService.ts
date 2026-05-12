import type { DownloadOptions, ExportResult } from './types';

export const fileDownloadService = {
    async download(options: DownloadOptions): Promise<ExportResult> {
        try {
            const blob = this.createBlob(options.data, options.type);
            this.triggerDownload(blob, options.filename);
            return {
                success: true,
                filename: options.filename
            };
        } catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : 'Failed to download file'
            };
        }
    },

    createBlob(data: string | Blob, type: string): Blob {
        if (data instanceof Blob) {
            return data;
        }
        return new Blob([data], { type });
    },

    triggerDownload(blob: Blob, filename: string): void {
        const url = URL.createObjectURL(blob);
        
        if (this.isIEBrowser()) {
            this.downloadForIE(blob, filename);
        } else {
            this.downloadForModernBrowsers(url, filename);
        }
        
        setTimeout(() => {
            URL.revokeObjectURL(url);
        }, 100);
    },

    downloadForModernBrowsers(url: string, filename: string): void {
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        setTimeout(() => {
            document.body.removeChild(link);
        }, 0);
    },

    downloadForIE(blob: Blob, filename: string): void {
        const navigatorWindow = window.navigator as any;
        if (navigatorWindow.msSaveOrOpenBlob) {
            navigatorWindow.msSaveOrOpenBlob(blob, filename);
        }
    },

    isIEBrowser(): boolean {
        const navigatorWindow = window.navigator as any;
        return typeof navigatorWindow.msSaveOrOpenBlob !== 'undefined';
    },

    downloadText(content: string, filename: string, type: string = 'text/plain;charset=utf-8'): Promise<ExportResult> {
        return this.download({
            filename,
            data: content,
            type
        });
    },

    downloadJSON(data: any, filename: string): Promise<ExportResult> {
        return this.download({
            filename,
            data: JSON.stringify(data, null, 2),
            type: 'application/json;charset=utf-8'
        });
    },

    downloadFromDataUrl(dataUrl: string, filename: string): Promise<ExportResult> {
        const type = this.getMimeTypeFromDataUrl(dataUrl);
        const blob = this.dataUrlToBlob(dataUrl);
        return this.download({
            filename,
            data: blob,
            type
        });
    },

    dataUrlToBlob(dataUrl: string): Blob {
        const parts = dataUrl.split(',');
        const byteString = atob(parts[1]);
        const mimeString = parts[0].split(':')[1].split(';')[0];
        
        const arrayBuffer = new ArrayBuffer(byteString.length);
        const uint8Array = new Uint8Array(arrayBuffer);
        
        for (let i = 0; i < byteString.length; i++) {
            uint8Array[i] = byteString.charCodeAt(i);
        }
        
        return new Blob([arrayBuffer], { type: mimeString });
    },

    getMimeTypeFromDataUrl(dataUrl: string): string {
        const match = dataUrl.match(/^data:([^;]+);base64,/);
        return match ? match[1] : 'application/octet-stream';
    },

    generateTimestamp(): string {
        return new Date().getTime().toString();
    }
};

export type FileDownloadService = typeof fileDownloadService;
