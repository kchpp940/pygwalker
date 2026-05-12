import React from 'react';
import { FunnelIcon } from '@heroicons/react/24/outline';
import type { ToolbarButtonItem } from "@kanaries/graphic-walker/components/toolbar/toolbar-button"
import filterStore from "../store/filter";
import { tracker } from "@/utils/tracker";
import { Badge } from "@/components/ui/badge";

export function getFilterTool(): ToolbarButtonItem {
    const onClick = () => {
        tracker.track("click", {"entity": "enhanced_filter_icon"});
        filterStore.toggleFilterPanel();
    };
    
    return {
        key: "enhanced_filter",
        label: "Enhanced Filter",
        icon: (iconProps?: any) => {
            const badgeCount = filterStore.enabledConditions.length;
            return (
                <div className="relative inline-block">
                    <FunnelIcon {...iconProps} />
                    {badgeCount > 0 && (
                        <Badge 
                            className="absolute -top-2 -right-2 h-4 min-w-[16px] px-1 text-[10px] flex items-center justify-center"
                            variant="destructive"
                        >
                            {badgeCount > 9 ? '9+' : badgeCount}
                        </Badge>
                    )}
                </div>
            );
        },
        onClick,
    };
}
