# Vessel Tool - 肝脏血管三维重建与可视化工具包

![Python](https://img.shields.io/badge/Python-3.7%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Medical](https://img.shields.io/badge/Medical-Imaging-red)

一个专业的肝脏血管三维重建与可视化工具包，支持从DICOM图像到STL三维模型的完整处理流程。

## ✨ 主要功能

- 🏥 **DICOM图像处理**: 支持完整的DICOM序列读取和预处理
- 🩸 **血管分割处理**: 智能血管区域提取和噪声去除
- 🌳 **血管树构建**: 自动构建血管分支树结构和拓扑关系
- 🔍 **骨架提取**: 基于形态学的血管中心线提取
- 🎨 **三维可视化**: 高质量的血管三维重建和可视化
- 📐 **STL模型生成**: 支持3D打印和医学建模的STL文件输出
- ⚡ **批量处理**: 支持多患者数据的批量自动化处理

## 🚀 快速开始

### 安装依赖

```bash
# 克隆项目
git clone https://github.com/yourusername/vessel-tool.git
cd vessel-tool

# 安装依赖包
pip install -e .

# 或者使用开发版本安装
pip install -e .[dev]
```

### 基本使用

```python
from vessel_tool import VesselProcessor

# 创建处理器实例
processor = VesselProcessor(temp_folder='./tmp')

# 配置处理参数
config = {
    'dcm_path': 'path/to/dicom/folder',              # DICOM文件夹路径
    'seg_path': 'path/to/segmentation/result.nrrd',  # 分割结果文件路径
    'hilum_box_path': None,                          # 肝门边界框文件（可选）
    'output_folder': './output'                      # 输出文件夹路径
}

# 执行完整处理流程
result = processor.process_complete_pipeline(config)

# 检查结果
if result['success']:
    print(f"✅ 处理成功！输出文件: {result['output_file']}")
    print(f"⏱️ 处理时间: {result['processing_time']:.2f} 秒")
else:
    print(f"❌ 处理失败: {result['error']}")
```

## 📁 项目结构

```
vessel_tool/
├── vessel_tool/           # 主要代码包
│   ├── __init__.py       # 包初始化文件
│   ├── base.py           # 基础工具类
│   ├── tree.py           # 血管树处理模块
│   ├── visualization.py  # 可视化模块
│   └── main.py           # 主处理类
├── examples/             # 使用示例
│   └── basic_usage.py    # 基本使用示例
├── tests/                # 测试文件
├── docs/                 # 文档
├── setup.py              # 安装配置
└── README.md             # 项目说明
```

## 🔧 核心模块

### VesselBase - 基础工具类
提供通用的图像处理功能：
- DICOM序列读取
- 图像预处理（窗宽窗位调整）
- 连通组件分析
- 曲线拟合和切线计算

### VesselTree - 血管树处理类  
负责血管树的构建和分析：
- 血管分级标记
- 树结构构建
- 分支路径查找
- 树统计信息计算

### VesselVisualizer - 可视化类
负责三维渲染和STL文件生成：
- VTK网格处理
- 表面提取和平滑
- 管状结构生成
- STL文件导出

### VesselProcessor - 主处理类
整合所有功能模块，提供完整流程：
- 数据读取和预处理
- 血管树构建
- 三维重建
- 结果保存和统计

## 📊 支持的文件格式

### 输入格式
- **DICOM**: `.dcm` 文件夹
- **NRRD**: `.nrrd` 文件
- **NIfTI**: `.nii`, `.nii.gz` 文件
- **NumPy**: `.npy` 文件

### 输出格式
- **STL**: `.stl` 三维模型文件
- **JSON**: 血管树结构数据

## 💡 使用示例

### 1. 基础处理流程

```python
from vessel_tool import VesselProcessor

# 创建处理器
processor = VesselProcessor()

# 一键处理
config = {
    'dcm_path': './data/patient1/dicom',
    'seg_path': './data/patient1/vessel_seg.nrrd',
    'output_folder': './output/patient1'
}

result = processor.process_complete_pipeline(config)
```

### 2. 分步骤处理

```python
from vessel_tool import VesselProcessor

processor = VesselProcessor()

# 1. 读取数据
volume, zoom_factors, seg_data, hilum_box, spacing, origin, direction = \
    processor.read_data(dcm_folder, seg_path)

# 2. 构建血管树
vessel_tree = processor.get_all_lines_and_tree(seg_data, hilum_box, [256, 256, 0])

# 3. 获取统计信息
stats = processor.visualize_tree_statistics(vessel_tree)
print(f"血管分支数: {stats['total_branches']}")
print(f"最大深度: {stats['max_depth']}")

# 4. 生成三维模型
stl_mesh = processor.visualizer.render_vessel_tree(vessel_tree, ...)
```

### 3. 批量处理

```python
from vessel_tool import VesselProcessor

processor = VesselProcessor()

# 批量配置
batch_configs = [
    {'dcm_path': './data/patient1/dicom', 'seg_path': './data/patient1/seg.nrrd', 'output_folder': './output/patient1'},
    {'dcm_path': './data/patient2/dicom', 'seg_path': './data/patient2/seg.nrrd', 'output_folder': './output/patient2'},
    # 更多患者...
]

# 批量处理
for config in batch_configs:
    result = processor.process_complete_pipeline(config)
    print(f"患者处理{'成功' if result['success'] else '失败'}")
```

## 🔍 技术细节

### 血管树构建算法
1. **骨架提取**: 使用形态学骨架化算法提取血管中心线
2. **分级标记**: 基于连通性分析对血管进行分级
3. **树结构构建**: 递归构建层次化的血管树结构
4. **路径优化**: 查找最长路径并优化分支结构

### 三维重建流程
1. **表面提取**: 使用Marching Cubes算法提取血管表面
2. **网格优化**: 网格简化、平滑和三角化处理
3. **管状建模**: 基于中心线生成可变半径的管状结构
4. **坐标转换**: 从体素坐标转换为物理坐标系

### 性能优化
- **多线程处理**: 支持并行处理大型数据集
- **内存优化**: 分块处理大体积数据
- **算法优化**: 优化的连通组件分析和路径查找算法

## 📈 性能指标

| 数据规模 | 处理时间 | 内存占用 | 输出质量 |
|---------|---------|----------|----------|
| 512³体素 | ~2分钟 | ~4GB | 高精度STL |
| 256³体素 | ~30秒 | ~1GB | 标准STL |
| 128³体素 | ~10秒 | ~256MB | 快速预览 |

## 🛠️ 开发指南

### 环境设置

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装开发依赖
pip install -e .[dev]

# 运行测试
pytest tests/

# 代码格式化
black vessel_tool/
flake8 vessel_tool/
```

### 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 📄 API 文档

详细的API文档请参考：[API Documentation](docs/api.md)

## 🤝 致谢

- **VTK**: 三维可视化和图形处理
- **SimpleITK**: 医学图像读取和处理
- **scikit-image**: 图像分析和形态学操作
- **Open3D**: 点云处理和可视化

## 📧 联系方式

- **项目主页**: https://github.com/yourusername/vessel-tool
- **问题反馈**: https://github.com/yourusername/vessel-tool/issues
- **邮件联系**: your.email@example.com

## 📜 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🔮 路线图

- [ ] 支持更多医学图像格式
- [ ] 增加深度学习分割接口
- [ ] 实现实时可视化功能
- [ ] 添加血管测量和分析工具
- [ ] 支持多模态图像融合
- [ ] 开发Web界面和云处理服务

---

⭐ 如果这个项目对您有帮助，请给我们一个 Star！