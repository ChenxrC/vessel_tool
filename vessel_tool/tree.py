"""
血管树处理模块
包含血管分级、树结构构建、分支分析等功能
"""

import numpy as np
import copy
from collections import deque
from .base import VesselBase


class VesselTree(VesselBase):
    """血管树处理类，负责血管树的构建和分析"""
    
    def __init__(self):
        super().__init__()
    
    def label_vessel_grades(self, vessel_data, start_point):
        """
        对血管进行分级标记，构建线段
        
        参数：
        vessel_data: 血管二值数据
        start_point: 起始点坐标
        
        返回：
        tuple: (分级数组, 线段字典)
        """
        directions = [(-1, 0, 0), (1, 0, 0), (0, -1, 0), (0, 1, 0), (0, 0, -1), 
                      (0, 0, 1), (-1, -1, 0), (-1, 1, 0), (1, -1, 0), (1, 1, 0),
                      (-1, 0, -1), (-1, 0, 1), (1, 0, -1), (1, 0, 1), (0, -1, -1),
                      (0, -1, 1), (0, 1, -1), (0, 1, 1), (-1, -1, -1), (-1, -1, 1),
                      (-1, 1, -1), (-1, 1, 1), (1, -1, -1), (1, 1, -1), (1, -1, 1), (1, 1, 1)]
        
        grades = np.zeros(vessel_data.shape)
        queue = deque([(start_point, 1, (-1, -1, -1))])  # (位置, 等级, 前一个点)
        grades[start_point[0], start_point[1], start_point[2]] = 1
        point_list_with_prior = {}
        
        while queue:
            (x, y, z), current_grade, (px, py, pz) = queue.popleft()
            connections = 0
            
            for dx, dy, dz in directions:
                nx, ny, nz = x + dx, y + dy, z + dz
                if (0 <= nx < vessel_data.shape[0] and 
                    0 <= ny < vessel_data.shape[1] and 
                    0 <= nz < vessel_data.shape[2]):
                    
                    if vessel_data[nx, ny, nz] == 1 and grades[nx, ny, nz] == 0:
                        connections += 1
                        new_grade = current_grade + 1 if connections > 1 else current_grade
                        
                        grades[nx, ny, nz] = new_grade
                        queue.append(((nx, ny, nz), new_grade, (x, y, z)))
                        
                        if new_grade not in point_list_with_prior:
                            point_list_with_prior[new_grade] = []
                        point_list_with_prior[new_grade].append(((nx, ny, nz), (x, y, z)))
        
        seg_dic = self._get_all_segments(point_list_with_prior)
        return grades, seg_dic
    
    def _get_all_segments(self, point_list_with_prior):
        """
        从前序点集构建线段集合
        
        参数：
        point_list_with_prior: 带前序关系的点集
        
        返回：
        线段字典
        """
        seg_dic = {}
        
        for k in point_list_with_prior:
            readed = [0] * len(point_list_with_prior[k])
            seg_num = 0
            seg_dic[k] = {}
            find_flag = 0
            
            while sum(readed) < len(point_list_with_prior[k]):
                if find_flag != 1:
                    seg_num += 1
                    for i, point_pair in enumerate(point_list_with_prior[k]):
                        if readed[i] == 1:
                            continue
                        seg_dic[k][seg_num] = deque([point_list_with_prior[k][i]])
                        readed[i] = 1
                        break
                
                find_flag = 0
                for i, point_pair in enumerate(point_list_with_prior[k]):
                    if readed[i] == 1:
                        continue
                    
                    if point_pair[0] == seg_dic[k][seg_num][-1][1]:
                        seg_dic[k][seg_num].append(point_pair)
                        find_flag = 1
                        readed[i] = 1
                        break
                    elif point_pair[1] == seg_dic[k][seg_num][0][0]:
                        seg_dic[k][seg_num].appendleft(point_pair)
                        find_flag = 1
                        readed[i] = 1
                        break
        
        return seg_dic
    
    def build_tree_structure(self, blood_tree, layer, seg_dic, find_dad):
        """
        递归构建树结构
        
        参数：
        blood_tree: 血管树结构
        layer: 当前层级
        seg_dic: 线段字典
        find_dad: 父节点查找标记
        """
        for i in seg_dic:
            for j in seg_dic[i]:
                for k, point in enumerate(blood_tree['line']):
                    try:
                        if (tuple(seg_dic[i][j][-1][1]) == tuple(point[0]) and 
                            find_dad[i][j] == 0):
                            
                            new_tree = {
                                "line": list(seg_dic[i][j]),
                                "subtree": [],
                                "deep": [],
                                "subLength": [],
                                "dividePointIndex": [],
                                "layer": layer,
                            }
                            
                            find_dad[i][j] = 1
                            blood_tree['subtree'].append(new_tree)
                            blood_tree['dividePointIndex'].append(k)
                            
                            self.build_tree_structure(new_tree, layer + 1, seg_dic, find_dad)
                    except Exception as e:
                        print(f"树构建错误: {e}")
    
    def assign_depth(self, blood_tree):
        """
        分配树的深度信息
        
        参数：
        blood_tree: 血管树结构
        
        返回：
        tuple: (最大深度, 最大长度)
        """
        max_deep = 0
        max_length = 0
        max_length_ind = 0
        
        for i, subt in enumerate(blood_tree['subtree']):
            sb_deep, sb_length = self.assign_depth(subt)
            index = blood_tree['dividePointIndex'][i]
            
            max_deep = max(sb_deep, max_deep)
            if sb_length > max_length:
                max_length = sb_length
                max_length_ind = index
            
            blood_tree['deep'].append(sb_deep)
            blood_tree['subLength'].append(sb_length)
        
        return max_deep + 1, max_length + len(list(blood_tree['line'])[max_length_ind:])
    
    def find_longest_line(self, blood_tree):
        """
        找到树中最长的路径
        
        参数：
        blood_tree: 血管树结构
        
        返回：
        最长路径的点集
        """
        if len(blood_tree['line']) > 0 and len(blood_tree['subtree']) > 0:
            try:
                index = np.argmax(blood_tree['subLength'])
                new_line = (self.find_longest_line(blood_tree['subtree'][index]) + 
                           copy.deepcopy(blood_tree['line'][blood_tree['dividePointIndex'][index]:]))
                return new_line
            except Exception as e:
                print(f'查找最长路径错误: {e}')
                raise
        else:
            return copy.deepcopy(blood_tree['line'])
    
    def find_small_branches(self, blood_tree):
        """
        找到所有小分支
        
        参数：
        blood_tree: 血管树结构
        
        返回：
        小分支列表
        """
        branches = []
        
        if len(blood_tree['subtree']) == 0:
            return branches
        
        max_length_ind = np.argmax(blood_tree['subLength'])
        
        if blood_tree["dividePointIndex"][max_length_ind] == 0:
            for i in range(len(blood_tree["dividePointIndex"])):
                if i != max_length_ind:
                    branches.append({
                        'branch': copy.deepcopy(blood_tree['subtree'][i]),
                        'dividePointIndex': (blood_tree['subLength'][max_length_ind] + 
                                           blood_tree["dividePointIndex"][i] - 
                                           blood_tree["dividePointIndex"][max_length_ind])
                    })
            
            return branches + self.find_small_branches(blood_tree['subtree'][max_length_ind])
        
        if blood_tree["dividePointIndex"][max_length_ind] >= 1:
            new_tree = {
                "line": copy.deepcopy(blood_tree['line'][:blood_tree["dividePointIndex"][max_length_ind]]),
                "subtree": [],
                "deep": [],
                "subLength": [],
                "dividePointIndex": [],
                "layer": 999,
            }
            
            for i in range(len(blood_tree["dividePointIndex"])):
                if blood_tree["dividePointIndex"][i] < blood_tree["dividePointIndex"][max_length_ind]:
                    new_tree['subtree'].append(copy.deepcopy(blood_tree['subtree'][i]))
                    new_tree['dividePointIndex'].append(blood_tree["dividePointIndex"][i])
                    new_tree['subLength'].append(blood_tree['subLength'][i])
                elif (blood_tree["dividePointIndex"][i] >= blood_tree["dividePointIndex"][max_length_ind] 
                      and i != max_length_ind):
                    branches.append({
                        'branch': copy.deepcopy(blood_tree['subtree'][i]),
                        'dividePointIndex': (blood_tree['subLength'][max_length_ind] + 
                                           blood_tree["dividePointIndex"][i] - 
                                           blood_tree["dividePointIndex"][max_length_ind])
                    })
            
            branches.append({
                'branch': new_tree,
                'dividePointIndex': blood_tree['subLength'][max_length_ind]
            })
            
            return branches + self.find_small_branches(blood_tree['subtree'][max_length_ind])
    
    def create_new_tree_from_old(self, blood_tree):
        """
        从旧树结构创建新的优化树结构
        
        参数：
        blood_tree: 原始血管树结构
        
        返回：
        优化后的新树结构
        """
        new_line = self.find_longest_line(blood_tree)
        new_tree = {
            "line": new_line,
            "subtree": [],
            "deep": [],
            "subLength": [],
            "dividePointIndex": [],
            "layer": 0,
        }
        
        branches = self.find_small_branches(blood_tree)
        for br in branches:
            new_tree['subtree'].append(self.create_new_tree_from_old(br['branch']))
            new_tree["dividePointIndex"].append(br['dividePointIndex'])
            if br['branch']['subLength']:
                new_tree["subLength"].append(max(br['branch']['subLength']))
        
        return new_tree
    
    def empty_depth_info(self, blood_tree):
        """
        清空深度信息
        
        参数：
        blood_tree: 血管树结构
        """
        blood_tree['subLength'] = []
        for subt in blood_tree['subtree']:
            self.empty_depth_info(subt)
    
    def get_tree_from_region(self, data, center_middle, skeleton):
        """
        从区域数据构建血管树
        
        参数：
        data: 图像数据
        center_middle: 中心点
        skeleton: 骨架点集
        
        返回：
        构建的血管树
        """
        try:
            sk_coords = skeleton.coords
        except:
            sk_coords = skeleton
        
        most_recent = np.argmin(np.sum((center_middle - sk_coords)**2, axis=1))
        most_recent_coord = sk_coords[most_recent]
        
        blood_tree = {
            "line": [(most_recent_coord, (0, 0, 0))],
            "subtree": [],
            "deep": [],
            "subLength": [],
            "dividePointIndex": [],
            "layer": 0,
        }
        
        skeleton_data = np.zeros(data.shape)
        skeleton_data[sk_coords[:, 0], sk_coords[:, 1], sk_coords[:, 2]] = 1
        
        grades, seg_dic = self.label_vessel_grades(skeleton_data, most_recent_coord)
        max_length = max([len(seg_dic[k]) for k in seg_dic.keys()])
        find_dad = np.array([[0 for j in range(max_length + 3)] 
                            for i in range(len(seg_dic.keys()) + 3)])
        
        self.build_tree_structure(blood_tree, 0, seg_dic, find_dad)
        self.assign_depth(blood_tree)
        new_tree = self.create_new_tree_from_old(blood_tree)
        
        return new_tree 