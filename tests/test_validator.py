import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.validator import Validator, ValidationError


class TestValidator:
    """测试参数验证器"""
    
    def test_validate_repo_url_valid(self):
        """测试有效的仓库URL"""
        # 标准格式
        assert Validator.validate_repo_url("https://github.com/user/repo") == "https://github.com/user/repo"
        # 带斜杠结尾
        assert Validator.validate_repo_url("https://github.com/user/repo/") == "https://github.com/user/repo"
        # 包含连字符和点
        assert Validator.validate_repo_url("https://github.com/user-name/repo.name") == "https://github.com/user-name/repo.name"
    
    def test_validate_repo_url_invalid(self):
        """测试无效的仓库URL"""
        # 空URL
        with pytest.raises(ValidationError, match="仓库URL不能为空"):
            Validator.validate_repo_url("")
        
        # 非GitHub URL
        with pytest.raises(ValidationError, match="无效的GitHub仓库URL格式"):
            Validator.validate_repo_url("https://gitlab.com/user/repo")
        
        # 格式错误
        with pytest.raises(ValidationError, match="无效的GitHub仓库URL格式"):
            Validator.validate_repo_url("github.com/user/repo")
        
        # 路径穿越（注意：现在会在格式验证阶段就失败）
        with pytest.raises(ValidationError, match="无效的GitHub仓库URL格式"):
            Validator.validate_repo_url("https://github.com/user/../repo")
    
    def test_validate_file_types(self):
        """测试文件类型验证"""
        # 有效的文件类型
        assert Validator.validate_file_types("py,js,md") == ['py', 'js', 'md']
        assert Validator.validate_file_types(".py,.js") == ['py', 'js']
        assert Validator.validate_file_types("") == []
        
        # 无效的文件类型
        with pytest.raises(ValidationError, match="无效的文件扩展名"):
            Validator.validate_file_types("py,js,md$")
    
    def test_validate_exclude_names(self):
        """测试排除文件名验证"""
        # 有效的排除模式
        assert Validator.validate_exclude_names("test_*.py,README.md") == ['test_*.py', 'README.md']
        assert Validator.validate_exclude_names("") == []
        
        # 超长输入
        with pytest.raises(ValidationError, match="排除文件名参数长度不能超过"):
            Validator.validate_exclude_names("a" * 200)
    
    def test_validate_exclude_dirs(self):
        """测试排除目录验证"""
        # 有效的目录
        assert Validator.validate_exclude_dirs("tests,docs,.github") == ['tests', 'docs', '.github']
        assert Validator.validate_exclude_dirs("") == []
        
        # 超过长度限制（而不是数量限制）
        long_dirs = "a" * 200
        with pytest.raises(ValidationError, match="排除目录参数长度不能超过"):
            Validator.validate_exclude_dirs(long_dirs)
        
        # 测试数量限制
        many_dirs = ",".join([f"d{i}" for i in range(25)])
        with pytest.raises(ValidationError, match="排除目录数量不能超过"):
            Validator.validate_exclude_dirs(many_dirs)
    
    def test_validate_output_format(self):
        """测试输出格式验证"""
        # 有效格式
        assert Validator.validate_output_format("md") == "md"
        assert Validator.validate_output_format("txt") == "txt"
        assert Validator.validate_output_format("") == "txt"  # 默认值
        
        # 无效格式
        with pytest.raises(ValidationError, match="不支持的输出格式"):
            Validator.validate_output_format("pdf")
    
    def test_validate_all_params(self):
        """测试完整参数验证"""
        params = {
            'repo_url': 'https://github.com/user/repo',
            'file_types': 'py,js',
            'exclude_names': 'test_*.py',
            'exclude_dirs': 'tests',
            'output_format': 'md',
            'use_default_filters': 'true'
        }
        
        result = Validator.validate_all_params(params)
        
        assert result['repo_url'] == 'https://github.com/user/repo'
        assert result['owner'] == 'user'
        assert result['repo'] == 'repo'
        assert result['file_types'] == ['py', 'js']
        assert result['exclude_names'] == ['test_*.py']
        assert result['exclude_dirs'] == ['tests']
        assert result['output_format'] == 'md'
        assert result['use_default_filters'] is True


if __name__ == '__main__':
    pytest.main([__file__, '-v']) 