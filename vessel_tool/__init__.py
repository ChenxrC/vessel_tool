"""
Vessel Tool - 肝脏血管三维重建与可视化工具包

这个工具包提供了完整的肝脏血管三维重建流程，包括：
- DICOM图像读取和处理
- 血管分割和骨架提取
- 血管树构建和分析
- 三维可视化和STL模型生成
"""

__version__ = "1.0.0"
__author__ = "Vessel Tool Team"

from .base import VesselBase
from .tree import VesselTree
from .visualization import VesselVisualizer
from .main import VesselProcessor

__all__ = [
    'VesselBase',
    'VesselTree', 
    'VesselVisualizer',
    'VesselProcessor'
] 