import React from "react";

import { tracker } from "@/utils/tracker";
import { ComputerDesktopIcon } from "@heroicons/react/24/outline";

import type { ToolbarButtonItem } from "@kanaries/graphic-walker/components/toolbar/toolbar-button";
import commonStore from "@/store/common";
import communicationStore from "@/store/communication";

export function getOpenDesktopTool(): ToolbarButtonItem {
    const onClick = async () => {
        if (!commonStore.storeRef?.current) return;
        
        tracker.track("click", { entity: "open_desktop_icon" });
        await communicationStore.comm?.sendMsg("open_in_desktop", {
            spec: JSON.parse(JSON.stringify(commonStore.storeRef.current?.visList)),
            fields: JSON.parse(JSON.stringify(commonStore.storeRef.current?.meta)),
        });
    };
    return {
        key: "open_in_desktop",
        label: "open_desktop",
        icon: (iconProps?: any) => <ComputerDesktopIcon {...iconProps} />,
        onClick,
    };
}
