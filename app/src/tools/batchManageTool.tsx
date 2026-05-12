import React, { useMemo } from 'react';
import { ListChecksIcon } from 'lucide-react';
import type { ToolbarButtonItem } from "@kanaries/graphic-walker/components/toolbar/toolbar-button";
import type { VizSpecStore } from '@kanaries/graphic-walker/store/visualSpecStore';
import type { IAppProps } from '../interfaces';
import { Button } from "@/components/ui/button";
import { tracker } from "@/utils/tracker";
import commonStore from '@/store/common';

interface IBatchManageToolConfig {
    props: IAppProps;
    storeRef: React.MutableRefObject<VizSpecStore | null>;
    setIsChanged: React.Dispatch<React.SetStateAction<boolean>>;
    onSpecUpdate?: (newSpec: any[]) => void;
}

function getBatchManageTool(
    props: IAppProps,
    storeRef: React.MutableRefObject<VizSpecStore | null>,
    setIsChanged: React.Dispatch<React.SetStateAction<boolean>>,
    onSpecUpdate?: (newSpec: any[]) => void
): ToolbarButtonItem {
    const handleOpen = () => {
        commonStore.setBatchManageConfig({
            props,
            storeRef,
            setIsChanged,
            onSpecUpdate
        });
        commonStore.setBatchManageModalOpen(true);
        tracker.track("click", { "entity": "batch_manage_open", "spec_type": props.specType });
    };

    return {
        key: "batch-manage",
        label: "batch manage",
        icon: (iconProps?: any) => <ListChecksIcon {...iconProps} />,
        form: (
            <div className='flex flex-col min-w-[200px]'>
                <Button
                    variant="ghost"
                    aria-label="batch manage charts"
                    onClick={handleOpen}
                    className="flex items-center gap-2 justify-start"
                >
                    <ListChecksIcon className="h-4 w-4" />
                    <span>Batch Manage Charts</span>
                </Button>
            </div>
        ),
        onClick: handleOpen
    };
}

const BatchManageIcon = () => <ListChecksIcon className="h-4 w-4" />;

export { getBatchManageTool, BatchManageIcon };
export type { IBatchManageToolConfig };
