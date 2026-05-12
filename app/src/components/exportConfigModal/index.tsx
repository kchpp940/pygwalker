import React, { useState, useCallback, useEffect } from "react";
import { observer } from "mobx-react-lite";
import JSZip from "jszip";
import { tracker } from "@/utils/tracker";
import { download } from "@/utils/save";
import filterStore from "@/store/filter";
import type { IAppProps } from "@/interfaces";
import type { IGWHandler } from "@kanaries/graphic-walker/interfaces";
import type { VizSpecStore } from "@kanaries/graphic-walker/store/visualSpecStore";
import type { IChartExportResult } from "@kanaries/graphic-walker/interfaces";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { darkModeContext } from "@/store/context";
import commonStore from "@/store/common";

type ExportFormat = "png" | "svg" | "json" | "code";
type ImageScale = 1 | 2 | 3 | 4;
type ExportContent = "filtered" | "unfiltered";

interface IExportConfigModalProps {
    open: boolean;
    setOpen: (open: boolean) => void;
    props: IAppProps;
    gwRef: React.MutableRefObject<IGWHandler | null>;
    storeRef: React.MutableRefObject<VizSpecStore | null>;
    sourceCode: string;
}

const ExportConfigModal: React.FC<IExportConfigModalProps> = observer(({
    open,
    setOpen,
    props,
    gwRef,
    storeRef,
    sourceCode
}) => {
    const darkMode = React.useContext(darkModeContext);
    const [exportFormat, setExportFormat] = useState<ExportFormat>("png");
    const [imageScale, setImageScale] = useState<ImageScale>(2);
    const [includeTitle, setIncludeTitle] = useState(true);
    const [includeDescription, setIncludeDescription] = useState(true);
    const [exportContent, setExportContent] = useState<ExportContent>("filtered");
    const [exportMultipleCharts, setExportMultipleCharts] = useState(false);
    const [isExporting, setIsExporting] = useState(false);
    const [visSpec, setVisSpec] = useState<any[]>([]);

    const visSpecCount = visSpec.length;
    const hasMultipleCharts = visSpecCount > 1;
    const hasActiveFilters = filterStore.hasActiveFilters;

    useEffect(() => {
        if (open && storeRef.current) {
            const spec = storeRef.current.exportCode();
            setVisSpec(spec);
        }
    }, [open]);

    useEffect(() => {
        if ((exportFormat === "png" || exportFormat === "svg") && exportContent === "unfiltered") {
            setExportContent("filtered");
        }
    }, [exportFormat, exportContent]);

    const closeModal = useCallback(() => {
        setOpen(false);
    }, [setOpen]);

    const getCurrentVisSpec = () => {
        if (!storeRef.current) return [];
        const allSpec = storeRef.current.exportCode();
        
        if (!exportMultipleCharts && storeRef.current.visIndex !== undefined) {
            return [allSpec[storeRef.current.visIndex]];
        }
        return allSpec;
    };

    const scaleImage = async (dataUrl: string, scale: number): Promise<string> => {
        if (scale === 1) return dataUrl;
        
        return new Promise((resolve) => {
            const img = new Image();
            img.onload = () => {
                const canvas = document.createElement("canvas");
                canvas.width = img.width * scale;
                canvas.height = img.height * scale;
                const ctx = canvas.getContext("2d");
                if (ctx) {
                    ctx.scale(scale, scale);
                    ctx.drawImage(img, 0, 0);
                    resolve(canvas.toDataURL("image/png"));
                } else {
                    resolve(dataUrl);
                }
            };
            img.onerror = () => resolve(dataUrl);
            img.src = dataUrl;
        });
    };

    const addTitleAndDescriptionToImage = async (
        dataUrl: string, 
        title: string, 
        description: string,
        scale: number
    ): Promise<string> => {
        if (!includeTitle && !includeDescription) return dataUrl;

        return new Promise((resolve) => {
            const img = new Image();
            img.onload = () => {
                const canvas = document.createElement("canvas");
                const titleHeight = includeTitle ? 40 * scale : 0;
                const descHeight = includeDescription && description ? 50 * scale : 0;
                const padding = 20 * scale;
                const topPadding = titleHeight + descHeight + padding;
                
                canvas.width = img.width;
                canvas.height = img.height + topPadding;
                const ctx = canvas.getContext("2d");
                if (ctx) {
                    ctx.fillStyle = "#ffffff";
                    ctx.fillRect(0, 0, canvas.width, canvas.height);
                    ctx.drawImage(img, 0, topPadding);
                    
                    ctx.fillStyle = "#333333";
                    
                    if (includeTitle && title) {
                        ctx.font = `bold ${18 * scale}px Arial, sans-serif`;
                        ctx.textAlign = "center";
                        ctx.fillText(title, canvas.width / 2, 30 * scale);
                    }
                    
                    if (includeDescription && description) {
                        ctx.fillStyle = "#666666";
                        ctx.font = `${13 * scale}px Arial, sans-serif`;
                        const maxWidth = canvas.width - 40 * scale;
                        const words = description.split(" ");
                        const lines: string[] = [];
                        let currentLine = "";
                        
                        for (const word of words) {
                            const testLine = currentLine ? currentLine + " " + word : word;
                            const metrics = ctx.measureText(testLine);
                            if (metrics.width > maxWidth && currentLine) {
                                lines.push(currentLine);
                                currentLine = word;
                            } else {
                                currentLine = testLine;
                            }
                        }
                        if (currentLine) lines.push(currentLine);
                        
                        const descStartY = includeTitle ? 45 * scale : 25 * scale;
                        lines.slice(0, 2).forEach((line, i) => {
                            ctx.fillText(line, canvas.width / 2, descStartY + i * 18 * scale);
                        });
                    }
                    
                    resolve(canvas.toDataURL("image/png"));
                } else {
                    resolve(dataUrl);
                }
            };
            img.onerror = () => resolve(dataUrl);
            img.src = dataUrl;
        });
    };

    const exportSingleImage = async (format: "png" | "svg", chartData: IChartExportResult, spec: any) => {
        if (format === "svg") {
            let svgContent = chartData.charts[0]?.data || "";
            
            if (svgContent.startsWith("<svg")) {
                svgContent = `<?xml version="1.0" encoding="UTF-8"?>\n${svgContent}`;
                const blob = new Blob([svgContent], { type: "image/svg+xml;charset=utf-8" });
                const url = URL.createObjectURL(blob);
                download(url, `${spec?.name || "chart"}.svg`, "image/svg+xml");
            }
            return;
        }
        
        let imageData = chartData.charts[0]?.data || "";
        
        if (imageData.startsWith("data:image/")) {
            imageData = await scaleImage(imageData, imageScale);
            imageData = await addTitleAndDescriptionToImage(
                imageData, 
                spec?.name || "", 
                spec?.description || "",
                imageScale
            );
            
            download(imageData, `${spec?.name || "chart"}.png`, "image/png");
        }
    };

    const exportMultipleImages = async (format: "png" | "svg", allCharts: IChartExportResult[]) => {
        if (allCharts.length === 1) {
            const spec = visSpec[0];
            await exportSingleImage(format, allCharts[0], spec);
            return;
        }
        
        const zip = new JSZip();
        
        for (let i = 0; i < allCharts.length; i++) {
            const chart = allCharts[i];
            const spec = visSpec[i] || { name: `chart_${i + 1}` };
            const chartData = chart.charts[0]?.data || "";
            
            if (format === "svg") {
                if (chartData.startsWith("<svg")) {
                    const svgContent = `<?xml version="1.0" encoding="UTF-8"?>\n${chartData}`;
                    zip.file(`${spec?.name || `chart_${i + 1}`}.svg`, svgContent);
                }
            } else {
                if (chartData.startsWith("data:image/")) {
                    let imageData = await scaleImage(chartData, imageScale);
                    imageData = await addTitleAndDescriptionToImage(
                        imageData,
                        spec?.name || "",
                        spec?.description || "",
                        imageScale
                    );
                    const base64Data = imageData.split(",")[1];
                    zip.file(`${spec?.name || `chart_${i + 1}`}.png`, base64Data, { base64: true });
                }
            }
        }
        
        const content = await zip.generateAsync({ type: "blob" });
        const url = URL.createObjectURL(content);
        download(url, `charts_${Date.now()}.zip`, "application/zip");
    };

    const exportImages = async () => {
        if (!gwRef.current) return;
        
        const gwMode: "data-url" | "svg" = exportFormat === "svg" ? "svg" : "data-url";
        const imgFormat: "png" | "svg" = exportFormat === "svg" ? "svg" : "png";

        if (exportMultipleCharts && gwRef.current.exportChartList) {
            const allCharts: IChartExportResult[] = [];
            for await (const chart of gwRef.current.exportChartList(gwMode)) {
                allCharts.push(chart.data);
            }
            await exportMultipleImages(imgFormat, allCharts);
        } else {
            const chartData = await gwRef.current.exportChart!(gwMode);
            const currentSpec = getCurrentVisSpec()[0];
            await exportSingleImage(imgFormat, chartData, currentSpec);
        }
    };

    const buildSpecWithContentPreference = (spec: any): any => {
        if (exportContent === "filtered" || !spec) return spec;
        
        const clonedSpec = JSON.parse(JSON.stringify(spec));
        
        if (clonedSpec.config?.filter || clonedSpec.filter) {
            delete clonedSpec.config?.filter;
            delete clonedSpec.filter;
        }
        
        if (clonedSpec.encodings?.filter?.length > 0) {
            clonedSpec.encodings.filter = [];
        }
        
        if (clonedSpec.config?.workflow) {
            clonedSpec.config.workflow = clonedSpec.config.workflow.filter(
                (step: any) => step.type !== "filter" && step.type !== "filter"
            );
        }
        
        return clonedSpec;
    };

    const exportJson = async () => {
        let spec = getCurrentVisSpec();
        
        if (exportContent === "unfiltered") {
            spec = spec.map(s => buildSpecWithContentPreference(s));
        }
        
        const jsonStr = JSON.stringify(spec, null, 2);
        const blob = new Blob([jsonStr], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        download(url, `chart_spec_${Date.now()}.json`, "application/json");
    };

    const exportPythonCode = async () => {
        let spec = getCurrentVisSpec();
        
        if (exportContent === "unfiltered") {
            spec = spec.map(s => buildSpecWithContentPreference(s));
        }
        
        let code = `# Generated by PyGWalker\nimport pygwalker as pyg\n`;
        
        if (sourceCode) {
            code += `\n# Original source code:\n# ${sourceCode.split('\n').join('\n# ')}\n\n`;
        }
        
        code += `\n# Visualization Specification:\nvis_spec = ${JSON.stringify(spec, null, 4)}\n`;
        
        code += `\n# Create a PyGWalker instance with the specification\nwalker = pyg.walk(\n    df,  # Replace with your DataFrame\n    spec=vis_spec\n)`;
        
        const blob = new Blob([code], { type: "text/plain" });
        const url = URL.createObjectURL(blob);
        download(url, `pygwalker_code_${Date.now()}.py`, "text/plain");
    };

    const handleExport = async () => {
        if (isExporting) return;
        
        setIsExporting(true);
        tracker.track("click", {
            entity: "export_config_submit",
            format: exportFormat,
            scale: imageScale,
            includeTitle,
            includeDescription,
            exportContent,
            exportMultipleCharts
        });

        try {
            if (exportFormat === "png" || exportFormat === "svg") {
                await exportImages();
            } else if (exportFormat === "json") {
                await exportJson();
            } else if (exportFormat === "code") {
                await exportPythonCode();
            }
            
            closeModal();
            commonStore.setNotification({
                type: "success",
                title: "Export Success",
                message: "Your export has been completed successfully.",
            }, 4000);
        } catch (error) {
            console.error("Export error:", error);
            commonStore.setNotification({
                type: "error",
                title: "Export Failed",
                message: "An error occurred during export. Please try again.",
            }, 4000);
        } finally {
            setIsExporting(false);
        }
    };

    const showTitleDescOption = exportFormat === "png" || exportFormat === "svg";

    return (
        <Dialog
            open={open}
            modal={false}
            onOpenChange={setOpen}
        >
            <DialogContent className="sm:max-w-[520px]">
                <DialogHeader>
                    <DialogTitle>Export Configuration</DialogTitle>
                    <DialogDescription>
                        Customize your export settings below.
                    </DialogDescription>
                </DialogHeader>
                
                <div className="space-y-6 py-4">
                    <div className="space-y-3">
                        <Label>Export Format</Label>
                        <ToggleGroup 
                            type="single" 
                            value={exportFormat} 
                            onValueChange={(value) => value && setExportFormat(value as ExportFormat)}
                            className="justify-start"
                        >
                            <ToggleGroupItem value="png" className="flex-1">PNG</ToggleGroupItem>
                            <ToggleGroupItem value="svg" className="flex-1">SVG</ToggleGroupItem>
                            <ToggleGroupItem value="json" className="flex-1">JSON</ToggleGroupItem>
                            <ToggleGroupItem value="code" className="flex-1">Code</ToggleGroupItem>
                        </ToggleGroup>
                    </div>
                    
                    {exportFormat === "png" && (
                        <div className="space-y-3">
                            <Label>Image Scale</Label>
                            <Select 
                                value={imageScale.toString()} 
                                onValueChange={(value) => setImageScale(parseInt(value) as ImageScale)}
                            >
                                <SelectTrigger>
                                    <SelectValue placeholder="Select scale" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="1">1x (Original)</SelectItem>
                                    <SelectItem value="2">2x (Recommended)</SelectItem>
                                    <SelectItem value="3">3x (High Quality)</SelectItem>
                                    <SelectItem value="4">4x (Ultra High)</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    )}
                    
                    {showTitleDescOption && (
                        <div className="space-y-3">
                            <Label>Title &amp; Description</Label>
                            <div className="flex items-center space-x-3">
                                <Checkbox 
                                    id="includeTitle" 
                                    checked={includeTitle}
                                    onCheckedChange={(checked) => setIncludeTitle(checked as boolean)}
                                />
                                <Label htmlFor="includeTitle" className="cursor-pointer">
                                    Include Chart Title
                                </Label>
                            </div>
                            <div className="flex items-center space-x-3">
                                <Checkbox 
                                    id="includeDescription" 
                                    checked={includeDescription}
                                    onCheckedChange={(checked) => setIncludeDescription(checked as boolean)}
                                />
                                <Label htmlFor="includeDescription" className="cursor-pointer">
                                    Include Chart Description
                                </Label>
                            </div>
                        </div>
                    )}
                    
                    <div className="space-y-3">
                        <Label>Data Content</Label>
                        {exportFormat === "png" || exportFormat === "svg" ? (
                            <div className="rounded-md border border-border p-3 bg-muted/30">
                                <div className="flex items-center space-x-2">
                                    <span className="text-sm font-medium">Current Filtered Results</span>
                                    {hasActiveFilters && (
                                        <span className="text-xs text-blue-500">
                                            ({filterStore.enabledConditions.length} filters active)
                                        </span>
                                    )}
                                </div>
                                <p className="text-xs text-muted-foreground mt-1">
                                    Images are rendered from the current screen state. 
                                    To export unfiltered data, use JSON or Code format.
                                </p>
                            </div>
                        ) : (
                            <Select 
                                value={exportContent}
                                onValueChange={(value) => setExportContent(value as ExportContent)}
                            >
                                <SelectTrigger>
                                    <SelectValue placeholder="Select content to export" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="filtered">
                                        Current Filtered Results
                                        {hasActiveFilters && (
                                            <span className="ml-2 text-blue-500">
                                                ({filterStore.enabledConditions.length} filters active)
                                            </span>
                                        )}
                                    </SelectItem>
                                    <SelectItem value="unfiltered">
                                        Unfiltered Full Dataset
                                        {hasActiveFilters && (
                                            <span className="ml-2 text-orange-500">
                                                (ignores current filters)
                                            </span>
                                        )}
                                    </SelectItem>
                                </SelectContent>
                            </Select>
                        )}
                    </div>
                    
                    {hasMultipleCharts && (
                        <div className="flex items-center space-x-3">
                            <Checkbox 
                                id="exportMultipleCharts" 
                                checked={exportMultipleCharts}
                                onCheckedChange={(checked) => setExportMultipleCharts(checked as boolean)}
                            />
                            <Label htmlFor="exportMultipleCharts" className="cursor-pointer">
                                Export All Charts ({visSpecCount} charts)
                                {exportMultipleCharts && (
                                    <span className="ml-2 text-green-500">
                                        (will export as ZIP archive)
                                    </span>
                                )}
                            </Label>
                        </div>
                    )}
                </div>
                
                <div className="flex justify-end space-x-3 pt-2">
                    <Button variant="outline" onClick={closeModal} disabled={isExporting}>
                        Cancel
                    </Button>
                    <Button onClick={handleExport} disabled={isExporting}>
                        {isExporting ? "Exporting..." : "Export"}
                    </Button>
                </div>
            </DialogContent>
        </Dialog>
    );
});

export default ExportConfigModal;
