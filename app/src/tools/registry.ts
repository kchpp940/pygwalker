import React from 'react';
import { observer } from "mobx-react-lite";
import type { ToolbarButtonItem } from "@kanaries/graphic-walker/components/toolbar/toolbar-button";

import commonStore from '../store/common';
import { getRuncellTool } from './runcellTool';
import { getExportTool } from './exportTool';
import { getOpenDesktopTool } from './openDesktop';
import { getSaveTool } from './saveTool';
import { getExportDataframeTool } from './exportDataframe';

export interface ToolFactory {
    key: string;
    factory: () => ToolbarButtonItem;
    condition?: () => boolean;
}

export class ToolRegistry {
    private tools: Map<string, ToolFactory> = new Map();
    private toolCache: Map<string, ToolbarButtonItem> = new Map();

    register(factory: ToolFactory): void {
        this.tools.set(factory.key, factory);
    }

    unregister(key: string): void {
        this.tools.delete(key);
        this.toolCache.delete(key);
    }

    getTool(key: string): ToolbarButtonItem | null {
        const factory = this.tools.get(key);
        if (!factory) return null;
        
        if (factory.condition && !factory.condition()) {
            return null;
        }

        const cached = this.toolCache.get(key);
        if (cached) return cached;

        const tool = factory.factory();
        this.toolCache.set(key, tool);
        return tool;
    }

    getAllTools(): ToolbarButtonItem[] {
        const tools: ToolbarButtonItem[] = [];
        this.tools.forEach((factory, key) => {
            if (factory.condition && !factory.condition()) {
                return;
            }
            const tool = this.toolCache.get(key) || factory.factory();
            if (!this.toolCache.has(key)) {
                this.toolCache.set(key, tool);
            }
            tools.push(tool);
        });
        return tools;
    }

    clearCache(): void {
        this.toolCache.clear();
    }
}

const defaultTools: ToolFactory[] = [
    {
        key: "runcell",
        factory: () => getRuncellTool(),
    },
    {
        key: "export",
        factory: () => getExportTool(),
    },
    {
        key: "openDesktop",
        factory: () => getOpenDesktopTool(),
        condition: () => commonStore.appProps !== null && commonStore.storeRef !== null,
    },
    {
        key: "save",
        factory: () => getSaveTool(),
        condition: () => {
            const props = commonStore.appProps;
            if (!props || !props.useSaveTool) return false;
            const validEnvs = ["jupyter_widgets", "streamlit", "gradio", "marimo", "anywidget", "web_server"];
            return props.env ? validEnvs.indexOf(props.env) !== -1 : false;
        },
    },
    {
        key: "exportDataframe",
        factory: () => getExportDataframeTool(),
        condition: () => commonStore.appProps?.isExportDataFrame || false,
    },
];

export const toolRegistry = new ToolRegistry();

defaultTools.forEach(tool => toolRegistry.register(tool));

export default toolRegistry;
