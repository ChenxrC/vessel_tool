#!/usr/bin/env python3
"""
Vessel Tool 命令行接口

提供简单的命令行操作接口
"""

import argparse
import json
import sys
import os
from vessel_tool import VesselProcessor


def main():
    """主命令行函数"""
    parser = argparse.ArgumentParser(
        description="肝脏血管三维重建与可视化工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s -d /path/to/dicom -s /path/to/segmentation.nrrd -o /path/to/output
  %(prog)s -c config.json
  %(prog)s --batch batch_config.json
        """
    )
    
    # 基本参数
    parser.add_argument('-d', '--dicom', type=str, 
                       help='DICOM文件夹路径')
    parser.add_argument('-s', '--segmentation', type=str,
                       help='分割结果文件路径')
    parser.add_argument('-o', '--output', type=str,
                       help='输出文件夹路径')
    parser.add_argument('-b', '--hilum-box', type=str,
                       help='肝门边界框文件路径（可选）')
    
    # 配置文件参数
    parser.add_argument('-c', '--config', type=str,
                       help='配置文件路径（JSON格式）')
    parser.add_argument('--batch', type=str,
                       help='批量处理配置文件路径（JSON格式）')
    
    # 处理参数
    parser.add_argument('--temp-folder', type=str, default='./tmp',
                       help='临时文件夹路径（默认: ./tmp）')
    parser.add_argument('--max-radius', type=float, default=10.0,
                       help='血管最大半径（默认: 10.0）')
    parser.add_argument('--min-radius', type=float, default=2.0,
                       help='血管最小半径（默认: 2.0）')
    
    # 输出参数
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='详细输出模式')
    parser.add_argument('--quiet', action='store_true',
                       help='静默模式')
    parser.add_argument('--stats', action='store_true',
                       help='输出血管树统计信息')
    
    args = parser.parse_args()
    
    # 设置输出级别
    if args.quiet:
        import logging
        logging.basicConfig(level=logging.ERROR)
    elif args.verbose:
        import logging
        logging.basicConfig(level=logging.DEBUG)
    
    try:
        processor = VesselProcessor(temp_folder=args.temp_folder)
        
        if args.batch:
            # 批量处理模式
            result = process_batch(processor, args.batch, args)
        elif args.config:
            # 配置文件模式
            result = process_with_config(processor, args.config, args)
        elif args.dicom and args.segmentation and args.output:
            # 直接参数模式
            result = process_direct(processor, args)
        else:
            print("错误：请提供有效的输入参数", file=sys.stderr)
            parser.print_help()
            sys.exit(1)
        
        # 输出结果
        if result['success']:
            if not args.quiet:
                print(f"✅ 处理成功！")
                print(f"📁 输出文件: {result.get('output_file', 'N/A')}")
                print(f"⏱️ 处理时间: {result['processing_time']:.2f} 秒")
                
                if args.stats and 'tree_info' in result:
                    print(f"🌳 血管树统计:")
                    for key, value in result['tree_info'].items():
                        print(f"   {key}: {value}")
            sys.exit(0)
        else:
            print(f"❌ 处理失败: {result['error']}", file=sys.stderr)
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ 程序执行出错: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def process_direct(processor, args):
    """直接参数处理模式"""
    config = {
        'dcm_path': args.dicom,
        'seg_path': args.segmentation,
        'output_folder': args.output,
        'hilum_box_path': args.hilum_box
    }
    
    if not args.quiet:
        print("开始处理血管重建...")
        print(f"DICOM路径: {config['dcm_path']}")
        print(f"分割结果: {config['seg_path']}")
        print(f"输出路径: {config['output_folder']}")
    
    return processor.process_complete_pipeline(config)


def process_with_config(processor, config_file, args):
    """配置文件处理模式"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        if not args.quiet:
            print(f"使用配置文件: {config_file}")
            print("开始处理血管重建...")
        
        return processor.process_complete_pipeline(config)
        
    except FileNotFoundError:
        raise ValueError(f"配置文件不存在: {config_file}")
    except json.JSONDecodeError as e:
        raise ValueError(f"配置文件格式错误: {e}")


def process_batch(processor, batch_file, args):
    """批量处理模式"""
    try:
        with open(batch_file, 'r', encoding='utf-8') as f:
            batch_configs = json.load(f)
        
        if not isinstance(batch_configs, list):
            raise ValueError("批量配置文件应包含配置列表")
        
        results = []
        success_count = 0
        
        for i, config in enumerate(batch_configs, 1):
            if not args.quiet:
                print(f"\n处理第 {i}/{len(batch_configs)} 个任务...")
            
            result = processor.process_complete_pipeline(config)
            results.append(result)
            
            if result['success']:
                success_count += 1
                if not args.quiet:
                    print(f"✅ 任务 {i} 处理成功")
            else:
                if not args.quiet:
                    print(f"❌ 任务 {i} 处理失败: {result['error']}")
        
        # 汇总结果
        total_time = sum(r['processing_time'] for r in results)
        
        summary_result = {
            'success': True,
            'batch_summary': {
                'total_tasks': len(batch_configs),
                'success_count': success_count,
                'failure_count': len(batch_configs) - success_count,
                'total_time': total_time,
                'average_time': total_time / len(batch_configs)
            },
            'processing_time': total_time,
            'individual_results': results
        }
        
        if not args.quiet:
            print(f"\n📊 批量处理汇总:")
            print(f"成功任务: {success_count}/{len(batch_configs)}")
            print(f"总耗时: {total_time:.2f} 秒")
            print(f"平均耗时: {total_time/len(batch_configs):.2f} 秒/任务")
        
        return summary_result
        
    except FileNotFoundError:
        raise ValueError(f"批量配置文件不存在: {batch_file}")
    except json.JSONDecodeError as e:
        raise ValueError(f"批量配置文件格式错误: {e}")


def create_sample_config():
    """创建示例配置文件"""
    sample_config = {
        "dcm_path": "/path/to/dicom/folder",
        "seg_path": "/path/to/segmentation/result.nrrd",
        "hilum_box_path": null,
        "output_folder": "/path/to/output"
    }
    
    sample_batch = [
        {
            "dcm_path": "/path/to/patient1/dicom",
            "seg_path": "/path/to/patient1/segmentation.nrrd",
            "output_folder": "/path/to/output/patient1"
        },
        {
            "dcm_path": "/path/to/patient2/dicom",
            "seg_path": "/path/to/patient2/segmentation.nrrd",
            "output_folder": "/path/to/output/patient2"
        }
    ]
    
    # 保存示例配置
    with open('sample_config.json', 'w', encoding='utf-8') as f:
        json.dump(sample_config, f, indent=2, ensure_ascii=False)
    
    with open('sample_batch.json', 'w', encoding='utf-8') as f:
        json.dump(sample_batch, f, indent=2, ensure_ascii=False)
    
    print("✅ 已创建示例配置文件:")
    print("   - sample_config.json (单个任务配置)")
    print("   - sample_batch.json (批量任务配置)")


if __name__ == '__main__':
    # 如果用户请求创建示例配置
    if len(sys.argv) > 1 and sys.argv[1] == '--create-sample':
        create_sample_config()
    else:
        main() 