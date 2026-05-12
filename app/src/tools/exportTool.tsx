import React from 'react';

import { tracker } from "@/utils/tracker";
import { CodeBracketSquareIcon } from '@heroicons/react/24/outline';
import commonStore from '../store/common';

import type { ToolbarButtonItem } from "@kanaries/graphic-walker/components/toolbar/toolbar-button"


export function getExportTool() : ToolbarButtonItem {
    const onClick = () => {
        commonStore.openModal("exportConfig");
        tracker.track("click", {"entity": "export_code_icon"});
    }
    return {
        key: "export_pygwalker_code",
        label: "export",
        icon: (iconProps?: any) => <CodeBracketSquareIcon {...iconProps} />,
        onClick
    }
}
