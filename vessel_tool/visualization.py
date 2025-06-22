"""
可视化模块
包含VTK相关的三维可视化和STL文件生成功能
"""

import numpy as np
import vtk
import copy
import time
from stl import mesh
from .base import VesselBase


class VesselVisualizer(VesselBase):
    """血管可视化类，负责三维渲染和STL文件生成"""
    
    def __init__(self):
        super().__init__()
    
    def numpy_to_vtk_image(self, data):
        """
        将NumPy数组转换为vtkImageData
        
        参数：
        data: 输入的NumPy数组
        
        返回：
        vtkImageData对象
        """
        image = vtk.vtkImageData()
        image.SetDimensions(data.shape)
        image.AllocateScalars(vtk.VTK_UNSIGNED_CHAR, 1)
        
        flat_data = np.transpose(data, (2, 1, 0)).ravel()
        for i in range(len(flat_data)):
            image.GetPointData().GetScalars().SetTuple1(i, flat_data[i])
        
        return image
    
    def extract_surface(self, image):
        """
        使用Marching Cubes算法提取表面
        
        参数：
        image: vtkImageData对象
        
        返回：
        提取的表面网格
        """
        extractor = vtk.vtkDiscreteMarchingCubes()
        extractor.SetInputData(image)
        extractor.GenerateValues(1, 1, 1)  # 提取值为1的表面
        extractor.Update()
        return extractor.GetOutput()
    
    def smooth_mesh(self, polydata, iterations=15, relaxation_factor=0.1):
        """
        网格平滑处理
        
        参数：
        polydata: 输入的网格数据
        iterations: 平滑迭代次数
        relaxation_factor: 松弛因子
        
        返回：
        平滑后的网格
        """
        smoother = vtk.vtkSmoothPolyDataFilter()
        smoother.SetInputData(polydata)
        smoother.SetNumberOfIterations(iterations)
        smoother.SetRelaxationFactor(relaxation_factor)
        smoother.FeatureEdgeSmoothingOff()
        smoother.BoundarySmoothingOn()
        smoother.Update()
        return smoother.GetOutput()
    
    def decimate_mesh(self, input_polydata, reduction_rate=0.95):
        """
        网格简化
        
        参数：
        input_polydata: 输入网格
        reduction_rate: 简化比例
        
        返回：
        简化后的网格
        """
        decimator = vtk.vtkDecimatePro()
        decimator.SetInputData(input_polydata)
        decimator.SetTargetReduction(reduction_rate)
        decimator.PreserveTopologyOn()
        decimator.Update()
        return decimator.GetOutput()
    
    def convert_to_triangles(self, mesh):
        """
        将网格转换为三角形网格
        
        参数：
        mesh: 输入网格
        
        返回：
        三角形网格
        """
        tri_filter = vtk.vtkTriangleFilter()
        tri_filter.SetInputData(mesh)
        tri_filter.PassLinesOff()
        tri_filter.PassVertsOff()
        tri_filter.Update()
        return tri_filter.GetOutput()
    
    def save_as_stl(self, polydata, filename):
        """
        保存为STL文件
        
        参数：
        polydata: 网格数据
        filename: 输出文件名
        """
        stl_writer = vtk.vtkSTLWriter()
        stl_writer.SetFileName(filename)
        stl_writer.SetInputData(polydata)
        stl_writer.Write()
    
    def create_tube(self, points, max_radius=0.1, min_radius=0.1, k=0.6):
        """
        创建管状结构
        
        参数：
        points: 中心线点集
        max_radius: 最大半径
        min_radius: 最小半径
        k: 半径变化系数
        
        返回：
        管状网格
        """
        # 创建点数据
        points_vtk = vtk.vtkPoints()
        for p in points:
            points_vtk.InsertNextPoint(p)
        
        # 创建线段
        lines = vtk.vtkCellArray()
        line = vtk.vtkPolyLine()
        line.GetPointIds().SetNumberOfIds(len(points))
        for i, _ in enumerate(points):
            line.GetPointIds().SetId(i, i)
        lines.InsertNextCell(line)
        
        # 创建PolyData
        poly_data = vtk.vtkPolyData()
        poly_data.SetPoints(points_vtk)
        poly_data.SetLines(lines)
        
        # 使用管道过滤器
        tube_filter = vtk.vtkTubeFilter()
        tube_filter.SetVaryRadiusToVaryRadiusByAbsoluteScalar()
        
        # 创建半径变化数组
        radii = vtk.vtkFloatArray()
        radii.SetNumberOfValues(poly_data.GetNumberOfPoints())
        for i in range(poly_data.GetNumberOfPoints()):
            radius = self._linear_interpolation(
                i, min_radius, max_radius, 
                poly_data.GetNumberOfPoints(), k
            )
            radii.SetValue(i, radius)
        
        poly_data.GetPointData().SetScalars(radii)
        
        tube_filter.SetInputData(poly_data)
        tube_filter.SetNumberOfSides(30)
        tube_filter.CappingOn()
        tube_filter.Update()
        
        return tube_filter.GetOutput()
    
    def _linear_interpolation(self, t, eta_min, eta_max, T_max, k=0.6):
        """
        线性插值计算半径
        
        参数：
        t: 当前位置
        eta_min: 最小值
        eta_max: 最大值
        T_max: 最大位置
        k: 插值系数
        
        返回：
        插值结果
        """
        return eta_min + (eta_max - eta_min) * (t / (T_max - 1)) * k
    
    def merge_meshes(self, mesh1, mesh2):
        """
        合并两个网格
        
        参数：
        mesh1, mesh2: 要合并的网格
        
        返回：
        合并后的网格
        """
        append_filter = vtk.vtkAppendPolyData()
        append_filter.AddInputData(mesh1)
        append_filter.AddInputData(mesh2)
        append_filter.Update()
        return append_filter.GetOutput()
    
    def create_hemisphere(self, radius, center, resolution=30):
        """
        创建半球
        
        参数：
        radius: 半径
        center: 中心点
        resolution: 分辨率
        
        返回：
        半球网格
        """
        sphere_source = vtk.vtkSphereSource()
        sphere_source.SetRadius(radius)
        sphere_source.SetCenter(center)
        sphere_source.SetThetaResolution(resolution)
        sphere_source.SetPhiResolution(resolution)
        sphere_source.SetStartPhi(-180)
        sphere_source.SetEndPhi(180)
        sphere_source.Update()
        return sphere_source.GetOutput()
    
    def visualize_mesh(self, poly_data):
        """
        可视化网格
        
        参数：
        poly_data: 要可视化的网格数据
        """
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(poly_data)
        
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        
        renderer = vtk.vtkRenderer()
        render_window = vtk.vtkRenderWindow()
        render_window.AddRenderer(renderer)
        
        render_window_interactor = vtk.vtkRenderWindowInteractor()
        render_window_interactor.SetRenderWindow(render_window)
        
        renderer.AddActor(actor)
        renderer.SetBackground(0.1, 0.2, 0.3)
        
        render_window.Render()
        render_window_interactor.Start()
    
    def render_vessel_tree(self, blood_tree, layer, main_mesh=None, 
                          last_layer_max_radius=5, last_layer_min_radius=3,
                          last_layers_line=None, previous=None, k=0.6, 
                          smoothed_big_component=None):
        """
        渲染血管树
        
        参数：
        blood_tree: 血管树结构
        layer: 当前层级
        main_mesh: 主要网格
        last_layer_max_radius: 上层最大半径
        last_layer_min_radius: 上层最小半径
        last_layers_line: 上层线条
        previous: 之前的网格
        k: 半径变化系数
        smoothed_big_component: 平滑的大组件
        
        返回：
        渲染后的网格
        """
        if len(blood_tree['line']) == 0:
            return
        
        # 提取点坐标
        points_line = [p[0] for p in blood_tree['line']]
        
        # 处理单点情况
        if len(points_line) == 1:
            if smoothed_big_component is not None:
                mesh = self.decimate_mesh(
                    self.convert_to_triangles(smoothed_big_component), 0.9
                )
            else:
                mesh = self.create_hemisphere(
                    last_layer_max_radius * k, points_line[0], 30
                )
            
            if previous is None:
                previous = mesh
            else:
                previous = self.merge_meshes(mesh, previous)
            
            # 递归处理子树
            for subt in blood_tree['subtree']:
                previous = self.render_vessel_tree(
                    subt, layer + 1, main_mesh=1,
                    last_layer_max_radius=last_layer_max_radius,
                    last_layer_min_radius=last_layer_min_radius,
                    last_layers_line=points_line, previous=previous, k=k
                )
        else:
            # 处理多点情况
            if len(blood_tree['subtree']) == 0:
                points_line = np.asarray(self.mean_insert(points_line, 2))
                points_line = self.gaussian_filter_smooth(points_line)
            else:
                points_line = np.asarray(self.mean_insert(points_line, 2))
                points_line = self.gaussian_filter_smooth(points_line)
            
            # 计算半径
            if last_layers_line is not None:
                last_layers_line = np.array(last_layers_line)
                last_point = np.array(points_line[-1])
                closest_point = np.argmin(
                    np.sum((last_layers_line - last_point)**2, axis=1)
                )
                max_radius = self._linear_interpolation(
                    closest_point, last_layer_min_radius, 
                    last_layer_max_radius, len(last_layers_line), k
                )
                min_radius = last_layer_min_radius
            else:
                max_radius = last_layer_max_radius
                min_radius = last_layer_min_radius
            
            # 创建管状网格
            mesh = self.convert_to_triangles(
                self.create_tube(points_line, max_radius=max_radius, 
                               min_radius=min_radius, k=k)
            )
            
            if previous is None:
                if smoothed_big_component is not None:
                    previous = self.convert_to_triangles(
                        self.merge_meshes(mesh, smoothed_big_component)
                    )
                else:
                    previous = mesh
            else:
                previous = self.merge_meshes(mesh, previous)
            
            # 递归处理子树
            for subt in blood_tree['subtree']:
                previous = self.render_vessel_tree(
                    subt, layer + 1, main_mesh=1,
                    last_layer_max_radius=max_radius,
                    last_layer_min_radius=min_radius,
                    last_layers_line=points_line, previous=previous, k=k
                )
        
        return previous
    
    def load_stl(self, stl_file):
        """
        加载STL文件
        
        参数：
        stl_file: STL文件路径
        
        返回：
        顶点数组
        """
        stl_mesh = mesh.Mesh.from_file(stl_file)
        return stl_mesh.vectors.reshape(-1, 3)
    
    def save_stl(self, stl_file, vertices, faces):
        """
        保存STL文件
        
        参数：
        stl_file: 输出文件路径
        vertices: 顶点数组
        faces: 面数组
        """
        new_mesh = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
        new_mesh.vectors = faces
        new_mesh.save(stl_file)
    
    def voxel_to_physical_coordinates(self, zoom_factors, voxel_coords, 
                                    spacing, origin, direction):
        """
        将体素坐标转换为物理坐标
        
        参数：
        zoom_factors: 缩放因子
        voxel_coords: 体素坐标
        spacing: 像素间距
        origin: 原点
        direction: 方向矩阵
        
        返回：
        物理坐标
        """
        spacing = np.array([
            spacing[0] / zoom_factors[0],
            spacing[1] / zoom_factors[1],
            spacing[2]
        ])
        
        physical_coords = (np.dot(direction, voxel_coords.T * spacing[:, None]) + 
                          origin[:, None])
        return physical_coords.T
    
    def process_and_save_mesh(self, mesh, tmp_path, target_path, spacing, 
                            origin, direction, zoom_factors):
        """
        处理并保存网格，包括简化、平滑和坐标转换
        
        参数：
        mesh: 输入网格
        tmp_path: 临时文件路径
        target_path: 目标文件路径
        spacing: 像素间距
        origin: 原点
        direction: 方向矩阵
        zoom_factors: 缩放因子
        """
        # 保存临时文件
        self.save_as_stl(mesh, tmp_path)
        
        # 简化和平滑
        simplified_mesh = self.decimate_mesh(
            self.smooth_mesh(mesh, 15, 0.5), 0.99
        )
        
        # 保存处理后的文件
        self.save_as_stl(simplified_mesh, target_path)
        
        # 坐标转换
        voxel_coords = self.load_stl(target_path)
        physical_coords = self.voxel_to_physical_coordinates(
            zoom_factors, voxel_coords, spacing, origin, direction
        )
        
        # 重新保存转换后的文件
        faces = physical_coords.reshape(-1, 3, 3)
        self.save_stl(target_path, physical_coords, faces) 