import React, { useState } from 'react';
import communicationStore from "../store/communication"
import commonStore from '../store/common';
import { tracker } from "@/utils/tracker";
import filterStore from "../store/filter";

import { DocumentArrowDownIcon } from '@heroicons/react/24/outline';
import { Loader2 } from "lucide-react"

import type { IAppProps } from '../interfaces';
import { parser_dsl_with_meta } from "@kanaries/gw-dsl-parser";
import type { ToolbarButtonItem } from "@kanaries/graphic-walker/components/toolbar/toolbar-button"
import type { VizSpecStore } from '@kanaries/graphic-walker/store/visualSpecStore'
import type { IRow, IDataQueryPayload } from '@kanaries/graphic-walker/interfaces';
import { filterRows } from "../utils/filter";
import { getDatasFromKernelByPayload, getDatasFromKernelBySql } from "../dataSource";

export function getExportDataframeTool(
    props: IAppProps,
    storeRef: React.MutableRefObject<VizSpecStore | null>
) : ToolbarButtonItem {
    const [exporting, setExporting] = useState(false);

    const exportSuccess = () => {
        commonStore.setNotification({
            type: "success",
            title: "Tips",
            message: <>
            <p className='py-1'>export success, created new dataframe: </p>
            <p className='font-semibold py-1'>`walker.last_exported_dataframe`</p>
            <p className='py-1'>if you forgot set variable walker, you can use</p>
            <p className='font-semibold py-1'>`pyg.GlobalVarManager.last_exported_dataframe`</p>
            <p className='py-1'>to get current exported dataframe</p>
            </>
        }, 20_000);

        setTimeout(() => {
            setExporting(false);
        }, 500);
    }

    const exportWithFilter = async () => {
        let dataToExport: IRow[] = [];

        if (!props.useKernelCalc) {
            dataToExport = props.dataSource ? [...props.dataSource] : [];
        } else {
            const workflow = storeRef.current?.workflow ?? [];
            const payload: IDataQueryPayload = {
                workflow: workflow,
                limit: undefined
            };
            
            if (props.parseDslType === "server") {
                dataToExport = await getDatasFromKernelByPayload(payload);
            } else {
                dataToExport = await getDatasFromKernelBySql(props.fieldMetas)(payload);
            }
        }

        if (filterStore.hasActiveFilters) {
            dataToExport = filterRows(
                dataToExport,
                filterStore.conditions,
                filterStore.logic
            );
        }

        await communicationStore.comm?.sendMsg("export_dataframe_by_data", {
            records: dataToExport,
            encodings: storeRef.current?.currentVis.encodings,
        });
    };

    const onClick = async () => {
        if (exporting) return;
        setExporting(true);
        tracker.track("click", {"entity": "export_dataframe_icon"});

        try {
            if (filterStore.hasActiveFilters) {
                await exportWithFilter();
            } else if (props.parseDslType === "server") {
                await communicationStore.comm?.sendMsg("export_dataframe_by_payload", {
                    payload: {
                        workflow: storeRef.current?.workflow,
                    },
                    encodings: storeRef.current?.currentVis.encodings,
                });
            } else {
                const sql = parser_dsl_with_meta(
                    "pygwalker_mid_table",
                    JSON.stringify({workflow: storeRef.current?.workflow}),
                    JSON.stringify({"pygwalker_mid_table": props.fieldMetas})
                );
                await communicationStore.comm?.sendMsg("export_dataframe_by_sql", {
                    sql: sql,
                    encodings: storeRef.current?.currentVis.encodings
                });
            }
            exportSuccess();
        } catch (_) {
            setExporting(false);
        }
    }

    return {
        key: "export_dataframe",
        label: "export_dataframe",
        icon: (iconProps?: any) => {
            return exporting ? <Loader2 className='animate-spin' />  : <DocumentArrowDownIcon {...iconProps} />
        },
        onClick: onClick,
    }
}
