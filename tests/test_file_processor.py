import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.file_processor import FileProcessor
from config import Config


class TestFileProcessor:
    """测试文件处理器"""
    
    def test_init_without_default_filters(self):
        """测试不使用默认过滤的初始化"""
        processor = FileProcessor(
            file_types=['py', 'js'],
            exclude_names=['test_*.py'],
            exclude_dirs=['tests']
        )
        
        assert processor.file_types == ['py', 'js']
        assert processor.exclude_names == ['test_*.py']
        assert processor.exclude_dirs == ['tests']
        assert processor.use_default_filters is False
        assert processor.exclude_extensions == []
    
    def test_init_with_default_filters(self):
        """测试使用默认过滤的初始化"""
        processor = FileProcessor(
            file_types=['py'],
            exclude_names=['custom.txt'],
            exclude_dirs=['custom_dir'],
            use_default_filters=True
        )
        
        assert processor.use_default_filters is True
        # 验证默认目录被包含
        assert '.git' in processor.exclude_dirs
        assert 'node_modules' in processor.exclude_dirs
        assert 'custom_dir' in processor.exclude_dirs
        # 验证默认文件被包含
        assert 'LICENSE' in processor.exclude_names
        assert '.gitignore' in processor.exclude_names
        assert 'custom.txt' in processor.exclude_names
        # 验证扩展名列表
        assert '.log' in processor.exclude_extensions
        assert '.tmp' in processor.exclude_extensions
    
    def test_should_include_file_basic(self):
        """测试基本的文件包含逻辑"""
        processor = FileProcessor(file_types=['py', 'js'])
        
        # 应该包含的文件
        assert processor.should_include_file({
            'name': 'main.py',
            'path': 'src/main.py',
            'type': 'file'
        }) is True
        
        # 不应该包含的文件（错误的扩展名）
        assert processor.should_include_file({
            'name': 'readme.md',
            'path': 'readme.md',
            'type': 'file'
        }) is False
        
        # 不应该包含的（不是文件）
        assert processor.should_include_file({
            'name': 'src',
            'path': 'src',
            'type': 'dir'
        }) is False
    
    def test_should_include_file_with_exclude_dirs(self):
        """测试目录排除功能"""
        processor = FileProcessor(
            file_types=['py'],
            exclude_dirs=['tests', '__pycache__']
        )
        
        # 在排除目录中的文件
        assert processor.should_include_file({
            'name': 'test_main.py',
            'path': 'tests/test_main.py',
            'type': 'file'
        }) is False
        
        # 不在排除目录中的文件
        assert processor.should_include_file({
            'name': 'main.py',
            'path': 'src/main.py',
            'type': 'file'
        }) is True
    
    def test_should_include_file_with_exclude_names(self):
        """测试文件名排除功能"""
        processor = FileProcessor(
            file_types=['py'],
            exclude_names=['test_*.py', '*.pyc']
        )
        
        # 匹配排除模式的文件
        assert processor.should_include_file({
            'name': 'test_main.py',
            'path': 'test_main.py',
            'type': 'file'
        }) is False
        
        # 不匹配排除模式的文件
        assert processor.should_include_file({
            'name': 'main.py',
            'path': 'main.py',
            'type': 'file'
        }) is True
    
    def test_should_include_file_with_default_filters(self):
        """测试默认过滤功能"""
        processor = FileProcessor(use_default_filters=True)
        
        # 应该排除的文件（默认扩展名）
        assert processor.should_include_file({
            'name': 'debug.log',
            'path': 'debug.log',
            'type': 'file'
        }) is False
        
        assert processor.should_include_file({
            'name': 'image.jpg',
            'path': 'assets/image.jpg',
            'type': 'file'
        }) is False
        
        # 应该包含的文件
        assert processor.should_include_file({
            'name': 'main.py',
            'path': 'main.py',
            'type': 'file'
        }) is True
    
    def test_filter_files(self):
        """测试文件列表过滤"""
        processor = FileProcessor(
            file_types=['py', 'js'],
            exclude_dirs=['tests']
        )
        
        files = [
            {'name': 'main.py', 'path': 'main.py', 'type': 'file'},
            {'name': 'app.js', 'path': 'app.js', 'type': 'file'},
            {'name': 'test.py', 'path': 'tests/test.py', 'type': 'file'},
            {'name': 'readme.md', 'path': 'readme.md', 'type': 'file'},
            {'name': 'src', 'path': 'src', 'type': 'dir'}
        ]
        
        filtered = processor.filter_files(files)
        
        assert len(filtered) == 2
        assert filtered[0]['name'] == 'main.py'
        assert filtered[1]['name'] == 'app.js'
    
    def test_generate_output_filename(self):
        """测试输出文件名生成"""
        processor = FileProcessor()
        
        # Markdown格式
        filename_md = processor.generate_output_filename('my-repo', 'md')
        assert filename_md.startswith('my-repo_merged_')
        assert filename_md.endswith('.md')
        
        # 文本格式
        filename_txt = processor.generate_output_filename('my-repo', 'txt')
        assert filename_txt.startswith('my-repo_merged_')
        assert filename_txt.endswith('.txt')
    
    def test_merge_files_content_markdown(self):
        """测试Markdown格式的文件合并"""
        processor = FileProcessor()
        
        files_content = [
            {
                'path': 'main.py',
                'content': 'print("Hello")',
                'size': 14,
                'is_binary': False,
                'is_oversized': False
            },
            {
                'path': 'README.md',
                'content': '# Project',
                'size': 9,
                'is_binary': False,
                'is_oversized': False
            }
        ]
        
        merged, total_size = processor.merge_files_content(files_content, 'md', 'test-repo')
        
        assert '# test-repo - 代码聚合文件' in merged
        assert '## /main.py' in merged
        assert '```python' in merged
        assert 'print("Hello")' in merged
        assert '## /README.md' in merged
        assert '# Project' in merged
        assert total_size == 23
    
    def test_merge_files_content_text(self):
        """测试纯文本格式的文件合并"""
        processor = FileProcessor()
        
        files_content = [
            {
                'path': 'main.py',
                'content': 'print("Hello")',
                'size': 14,
                'is_binary': False,
                'is_oversized': False
            }
        ]
        
        merged, total_size = processor.merge_files_content(files_content, 'txt', 'test-repo')
        
        assert 'test-repo - 代码聚合文件' in merged
        assert '===== /main.py =====' in merged
        assert 'print("Hello")' in merged
        assert total_size == 14


if __name__ == '__main__':
    pytest.main([__file__, '-v']) 