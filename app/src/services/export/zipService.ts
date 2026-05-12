import JSZip from 'jszip';
import type { ZipEntry, ExportResult, ExportOptions } from './types';
import { fileDownloadService } from './fileDownloadService';

export const zipService = {
    async createZip(entries: ZipEntry[]): Promise<JSZip> {
        const zip = new JSZip();
        
        for (const entry of entries) {
            const compression = entry.compress ? 'DEFLATE' : undefined;
            
            if (typeof entry.content === 'string') {
                zip.file(entry.filename, entry.content, { compression });
            } else {
                zip.file(entry.filename, entry.content, { compression });
            }
        }
        
        return zip;
    },

    async generateZipBlob(zip: JSZip, compress: boolean = true): Promise<Blob> {
        return zip.generateAsync({
            type: 'blob',
            compression: compress ? 'DEFLATE' : 'STORE',
            compressionOptions: { level: 6 }
        });
    },

    async exportZip(
        entries: ZipEntry[],
        options: ExportOptions = {}
    ): Promise<ExportResult> {
        try {
            const zip = await this.createZip(entries);
            const blob = await this.generateZipBlob(zip, options.compress !== false);
            
            const filename = options.filename || 
                `export_${fileDownloadService.generateTimestamp()}.zip`;
            
            return fileDownloadService.download({
                filename,
                data: blob,
                type: 'application/zip'
            });
        } catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : 'Failed to create ZIP file'
            };
        }
    },

    async exportMultipleImages(
        images: Array<{ dataUrl: string; filename: string }>,
        options: ExportOptions = {}
    ): Promise<ExportResult> {
        const entries: ZipEntry[] = [];
        
        for (const image of images) {
            const blob = fileDownloadService.dataUrlToBlob(image.dataUrl);
            entries.push({
                filename: image.filename,
                content: blob,
                compress: false
            });
        }
        
        return this.exportZip(entries, options);
    },

    async exportWithMetadata(
        contentEntries: ZipEntry[],
        metadata: Record<string, any>,
        options: ExportOptions = {}
    ): Promise<ExportResult> {
        const entries = [...contentEntries];
        
        entries.push({
            filename: 'metadata.json',
            content: JSON.stringify(metadata, null, 2),
            compress: true
        });
        
        return this.exportZip(entries, options);
    },

    readZip(blob: Blob): Promise<JSZip> {
        return JSZip.loadAsync(blob);
    },

    async extractFile(zip: JSZip, filename: string): Promise<string | null> {
        const file = zip.file(filename);
        if (!file) return null;
        return file.async('string');
    },

    async extractAllFiles(zip: JSZip): Promise<Record<string, string>> {
        const files: Record<string, string> = {};
        
        for (const [filename, file] of Object.entries(zip.files)) {
            if (!file.dir) {
                files[filename] = await file.async('string');
            }
        }
        
        return files;
    }
};

export type ZipService = typeof zipService;
