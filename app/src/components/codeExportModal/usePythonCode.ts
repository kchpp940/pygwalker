import type { IChart } from "@kanaries/graphic-walker/interfaces";
import { useMemo } from "react"
import { codeExportService } from '../../services/export';

export function usePythonCode (props: {
    sourceCode: string;
    visSpec: IChart[];
    version: string;
}) {
    const { sourceCode, visSpec, version } = props;
    const pyCode = useMemo(() => {
        return codeExportService.generatePythonCode(sourceCode, visSpec, version);
    }, [sourceCode, visSpec, version])
    return {
        pyCode
    }
}