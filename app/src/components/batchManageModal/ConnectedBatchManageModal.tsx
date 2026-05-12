import React from 'react';
import { observer } from "mobx-react-lite";
import commonStore from '@/store/common';
import BatchManageModal from './index';
import type { IChartItem } from '@/interfaces';

const ConnectedBatchManageModal: React.FC = observer(() => {
    const { batchManageModalOpen, setBatchManageModalOpen, batchManageConfig } = commonStore;

    if (!batchManageConfig) return null;

    const { storeRef, setIsChanged, onSpecUpdate, props } = batchManageConfig;

    const charts: IChartItem[] = React.useMemo(() => {
        const spec = storeRef.current?.exportCode();
        if (!spec) return [];
        return spec.map((s, index) => ({
            index,
            name: s.name || `Chart ${index + 1}`,
            visId: s.visId || `chart-${index}`
        }));
    }, [storeRef.current?.exportCode()]);

    const handleUpdate = (newSpec: any[]) => {
        storeRef.current?.importCode(newSpec);
        setIsChanged(true);
        onSpecUpdate?.(newSpec);
    };

    return (
        <BatchManageModal
            open={batchManageModalOpen}
            onOpenChange={setBatchManageModalOpen}
            charts={charts}
            getCurrentSpec={() => storeRef.current?.exportCode() || []}
            onUpdate={handleUpdate}
            props={props}
        />
    );
});

export default ConnectedBatchManageModal;
