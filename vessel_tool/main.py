"""
主处理类
整合所有功能模块，提供完整的血管处理流程
"""

import os
import time
import numpy as np
import scipy.ndimage
from typing import Union
from .base import VesselBase
from .tree import VesselTree
from .visualization import VesselVisualizer


class VesselProcessor:
    """血管处理主类，提供完整的肝脏血管三维重建流程"""
    
    def __init__(self, temp_folder='./tmp'):
        """
        初始化血管处理器
        
        参数：
        temp_folder: 临时文件夹路径
        """
        self.temp_folder = temp_folder
        self.base = VesselBase()
        self.tree = VesselTree() 
        self.visualizer = VesselVisualizer()
        
        # 确保临时文件夹存在
        os.makedirs(temp_folder, exist_ok=True)
    
    def read_file(self, filename):
        """
        读取各种格式的医学图像文件
        
        参数：
        filename: 文件路径
        
        返回：
        图像数据数组
        """
        try:
            if filename.endswith('.nrrd'):
                import nrrd
                img_data, header = nrrd.read(filename)
                return img_data
            elif filename.endswith('.nii.gz') or filename.endswith('.nii'):
                import nibabel as nib
                img_data = nib.load(filename)
                return img_data.get_fdata()
            elif filename.endswith('.npy'):
                return np.load(filename)
            else:
                raise ValueError(f"不支持的文件格式: {filename}")
        except Exception as e:
            print(f"读取文件失败: {e}")
            raise
    
    def read_data(self, dcm_folder, seg_result_path, hilum_box_file=None):
        """
        读取DICOM数据和分割结果
        
        参数：
        dcm_folder: DICOM文件夹路径
        seg_result_path: 分割结果文件路径
        hilum_box_file: 肝门区域文件路径
        
        返回：
        tuple: (原始图像, 缩放因子, 分割结果, 肝门边界框, 像素间距, 原点, 方向矩阵)
        """
        print("正在读取DICOM数据...")
        volume_image, spacing, origin, direction = self.base.load_dicom_series_as_3d_array(dcm_folder)
        
        print("正在读取分割结果...")
        zoom_factors = (512/volume_image.shape[0], 512/volume_image.shape[1], 1)
        res_data = self.read_file(seg_result_path)
        
        if hilum_box_file is not None:
            hilum_box = self.read_file(hilum_box_file)
            hilum_box = hilum_box[:3, :][::-1, :].astype(np.int32)
        else:
            hilum_box = np.array([[0, 512], [0, 512], [0, 512]])
        
        res_data = scipy.ndimage.zoom(res_data, zoom_factors, order=0)
        
        return volume_image, zoom_factors, res_data, hilum_box, spacing, origin, direction
    
    def get_hilum_structures(self, res_data, hilum_box):
        """
        获取肝门区域结构
        
        参数：
        res_data: 分割数据
        hilum_box: 肝门边界框
        
        返回：
        平滑的肝门结构STL
        """
        print("正在处理肝门区域...")
        big_artery = np.where(res_data == 1, 1, 0)
        middle_region = 20
        offset = 15
        
        print(f'肝门边界框: {hilum_box}')
        big_artery_stl = self._get_smoothed_biggest_stl(
            big_artery, hilum_box, middle_region, offset
        )
        
        return big_artery_stl
    
    def _get_smoothed_biggest_stl(self, data, hilum_box, middle_region, offset):
        """
        获取平滑的最大连通组件STL
        
        参数：
        data: 输入数据
        hilum_box: 肝门边界框
        middle_region: 中间区域大小
        offset: 偏移量
        
        返回：
        平滑的STL网格
        """
        # 限制处理区域
        data[:max(1, hilum_box[0][0]-middle_region), :, :] = 0
        data[min(hilum_box[0][1]+middle_region, 511):, :, :] = 0
        data[:, :max(hilum_box[1][0]-middle_region, 1), :] = 0
        data[:, min(hilum_box[1][1]+middle_region, 511):, :] = 0
        data[:, :, :max(hilum_box[2][0]-middle_region-offset, 1)] = 0
        data[:, :, min(511, hilum_box[2][1]+middle_region-offset):] = 0
        
        # 获取最大连通组件
        data, box = self.base.retain_largest_connected_component(data)
        
        # 转换为VTK格式并提取表面
        vtk_image = self.visualizer.numpy_to_vtk_image(data)
        polydata = self.visualizer.extract_surface(vtk_image)
        smoothed = self.visualizer.smooth_mesh(polydata)
        
        return smoothed
    
    def get_all_lines_and_tree(self, data, region_box, center_point, threshold=0.01):
        """
        获取所有血管线条和树结构
        
        参数：
        data: 分割数据
        region_box: 区域边界框
        center_point: 中心点
        threshold: 阈值
        
        返回：
        主血管树
        """
        print("正在构建血管树结构...")
        
        # 获取连通组件
        bigger_regions, smaller_regions = self.base.retain_connected_component_list(data, 1)
        
        if not bigger_regions:
            raise ValueError("未找到足够大的血管连通组件")
        
        # 构建主血管树
        main_tree = self.tree.get_tree_from_region(data, center_point, bigger_regions[0])
        
        # 清空并重新分配深度信息
        self.tree.empty_depth_info(main_tree)
        self.tree.assign_depth(main_tree)
        
        # 创建优化的树结构
        main_tree = self.tree.create_new_tree_from_old(main_tree)
        
        return main_tree
    
    def process_complete_pipeline(self, config):
        """
        完整的血管处理流水线
        
        参数：
        config: 配置字典，包含以下键：
            - dcm_path: DICOM文件夹路径
            - seg_path: 分割结果路径
            - hilum_box_path: 肝门边界框路径（可选）
            - output_folder: 输出文件夹路径
        
        返回：
        处理结果信息
        """
        start_time = time.time()
        
        try:
            # 1. 读取数据
            dcm_folder = config['dcm_path']
            seg_result_path = config['seg_path']
            hilum_box_path = config.get('hilum_box_path')
            output_folder = config['output_folder']
            
            # 确保输出文件夹存在
            os.makedirs(output_folder, exist_ok=True)
            
            # 读取数据
            (volume_image, zoom_factors, res_data, hilum_box, 
             spacing, origin, direction) = self.read_data(
                dcm_folder, seg_result_path, hilum_box_path
            )
            
            # 2. 构建血管树
            main_tree = self.get_all_lines_and_tree(
                res_data, hilum_box, [256, 256, 0], threshold=0.01
            )
            
            # 3. 获取肝门结构
            big_artery_stl = self.get_hilum_structures(res_data, hilum_box)
            
            # 4. 渲染血管树
            print("正在渲染血管树...")
            mesh_artery = self.visualizer.render_vessel_tree(
                main_tree,
                layer=0,
                last_layer_max_radius=10,
                last_layer_min_radius=2,
                last_layers_line=None,
                previous=None,
                k=1,
                smoothed_big_component=big_artery_stl
            )
            
            # 5. 保存结果
            tmp_path = os.path.join(self.temp_folder, 'artery_tmp.stl')
            output_path = os.path.join(output_folder, '动脉.stl')
            
            print("正在保存STL文件...")
            self.visualizer.process_and_save_mesh(
                mesh_artery, tmp_path, output_path, 
                spacing, origin, direction, zoom_factors
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            result = {
                'success': True,
                'processing_time': processing_time,
                'output_file': output_path,
                'tree_info': {
                    'total_branches': len(main_tree.get('subtree', [])),
                    'max_depth': self._calculate_tree_depth(main_tree)
                }
            }
            
            print(f"处理完成！耗时: {processing_time:.2f} 秒")
            print(f"输出文件: {output_path}")
            
            return result
            
        except Exception as e:
            print(f"处理过程中出现错误: {e}")
            return {
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time
            }
    
    def _calculate_tree_depth(self, tree):
        """
        计算树的深度
        
        参数：
        tree: 血管树结构
        
        返回：
        树的最大深度
        """
        if not tree.get('subtree'):
            return 1
        
        max_depth = 0
        for subtree in tree['subtree']:
            depth = self._calculate_tree_depth(subtree)
            max_depth = max(max_depth, depth)
        
        return max_depth + 1
    
    def visualize_tree_statistics(self, tree):
        """
        可视化血管树统计信息
        
        参数：
        tree: 血管树结构
        
        返回：
        统计信息字典
        """
        stats = {
            'total_points': 0,
            'total_branches': 0,
            'max_depth': 0,
            'average_branch_length': 0
        }
        
        def count_tree_stats(node, depth=0):
            stats['total_points'] += len(node.get('line', []))
            stats['total_branches'] += 1
            stats['max_depth'] = max(stats['max_depth'], depth)
            
            for subtree in node.get('subtree', []):
                count_tree_stats(subtree, depth + 1)
        
        count_tree_stats(tree)
        
        if stats['total_branches'] > 0:
            stats['average_branch_length'] = stats['total_points'] / stats['total_branches']
        
        return stats 