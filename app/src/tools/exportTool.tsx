import React from 'react';

import { tracker } from "@/utils/tracker";
import { ArrowDownTrayIcon } from '@heroicons/react/24/outline';

import type { ToolbarButtonItem } from "@kanaries/graphic-walker/components/toolbar/toolbar-button"


export function getExportTool(
    setExportConfigOpen: React.Dispatch<React.SetStateAction<boolean>>
) : ToolbarButtonItem {
    const onClick = () => {
        setExportConfigOpen(true);
        tracker.track("click", {"entity": "export_config_icon"});
    }
    return {
        key: "export_config",
        label: "export",
        icon: (iconProps?: any) => <ArrowDownTrayIcon {...iconProps} />,
        onClick
    }
}

export function getCodeExportTool(
    setExportOpen: React.Dispatch<React.SetStateAction<boolean>>
) : ToolbarButtonItem {
    const onClick = () => {
        setExportOpen(true);
        tracker.track("click", {"entity": "export_code_icon"});
    }
    return {
        key: "export_pygwalker_code",
        label: "export_code",
        icon: (iconProps?: any) => <ArrowDownTrayIcon {...iconProps} />,
        onClick
    }
}
