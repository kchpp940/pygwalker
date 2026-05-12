import commonStore, { INotification } from '@/store/common';
import type { ExportResult } from './types';

export type NotificationType = INotification['type'];

export interface ShowNotificationOptions {
    title?: string;
    message: string | React.ReactElement;
    type?: NotificationType;
    timeout?: number;
}

export const notificationService = {
    show(options: ShowNotificationOptions): void {
        const notification: INotification = {
            title: options.title || 'Notification',
            message: options.message,
            type: options.type || 'info'
        };
        commonStore.setNotification(notification, options.timeout);
    },

    success(message: string | React.ReactElement, title: string = 'Success', timeout: number = 4000): void {
        this.show({
            title,
            message,
            type: 'success',
            timeout
        });
    },

    error(message: string | React.ReactElement, title: string = 'Error', timeout: number = 5000): void {
        this.show({
            title,
            message,
            type: 'error',
            timeout
        });
    },

    info(message: string | React.ReactElement, title: string = 'Info', timeout: number = 4000): void {
        this.show({
            title,
            message,
            type: 'info',
            timeout
        });
    },

    warning(message: string | React.ReactElement, title: string = 'Warning', timeout: number = 4000): void {
        this.show({
            title,
            message,
            type: 'warning',
            timeout
        });
    },

    handleExportResult(result: ExportResult, successMessage?: string, errorMessage?: string): void {
        if (result.success) {
            this.success(
                successMessage || `${result.filename} has been downloaded successfully.`,
                'Export Success'
            );
        } else {
            this.error(
                errorMessage || result.error || 'Export failed.',
                'Export Error'
            );
        }
    },

    clear(): void {
        commonStore.setNotification(null);
    }
};

export type NotificationService = typeof notificationService;
