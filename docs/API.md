# Vessel Tool API 文档

## 概述

Vessel Tool 提供了完整的肝脏血管三维重建API，包含四个主要模块：

- **VesselBase**: 基础工具类
- **VesselTree**: 血管树处理类
- **VesselVisualizer**: 可视化类
- **VesselProcessor**: 主处理类

## VesselBase - 基础工具类

### 初始化
```python
from vessel_tool import VesselBase
base = VesselBase()
```

### 主要方法

#### `load_dicom_series_as_3d_array(folder_path)`
读取DICOM序列并转换为三维数组

**参数:**
- `folder_path` (str): DICOM文件夹路径

**返回:**
- `tuple`: (3D图像数组, 像素间距, 原点, 方向矩阵)

**示例:**
```python
volume, spacing, origin, direction = base.load_dicom_series_as_3d_array('./dicom_folder')
```

#### `retain_largest_connected_component(data)`
保留最大连通组件

**参数:**
- `data` (numpy.ndarray): 二值图像数组

**返回:**
- `tuple`: (处理后的数组, 边界框)

#### `ww_wc(img, k='lungNoduleClass')`
窗宽窗位调整

**参数:**
- `img` (numpy.ndarray): 输入图像
- `k` (str): 预设类型

**返回:**
- `numpy.ndarray`: 调整后的图像

#### `fit_curve_and_compute_tangents(points)`
拟合曲线并计算切线方向

**参数:**
- `points` (list): 输入点集

**返回:**
- `numpy.ndarray`: 切线向量数组

## VesselTree - 血管树处理类

### 初始化
```python
from vessel_tool import VesselTree
tree = VesselTree()
```

### 主要方法

#### `label_vessel_grades(vessel_data, start_point)`
对血管进行分级标记

**参数:**
- `vessel_data` (numpy.ndarray): 血管二值数据
- `start_point` (tuple): 起始点坐标

**返回:**
- `tuple`: (分级数组, 线段字典)

#### `get_tree_from_region(data, center_middle, skeleton)`
从区域数据构建血管树

**参数:**
- `data` (numpy.ndarray): 图像数据
- `center_middle` (list): 中心点
- `skeleton` (object): 骨架点集

**返回:**
- `dict`: 构建的血管树

#### `assign_depth(blood_tree)`
分配树的深度信息

**参数:**
- `blood_tree` (dict): 血管树结构

**返回:**
- `tuple`: (最大深度, 最大长度)

#### `create_new_tree_from_old(blood_tree)`
从旧树结构创建新的优化树结构

**参数:**
- `blood_tree` (dict): 原始血管树结构

**返回:**
- `dict`: 优化后的新树结构

## VesselVisualizer - 可视化类

### 初始化
```python
from vessel_tool import VesselVisualizer
visualizer = VesselVisualizer()
```

### 主要方法

#### `extract_surface(image)`
使用Marching Cubes算法提取表面

**参数:**
- `image` (vtk.vtkImageData): vtkImageData对象

**返回:**
- `vtk.vtkPolyData`: 提取的表面网格

#### `smooth_mesh(polydata, iterations=15, relaxation_factor=0.1)`
网格平滑处理

**参数:**
- `polydata` (vtk.vtkPolyData): 输入的网格数据
- `iterations` (int): 平滑迭代次数
- `relaxation_factor` (float): 松弛因子

**返回:**
- `vtk.vtkPolyData`: 平滑后的网格

#### `create_tube(points, max_radius=0.1, min_radius=0.1, k=0.6)`
创建管状结构

**参数:**
- `points` (list): 中心线点集
- `max_radius` (float): 最大半径
- `min_radius` (float): 最小半径
- `k` (float): 半径变化系数

**返回:**
- `vtk.vtkPolyData`: 管状网格

#### `render_vessel_tree(blood_tree, layer, **kwargs)`
渲染血管树

**参数:**
- `blood_tree` (dict): 血管树结构
- `layer` (int): 当前层级
- `**kwargs`: 其他参数

**返回:**
- `vtk.vtkPolyData`: 渲染后的网格

#### `save_as_stl(polydata, filename)`
保存为STL文件

**参数:**
- `polydata` (vtk.vtkPolyData): 网格数据
- `filename` (str): 输出文件名

## VesselProcessor - 主处理类

### 初始化
```python
from vessel_tool import VesselProcessor
processor = VesselProcessor(temp_folder='./tmp')
```

### 主要方法

#### `process_complete_pipeline(config)`
完整的血管处理流水线

**参数:**
- `config` (dict): 配置字典，包含以下键：
  - `dcm_path`: DICOM文件夹路径
  - `seg_path`: 分割结果路径
  - `hilum_box_path`: 肝门边界框路径（可选）
  - `output_folder`: 输出文件夹路径

**返回:**
- `dict`: 处理结果信息

**示例:**
```python
config = {
    'dcm_path': './data/dicom',
    'seg_path': './data/segmentation.nrrd',
    'output_folder': './output'
}
result = processor.process_complete_pipeline(config)
```

#### `read_data(dcm_folder, seg_result_path, hilum_box_file=None)`
读取DICOM数据和分割结果

**参数:**
- `dcm_folder` (str): DICOM文件夹路径
- `seg_result_path` (str): 分割结果文件路径
- `hilum_box_file` (str, optional): 肝门区域文件路径

**返回:**
- `tuple`: (原始图像, 缩放因子, 分割结果, 肝门边界框, 像素间距, 原点, 方向矩阵)

#### `get_all_lines_and_tree(data, region_box, center_point, threshold=0.01)`
获取所有血管线条和树结构

**参数:**
- `data` (numpy.ndarray): 分割数据
- `region_box` (numpy.ndarray): 区域边界框
- `center_point` (list): 中心点
- `threshold` (float): 阈值

**返回:**
- `dict`: 主血管树

#### `visualize_tree_statistics(tree)`
可视化血管树统计信息

**参数:**
- `tree` (dict): 血管树结构

**返回:**
- `dict`: 统计信息字典

## 数据结构

### 血管树结构
```python
blood_tree = {
    "line": [((x1, y1, z1), (parent_x, parent_y, parent_z)), ...],  # 血管线条点集
    "subtree": [sub_tree1, sub_tree2, ...],                        # 子树列表
    "deep": [depth1, depth2, ...],                                 # 深度信息
    "subLength": [length1, length2, ...],                          # 子树长度
    "dividePointIndex": [index1, index2, ...],                     # 分岔点索引
    "layer": int                                                    # 层级
}
```

### 处理结果结构
```python
result = {
    'success': bool,                    # 处理是否成功
    'processing_time': float,           # 处理时间（秒）
    'output_file': str,                 # 输出文件路径
    'error': str,                       # 错误信息（失败时）
    'tree_info': {                      # 血管树信息
        'total_branches': int,          # 分支总数
        'max_depth': int               # 最大深度
    }
}
```

## 异常处理

### 常见异常

#### `ValueError`
- 文件格式不支持
- 参数值无效
- 数据结构不匹配

#### `FileNotFoundError`
- 输入文件不存在
- 输出目录创建失败

#### `RuntimeError`
- VTK处理错误
- 内存不足

### 异常处理示例
```python
try:
    result = processor.process_complete_pipeline(config)
    if result['success']:
        print(f"处理成功: {result['output_file']}")
    else:
        print(f"处理失败: {result['error']}")
except ValueError as e:
    print(f"参数错误: {e}")
except FileNotFoundError as e:
    print(f"文件不存在: {e}")
except Exception as e:
    print(f"未知错误: {e}")
```

## 性能优化建议

1. **内存管理**: 处理大型数据时，建议增加系统内存或使用数据分块处理
2. **并行处理**: 批量处理时可使用多进程提高效率
3. **临时文件**: 设置合适的临时文件夹，确保有足够的磁盘空间
4. **参数调优**: 根据数据特点调整半径参数和平滑参数

## 扩展开发

### 自定义处理器
```python
class CustomVesselProcessor(VesselProcessor):
    def custom_preprocessing(self, data):
        # 自定义预处理逻辑
        return processed_data
    
    def process_complete_pipeline(self, config):
        # 调用自定义预处理
        config['data'] = self.custom_preprocessing(config['data'])
        return super().process_complete_pipeline(config)
```

### 自定义可视化
```python
class CustomVisualizer(VesselVisualizer):
    def custom_render(self, tree):
        # 自定义渲染逻辑
        return custom_mesh
```

## 相关资源

- [VTK 文档](https://vtk.org/documentation/)
- [SimpleITK 指南](https://simpleitk.readthedocs.io/)
- [scikit-image 文档](https://scikit-image.org/docs/)
- [Open3D 教程](http://www.open3d.org/docs/) 