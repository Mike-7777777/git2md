import re
from typing import List, Dict, Any, Union
from urllib.parse import urlparse
from config import Config

class ValidationError(Exception):
    """自定义校验异常"""
    pass

class Validator:
    """参数校验器"""
    
    @staticmethod
    def validate_repo_url(repo_url: str) -> str:
        """验证GitHub仓库URL"""
        if not repo_url:
            raise ValidationError("仓库URL不能为空")
        
        # 基本长度检查
        if len(repo_url) > Config.MAX_PARAM_LENGTH:
            raise ValidationError(f"仓库URL长度不能超过{Config.MAX_PARAM_LENGTH}个字符")
        
        # URL格式校验
        pattern = r'^https?://github\.com/[\w\-\.]+/[\w\-\.]+/?$'
        if not re.match(pattern, repo_url):
            raise ValidationError("无效的GitHub仓库URL格式")
        
        # 提取owner和repo信息用于验证
        parts = repo_url.rstrip('/').split('/')
        owner = parts[-2]
        repo = parts[-1]
        
        # 验证owner和repo名称
        if not re.match(r'^[\w\-\.]+$', owner):
            raise ValidationError("仓库所有者名称包含非法字符")
        if not re.match(r'^[\w\-\.]+$', repo):
            raise ValidationError("仓库名称包含非法字符")
        
        # 防止路径穿越
        if '..' in repo_url or './' in repo_url:
            raise ValidationError("URL包含非法路径字符")
        
        return repo_url.rstrip('/')
    
    @staticmethod
    def validate_file_types(file_types: str) -> List[str]:
        """校验文件类型参数"""
        if not file_types:
            return []
        
        file_types = file_types.strip()
        if len(file_types) > Config.MAX_PARAM_LENGTH:
            raise ValidationError(f"文件类型参数长度不能超过{Config.MAX_PARAM_LENGTH}字符")
        
        # 分割并清理
        types = [t.strip().lower().lstrip('.') for t in file_types.split(',') if t.strip()]
        
        if len(types) > Config.MAX_PARAM_ITEMS:
            raise ValidationError(f"文件类型数量不能超过{Config.MAX_PARAM_ITEMS}个")
        
        # 检查格式
        for ext in types:
            if not re.match(r'^[a-zA-Z0-9]+$', ext):
                raise ValidationError(f"无效的文件扩展名：{ext}")
        
        return types
    
    @staticmethod
    def validate_exclude_names(exclude_names: str) -> List[str]:
        """校验排除文件名参数"""
        if not exclude_names:
            return []
        
        exclude_names = exclude_names.strip()
        if len(exclude_names) > Config.MAX_PARAM_LENGTH:
            raise ValidationError(f"排除文件名参数长度不能超过{Config.MAX_PARAM_LENGTH}字符")
        
        # 分割并清理
        names = [n.strip() for n in exclude_names.split(',') if n.strip()]
        
        if len(names) > Config.MAX_PARAM_ITEMS:
            raise ValidationError(f"排除文件名数量不能超过{Config.MAX_PARAM_ITEMS}个")
        
        return names
    
    @staticmethod
    def validate_exclude_dirs(exclude_dirs: str) -> List[str]:
        """校验排除目录参数"""
        if not exclude_dirs:
            return []
        
        exclude_dirs = exclude_dirs.strip()
        if len(exclude_dirs) > Config.MAX_PARAM_LENGTH:
            raise ValidationError(f"排除目录参数长度不能超过{Config.MAX_PARAM_LENGTH}字符")
        
        # 分割并清理
        dirs = [d.strip() for d in exclude_dirs.split(',') if d.strip()]
        
        if len(dirs) > Config.MAX_PARAM_ITEMS:
            raise ValidationError(f"排除目录数量不能超过{Config.MAX_PARAM_ITEMS}个")
        
        return dirs
    
    @staticmethod
    def validate_output_format(output_format: str) -> str:
        """校验输出格式参数"""
        if not output_format:
            return 'txt'
        
        output_format = output_format.strip().lower()
        if output_format not in Config.SUPPORTED_OUTPUT_FORMATS:
            raise ValidationError(f"不支持的输出格式：{output_format}，支持的格式：{', '.join(Config.SUPPORTED_OUTPUT_FORMATS)}")
        
        return output_format
    
    @classmethod
    def validate_all_params(cls, params: Dict[str, Any]) -> Dict[str, Union[str, List[str], bool]]:
        """验证所有参数"""
        validated: Dict[str, Union[str, List[str], bool]] = {}
        
        # 验证repo_url（必填）
        validated['repo_url'] = cls.validate_repo_url(params.get('repo_url'))
        
        # 从URL中提取owner和repo
        parsed = validated['repo_url'].rstrip('/').split('/')
        validated['owner'] = parsed[-2]
        validated['repo'] = parsed[-1]
        
        # 验证其他参数（可选）
        file_types = params.get('file_types', '')
        if file_types:
            validated['file_types'] = cls.validate_file_types(file_types)
        else:
            validated['file_types'] = []
        
        exclude_names = params.get('exclude_names', '')
        if exclude_names:
            validated['exclude_names'] = cls.validate_exclude_names(exclude_names)
        else:
            validated['exclude_names'] = []
        
        exclude_dirs = params.get('exclude_dirs', '')
        if exclude_dirs:
            validated['exclude_dirs'] = cls.validate_exclude_dirs(exclude_dirs)
        else:
            validated['exclude_dirs'] = []
        
        # 验证output_format（可选，有默认值）
        output_format = params.get('output_format', 'md')
        validated['output_format'] = cls.validate_output_format(output_format)
        
        # 验证use_default_filters（可选，布尔值）
        use_default_filters = params.get('use_default_filters', False)
        if isinstance(use_default_filters, str):
            validated['use_default_filters'] = use_default_filters.lower() in ['true', '1', 'on', 'yes']
        else:
            validated['use_default_filters'] = bool(use_default_filters)
        
        return validated 