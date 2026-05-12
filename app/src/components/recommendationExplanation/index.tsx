import React, { useState } from 'react';
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from '../ui/dialog';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';

export interface ChartTypeExplanation {
    type: string;
    reasons: string[];
    advantages: string[];
}

export interface FieldExplanation {
    fieldName: string;
    fieldType: string;
    semanticType: string;
    reason: string;
    encoding: string | null;
}

export interface AggregationExplanation {
    fieldName: string;
    aggregationType: string;
    reason: string;
}

export interface RecommendationExplanationData {
    chartType: ChartTypeExplanation;
    fields: FieldExplanation[];
    aggregations: AggregationExplanation[];
    visualEncoding: Record<string, string>;
    overallSummary: string;
    dataInsights: string[];
}

interface RecommendationExplanationProps {
    explanation: RecommendationExplanationData | null;
    isLoading?: boolean;
    trigger?: React.ReactNode;
    open?: boolean;
    onOpenChange?: (open: boolean) => void;
}

const chartTypeNames: Record<string, string> = {
    bar: '柱状图',
    line: '折线图',
    area: '面积图',
    scatter: '散点图',
    pie: '饼图',
    histogram: '直方图',
    box_plot: '箱线图',
    map: '地图',
    table: '表格'
};

const fieldTypeNames: Record<string, string> = {
    dimension: '维度',
    measure: '度量'
};

const semanticTypeNames: Record<string, string> = {
    nominal: '名义型',
    ordinal: '有序型',
    temporal: '时间型',
    quantitative: '数值型',
    geo: '地理型'
};

const encodingTypeNames: Record<string, string> = {
    x: 'X轴',
    y: 'Y轴',
    color: '颜色',
    size: '大小',
    shape: '形状',
    text: '文本',
    row: '行',
    column: '列',
    detail: '详情'
};

const aggregationTypeNames: Record<string, string> = {
    sum: '求和',
    avg: '平均值',
    count: '计数',
    min: '最小值',
    max: '最大值',
    median: '中位数',
    none: '无'
};

export const RecommendationExplanation: React.FC<RecommendationExplanationProps> = ({
    explanation,
    isLoading = false,
    trigger,
    open,
    onOpenChange
}) => {
    const [internalOpen, setInternalOpen] = useState(false);
    const isControlled = open !== undefined;
    const currentOpen = isControlled ? open! : internalOpen;
    const setCurrentOpen = isControlled ? onOpenChange! : setInternalOpen;

    if (isLoading) {
        return (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <div className="animate-spin h-4 w-4 border-2 border-current border-t-transparent rounded-full" />
                正在生成推荐解释...
            </div>
        );
    }

    if (!explanation) {
        return null;
    }

    const defaultTrigger = (
        <Button variant="outline" size="sm" className="gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
                <circle cx="12" cy="12" r="10" />
                <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
                <path d="M12 17h.01" />
            </svg>
            推荐解释
        </Button>
    );

    return (
        <Dialog open={currentOpen} onOpenChange={setCurrentOpen}>
            <DialogTrigger asChild>
                {trigger || defaultTrigger}
            </DialogTrigger>
            <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle className="text-lg font-semibold flex items-center gap-2">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5 text-primary">
                            <circle cx="12" cy="12" r="10" />
                            <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
                            <path d="M12 17h.01" />
                        </svg>
                        可视化推荐解释
                    </DialogTitle>
                </DialogHeader>

                <div className="space-y-6">
                    <div className="p-4 bg-primary/5 rounded-lg border border-primary/20">
                        <h3 className="text-sm font-medium text-primary mb-2">总体摘要</h3>
                        <p className="text-sm text-foreground leading-relaxed">
                            {explanation.overallSummary}
                        </p>
                    </div>

                    <Tabs defaultValue="chart" className="w-full">
                        <TabsList className="w-full grid grid-cols-4">
                            <TabsTrigger value="chart">图表类型</TabsTrigger>
                            <TabsTrigger value="fields">字段选择</TabsTrigger>
                            <TabsTrigger value="aggregation">聚合方式</TabsTrigger>
                            <TabsTrigger value="insights">数据洞察</TabsTrigger>
                        </TabsList>

                        <TabsContent value="chart" className="space-y-4 pt-4">
                            <div className="space-y-3">
                                <div className="flex items-center gap-2">
                                    <Badge variant="secondary" className="text-base px-3 py-1">
                                        {chartTypeNames[explanation.chartType.type] || explanation.chartType.type}
                                    </Badge>
                                </div>

                                <div>
                                    <h4 className="text-sm font-medium mb-2">选择原因</h4>
                                    <ul className="space-y-1">
                                        {explanation.chartType.reasons.map((reason, index) => (
                                            <li key={index} className="text-sm text-muted-foreground flex items-start gap-2">
                                                <span className="text-primary mt-0.5">•</span>
                                                {reason}
                                            </li>
                                        ))}
                                    </ul>
                                </div>

                                <div>
                                    <h4 className="text-sm font-medium mb-2">图表优势</h4>
                                    <ul className="space-y-1">
                                        {explanation.chartType.advantages.map((advantage, index) => (
                                            <li key={index} className="text-sm text-muted-foreground flex items-start gap-2">
                                                <span className="text-green-500 mt-0.5">✓</span>
                                                {advantage}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            </div>
                        </TabsContent>

                        <TabsContent value="fields" className="space-y-4 pt-4">
                            <div className="space-y-3">
                                {explanation.fields.map((field, index) => (
                                    <div key={index} className="p-3 bg-card rounded-lg border">
                                        <div className="flex items-center gap-2 mb-2">
                                            <span className="font-medium text-sm">{field.fieldName}</span>
                                            <Badge variant="outline" className="text-xs">
                                                {fieldTypeNames[field.fieldType] || field.fieldType}
                                            </Badge>
                                            <Badge variant="outline" className="text-xs">
                                                {semanticTypeNames[field.semanticType] || field.semanticType}
                                            </Badge>
                                            {field.encoding && (
                                                <Badge variant="secondary" className="text-xs">
                                                    {encodingTypeNames[field.encoding] || field.encoding}
                                                </Badge>
                                            )}
                                        </div>
                                        <p className="text-sm text-muted-foreground">
                                            {field.reason}
                                        </p>
                                    </div>
                                ))}
                            </div>

                            {explanation.visualEncoding && Object.keys(explanation.visualEncoding).length > 0 && (
                                <div className="mt-4">
                                    <h4 className="text-sm font-medium mb-2">可视编码</h4>
                                    <div className="grid grid-cols-2 gap-2">
                                        {Object.entries(explanation.visualEncoding).map(([encoding, fields]) => (
                                            <div key={encoding} className="flex items-center gap-2 text-sm">
                                                <Badge variant="outline">
                                                    {encodingTypeNames[encoding] || encoding}
                                                </Badge>
                                                <span className="text-muted-foreground">{fields}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </TabsContent>

                        <TabsContent value="aggregation" className="space-y-4 pt-4">
                            {explanation.aggregations.length > 0 ? (
                                <div className="space-y-3">
                                    {explanation.aggregations.map((agg, index) => (
                                        <div key={index} className="p-3 bg-card rounded-lg border">
                                            <div className="flex items-center gap-2 mb-2">
                                                <span className="font-medium text-sm">{agg.fieldName}</span>
                                                <Badge variant="secondary">
                                                    {aggregationTypeNames[agg.aggregationType] || agg.aggregationType}
                                                </Badge>
                                            </div>
                                            <p className="text-sm text-muted-foreground">
                                                {agg.reason}
                                            </p>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="text-sm text-muted-foreground text-center py-8">
                                    该图表未使用聚合函数
                                </div>
                            )}
                        </TabsContent>

                        <TabsContent value="insights" className="space-y-4 pt-4">
                            {explanation.dataInsights.length > 0 ? (
                                <div className="space-y-2">
                                    {explanation.dataInsights.map((insight, index) => (
                                        <div key={index} className="p-3 bg-amber-50 dark:bg-amber-950/30 rounded-lg border border-amber-200 dark:border-amber-800">
                                            <p className="text-sm text-amber-800 dark:text-amber-200 flex items-start gap-2">
                                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4 mt-0.5 flex-shrink-0">
                                                    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                                                    <line x1="12" y1="9" x2="12" y2="13" />
                                                    <line x1="12" y1="17" x2="12.01" y2="17" />
                                                </svg>
                                                {insight}
                                            </p>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="text-sm text-muted-foreground text-center py-8">
                                    未发现需要特别注意的数据问题
                                </div>
                            )}
                        </TabsContent>
                    </Tabs>
                </div>
            </DialogContent>
        </Dialog>
    );
};

export default RecommendationExplanation;
