import os
import re
import fnmatch
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
from config import Config

class FileProcessor:
    """文件处理器"""
    
    def __init__(self, file_types: Optional[List[str]] = None, 
                 exclude_names: Optional[List[str]] = None, 
                 exclude_dirs: Optional[List[str]] = None, 
                 use_default_filters: bool = False) -> None:
        self.file_types = file_types or []
        self.exclude_names = exclude_names or []
        self.exclude_dirs = exclude_dirs or []
        self.use_default_filters = use_default_filters
        
        # 如果使用默认过滤，合并默认规则
        if self.use_default_filters:
            # 合并排除目录（去重）
            default_dirs = set(Config.DEFAULT_EXCLUDE_DIRS)
            user_dirs = set(self.exclude_dirs)
            self.exclude_dirs = list(default_dirs | user_dirs)
            
            # 合并排除文件名（去重）
            default_files = set(Config.DEFAULT_EXCLUDE_FILES)
            user_files = set(self.exclude_names)
            self.exclude_names = list(default_files | user_files)
            
            # 处理默认排除的扩展名
            self.exclude_extensions = Config.DEFAULT_EXCLUDE_EXTENSIONS
        else:
            self.exclude_extensions = []
    
    def should_include_file(self, file_info: Dict[str, str]) -> bool:
        """判断文件是否应该包含"""
        file_name = file_info['name']
        file_path = file_info['path']
        
        # 检查是否为文件
        if file_info.get('type') != 'file':
            return False
        
        # 检查是否在排除目录中
        for exclude_dir in self.exclude_dirs:
            # 检查路径中是否包含排除的目录
            if exclude_dir in file_path.split('/'):
                return False
            # 检查路径是否以排除目录开头
            if file_path.startswith(exclude_dir + '/'):
                return False
        
        # 检查文件名是否匹配排除模式
        for pattern in self.exclude_names:
            if fnmatch.fnmatch(file_name, pattern):
                return False
        
        # 如果使用默认过滤，检查文件扩展名
        if self.use_default_filters:
            file_ext = os.path.splitext(file_name)[1].lower()
            if file_ext in self.exclude_extensions:
                return False
        
        # 检查文件类型（如果指定了）
        if self.file_types:
            file_ext = os.path.splitext(file_name)[1].lstrip('.').lower()
            if file_ext not in self.file_types:
                return False
        
        return True
    
    def filter_files(self, files: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """过滤文件列表"""
        filtered = []
        
        for file_info in files:
            if self.should_include_file(file_info):
                filtered.append(file_info)
        
        return filtered
    
    def merge_files_content(self, files_content: List[Dict[str, Any]], 
                          output_format: str, repo_name: str) -> Tuple[str, int]:
        """合并文件内容"""
        if not files_content:
            return "", 0
        
        merged_content = []
        total_size = 0
        
        if output_format == 'md':
            # 标题和基本信息
            merged_content.append(f"# {repo_name} - 代码聚合文件\n\n")
            merged_content.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            merged_content.append(f"文件数量: {len(files_content)}\n\n")
            
            # 生成目录（TOC）
            merged_content.append("## 📑 目录\n\n")
            
            # 按文件路径排序，确保目录有序
            sorted_files = sorted(files_content, key=lambda x: x['path'])
            
            for file_info in sorted_files:
                file_path = file_info['path']
                # 生成锚点链接（将路径转换为有效的锚点）
                anchor = self._generate_anchor(file_path)
                merged_content.append(f"- [{file_path}](#{anchor})\n")
            
            merged_content.append("\n---\n\n")
        else:
            merged_content.append(f"{repo_name} - 代码聚合文件\n")
            merged_content.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            merged_content.append(f"文件数量: {len(files_content)}\n")
            merged_content.append("=" * 80 + "\n\n")
        
        # 按文件路径排序输出内容
        sorted_files = sorted(files_content, key=lambda x: x['path'])
        
        for file_info in sorted_files:
            file_path = file_info['path']
            content = file_info['content']
            file_size = file_info.get('size', 0)
            is_binary = file_info.get('is_binary', False)
            is_oversized = file_info.get('is_oversized', False)
            
            total_size += file_size
            
            if output_format == 'md':
                # Markdown格式 - 添加锚点ID
                anchor = self._generate_anchor(file_path)
                merged_content.append(f"## <a id=\"{anchor}\"></a>📄 /{file_path}\n\n")
                
                if is_binary or is_oversized:
                    merged_content.append(f"{content}\n\n")
                else:
                    # 根据文件扩展名确定代码块语言
                    file_ext = Path(file_path).suffix.lstrip('.').lower()
                    
                    # 常见编程语言映射
                    lang_map = {
                        'py': 'python',
                        'js': 'javascript',
                        'ts': 'typescript',
                        'jsx': 'jsx',
                        'tsx': 'tsx',
                        'java': 'java',
                        'cpp': 'cpp',
                        'c': 'c',
                        'cs': 'csharp',
                        'php': 'php',
                        'rb': 'ruby',
                        'go': 'go',
                        'rs': 'rust',
                        'kt': 'kotlin',
                        'swift': 'swift',
                        'html': 'html',
                        'css': 'css',
                        'scss': 'scss',
                        'sass': 'sass',
                        'less': 'less',
                        'sql': 'sql',
                        'sh': 'bash',
                        'yml': 'yaml',
                        'yaml': 'yaml',
                        'json': 'json',
                        'xml': 'xml',
                        'md': 'markdown',
                        'dockerfile': 'dockerfile'
                    }
                    
                    # 对于文本文件（md, txt等），直接插入内容
                    if file_ext in ['md', 'txt', 'rst']:
                        merged_content.append(f"{content}\n\n")
                    else:
                        # 对于代码文件，使用代码块
                        lang = lang_map.get(file_ext, file_ext)
                        merged_content.append(f"```{lang}\n{content}\n```\n\n")
                
                # 添加返回顶部链接
                merged_content.append("[⬆️ 返回目录](#-目录)\n\n")
            else:
                # TXT格式
                merged_content.append(f"===== /{file_path} =====\n")
                merged_content.append(f"{content}\n\n")
        
        final_content = ''.join(merged_content)
        return final_content, total_size
    
    def _generate_anchor(self, file_path: str) -> str:
        """生成有效的Markdown锚点"""
        # 移除特殊字符，只保留字母、数字、连字符和下划线
        # 替换路径分隔符为连字符
        anchor = file_path.replace('/', '-').replace('\\', '-')
        # 替换其他特殊字符为连字符
        anchor = re.sub(r'[^a-zA-Z0-9_-]', '-', anchor)
        # 移除连续的连字符
        anchor = re.sub(r'-+', '-', anchor)
        # 移除开头和结尾的连字符
        anchor = anchor.strip('-')
        # 转换为小写
        return anchor.lower()
    
    def generate_output_filename(self, repo_name: str, output_format: str) -> str:
        """生成输出文件名"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{repo_name}_merged_{timestamp}.{output_format}"
    
    def save_merged_file(self, content: str, filename: str) -> Dict[str, Any]:
        """保存合并后的文件"""
        file_path = os.path.join(Config.DOWNLOAD_FOLDER, filename)
        
        # 确保目录存在
        os.makedirs(Config.DOWNLOAD_FOLDER, exist_ok=True)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 获取文件大小
            file_size = os.path.getsize(file_path)
            
            return {
                'file_path': file_path,
                'file_name': filename,
                'file_size': file_size
            }
        except Exception as e:
            raise Exception(f"保存文件失败：{str(e)}") 