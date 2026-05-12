import { makeObservable, observable, action } from 'mobx';
import { ReactElement } from "react";

import type { IGWHandler } from '@kanaries/graphic-walker/interfaces';
import type { VizSpecStore } from '@kanaries/graphic-walker/store/visualSpecStore'
import type { IAppProps } from '../interfaces';

interface IInitModalInfo {
    total: number;
    curIndex: number;
    title: string;
}

export interface INotification {
    title: string;
    message: string | ReactElement;
    type: "success" | "error" | "info" | "warning";
}

export type ModalType = "codeExport" | "uploadSpec" | "uploadChart" | "init" | "exportConfig";

class CommonStore {
    _notifyTimeoutFunc = setTimeout(() => {}, 0);

    initModalOpen: boolean = false;
    initModalInfo: IInitModalInfo = {
        total: 0,
        curIndex: 0,
        title: "",
    };
    showCloudTool: boolean = false;
    version: string = "";
    notification: INotification | null = null;
    uploadSpecModalOpen: boolean = false;
    uploadChartModalOpen: boolean = false;
    codeExportModalOpen: boolean = false;
    exportConfigModalOpen: boolean = false;
    isStreamlitComponent: boolean = false;
    
    gwRef: React.MutableRefObject<IGWHandler | null> | null = null;
    storeRef: React.MutableRefObject<VizSpecStore | null> | null = null;
    appProps: IAppProps | null = null;
    isChanged: boolean = false;
    sourceInvokeCode: string = "";

    setInitModalOpen(value: boolean) {
        this.initModalOpen = value;
    }

    setInitModalInfo(info: IInitModalInfo) {
        this.initModalInfo = info;
    }

    setShowCloudTool(value: boolean) {
        this.showCloudTool = value;
    }

    setVersion(value: string) {
        this.version = value;
    }
    
    setNotification(value: INotification | null, timeout: number = 5_000) {
        clearTimeout(this._notifyTimeoutFunc);
        this.notification = value;
        this._notifyTimeoutFunc = setTimeout(() => {
            this.notification = null;
        }, timeout);
    }

    setUploadSpecModalOpen(value: boolean) {
        this.uploadSpecModalOpen = value;
    }

    setUploadChartModalOpen(value: boolean) {
        this.uploadChartModalOpen = value;
    }

    setCodeExportModalOpen(value: boolean) {
        this.codeExportModalOpen = value;
    }

    setExportConfigModalOpen(value: boolean) {
        this.exportConfigModalOpen = value;
    }

    setIsStreamlitComponent(value: boolean) {
        this.isStreamlitComponent = value;
    }

    setGwRef(ref: React.MutableRefObject<IGWHandler | null> | null) {
        this.gwRef = ref;
    }

    setStoreRef(ref: React.MutableRefObject<VizSpecStore | null> | null) {
        this.storeRef = ref;
    }

    setAppProps(props: IAppProps | null) {
        this.appProps = props;
    }

    setIsChanged(value: boolean) {
        this.isChanged = value;
    }

    setSourceInvokeCode(code: string) {
        this.sourceInvokeCode = code;
    }

    openModal(modalType: ModalType) {
        switch (modalType) {
            case "codeExport":
                this.codeExportModalOpen = true;
                break;
            case "uploadSpec":
                this.uploadSpecModalOpen = true;
                break;
            case "uploadChart":
                this.uploadChartModalOpen = true;
                break;
            case "init":
                this.initModalOpen = true;
                break;
            case "exportConfig":
                this.exportConfigModalOpen = true;
                break;
        }
    }

    closeModal(modalType: ModalType) {
        switch (modalType) {
            case "codeExport":
                this.codeExportModalOpen = false;
                break;
            case "uploadSpec":
                this.uploadSpecModalOpen = false;
                break;
            case "uploadChart":
                this.uploadChartModalOpen = false;
                break;
            case "init":
                this.initModalOpen = false;
                break;
            case "exportConfig":
                this.exportConfigModalOpen = false;
                break;
        }
    }

    toggleModal(modalType: ModalType) {
        switch (modalType) {
            case "codeExport":
                this.codeExportModalOpen = !this.codeExportModalOpen;
                break;
            case "uploadSpec":
                this.uploadSpecModalOpen = !this.uploadSpecModalOpen;
                break;
            case "uploadChart":
                this.uploadChartModalOpen = !this.uploadChartModalOpen;
                break;
            case "init":
                this.initModalOpen = !this.initModalOpen;
                break;
            case "exportConfig":
                this.exportConfigModalOpen = !this.exportConfigModalOpen;
                break;
        }
    }

    constructor() {
        makeObservable(this, {
            initModalOpen: observable,
            initModalInfo: observable,
            showCloudTool: observable,
            version: observable,
            notification: observable,
            uploadSpecModalOpen: observable,
            uploadChartModalOpen: observable,
            codeExportModalOpen: observable,
            exportConfigModalOpen: observable,
            isStreamlitComponent: observable,
            gwRef: observable,
            storeRef: observable,
            appProps: observable,
            isChanged: observable,
            sourceInvokeCode: observable,
            setInitModalOpen: action,
            setInitModalInfo: action,
            setShowCloudTool: action,
            setVersion: action,
            setNotification: action,
            setUploadSpecModalOpen: action,
            setUploadChartModalOpen: action,
            setCodeExportModalOpen: action,
            setExportConfigModalOpen: action,
            setIsStreamlitComponent: action,
            setGwRef: action,
            setStoreRef: action,
            setAppProps: action,
            setIsChanged: action,
            setSourceInvokeCode: action,
            openModal: action,
            closeModal: action,
            toggleModal: action
        });
    }
}

const commonStore = new CommonStore();

export default commonStore;