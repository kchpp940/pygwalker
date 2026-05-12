import * as htmlToImage from 'html-to-image';
import type { IChartExportResult } from '@kanaries/graphic-walker/interfaces';

export function download(data: string, filename: string, type: string) {
    var file = new Blob([data], { type: type });
    // @ts-ignore
    if (window.navigator.msSaveOrOpenBlob)
        // IE10+
        // @ts-ignore
        window.navigator.msSaveOrOpenBlob(file, filename);
    else {
        // Others
        var a = document.createElement("a"),
            url = URL.createObjectURL(file);
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        setTimeout(function () {
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        }, 0);
    }
}

export async function formatExportedChartDatas(chartData: IChartExportResult) {
    const chartDom = chartData.container();
    if (chartDom === null) {
        return {
            ...chartData,
            singleChart: ""
        };
    }
    // export png don't support geo chart
    if (chartData.charts.length === 0) {
        return {
            ...chartData,
            nCols: 1,
            nRows: 1,
            charts: [{
                colIndex: 0,
                rowIndex: 0,
                width: chartDom?.clientWidth,
                height: chartDom?.clientHeight,
                canvasWidth: chartDom?.clientWidth,
                canvasHeight: chartDom?.clientHeight,
                data: "",
                canvas: () => null
            }],
            singleChart: ""
        }
    }
    
    // 优先使用 Vega 原生生成的图表数据（包含完整的图例、坐标轴标题和颜色映射）
    // 当有多个图表时，html-to-image 可能无法正确捕获 Shadow DOM 中的内容
    if (chartData.charts.length === 1 && chartData.charts[0].data && chartData.charts[0].data.startsWith("data:image/")) {
        return {
            ...chartData,
            singleChart: chartData.charts[0].data
        };
    }
    
    // 回退到 html-to-image（用于多图表等场景）
    const singleChart = await htmlToImage.toPng(
        chartDom!,
        {width: chartDom?.scrollWidth, height: chartDom?.scrollHeight}
    )
    return {
        ...chartData,
        singleChart
    }
}

export function getTimezoneOffsetSeconds(): number {
    return -new Date().getTimezoneOffset() * 60;
}
