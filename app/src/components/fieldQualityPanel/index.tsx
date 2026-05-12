import React, { useState } from "react";
import { ChevronDownIcon, ChevronUpIcon, InfoCircledIcon, ExclamationTriangleIcon, CheckCircledIcon, Cross2Icon } from "@radix-ui/react-icons";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import type { IFieldQuality, IFieldDistribution, IFieldAnomaly } from "@/interfaces";
import { cn } from "@/lib/utils";

interface IFieldQualityPanelProps {
    fieldQualities?: Record<string, IFieldQuality>;
    fieldNames?: Record<string, string>;
}

interface IFieldQualityItemProps {
    fid: string;
    quality: IFieldQuality;
    displayName: string;
}

const getQualityStatus = (quality: IFieldQuality): "good" | "warning" | "error" => {
    if (!quality.isSuitableForAnalysis) return "error";
    if (quality.warnings.length > 0) return "warning";
    if (quality.anomalies.some(a => a.severity === "high")) return "warning";
    return "good";
};

const StatusIcon: React.FC<{ status: "good" | "warning" | "error" }> = ({ status }) => {
    switch (status) {
        case "good":
            return <CheckCircledIcon className="h-4 w-4 text-green-500" />;
        case "warning":
            return <ExclamationTriangleIcon className="h-4 w-4 text-yellow-500" />;
        case "error":
            return <ExclamationTriangleIcon className="h-4 w-4 text-red-500" />;
    }
};

const MissingRateBar: React.FC<{ rate: number }> = ({ rate }) => {
    const percentage = rate * 100;
    const color = rate > 0.5 ? "bg-red-500" : rate > 0.2 ? "bg-yellow-500" : "bg-green-500";
    
    return (
        <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground w-20">{percentage.toFixed(1)}%</span>
            <div className="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                <div 
                    className={cn("h-full transition-all", color)} 
                    style={{ width: `${Math.min(percentage, 100)}%` }}
                />
            </div>
        </div>
    );
};

const DistributionInfo: React.FC<{ distribution: IFieldDistribution; dataType: string }> = ({ distribution, dataType }) => {
    if (dataType === "number" || distribution.type === "number") {
        return (
            <div className="space-y-2">
                <div className="text-sm font-medium">数值分布</div>
                <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="bg-gray-50 dark:bg-gray-800 p-2 rounded">
                        <div className="text-muted-foreground">最小值</div>
                        <div className="font-mono">{distribution.min?.toFixed(3) ?? "-"}</div>
                    </div>
                    <div className="bg-gray-50 dark:bg-gray-800 p-2 rounded">
                        <div className="text-muted-foreground">最大值</div>
                        <div className="font-mono">{distribution.max?.toFixed(3) ?? "-"}</div>
                    </div>
                    <div className="bg-gray-50 dark:bg-gray-800 p-2 rounded">
                        <div className="text-muted-foreground">均值</div>
                        <div className="font-mono">{distribution.mean?.toFixed(3) ?? "-"}</div>
                    </div>
                    <div className="bg-gray-50 dark:bg-gray-800 p-2 rounded">
                        <div className="text-muted-foreground">标准差</div>
                        <div className="font-mono">{distribution.stddev?.toFixed(3) ?? "-"}</div>
                    </div>
                </div>
            </div>
        );
    }
    
    if (dataType === "string" || distribution.type === "string") {
        const topValues = distribution.topValues || [];
        if (topValues.length === 0) {
            return <div className="text-xs text-muted-foreground">无分布数据</div>;
        }
        
        const total = topValues.reduce((sum, v) => sum + v.count, 0);
        
        return (
            <div className="space-y-2">
                <div className="text-sm font-medium">Top 值分布</div>
                <div className="space-y-1">
                    {topValues.slice(0, 5).map((value, index) => (
                        <div key={index} className="flex items-center gap-2">
                            <span className="text-xs w-4 text-muted-foreground">{index + 1}.</span>
                            <span className="text-xs truncate flex-1 max-w-[120px]" title={value.value}>
                                {value.value}
                            </span>
                            <div className="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                                <div 
                                    className="h-full bg-blue-500"
                                    style={{ width: `${(value.count / total) * 100}%` }}
                                />
                            </div>
                            <span className="text-xs text-muted-foreground w-12 text-right">
                                {((value.count / total) * 100).toFixed(0)}%
                            </span>
                        </div>
                    ))}
                </div>
                {distribution.entropy !== undefined && (
                    <div className="text-xs text-muted-foreground">
                        信息熵: {distribution.entropy.toFixed(2)}
                    </div>
                )}
            </div>
        );
    }
    
    if (dataType === "datetime" || dataType === "datetime_tz" || distribution.type === "datetime") {
        return (
            <div className="space-y-2">
                <div className="text-sm font-medium">日期范围</div>
                <div className="text-xs space-y-1">
                    <div>最早: {distribution.minDate || "-"}</div>
                    <div>最晚: {distribution.maxDate || "-"}</div>
                </div>
            </div>
        );
    }
    
    return <div className="text-xs text-muted-foreground">无分布数据</div>;
};

const AnomalyList: React.FC<{ anomalies: IFieldAnomaly[] }> = ({ anomalies }) => {
    if (anomalies.length === 0) {
        return <div className="text-xs text-muted-foreground">未检测到异常</div>;
    }
    
    return (
        <div className="space-y-2">
            <div className="text-sm font-medium">异常检测</div>
            <div className="space-y-2">
                {anomalies.map((anomaly, index) => (
                    <div 
                        key={index} 
                        className={cn(
                            "p-2 rounded text-xs border",
                            anomaly.severity === "high" 
                                ? "bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800" 
                                : "bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800"
                        )}
                    >
                        <div className="flex items-center gap-1 mb-1">
                            <ExclamationTriangleIcon className={cn(
                                "h-3 w-3",
                                anomaly.severity === "high" ? "text-red-500" : "text-yellow-500"
                            )} />
                            <span className="font-medium">
                                {anomaly.type === "outlier" ? "异常值" : 
                                 anomaly.type === "dominant_value" ? "主导值" : anomaly.type}
                            </span>
                            <Badge variant={anomaly.severity === "high" ? "destructive" : "secondary"} className="ml-auto">
                                {anomaly.severity === "high" ? "高" : "中"}
                            </Badge>
                        </div>
                        <div className="text-muted-foreground">{anomaly.description}</div>
                        {anomaly.samples && anomaly.samples.length > 0 && (
                            <div className="mt-1 text-muted-foreground">
                                示例: {anomaly.samples.slice(0, 3).join(", ")}
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
};

const FieldQualityItem: React.FC<IFieldQualityItemProps> = ({ fid, quality, displayName }) => {
    const [expanded, setExpanded] = useState(false);
    const status = getQualityStatus(quality);
    
    return (
        <div className="border rounded-lg overflow-hidden transition-all">
            <div 
                className="flex items-center gap-3 p-3 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800"
                onClick={() => setExpanded(!expanded)}
            >
                <StatusIcon status={status} />
                <div className="flex-1 min-w-0">
                    <div className="font-medium truncate">{displayName}</div>
                    <div className="text-xs text-muted-foreground truncate">{fid}</div>
                </div>
                <div className="flex items-center gap-2">
                    <Badge 
                        variant={status === "good" ? "secondary" : status === "warning" ? "outline" : "destructive"}
                    >
                        {quality.dataType}
                    </Badge>
                    {expanded ? (
                        <ChevronUpIcon className="h-4 w-4 text-muted-foreground" />
                    ) : (
                        <ChevronDownIcon className="h-4 w-4 text-muted-foreground" />
                    )}
                </div>
            </div>
            
            {expanded && (
                <div className="p-3 pt-0 space-y-4 border-t bg-gray-50/50 dark:bg-gray-900/50">
                    <div className="pt-3">
                        <div className="text-sm font-medium mb-2">基础统计</div>
                        <div className="grid grid-cols-2 gap-3">
                            <div>
                                <div className="text-xs text-muted-foreground mb-1">缺失率</div>
                                <MissingRateBar rate={quality.missingRate} />
                            </div>
                            <div>
                                <div className="text-xs text-muted-foreground mb-1">唯一值</div>
                                <div className="text-sm font-mono">{quality.uniqueCount}</div>
                            </div>
                            <div>
                                <div className="text-xs text-muted-foreground mb-1">多样性</div>
                                <div className="text-sm font-mono">{(quality.distinctRate * 100).toFixed(1)}%</div>
                            </div>
                            <div>
                                <div className="text-xs text-muted-foreground mb-1">分析适用性</div>
                                <div className="flex items-center gap-1">
                                    {quality.isSuitableForAnalysis ? (
                                        <><CheckCircledIcon className="h-3 w-3 text-green-500" /><span className="text-xs">适合</span></>
                                    ) : (
                                        <><ExclamationTriangleIcon className="h-3 w-3 text-red-500" /><span className="text-xs">不推荐</span></>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <DistributionInfo distribution={quality.distribution} dataType={quality.dataType} />
                    
                    <AnomalyList anomalies={quality.anomalies} />
                    
                    {quality.warnings.length > 0 && (
                        <div className="space-y-2">
                            <div className="text-sm font-medium">警告提示</div>
                            <ul className="space-y-1">
                                {quality.warnings.map((warning, index) => (
                                    <li key={index} className="flex items-start gap-2 text-xs">
                                        <InfoCircledIcon className="h-3 w-3 text-blue-500 mt-0.5 flex-shrink-0" />
                                        <span>{warning}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

const FieldQualityPanel: React.FC<IFieldQualityPanelProps> = ({ fieldQualities, fieldNames }) => {
    const [open, setOpen] = useState(false);
    
    if (!fieldQualities || Object.keys(fieldQualities).length === 0) {
        return null;
    }
    
    const qualities = Object.entries(fieldQualities);
    const goodCount = qualities.filter(([_, q]) => getQualityStatus(q) === "good").length;
    const warningCount = qualities.filter(([_, q]) => getQualityStatus(q) === "warning").length;
    const errorCount = qualities.filter(([_, q]) => getQualityStatus(q) === "error").length;
    
    return (
        <>
            <button
                onClick={() => setOpen(true)}
                className="fixed right-2 top-2 z-50 flex items-center gap-2 px-3 py-1.5 bg-background border rounded-md shadow-sm hover:bg-accent transition-colors"
            >
                <InfoCircledIcon className="h-4 w-4" />
                <span className="text-xs font-medium">字段质量</span>
                <div className="flex items-center gap-1 ml-2">
                    {goodCount > 0 && (
                        <span className="flex items-center gap-1 text-xs">
                            <CheckCircledIcon className="h-3 w-3 text-green-500" />
                            {goodCount}
                        </span>
                    )}
                    {warningCount > 0 && (
                        <span className="flex items-center gap-1 text-xs">
                            <ExclamationTriangleIcon className="h-3 w-3 text-yellow-500" />
                            {warningCount}
                        </span>
                    )}
                    {errorCount > 0 && (
                        <span className="flex items-center gap-1 text-xs">
                            <ExclamationTriangleIcon className="h-3 w-3 text-red-500" />
                            {errorCount}
                        </span>
                    )}
                </div>
            </button>
            
            <Dialog open={open} onOpenChange={setOpen}>
                <DialogContent className="max-w-3xl max-h-[80vh] overflow-hidden flex flex-col">
                    <DialogHeader>
                        <DialogTitle className="flex items-center gap-2">
                            <InfoCircledIcon className="h-5 w-5" />
                            字段质量概览
                        </DialogTitle>
                        <DialogDescription>
                            查看每个字段的数据质量统计，帮助您在分析前评估字段的可用性。
                        </DialogDescription>
                    </DialogHeader>
                    
                    <div className="flex items-center gap-4 py-2 border-b">
                        <div className="flex items-center gap-1">
                            <CheckCircledIcon className="h-4 w-4 text-green-500" />
                            <span className="text-xs">良好: {goodCount}</span>
                        </div>
                        <div className="flex items-center gap-1">
                            <ExclamationTriangleIcon className="h-4 w-4 text-yellow-500" />
                            <span className="text-xs">警告: {warningCount}</span>
                        </div>
                        <div className="flex items-center gap-1">
                            <ExclamationTriangleIcon className="h-4 w-4 text-red-500" />
                            <span className="text-xs">问题: {errorCount}</span>
                        </div>
                    </div>
                    
                    <div className="flex-1 overflow-y-auto space-y-2 pr-2">
                        {qualities.map(([fid, quality]) => (
                            <FieldQualityItem 
                                key={fid}
                                fid={fid}
                                quality={quality}
                                displayName={fieldNames?.[fid] || fid}
                            />
                        ))}
                    </div>
                </DialogContent>
            </Dialog>
        </>
    );
};

export default FieldQualityPanel;
