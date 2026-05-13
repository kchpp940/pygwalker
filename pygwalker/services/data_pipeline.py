from typing import List, Dict, Any, Optional, Union, Callable, Protocol, runtime_checkable
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class DataPipelineStage(Enum):
    """数据管道阶段枚举"""
    SOURCE = "source"
    FILTER = "filter"
    TRANSFORM = "transform"
    SAMPLE = "sample"
    AGGREGATE = "aggregate"
    OUTPUT = "output"


@runtime_checkable
class DataSource(Protocol):
    """数据源协议 - 定义数据获取接口"""
    
    def get_datas_by_payload(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """通过 payload 获取数据"""
        ...
    
    def get_datas_by_sql(self, sql: str) -> List[Dict[str, Any]]:
        """通过 SQL 获取数据"""
        ...
    
    def batch_get_datas_by_payload(self, payload_list: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """批量通过 payload 获取数据"""
        ...
    
    def batch_get_datas_by_sql(self, sql_list: List[str]) -> List[List[Dict[str, Any]]]:
        """批量通过 SQL 获取数据"""
        ...


@dataclass
class PipelineContext:
    """数据管道上下文 - 存储管道执行过程中的状态和元数据"""
    
    source_type: str
    payload: Optional[Dict[str, Any]] = None
    sql: Optional[str] = None
    filters: List[Dict[str, Any]] = field(default_factory=list)
    filter_logic: str = "AND"
    sampling_strategy: Optional[str] = None
    sample_size: Optional[int] = None
    byte_limit: Optional[int] = None
    preserve_boundaries: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def update(self, **kwargs) -> "PipelineContext":
        """更新上下文属性"""
        for key, value in kwargs.items():
            setattr(self, key, value)
        return self


class PipelineStage:
    """管道阶段基类"""
    
    def __init__(self, name: str):
        self.name = name
    
    def execute(self, data: List[Dict[str, Any]], context: PipelineContext) -> List[Dict[str, Any]]:
        """执行阶段 - 子类需要重写此方法"""
        raise NotImplementedError
    
    def __call__(self, data: List[Dict[str, Any]], context: PipelineContext) -> List[Dict[str, Any]]:
        return self.execute(data, context)


class FilterStage(PipelineStage):
    """过滤阶段 - 应用过滤条件到数据"""
    
    def __init__(self):
        super().__init__("filter")
    
    def execute(self, data: List[Dict[str, Any]], context: PipelineContext) -> List[Dict[str, Any]]:
        if not context.filters:
            return data
        
        enabled_filters = [f for f in context.filters if f.get("enabled", True)]
        if not enabled_filters:
            return data
        
        try:
            return self._apply_filters(data, enabled_filters, context.filter_logic)
        except Exception as e:
            logger.warning(f"Filter stage failed: {e}, returning original data")
            return data
    
    def _apply_filters(
        self, 
        data: List[Dict[str, Any]], 
        filters: List[Dict[str, Any]], 
        logic: str
    ) -> List[Dict[str, Any]]:
        """应用多个过滤条件"""
        if logic == "AND":
            return [
                row for row in data 
                if all(self._match_condition(row, f) for f in filters)
            ]
        else:
            return [
                row for row in data 
                if any(self._match_condition(row, f) for f in filters)
            ]
    
    def _match_condition(self, row: Dict[str, Any], condition: Dict[str, Any]) -> bool:
        """检查单行是否满足过滤条件"""
        fid = condition.get("fid")
        condition_type = condition.get("conditionType", condition.get("type"))
        value = condition.get("value")
        
        if fid not in row:
            return False
        
        row_value = row[fid]
        
        if condition_type == "range":
            return self._match_range(row_value, value)
        elif condition_type == "temporal range":
            return self._match_temporal_range(row_value, value)
        elif condition_type == "one of":
            return self._match_one_of(row_value, value)
        elif condition_type == "not in":
            return not self._match_one_of(row_value, value)
        elif condition_type == "contains":
            return self._match_contains(row_value, value)
        elif condition_type == "equals":
            return row_value == value
        elif condition_type == "greater than":
            return self._match_greater_than(row_value, value)
        elif condition_type == "less than":
            return self._match_less_than(row_value, value)
        elif condition.get("rule"):
            rule = condition["rule"]
            rule_type = rule.get("type")
            rule_value = rule.get("value")
            if rule_type == "range":
                return self._match_range(row_value, rule_value)
            elif rule_type == "temporal range":
                return self._match_temporal_range(row_value, rule_value)
            elif rule_type == "one of":
                return self._match_one_of(row_value, rule_value)
            elif rule_type == "not in":
                return not self._match_one_of(row_value, rule_value)
        
        return True
    
    def _match_range(self, value: Any, range_value: List[Any]) -> bool:
        if not isinstance(range_value, (list, tuple)) or len(range_value) != 2:
            return True
        min_val, max_val = range_value
        if not isinstance(value, (int, float)):
            return False
        above_min = min_val is None or value >= min_val
        below_max = max_val is None or value <= max_val
        return above_min and below_max
    
    def _match_temporal_range(self, value: Any, range_value: List[Any]) -> bool:
        if not isinstance(range_value, (list, tuple)) or len(range_value) != 2:
            return True
        min_val, max_val = range_value
        
        import datetime
        try:
            if isinstance(value, datetime.datetime):
                timestamp = value.timestamp() * 1000
            elif isinstance(value, str):
                timestamp = datetime.datetime.fromisoformat(value.replace('Z', '+00:00')).timestamp() * 1000
            else:
                timestamp = float(value)
            
            above_min = min_val is None or timestamp >= min_val
            below_max = max_val is None or timestamp <= max_val
            return above_min and below_max
        except (ValueError, TypeError):
            return False
    
    def _match_one_of(self, value: Any, values: List[Any]) -> bool:
        if not isinstance(values, (list, tuple, set)):
            return True
        return value in values
    
    def _match_contains(self, value: Any, substring: str) -> bool:
        if not isinstance(value, str) or not isinstance(substring, str):
            return False
        return substring.lower() in value.lower()
    
    def _match_greater_than(self, value: Any, threshold: Any) -> bool:
        if threshold is None:
            return True
        if not isinstance(value, (int, float)) or not isinstance(threshold, (int, float)):
            return False
        return value > threshold
    
    def _match_less_than(self, value: Any, threshold: Any) -> bool:
        if threshold is None:
            return True
        if not isinstance(value, (int, float)) or not isinstance(threshold, (int, float)):
            return False
        return value < threshold


class SamplingStage(PipelineStage):
    """采样阶段 - 对数据进行采样"""
    
    def __init__(self):
        super().__init__("sample")
    
    def execute(self, data: List[Dict[str, Any]], context: PipelineContext) -> List[Dict[str, Any]]:
        if context.sampling_strategy is None:
            return data
        
        try:
            if context.sampling_strategy == "smart":
                return self._smart_sample(data, context)
            elif context.sampling_strategy == "scatter":
                return self._scatter_sample(data, context)
            elif context.sampling_strategy == "byte_limit":
                return self._byte_limit_sample(data, context)
            elif context.sampling_strategy == "random":
                return self._random_sample(data, context)
            else:
                return data
        except Exception as e:
            logger.warning(f"Sampling stage failed: {e}, returning original data")
            return data
    
    def _smart_sample(self, data: List[Dict[str, Any]], context: PipelineContext) -> List[Dict[str, Any]]:
        """智能采样 - 保留数据分布特征"""
        from pygwalker.utils.estimate_tools import smart_sample_datas
        
        if context.sample_size is None:
            return data
        
        return smart_sample_datas(
            data, 
            context.sample_size, 
            preserve_boundaries=context.preserve_boundaries
        )
    
    def _scatter_sample(self, data: List[Dict[str, Any]], context: PipelineContext) -> List[Dict[str, Any]]:
        """散点图专用采样"""
        from pygwalker._constants import (
            SCATTER_PLOT_SAMPLE_LIMIT,
            SCATTER_PLOT_LARGE_DATA_THRESHOLD
        )
        from pygwalker.utils.estimate_tools import smart_sample_datas
        
        n = len(data)
        
        if n <= SCATTER_PLOT_LARGE_DATA_THRESHOLD:
            return data
        
        sample_size = min(SCATTER_PLOT_SAMPLE_LIMIT, SCATTER_PLOT_LARGE_DATA_THRESHOLD // 2)
        
        return smart_sample_datas(data, sample_size, preserve_boundaries=True)
    
    def _byte_limit_sample(self, data: List[Dict[str, Any]], context: PipelineContext) -> List[Dict[str, Any]]:
        """基于字节限制的采样"""
        from pygwalker.utils.estimate_tools import sample_datas_by_byte_limit
        
        if context.byte_limit is None:
            return data
        
        return sample_datas_by_byte_limit(
            data, 
            context.byte_limit,
            min_sample_size=context.sample_size or 100
        )
    
    def _random_sample(self, data: List[Dict[str, Any]], context: PipelineContext) -> List[Dict[str, Any]]:
        """随机采样"""
        import random
        
        if context.sample_size is None or len(data) <= context.sample_size:
            return data
        
        indices = sorted(random.sample(range(len(data)), context.sample_size))
        return [data[i] for i in indices]


class DataPipeline:
    """统一数据管道 - 协调各个阶段的执行"""
    
    def __init__(
        self,
        data_source: DataSource,
        stages: Optional[List[PipelineStage]] = None,
        context: Optional[PipelineContext] = None
    ):
        self.data_source = data_source
        self.stages = stages or [
            FilterStage(),
            SamplingStage()
        ]
        self.context = context or PipelineContext(source_type="unknown")
    
    @classmethod
    def create(
        cls,
        data_source: DataSource,
        **context_kwargs
    ) -> "DataPipeline":
        """工厂方法创建数据管道"""
        context = PipelineContext(
            source_type=getattr(data_source, 'dataset_type', 'unknown'),
            **context_kwargs
        )
        return cls(data_source, context=context)
    
    def configure(self, **kwargs) -> "DataPipeline":
        """配置管道上下文"""
        self.context.update(**kwargs)
        return self
    
    def add_stage(self, stage: PipelineStage) -> "DataPipeline":
        """添加处理阶段"""
        self.stages.append(stage)
        return self
    
    def _fetch_data(self) -> List[Dict[str, Any]]:
        """从数据源获取原始数据"""
        if self.context.payload is not None:
            return self.data_source.get_datas_by_payload(self.context.payload)
        elif self.context.sql is not None:
            return self.data_source.get_datas_by_sql(self.context.sql)
        else:
            raise ValueError("Either payload or sql must be provided in context")
    
    def execute(
        self,
        payload: Optional[Dict[str, Any]] = None,
        sql: Optional[str] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        执行数据管道
        
        Args:
            payload: 数据查询 payload
            sql: 数据查询 SQL
            **kwargs: 其他上下文参数
            
        Returns:
            处理后的数据列表
        """
        if payload is not None:
            self.context.payload = payload
        if sql is not None:
            self.context.sql = sql
        
        if kwargs:
            self.context.update(**kwargs)
        
        data = self._fetch_data()
        
        for stage in self.stages:
            data = stage.execute(data, self.context)
        
        return data
    
    def execute_batch(
        self,
        payload_list: Optional[List[Dict[str, Any]]] = None,
        sql_list: Optional[List[str]] = None,
        **kwargs
    ) -> List[List[Dict[str, Any]]]:
        """
        批量执行数据管道
        
        Args:
            payload_list: 数据查询 payload 列表
            sql_list: 数据查询 SQL 列表
            **kwargs: 其他上下文参数
            
        Returns:
            处理后的数据列表的列表
        """
        if kwargs:
            self.context.update(**kwargs)
        
        if payload_list is not None:
            raw_datas = self.data_source.batch_get_datas_by_payload(payload_list)
        elif sql_list is not None:
            raw_datas = self.data_source.batch_get_datas_by_sql(sql_list)
        else:
            raise ValueError("Either payload_list or sql_list must be provided")
        
        results = []
        for data in raw_datas:
            for stage in self.stages:
                data = stage.execute(data, self.context)
            results.append(data)
        
        return results


class PipelineBuilder:
    """数据管道构建器"""
    
    def __init__(self, data_source: DataSource):
        self.data_source = data_source
        self.stages: List[PipelineStage] = []
        self.context_kwargs: Dict[str, Any] = {}
    
    def with_filter(
        self,
        filters: List[Dict[str, Any]],
        logic: str = "AND"
    ) -> "PipelineBuilder":
        """添加过滤配置"""
        if filters:
            self.stages.append(FilterStage())
            self.context_kwargs["filters"] = filters
            self.context_kwargs["filter_logic"] = logic
        return self
    
    def with_sampling(
        self,
        strategy: str,
        sample_size: Optional[int] = None,
        byte_limit: Optional[int] = None,
        preserve_boundaries: bool = False
    ) -> "PipelineBuilder":
        """添加采样配置"""
        self.stages.append(SamplingStage())
        self.context_kwargs["sampling_strategy"] = strategy
        if sample_size is not None:
            self.context_kwargs["sample_size"] = sample_size
        if byte_limit is not None:
            self.context_kwargs["byte_limit"] = byte_limit
        self.context_kwargs["preserve_boundaries"] = preserve_boundaries
        return self
    
    def with_scatter_sampling(self) -> "PipelineBuilder":
        """添加散点图专用采样"""
        return self.with_sampling("scatter")
    
    def with_byte_limit_sampling(self, byte_limit: int) -> "PipelineBuilder":
        """添加基于字节限制的采样"""
        return self.with_sampling("byte_limit", byte_limit=byte_limit)
    
    def with_smart_sampling(self, sample_size: int, preserve_boundaries: bool = True) -> "PipelineBuilder":
        """添加智能采样"""
        return self.with_sampling(
            "smart", 
            sample_size=sample_size, 
            preserve_boundaries=preserve_boundaries
        )
    
    def with_metadata(self, **metadata) -> "PipelineBuilder":
        """添加元数据"""
        existing_metadata = self.context_kwargs.get("metadata", {})
        existing_metadata.update(metadata)
        self.context_kwargs["metadata"] = existing_metadata
        return self
    
    def build(self) -> DataPipeline:
        """构建数据管道"""
        return DataPipeline(
            self.data_source,
            stages=self.stages,
            context=PipelineContext(
                source_type=getattr(self.data_source, 'dataset_type', 'unknown'),
                **self.context_kwargs
            )
        )


def create_pipeline_builder(data_source: DataSource) -> PipelineBuilder:
    """创建管道构建器的便捷函数"""
    return PipelineBuilder(data_source)
