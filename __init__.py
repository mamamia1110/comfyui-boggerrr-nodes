import importlib.util
import os
import sys
import json

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

python = sys.executable

def get_ext_dir(subpath=None, mkdir=False):
    dir = os.path.dirname(__file__)
    if subpath is not None:
        dir = os.path.join(dir, subpath)

    dir = os.path.abspath(dir)

    if mkdir and not os.path.exists(dir):
        os.makedirs(dir)
    return dir

def serialize(obj):
    if isinstance(obj, (str, int, float, bool, list, dict, type(None))):
        return obj
    return str(obj)  # 转为字符串

def load_nodes_from_directory(directory_name, package_prefix=""):
    """
    从指定目录加载节点
    
    Args:
        directory_name: 目录名称
        package_prefix: 包前缀，用于相对导入
    
    Returns:
        dict: 包含该目录所有节点信息的字典
    """
    global NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
    
    directory_path = get_ext_dir(directory_name)
    directory_nodes = {}
    
    if not os.path.exists(directory_path):
        print(f"Warning: Directory '{directory_name}' does not exist, skipping...")
        return directory_nodes
    
    print(f"Loading nodes from directory: {directory_name}")
    
    files = os.listdir(directory_path)
    for file in files:
        if not file.endswith(".py") or file.startswith("__"):
            continue
            
        name = os.path.splitext(file)[0]
        module_path = f"{package_prefix}.{directory_name}.{name}" if package_prefix else f".{directory_name}.{name}"
        
        try:
            print(f"  Loading module: {module_path}")
            imported_module = importlib.import_module(module_path, __name__)
            
            # 检查模块是否有节点映射
            if not hasattr(imported_module, 'NODE_CLASS_MAPPINGS'):
                print(f"    Warning: {file} does not have NODE_CLASS_MAPPINGS, skipping...")
                continue
            
            module_class_mappings = getattr(imported_module, 'NODE_CLASS_MAPPINGS', {})
            module_display_mappings = getattr(imported_module, 'NODE_DISPLAY_NAME_MAPPINGS', {})
            
            if module_class_mappings:
                print(f"    Found {len(module_class_mappings)} node(s): {list(module_class_mappings.keys())}")
                
                # 合并到全局映射
                NODE_CLASS_MAPPINGS.update(module_class_mappings)
                NODE_DISPLAY_NAME_MAPPINGS.update(module_display_mappings)
                
                # 序列化存储
                serialized_class_mappings = {k: serialize(v) for k, v in module_class_mappings.items()}
                serialized_display_mappings = {k: serialize(v) for k, v in module_display_mappings.items()}
                
                directory_nodes[file] = {
                    "NODE_CLASS_MAPPINGS": serialized_class_mappings, 
                    "NODE_DISPLAY_NAME_MAPPINGS": serialized_display_mappings
                }
            else:
                print(f"    Warning: {file} has empty NODE_CLASS_MAPPINGS")
                
        except Exception as e:
            print(f"    Error loading {file}: {str(e)}")
            continue
    
    return directory_nodes

# 需要扫描的目录列表 - 你可以在这里添加更多目录
NODE_DIRECTORIES = [
    "api_nodes",     # 现有的API节点目录
    # "utils",       # 如果utils目录有节点的话，取消注释
    # "custom_nodes", # 如果你有其他自定义节点目录
    # "extensions",   # 如果你有扩展目录
]

# 加载所有目录中的节点
all_nodes = {}
total_nodes_loaded = 0

print("=" * 50)
print("ComfyUI Doggerrr Nodes - Loading Custom Nodes")
print("=" * 50)

for directory in NODE_DIRECTORIES:
    directory_nodes = load_nodes_from_directory(directory)
    all_nodes.update(directory_nodes)
    
    # 统计该目录加载的节点数
    dir_node_count = sum(len(nodes["NODE_CLASS_MAPPINGS"]) for nodes in directory_nodes.values())
    total_nodes_loaded += dir_node_count

print("=" * 50)
print(f"Total nodes loaded: {total_nodes_loaded}")
print(f"Node classes: {list(NODE_CLASS_MAPPINGS.keys())}")
print("=" * 50)

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
