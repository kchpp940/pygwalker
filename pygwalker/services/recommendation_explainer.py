from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class VisualEncodingType(str, Enum):
    X = "x"
    Y = "y"
    COLOR = "color"
    SIZE = "size"
    SHAPE = "shape"
    ROW = "row"
    COLUMN = "column"
    TEXT = "text"
    DETAIL = "detail"


class ChartType(str, Enum):
    BAR = "bar"
    LINE = "line"
    AREA = "area"
    SCATTER = "scatter"
    PIE = "pie"
    HISTOGRAM = "histogram"
    BOX_PLOT = "box_plot"
    MAP = "map"
    TABLE = "table"


class AggregationType(str, Enum):
    SUM = "sum"
    AVG = "avg"
    COUNT = "count"
    MIN = "min"
    MAX = "max"
    MEDIAN = "median"
    NONE = "none"


@dataclass
class FieldExplanation:
    field_name: str
    field_type: str
    semantic_type: str
    reason: str
    encoding: Optional[VisualEncodingType] = None


@dataclass
class ChartTypeExplanation:
    chart_type: ChartType
    reasons: List[str]
    advantages: List[str]


@dataclass
class AggregationExplanation:
    field_name: str
    aggregation_type: AggregationType
    reason: str


@dataclass
class RecommendationExplanation:
    chart_type: ChartTypeExplanation
    fields: List[FieldExplanation]
    aggregations: List[AggregationExplanation]
    visual_encoding: Dict[VisualEncodingType, str]
    overall_summary: str
    data_insights: List[str]


class RecommendationExplainer:
    """
    A service to generate explanations for visualization recommendations.
    """

    def __init__(self, field_qualities: Dict[str, Any]):
        self.field_qualities = field_qualities

    def explain_recommendation(
        self,
        spec: Dict[str, Any],
        metas: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive explanation for a visualization recommendation.
        
        Args:
            spec: The visualization specification
            metas: Field metadata information
            
        Returns:
            A dictionary containing the explanation details
        """
        chart_type = self._identify_chart_type(spec)
        field_info = self._extract_field_info(spec, metas)
        
        chart_explanation = self._explain_chart_type(chart_type, field_info)
        field_explanations = self._explain_fields(field_info)
        aggregation_explanations = self._explain_aggregations(field_info)
        visual_encoding = self._extract_visual_encoding(spec)
        overall_summary = self._generate_overall_summary(
            chart_type, field_explanations, aggregation_explanations
        )
        data_insights = self._generate_data_insights(field_info)
        
        explanation = RecommendationExplanation(
            chart_type=chart_explanation,
            fields=field_explanations,
            aggregations=aggregation_explanations,
            visual_encoding=visual_encoding,
            overall_summary=overall_summary,
            data_insights=data_insights
        )
        
        return self._explanation_to_dict(explanation)

    def _identify_chart_type(self, spec: Dict[str, Any]) -> ChartType:
        """Identify the chart type from the specification."""
        config = spec.get("config", {})
        geom = config.get("geom", "")
        
        chart_type_map = {
            "interval": ChartType.BAR,
            "line": ChartType.LINE,
            "area": ChartType.AREA,
            "point": ChartType.SCATTER,
            "arc": ChartType.PIE,
            "histogram": ChartType.HISTOGRAM,
            "boxplot": ChartType.BOX_PLOT,
            "map": ChartType.MAP,
        }
        
        for key, value in chart_type_map.items():
            if key in geom.lower():
                return value
        
        encodings = spec.get("encodings", {})
        rows = encodings.get("rows", [])
        columns = encodings.get("columns", [])
        
        if rows and not columns and len(rows) <= 1:
            return ChartType.BAR
        elif rows and columns:
            return ChartType.SCATTER
        
        return ChartType.TABLE

    def _extract_field_info(
        self,
        spec: Dict[str, Any],
        metas: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract field information from the specification."""
        encodings = spec.get("encodings", {})
        field_info = []
        
        meta_map = {meta.get("fid") or meta.get("key"): meta for meta in metas}
        
        for channel_name, fields in encodings.items():
            if isinstance(fields, list):
                for field in fields:
                    fid = field.get("fid")
                    if fid:
                        meta = meta_map.get(fid, {})
                        quality = self.field_qualities.get(fid, {})
                        field_info.append({
                            "fid": fid,
                            "name": field.get("name", fid),
                            "channel": channel_name,
                            "analytic_type": field.get("analyticType", meta.get("analyticType", "dimension")),
                            "semantic_type": field.get("semanticType", meta.get("semanticType", "nominal")),
                            "aggregation": field.get("aggName", "none"),
                            "meta": meta,
                            "quality": quality
                        })
        
        return field_info

    def _explain_chart_type(
        self,
        chart_type: ChartType,
        field_info: List[Dict[str, Any]]
    ) -> ChartTypeExplanation:
        """Generate explanation for the chosen chart type."""
        reasons = []
        advantages = []
        
        dimensions = [f for f in field_info if f["analytic_type"] == "dimension"]
        measures = [f for f in field_info if f["analytic_type"] == "measure"]
        
        if chart_type == ChartType.BAR:
            if dimensions:
                reasons.append(f"包含 {len(dimensions)} 个分类维度，适合使用柱状图进行对比展示")
            if measures:
                reasons.append(f"包含 {len(measures)} 个度量字段，柱状图可以清晰展示数值差异")
            advantages.extend([
                "便于类别间的数值比较",
                "易于理解和解释",
                "适合展示分类数据的分布"
            ])
        
        elif chart_type == ChartType.LINE:
            time_fields = [f for f in dimensions if f["semantic_type"] in ["temporal", "datetime"]]
            if time_fields:
                reasons.append("包含时间维度，折线图适合展示趋势变化")
            reasons.append(f"包含 {len(measures)} 个连续度量，适合展示数据趋势")
            advantages.extend([
                "清晰展示数据随时间的变化趋势",
                "便于发现模式和季节性",
                "支持多系列对比"
            ])
        
        elif chart_type == ChartType.SCATTER:
            if len(measures) >= 2:
                reasons.append(f"包含 {len(measures)} 个度量字段，散点图适合探索变量关系")
            reasons.append("散点图可以发现数据中的聚类和异常值")
            advantages.extend([
                "探索两个变量之间的关系",
                "发现数据中的模式和聚类",
                "识别异常值"
            ])
        
        elif chart_type == ChartType.PIE:
            if len(dimensions) == 1:
                reasons.append("单个分类维度，饼图适合展示占比关系")
            advantages.extend([
                "直观展示各部分占整体的比例",
                "适合类别数量较少的场景"
            ])
        
        elif chart_type == ChartType.HISTOGRAM:
            if len(measures) >= 1:
                reasons.append("包含数值型度量，直方图适合展示分布情况")
            advantages.extend([
                "展示数据的分布形态",
                "发现数据的集中趋势和离散程度",
                "识别偏态和多峰分布"
            ])
        
        elif chart_type == ChartType.MAP:
            geo_fields = [f for f in dimensions if f["semantic_type"] in ["geo", "geography"]]
            if geo_fields:
                reasons.append("包含地理字段，地图适合展示空间分布")
            advantages.extend([
                "直观展示地理空间分布",
                "便于发现区域模式"
            ])
        
        else:
            reasons.append("根据字段类型和数量自动选择合适的图表类型")
            advantages.append("灵活适应不同数据特点")
        
        return ChartTypeExplanation(
            chart_type=chart_type,
            reasons=reasons if reasons else ["基于数据特征自动选择的最优图表类型"],
            advantages=advantages
        )

    def _explain_fields(
        self,
        field_info: List[Dict[str, Any]]
    ) -> List[FieldExplanation]:
        """Generate explanations for each field used in the visualization."""
        explanations = []
        
        for field in field_info:
            quality = field.get("quality", {})
            channel = field["channel"]
            encoding_map = {
                "rows": VisualEncodingType.Y,
                "columns": VisualEncodingType.X,
                "color": VisualEncodingType.COLOR,
                "size": VisualEncodingType.SIZE,
                "shape": VisualEncodingType.SHAPE,
                "text": VisualEncodingType.TEXT,
            }
            encoding = encoding_map.get(channel)
            
            reason_parts = []
            
            if field["analytic_type"] == "dimension":
                reason_parts.append(f"{field['name']} 是分类维度")
                if field["semantic_type"] == "temporal":
                    reason_parts.append("具有时间语义，适合用于趋势分析")
                elif field["semantic_type"] == "nominal":
                    reason_parts.append("是名义型数据，适合用于分组和对比")
                elif field["semantic_type"] == "ordinal":
                    reason_parts.append("是有序型数据，适合用于排序展示")
                
                distinct_rate = quality.get("distinctRate", 0)
                if 0.05 <= distinct_rate <= 0.5:
                    reason_parts.append("基数适中，便于分类展示")
                elif distinct_rate > 0.5:
                    reason_parts.append("基数较高，可能需要注意展示方式")
                
            else:
                reason_parts.append(f"{field['name']} 是数值度量")
                if quality.get("distribution"):
                    dist = quality["distribution"]
                    if dist.get("stddev") and dist.get("mean"):
                        cv = dist["stddev"] / dist["mean"] if dist["mean"] != 0 else 0
                        if cv > 0.3:
                            reason_parts.append("数据变异程度较大，适合聚合展示")
            
            missing_rate = quality.get("missingRate", 0)
            if missing_rate > 0.2:
                reason_parts.append(f"注意：该字段有 {missing_rate*100:.1f}% 的缺失值")
            
            reason = "。".join(reason_parts) + "。" if reason_parts else "自动选择用于可视化。"
            
            explanations.append(FieldExplanation(
                field_name=field["name"],
                field_type=field["analytic_type"],
                semantic_type=field["semantic_type"],
                reason=reason,
                encoding=encoding
            ))
        
        return explanations

    def _explain_aggregations(
        self,
        field_info: List[Dict[str, Any]]
    ) -> List[AggregationExplanation]:
        """Generate explanations for aggregation choices."""
        explanations = []
        
        for field in field_info:
            if field["analytic_type"] == "measure":
                aggregation = field["aggregation"].lower()
                
                reason = ""
                if aggregation == "sum":
                    reason = f"{field['name']} 使用求和聚合，适合展示总量和累积效果"
                elif aggregation == "avg":
                    reason = f"{field['name']} 使用平均值聚合，适合展示典型值和集中趋势"
                elif aggregation == "count":
                    reason = f"{field['name']} 使用计数聚合，适合统计数量和频率"
                elif aggregation == "min":
                    reason = f"{field['name']} 使用最小值聚合，适合发现下限和边界值"
                elif aggregation == "max":
                    reason = f"{field['name']} 使用最大值聚合，适合发现上限和边界值"
                elif aggregation == "median":
                    reason = f"{field['name']} 使用中位数聚合，对异常值不敏感，适合偏态分布"
                else:
                    reason = f"{field['name']} 使用 {aggregation} 聚合"
                
                explanations.append(AggregationExplanation(
                    field_name=field["name"],
                    aggregation_type=AggregationType(aggregation) if aggregation in [e.value for e in AggregationType] else AggregationType.NONE,
                    reason=reason
                ))
        
        return explanations

    def _extract_visual_encoding(
        self,
        spec: Dict[str, Any]
    ) -> Dict[VisualEncodingType, str]:
        """Extract visual encoding information."""
        encodings = spec.get("encodings", {})
        visual_encoding = {}
        
        encoding_map = {
            "rows": VisualEncodingType.Y,
            "columns": VisualEncodingType.X,
            "color": VisualEncodingType.COLOR,
            "size": VisualEncodingType.SIZE,
            "shape": VisualEncodingType.SHAPE,
            "text": VisualEncodingType.TEXT,
        }
        
        for channel, fields in encodings.items():
            if isinstance(fields, list) and fields and channel in encoding_map:
                field_names = [f.get("name", f.get("fid")) for f in fields]
                visual_encoding[encoding_map[channel]] = ", ".join(field_names)
        
        return visual_encoding

    def _generate_overall_summary(
        self,
        chart_type: ChartType,
        field_explanations: List[FieldExplanation],
        aggregation_explanations: List[AggregationExplanation]
    ) -> str:
        """Generate an overall summary of the recommendation."""
        chart_type_names = {
            ChartType.BAR: "柱状图",
            ChartType.LINE: "折线图",
            ChartType.AREA: "面积图",
            ChartType.SCATTER: "散点图",
            ChartType.PIE: "饼图",
            ChartType.HISTOGRAM: "直方图",
            ChartType.BOX_PLOT: "箱线图",
            ChartType.MAP: "地图",
            ChartType.TABLE: "表格"
        }
        
        chart_name = chart_type_names.get(chart_type, "图表")
        
        dimensions = [f for f in field_explanations if f.field_type == "dimension"]
        measures = [f for f in field_explanations if f.field_type == "measure"]
        
        summary_parts = [
            f"系统推荐使用 {chart_name}"
        ]
        
        if dimensions:
            dim_names = [f.field_name for f in dimensions]
            summary_parts.append(f"以 {', '.join(dim_names)} 为维度")
        
        if measures:
            mea_names = [f.field_name for f in measures]
            summary_parts.append(f"分析 {', '.join(mea_names)} 的{aggregation_explanations[0].aggregation_type.value if aggregation_explanations else '分布'}")
        
        return "，".join(summary_parts) + "。"

    def _generate_data_insights(
        self,
        field_info: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate potential data insights based on field qualities."""
        insights = []
        
        for field in field_info:
            quality = field.get("quality", {})
            name = field["name"]
            
            anomalies = quality.get("anomalies", [])
            for anomaly in anomalies:
                if anomaly.get("type") == "outlier":
                    insights.append(f"{name} 可能存在异常值，建议在分析时注意")
                elif anomaly.get("type") == "dominant_value":
                    insights.append(f"{name} 中存在占主导地位的值（{anomaly.get('percentage', 0):.1f}%）")
            
            warnings = quality.get("warnings", [])
            for warning in warnings:
                insights.append(f"{name}: {warning}")
            
            if field["analytic_type"] == "measure" and quality.get("distribution"):
                dist = quality["distribution"]
                if dist.get("stddev") and dist.get("mean"):
                    cv = dist["stddev"] / dist["mean"] if dist["mean"] != 0 else 0
                    if cv > 0.5:
                        insights.append(f"{name} 的数据离散程度较高（变异系数: {cv:.2f}）")
        
        return list(set(insights))[:5]

    def _explanation_to_dict(
        self,
        explanation: RecommendationExplanation
    ) -> Dict[str, Any]:
        """Convert explanation object to dictionary for JSON serialization."""
        return {
            "chartType": {
                "type": explanation.chart_type.chart_type.value,
                "reasons": explanation.chart_type.reasons,
                "advantages": explanation.chart_type.advantages
            },
            "fields": [
                {
                    "fieldName": f.field_name,
                    "fieldType": f.field_type,
                    "semanticType": f.semantic_type,
                    "reason": f.reason,
                    "encoding": f.encoding.value if f.encoding else None
                }
                for f in explanation.fields
            ],
            "aggregations": [
                {
                    "fieldName": a.field_name,
                    "aggregationType": a.aggregation_type.value,
                    "reason": a.reason
                }
                for a in explanation.aggregations
            ],
            "visualEncoding": {
                k.value: v for k, v in explanation.visual_encoding.items()
            },
            "overallSummary": explanation.overall_summary,
            "dataInsights": explanation.data_insights
        }
