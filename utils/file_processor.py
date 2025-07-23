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
        self.file_types = [ft.strip().lower() for ft in file_types if ft.strip()] if file_types else []
        self.exclude_names = [en.strip() for en in exclude_names if en.strip()] if exclude_names else []
        self.exclude_dirs = [ed.strip().strip('/') for ed in exclude_dirs if ed.strip()] if exclude_dirs else []
        
        if use_default_filters:
            self.exclude_dirs.extend(Config.DEFAULT_EXCLUDE_DIRS)
            # 默认过滤规则中没有'DEFAULT_EXCLUDE_FILENAMES'和'DEFAULT_EXCLUDE_EXTENSIONS'，此处注释掉
            # self.exclude_names.extend(Config.DEFAULT_EXCLUDE_FILENAMES)
            # if not self.file_types: # 如果用户未指定类型，则使用默认排除扩展名
            #      self.exclude_names.extend([f"*.{ext}" for ext in Config.DEFAULT_EXCLUDE_EXTENSIONS])
    
    def filter_files(self, files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """过滤文件列表"""
        
        def _is_excluded(file_path: str) -> bool:
            # 检查是否在排除目录中
            for dir_pattern in self.exclude_dirs:
                if f'/{dir_pattern}/' in f'/{file_path}' or file_path.startswith(dir_pattern + '/'):
                    return True
            
            # 检查是否匹配排除文件名
            file_name = Path(file_path).name
            for name_pattern in self.exclude_names:
                if fnmatch.fnmatch(file_name, name_pattern):
                    return True

            # 检查文件类型
            if self.file_types:
                file_ext = Path(file_path).suffix.lstrip('.').lower()
                if file_ext not in self.file_types:
                    return True
            
            return False

        return [f for f in files if f.get('type') == 'file' and not _is_excluded(f['path'])]
    
    def merge_files_content(self, files_content: List[Dict[str, Any]], 
                          output_format: str, repo_name: str) -> Tuple[str, int]:
        """合并文件内容"""
        if not files_content:
            return "", 0
        
        merged_content = []
        total_size = 0
        
        sorted_files = sorted(files_content, key=lambda x: x['path'])

        if output_format == 'md':
            # 标题和基本信息
            merged_content.append(f"# {repo_name} - 代码聚合文件\n\n")
            merged_content.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            merged_content.append(f"文件数量: {len(files_content)}\n\n")
            
            # 生成目录（TOC）
            merged_content.append("## 📑 目录\n\n")
            for file_info in sorted_files:
                file_path = file_info['path']
                anchor = self._generate_anchor(file_path)
                merged_content.append(f"- [{file_path}](#{anchor})\n")
            merged_content.append("\n---\n\n")
            
            # 文件内容
            for file_info in sorted_files:
                merged_content.append(self._format_file_content_md(file_info))
                total_size += file_info.get('size', 0)
        else: # TXT格式
            merged_content.append(f"{repo_name} - 代码聚合文件\n")
            merged_content.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            merged_content.append(f"文件数量: {len(files_content)}\n")
            merged_content.append("=" * 80 + "\n\n")
            
            for file_info in sorted_files:
                file_path = file_info['path']
                content = file_info['content']
                total_size += file_info.get('size', 0)
                merged_content.append(f"===== /{file_path} =====\n")
                merged_content.append(f"{content}\n\n")
        
        final_content = ''.join(merged_content)
        # Recalculate size based on final content for accuracy
        final_size = len(final_content.encode('utf-8'))
        return final_content, final_size
    
    def save_split_files(self, files_content: List[Dict[str, Any]], repo_name: str, output_format: str) -> Dict[str, Any]:
        """将内容拆分为多个文件并保存"""
        if not files_content:
            return {}

        max_size_bytes = Config.MAX_SPLIT_FILE_SIZE_MB * 1024 * 1024
        
        # 创建一个唯一的目录来存放本次任务的文件
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        task_dir_name = f"{repo_name}_split_{timestamp}"
        task_dir_path = os.path.join(Config.DOWNLOAD_FOLDER, task_dir_name)
        os.makedirs(task_dir_path, exist_ok=True)

        split_files = []
        file_index = 1
        current_content = []
        current_size = 0
        toc_entries = []

        header = f"# {repo_name} - 代码聚合文件 (部分 {file_index})\n\n"
        current_content.append(header)
        current_size += len(header.encode('utf-8'))

        sorted_files = sorted(files_content, key=lambda x: x['path'])

        for file_info in sorted_files:
            file_path = file_info['path']
            content = file_info['content']
            file_ext = Path(file_path).suffix.lstrip('.').lower()

            # 生成文件内容的Markdown表示
            file_md = []
            anchor = self._generate_anchor(file_path)
            file_md.append(f"## <a id=\"{anchor}\"></a>📄 /{file_path}\n\n")
            
            if file_info.get('is_binary') or file_info.get('is_oversized'):
                file_md.append(f"{content}\n\n")
            else:
                lang = self._get_lang_from_ext(file_ext)
                if file_ext in ['md', 'txt', 'rst']:
                    file_md.append(f"{content}\n\n")
                else:
                    file_md.append(f"```{lang}\n{content}\n```\n\n")
            
            file_md_str = ''.join(file_md)
            file_md_size = len(file_md_str.encode('utf-8'))

            # 检查是否需要切分
            if current_size + file_md_size > max_size_bytes and current_size > len(header.encode('utf-8')):
                # 保存当前文件
                split_filename = f"part_{file_index}.{output_format}"
                split_filepath = os.path.join(task_dir_path, split_filename)
                with open(split_filepath, 'w', encoding='utf-8') as f:
                    f.write(''.join(current_content))
                split_files.append({'name': split_filename, 'path': f"/{task_dir_name}/{split_filename}"})
                
                # 开始新文件
                file_index += 1
                current_content = []
                current_size = 0
                header = f"# {repo_name} - 代码聚合文件 (部分 {file_index})\n\n"
                current_content.append(header)
                current_size += len(header.encode('utf-8'))

            current_content.append(file_md_str)
            current_size += file_md_size
            toc_entries.append(f"- `/{file_path}` (在 [part_{file_index}.{output_format}](./part_{file_index}.{output_format}#{anchor}))\n")

        # 保存最后一个文件
        if current_content and current_size > len(header.encode('utf-8')):
            split_filename = f"part_{file_index}.{output_format}"
            split_filepath = os.path.join(task_dir_path, split_filename)
            with open(split_filepath, 'w', encoding='utf-8') as f:
                f.write(''.join(current_content))
            split_files.append({'name': split_filename, 'path': f"/{task_dir_name}/{split_filename}"})

        # 生成并保存目录文件
        toc_content = [f"# {repo_name} - 文件目录\n\n"]
        toc_content.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        toc_content.append(f"文件总数: {len(files_content)}\n\n")
        toc_content.append("## 📑 目录\n\n")
        toc_content.extend(toc_entries)
        
        toc_filename = "index.md"
        toc_filepath = os.path.join(task_dir_path, toc_filename)
        with open(toc_filepath, 'w', encoding='utf-8') as f:
            f.write("".join(toc_content))

        return {
            'file_path': task_dir_path,
            'file_name': task_dir_name,
            'file_count': len(files_content),
            'split_files': [{'name': toc_filename, 'path': f"/{task_dir_name}/{toc_filename}"}] + split_files
        }

    def _get_lang_from_ext(self, file_ext: str) -> str:
        """根据文件扩展名获取代码块语言"""
        lang_map = {
            'py': 'python', 'js': 'javascript', 'ts': 'typescript', 'jsx': 'jsx', 'tsx': 'tsx',
            'java': 'java', 'cpp': 'cpp', 'c': 'c', 'cs': 'csharp', 'php': 'php', 'rb': 'ruby',
            'go': 'go', 'rs': 'rust', 'kt': 'kotlin', 'swift': 'swift', 'html': 'html',
            'css': 'css', 'scss': 'scss', 'sass': 'sass', 'less': 'less', 'sql': 'sql',
            'sh': 'bash', 'yml': 'yaml', 'yaml': 'yaml', 'json': 'json', 'xml': 'xml',
            'md': 'markdown', 'dockerfile': 'dockerfile'
        }
        return lang_map.get(file_ext, file_ext)
    
    def _generate_anchor(self, file_path: str) -> str:
        """生成有效的Markdown锚点"""
        # 移除特殊字符，只保留字母、数字、连字符和下划线
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
    
    def _format_file_content_md(self, file_info: Dict[str, Any]) -> str:
        """将单个文件信息格式化为Markdown字符串"""
        file_path = file_info['path']
        content = file_info['content']
        is_binary = file_info.get('is_binary', False)
        is_oversized = file_info.get('is_oversized', False)
        
        anchor = self._generate_anchor(file_path)
        md_content = [f"## <a id=\"{anchor}\"></a>📄 /{file_path}\n\n"]
        
        if is_binary or is_oversized:
            md_content.append(f"{content}\n\n")
        else:
            file_ext = Path(file_path).suffix.lstrip('.').lower()
            lang = self._get_lang_from_ext(file_ext)
            
            if file_ext in ['md', 'txt', 'rst']:
                md_content.append(f"{content}\n\n")
            else:
                md_content.append(f"```{lang}\n{content}\n```\n\n")
        
        md_content.append("[⬆️ 返回目录](#-目录)\n\n")
        return "".join(md_content)