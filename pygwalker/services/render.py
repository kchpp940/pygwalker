import os
import json
import base64
import html as m_html
from typing import Dict, List, Any, Optional
import zlib

from jinja2 import Environment, PackageLoader

from pygwalker._typing import IAppearance
from pygwalker._constants import (
    ROOT_DIR,
    SCATTER_PLOT_SAMPLE_LIMIT,
    SCATTER_PLOT_LARGE_DATA_THRESHOLD,
    SMART_SAMPLE_MIN_SIZE
)
from pygwalker.utils.encode import DataFrameEncoder
from pygwalker.utils.estimate_tools import (
    estimate_average_data_size,
    smart_sample_datas,
    sample_datas_by_byte_limit
)
from pygwalker.services.global_var import GlobalVarManager

jinja_env = Environment(
    loader=PackageLoader("pygwalker"),
    autoescape=(()),  # select_autoescape()
)


def compress_data(data: str) -> str:
    compress = zlib.compressobj(zlib.Z_BEST_COMPRESSION, zlib.DEFLATED, 15, 8, 0)
    compressed_data = compress.compress(data.encode())
    compressed_data += compress.flush()
    return base64.b64encode(compressed_data).decode()


with open(os.path.join(ROOT_DIR, 'templates', 'dist', 'pygwalker-app.iife.js'), 'r', encoding='utf8') as f:
    GWALKER_SCRIPT = f.read()
    GWALKER_SCRIPT_BASE64 = compress_data(GWALKER_SCRIPT)


def get_max_limited_datas(datas: List[Dict[str, Any]], byte_limit: int) -> List[Dict[str, Any]]:
    """
    Smart data sampling based on byte limit.
    Preserves data distribution characteristics.
    """
    return sample_datas_by_byte_limit(
        datas,
        byte_limit,
        min_sample_size=SMART_SAMPLE_MIN_SIZE
    )


def is_scatter_plot_spec(spec: Dict[str, Any]) -> bool:
    """
    Check if a visualization spec represents a scatter plot.
    
    Scatter plot characteristics:
    - geoms contains "point" or "circle"
    - defaultAggregated is False (no aggregation)
    """
    config = spec.get("config", {})
    geoms = config.get("geoms", [])
    
    is_point_geom = any(g in geoms for g in ["point", "circle", "tick"])
    is_not_aggregated = not config.get("defaultAggregated", False)
    
    return is_point_geom and is_not_aggregated


def apply_scatter_plot_sampling(
    spec: Dict[str, Any],
    datas: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Apply sampling specifically for scatter plots.
    
    Strategy:
    1. Small datasets (< SCATTER_PLOT_LARGE_DATA_THRESHOLD): no sampling
    2. Large datasets: sample to SCATTER_PLOT_SAMPLE_LIMIT points
    
    NOTE: This function now uses the unified SamplingStage internally.
    """
    if not is_scatter_plot_spec(spec):
        return datas
    
    from pygwalker.services.data_pipeline import SamplingStage, PipelineContext
    
    sampling_stage = SamplingStage()
    context = PipelineContext(
        source_type="client",
        sampling_strategy="scatter",
        preserve_boundaries=True
    )
    
    return sampling_stage.execute(datas, context)


def render_iframe_messages_html(gid: str) -> str:
    return jinja_env.get_template("jupyter_iframe_message.html").render(gid=gid)


def render_gwalker_iframe(
    gid: int,
    html: str,
    width: Optional[str] = None,
    height: Optional[str] = None,
    appearance: IAppearance = "media",
) -> str:
    if height is None:
        height = "960px"
    if width is None:
        width = "100%"

    return jinja_env.get_template("pygwalker_iframe.html").render(
        gid=gid,
        srcdoc=m_html.escape(html),
        height=height,
        width=width,
        appearance=appearance,
        component_url=GlobalVarManager.component_url
    )


def render_gwalker_html(gid: int, props: Dict[str, Any]) -> str:
    container_id = f"gwalker-div-{gid}"
    template = jinja_env.get_template("pygwalker_main_page.html")
    html = template.render(
        gwalker={
            'id': container_id,
            'gw_script': GWALKER_SCRIPT_BASE64,
            "component_script": "PyGWalkerApp.GWalker(props, gw_id);",
            "props": compress_data(json.dumps(props, cls=DataFrameEncoder)),
        },
        component_url=GlobalVarManager.component_url
    )
    return html
