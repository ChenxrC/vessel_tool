#!/usr/bin/env python3
"""
Vessel Tool 基本使用示例

这个示例展示了如何使用 Vessel Tool 进行完整的肝脏血管三维重建流程
"""

import os
from vessel_tool import VesselProcessor


def main():
    """主函数：演示基本用法"""
    
    # 1. 创建血管处理器实例
    processor = VesselProcessor(temp_folder='./tmp')
    
    # 2. 配置输入和输出路径
    config = {
        'dcm_path': 'path/to/dicom/folder',              # DICOM文件夹路径
        'seg_path': 'path/to/segmentation/result.nrrd',  # 分割结果文件路径
        'hilum_box_path': None,                          # 肝门边界框文件（可选）
        'output_folder': './output'                      # 输出文件夹路径
    }
    
    # 3. 执行完整的处理流程
    print("开始血管重建处理...")
    result = processor.process_complete_pipeline(config)
    
    # 4. 检查结果
    if result['success']:
        print(f"✅ 处理成功！")
        print(f"📊 处理时间: {result['processing_time']:.2f} 秒")
        print(f"📁 输出文件: {result['output_file']}")
        print(f"🌳 血管树信息:")
        print(f"   - 分支数量: {result['tree_info']['total_branches']}")
        print(f"   - 最大深度: {result['tree_info']['max_depth']}")
    else:
        print(f"❌ 处理失败: {result['error']}")
        print(f"⏱️ 失败前耗时: {result['processing_time']:.2f} 秒")


def advanced_example():
    """高级使用示例：分步骤处理"""
    
    processor = VesselProcessor(temp_folder='./tmp')
    
    # 1. 读取数据
    volume_image, zoom_factors, res_data, hilum_box, spacing, origin, direction = \
        processor.read_data(
            dcm_folder='path/to/dicom/folder',
            seg_result_path='path/to/segmentation/result.nrrd',
            hilum_box_file=None
        )
    
    print(f"原始图像形状: {volume_image.shape}")
    print(f"分割结果形状: {res_data.shape}")
    
    # 2. 构建血管树
    main_tree = processor.get_all_lines_and_tree(
        res_data, hilum_box, [256, 256, 0]
    )
    
    # 3. 获取血管树统计信息
    stats = processor.visualize_tree_statistics(main_tree)
    print("血管树统计信息:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # 4. 获取肝门结构
    big_artery_stl = processor.get_hilum_structures(res_data, hilum_box)
    
    # 5. 渲染血管树
    mesh_artery = processor.visualizer.render_vessel_tree(
        main_tree,
        layer=0,
        last_layer_max_radius=10,
        last_layer_min_radius=2,
        smoothed_big_component=big_artery_stl
    )
    
    # 6. 保存结果
    output_path = './output/artery_advanced.stl'
    tmp_path = './tmp/artery_tmp.stl'
    
    processor.visualizer.process_and_save_mesh(
        mesh_artery, tmp_path, output_path,
        spacing, origin, direction, zoom_factors
    )
    
    print(f"高级处理完成，输出文件: {output_path}")


def batch_processing_example():
    """批量处理示例"""
    
    processor = VesselProcessor(temp_folder='./tmp')
    
    # 批量处理配置列表
    batch_configs = [
        {
            'dcm_path': 'data/patient1/dicom',
            'seg_path': 'data/patient1/segmentation.nrrd',
            'output_folder': 'output/patient1'
        },
        {
            'dcm_path': 'data/patient2/dicom', 
            'seg_path': 'data/patient2/segmentation.nrrd',
            'output_folder': 'output/patient2'
        },
        # 添加更多患者数据...
    ]
    
    results = []
    for i, config in enumerate(batch_configs, 1):
        print(f"\n处理第 {i}/{len(batch_configs)} 个患者...")
        result = processor.process_complete_pipeline(config)
        results.append(result)
        
        if result['success']:
            print(f"✅ 患者 {i} 处理成功")
        else:
            print(f"❌ 患者 {i} 处理失败: {result['error']}")
    
    # 统计批量处理结果
    success_count = sum(1 for r in results if r['success'])
    total_time = sum(r['processing_time'] for r in results)
    
    print(f"\n📊 批量处理统计:")
    print(f"成功: {success_count}/{len(batch_configs)}")
    print(f"总耗时: {total_time:.2f} 秒")
    print(f"平均耗时: {total_time/len(batch_configs):.2f} 秒/患者")


if __name__ == '__main__':
    # 运行基本示例
    print("=== 基本使用示例 ===")
    main()
    
    print("\n=== 高级使用示例 ===")
    advanced_example()
    
    print("\n=== 批量处理示例 ===")
    batch_processing_example() 