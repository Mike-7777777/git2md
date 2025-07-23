import os
import json
from datetime import timedelta

class Config:
    # 基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Token配置文件路径
    TOKEN_CONFIG_FILE = 'token_config.json'
    
    @staticmethod
    def _load_token_from_file():
        """从配置文件加载token"""
        try:
            if os.path.exists(Config.TOKEN_CONFIG_FILE):
                with open(Config.TOKEN_CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('github_token')
        except Exception:
            pass
        return None
    
    @staticmethod
    def get_github_token():
        """动态获取GitHub Token，优先从配置文件，其次从环境变量"""
        # 优先从配置文件读取
        token = Config._load_token_from_file()
        if token:
            return token
        
        # 其次从环境变量读取
        return os.environ.get('GITHUB_TOKEN')
    
    @staticmethod
    def save_token_to_file(token):
        """保存token到配置文件"""
        try:
            config = {}
            if os.path.exists(Config.TOKEN_CONFIG_FILE):
                with open(Config.TOKEN_CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            if token:
                config['github_token'] = token
            else:
                config.pop('github_token', None)
            
            with open(Config.TOKEN_CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            
            return True
        except Exception as e:
            print(f"保存token失败: {e}")
            return False
    
    # API请求优化配置
    REQUEST_DELAY = float(os.environ.get('REQUEST_DELAY', 0.5))  # 请求间隔（秒）
    CACHE_DURATION = int(os.environ.get('CACHE_DURATION', 300))  # 缓存持续时间（秒）
    MAX_RETRY_ATTEMPTS = int(os.environ.get('MAX_RETRY_ATTEMPTS', 3))  # 最大重试次数
    
    # 文件处理限制
    MAX_REPO_SIZE_MB = int(os.environ.get('MAX_REPO_SIZE_MB', 100))  # 最大仓库大小（MB）
    MAX_FILE_COUNT = int(os.environ.get('MAX_FILE_COUNT', 2000))   # 最大文件数量
    MAX_SINGLE_FILE_SIZE_MB = int(os.environ.get('MAX_SINGLE_FILE_SIZE_MB', 1))  # 单文件最大大小（MB）
    MAX_SPLIT_FILE_SIZE_MB = float(os.environ.get('MAX_SPLIT_FILE_SIZE_MB', 1.5)) # 切分文件最大大小(MB)
    MAX_PARAM_LENGTH = 128  # 参数最大长度
    MAX_PARAM_ITEMS = 20    # 参数项目最大数量
    
    # 临时文件配置
    DOWNLOAD_FOLDER = 'downloads'
    CACHE_FOLDER = 'cache'
    FILE_RETENTION_MINUTES = int(os.environ.get('FILE_RETENTION_MINUTES', 30))  # 文件保留时间（分钟）
    CONCURRENT_REQUESTS = int(os.environ.get('CONCURRENT_REQUESTS', 10))  # 并发请求数量
    
    # 请求超时配置
    REQUEST_TIMEOUT = 30  # 秒
    
    # 支持的文件格式
    SUPPORTED_OUTPUT_FORMATS = ['txt', 'md']
    
    # 默认排除的目录
    DEFAULT_EXCLUDE_DIRS = [
        # 素材和资源目录
        'assets', 'imgs', 'images', 'img', 'media', 'static/images', 
        'public/images', 'resources', 'pics', 'pictures', 'graphics',
        
        # 构建和输出目录
        'dist', 'build', 'bin', 'obj', 'out', 'output', 'target',
        
        # 依赖和包管理目录
        'node_modules', 'vendor', 'packages', 'bower_components',
        
        # IDE和编辑器目录
        '.vscode', '.idea', '.vs', '.vscode-test', '.atom',
        
        # 版本控制
        '.git', '.svn', '.hg',
        
        # 缓存和临时目录
        '__pycache__', '.pytest_cache', '.cache', 'coverage', 
        '.nyc_output', '.sass-cache', 'tmp', 'temp',
        
        # 其他
        '.github', '.gitlab', 'docs', 'doc', 'documentation'
    ]
    
    # 默认排除的文件名
    DEFAULT_EXCLUDE_FILES = [
        # 许可证和说明文件
        'LICENSE', 'LICENSE.md', 'LICENSE.txt', 'LICENCE',
        'COPYING', 'COPYING.md', 'NOTICE',
        
        # Git相关文件
        '.gitignore', '.gitattributes', '.gitmodules', '.gitkeep',
        
        # 配置文件
        '.env', '.env.example', '.env.local', '.env.development', 
        '.env.production', '.env.test',
        
        # 编辑器配置
        '.editorconfig', '.prettierrc', '.eslintrc', '.stylelintrc',
        
        # CI/CD配置
        '.travis.yml', '.gitlab-ci.yml', 'azure-pipelines.yml',
        'Jenkinsfile', '.circleci/config.yml',
        
        # Docker相关
        'Dockerfile', 'docker-compose.yml', '.dockerignore',
        
        # 系统文件
        'Thumbs.db', '.DS_Store', 'desktop.ini',
        
        # 包管理文件
        'package-lock.json', 'yarn.lock', 'composer.lock',
        'Gemfile.lock', 'poetry.lock', 'Pipfile.lock'
    ]
    
    # 默认排除的文件扩展名
    DEFAULT_EXCLUDE_EXTENSIONS = [
        # 日志和临时文件
        '.log', '.tmp', '.temp', '.cache', '.bak', '.backup',
        '.swp', '.swo', '.swn', '.swap',
        
        # 编译产物
        '.pyc', '.pyo', '.pyd', '.class', '.o', '.obj',
        '.exe', '.dll', '.so', '.dylib', '.a', '.lib',
        
        # 数据库文件
        '.db', '.sqlite', '.sqlite3', '.mdb', '.accdb',
        
        # 压缩文件
        '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2',
        '.xz', '.tgz', '.tar.gz',
        
        # 图片文件
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico',
        '.svg', '.webp', '.tiff', '.psd', '.ai',
        
        # 视频和音频文件
        '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm',
        '.mp3', '.wav', '.ogg', '.m4a', '.aac',
        
        # 字体文件
        '.ttf', '.otf', '.woff', '.woff2', '.eot',
        
        # Office文档
        '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        '.pdf', '.odt', '.ods', '.odp',
        
        # 锁文件
        '.lock', '.pid',
        
        # 其他二进制文件
        '.bin', '.dat', '.data'
    ]
    
    @staticmethod
    def init_app(app):
        # 确保下载目录存在
        os.makedirs(Config.DOWNLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.CACHE_FOLDER, exist_ok=True) 