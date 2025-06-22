"""
基础工具类模块
包含DICOM读取、图像处理、连通组件分析等基础功能
"""

import numpy as np
import SimpleITK as sitk
from scipy import ndimage
from skimage import measure, morphology
from scipy.interpolate import splprep, splev
from scipy.ndimage import gaussian_filter1d
import time
import traceback
from abc import ABC, abstractmethod


class VesselBase(ABC):
    """血管处理基础类，提供通用的图像处理功能"""
    
    def __init__(self):
        pass
    
    def load_dicom_series_as_3d_array(self, folder_path):
        """
        从文件夹中读取 DICOM 序列并转换为三维 NumPy 数组
        
        参数：
        folder_path: 包含 DICOM 文件的文件夹路径
        
        返回：
        tuple: (3D图像数组, 像素间距, 原点, 方向矩阵)
        """
        # 使用 ImageSeriesReader 读取 DICOM 序列
        reader = sitk.ImageSeriesReader()
        # 获取文件夹中所有 DICOM 文件的文件名
        dicom_series = reader.GetGDCMSeriesFileNames(folder_path)
        reader.SetFileNames(dicom_series)
        # 读取图像
        image = reader.Execute()
        # 将 SimpleITK 图像转换为 NumPy 数组
        img_array = sitk.GetArrayFromImage(image)
        
        spacing = np.array(image.GetSpacing())
        direction = np.array(image.GetDirection()).reshape(3, 3)
        origin = np.array(image.GetOrigin())
        
        return np.transpose(img_array, (2, 1, 0)), spacing, origin, direction
    
    def retain_largest_connected_component(self, data):
        """
        保留最大连通组件
        
        参数：
        data: 二值图像数组
        
        返回：
        tuple: (处理后的数组, 边界框)
        """
        st = time.time()
        labeled_array = measure.label(data, background=0)
        print(f'labeled_array time: {time.time() - st:.3f}s')
        
        st = time.time()
        regions = measure.regionprops(labeled_array)
        print(f'regions time: {time.time() - st:.3f}s')
        
        st = time.time()
        regions = sorted(regions, key=lambda x: x.area, reverse=True)
        print(f'sorted time: {time.time() - st:.3f}s')
        
        st = time.time()
        new_data = np.zeros_like(data)
        if len(regions) > 0:
            largest_component = regions[0]
            coords = largest_component.coords
            new_data[coords[:, 0], coords[:, 1], coords[:, 2]] = 1
            print(f'final time: {time.time() - st:.3f}s')
            return new_data, largest_component.bbox
        else:
            print("错误：未找到连通组件")
            return new_data, None
    
    def ww_wc(self, img, k='lungNoduleClass'):
        """
        窗宽窗位调整
        
        参数：
        img: 输入图像
        k: 预设类型
        
        返回：
        调整后的图像
        """
        ref_dict = {
            "tsetra": [-600, 5500], 
            "ADC": [1400, 1800], 
            "BVAL": [60, 140], 
            'lungNoduleClass': [-500, 1500]
        }
        
        wcenter = ref_dict[k][0]
        wwidth = ref_dict[k][1]
        minvalue = (2 * wcenter - wwidth) / 2.0 + 0.5
        maxvalue = (2 * wcenter + wwidth) / 2.0 + 0.5
        
        dfactor = 255.0 / (maxvalue - minvalue)
        
        zo = np.ones(img.shape) * minvalue
        Two55 = np.ones(img.shape) * maxvalue
        img = np.where(img < minvalue, zo, img)
        img = np.where(img > maxvalue, Two55, img)
        img = ((img - minvalue) * dfactor)
        
        return img
    
    def get_cosine_similarity(self, v1, v2):
        """
        计算两个向量的余弦相似度
        
        参数：
        v1, v2: 输入向量
        
        返回：
        余弦相似度值
        """
        V1 = v1 / np.linalg.norm(v1)
        V2 = v2 / np.linalg.norm(v2)
        return np.dot(V1, V2)
    
    def gaussian_filter_smooth(self, points, sigma=2.0):
        """
        高斯滤波平滑点集
        
        参数：
        points: 点集数组
        sigma: 高斯核标准差
        
        返回：
        平滑后的点集
        """
        smoothed_points = np.copy(points)
        for i in range(3):  # 假设点是三维的
            smoothed_points[:, i] = gaussian_filter1d(points[:, i], sigma)
        return smoothed_points
    
    def fit_curve_and_compute_tangents(self, points):
        """
        拟合曲线并计算切线方向
        
        参数：
        points: 输入点集
        
        返回：
        切线向量数组
        """
        points = np.array(points)
        if len(points) < 2:
            raise ValueError("点集至少需要包含两个点")
        
        # 如果点集只有两个点，直接计算线性切线方向
        if len(points) == 2:
            direction = points[1] - points[0]
            direction = direction / np.linalg.norm(direction)  # 归一化
            return [direction] * 2  # 两个点的切线方向相同
        
        # 对超过两个点的情况，使用B样条拟合
        if len(points) == 3:
            npoints = [
                points[0],
                (points[0] + points[1]) / 2, 
                points[1],
                (points[1] + points[2]) / 2, 
                points[2]
            ]
            points = np.array(npoints)
        
        try:
            tck, u = splprep(points[::max(1, len(points)//50)].T, s=10)
        except:
            raise ValueError("B样条拟合失败")
        
        # 求解切线方向 (求导)
        tangents = np.array(splev(u, tck, der=1))  # der=1 表示求一阶导数
        tangents = tangents.T  # 转置回 (n, 3) 形式
        # 归一化切线向量
        tangents = tangents / np.linalg.norm(tangents, axis=1)[:, np.newaxis]
        return tangents
    
    def mean_insert(self, points, num_insert=3):
        """
        在点之间插入均值点
        
        参数：
        points: 输入点集
        num_insert: 插入点数
        
        返回：
        插入点后的点集
        """
        newpoints = []
        for i, point in enumerate(points):
            if i + 1 < len(points):
                newpoints.append(point)
                newpoints.append(((np.array(point) + np.array(points[i+1])) / 2).tolist())
        newpoints.append(points[-1])
        newpoints.append((np.array(points[-1]) + 0.001).tolist())
        return newpoints
    
    def retain_connected_component_list(self, data, cls, pixel_threshold=50):
        """
        获取连通组件列表，按大小分类
        
        参数：
        data: 输入数据
        cls: 类别标签
        pixel_threshold: 像素阈值
        
        返回：
        tuple: (大连通组件列表, 小连通组件列表)
        """
        if cls == -1:
            now_data = np.where(data > 0, 1, 0)    
        else:
            now_data = np.where(data == cls, 1, 0)
        
        skeleton = morphology.skeletonize(now_data)
        labeled_array = measure.label(skeleton, background=0)
        regions = measure.regionprops(labeled_array)
        regions = sorted(regions, key=lambda x: x.area, reverse=True)
        
        bigger_regions = [rg for rg in regions if rg.area >= pixel_threshold]
        smaller_regions = [rg for rg in regions if rg.area < pixel_threshold]
        
        return bigger_regions, smaller_regions 