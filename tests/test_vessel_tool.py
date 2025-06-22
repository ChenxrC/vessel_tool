#!/usr/bin/env python3
"""
Vessel Tool 测试文件
"""

import unittest
import numpy as np
import tempfile
import os
from vessel_tool import VesselProcessor, VesselBase, VesselTree, VesselVisualizer


class TestVesselBase(unittest.TestCase):
    """测试基础工具类"""
    
    def setUp(self):
        self.base = VesselBase()
    
    def test_ww_wc(self):
        """测试窗宽窗位调整"""
        # 创建测试数据
        test_img = np.random.randint(-1000, 1000, (10, 10, 10))
        
        # 测试窗宽窗位调整
        result = self.base.ww_wc(test_img, 'lungNoduleClass')
        
        # 验证结果
        self.assertEqual(result.shape, test_img.shape)
        self.assertGreaterEqual(result.min(), 0)
        self.assertLessEqual(result.max(), 255)
    
    def test_cosine_similarity(self):
        """测试余弦相似度计算"""
        v1 = np.array([1, 0, 0])
        v2 = np.array([0, 1, 0])
        v3 = np.array([1, 0, 0])
        
        # 垂直向量的余弦相似度应该为0
        cos_sim_perpendicular = self.base.get_cosine_similarity(v1, v2)
        self.assertAlmostEqual(cos_sim_perpendicular, 0, places=5)
        
        # 相同向量的余弦相似度应该为1
        cos_sim_same = self.base.get_cosine_similarity(v1, v3)
        self.assertAlmostEqual(cos_sim_same, 1, places=5)
    
    def test_gaussian_filter_smooth(self):
        """测试高斯滤波平滑"""
        # 创建测试点集
        points = np.array([[0, 0, 0], [1, 1, 1], [2, 2, 2], [3, 3, 3]])
        
        # 应用高斯平滑
        smoothed = self.base.gaussian_filter_smooth(points, sigma=1.0)
        
        # 验证结果
        self.assertEqual(smoothed.shape, points.shape)
        # 平滑后的点应该与原始点有相似的趋势但更平滑
        self.assertTrue(np.allclose(smoothed.mean(axis=0), points.mean(axis=0), rtol=0.1))


class TestVesselTree(unittest.TestCase):
    """测试血管树处理类"""
    
    def setUp(self):
        self.tree = VesselTree()
    
    def test_label_vessel_grades(self):
        """测试血管分级标记"""
        # 创建简单的血管数据（直线）
        vessel_data = np.zeros((10, 10, 10))
        vessel_data[5, 5, :] = 1  # 创建一条直线血管
        
        start_point = (5, 5, 0)
        
        # 执行分级标记
        grades, seg_dic = self.tree.label_vessel_grades(vessel_data, start_point)
        
        # 验证结果
        self.assertEqual(grades.shape, vessel_data.shape)
        self.assertGreater(len(seg_dic), 0)
        self.assertGreater(grades.max(), 0)
    
    def test_tree_depth_calculation(self):
        """测试树深度计算"""
        # 创建测试树结构
        test_tree = {
            'line': [(0, 0, 0)],
            'subtree': [
                {
                    'line': [(1, 1, 1)],
                    'subtree': [
                        {
                            'line': [(2, 2, 2)],
                            'subtree': [],
                            'subLength': []
                        }
                    ],
                    'subLength': [1]
                }
            ],
            'subLength': [2]
        }
        
        max_deep, max_length = self.tree.assign_depth(test_tree)
        
        # 验证深度计算
        self.assertGreaterEqual(max_deep, 2)
        self.assertGreaterEqual(max_length, 1)


class TestVesselVisualizer(unittest.TestCase):
    """测试可视化类"""
    
    def setUp(self):
        self.visualizer = VesselVisualizer()
    
    def test_numpy_to_vtk_image(self):
        """测试NumPy到VTK图像转换"""
        # 创建测试数据
        test_data = np.random.randint(0, 2, (5, 5, 5)).astype(np.uint8)
        
        # 转换为VTK图像
        vtk_image = self.visualizer.numpy_to_vtk_image(test_data)
        
        # 验证结果
        self.assertEqual(vtk_image.GetDimensions(), test_data.shape)
        self.assertGreater(vtk_image.GetNumberOfPoints(), 0)
    
    def test_create_tube(self):
        """测试管状结构创建"""
        # 创建简单的中心线点集
        points = [[0, 0, 0], [1, 0, 0], [2, 0, 0], [3, 0, 0]]
        
        # 创建管状结构
        tube = self.visualizer.create_tube(points, max_radius=1.0, min_radius=0.5)
        
        # 验证结果
        self.assertGreater(tube.GetNumberOfPoints(), 0)
        self.assertGreater(tube.GetNumberOfCells(), 0)


class TestVesselProcessor(unittest.TestCase):
    """测试主处理类"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.processor = VesselProcessor(temp_folder=self.temp_dir)
    
    def tearDown(self):
        # 清理临时文件
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_read_file_numpy(self):
        """测试NumPy文件读取"""
        # 创建测试数据
        test_data = np.random.rand(10, 10, 10)
        test_file = os.path.join(self.temp_dir, 'test.npy')
        np.save(test_file, test_data)
        
        # 读取文件
        loaded_data = self.processor.read_file(test_file)
        
        # 验证结果
        np.testing.assert_array_equal(loaded_data, test_data)
    
    def test_tree_statistics(self):
        """测试血管树统计"""
        # 创建测试树结构
        test_tree = {
            'line': [((0, 0, 0), (0, 0, 0)), ((1, 1, 1), (0, 0, 0))],
            'subtree': [
                {
                    'line': [((2, 2, 2), (1, 1, 1))],
                    'subtree': []
                }
            ]
        }
        
        # 获取统计信息
        stats = self.processor.visualize_tree_statistics(test_tree)
        
        # 验证结果
        self.assertIn('total_points', stats)
        self.assertIn('total_branches', stats)
        self.assertIn('max_depth', stats)
        self.assertGreater(stats['total_branches'], 0)
        self.assertGreater(stats['max_depth'], 0)


if __name__ == '__main__':
    # 运行所有测试
    unittest.main(verbosity=2) 