import requests
import base64
import time
import json
import os
from github import Github, GithubException
from config import Config

class GitHubError(Exception):
    """GitHub操作异常"""
    pass

class GitHubHandler:
    """GitHub仓库处理器"""
    
    def __init__(self):
        self.github = None
        github_token = Config.get_github_token()
        if github_token:
            self.github = Github(github_token)
        else:
            self.github = Github()
        
        # 缓存机制
        self.cache = {}
        self.cache_dir = 'cache'
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 请求延迟配置
        self.request_delay = 0.5  # 秒
        self.last_request_time = 0
    
    def _wait_for_rate_limit(self):
        """等待速率限制"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.request_delay:
            time.sleep(self.request_delay - time_since_last)
        self.last_request_time = time.time()
    
    def _get_cache_path(self, key):
        """获取缓存文件路径"""
        return os.path.join(self.cache_dir, f"{key}.json")
    
    def _get_from_cache(self, key):
        """从缓存获取数据"""
        cache_path = self._get_cache_path(key)
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 检查缓存是否过期（5分钟）
                    if time.time() - data.get('timestamp', 0) < 300:
                        return data.get('content')
            except:
                pass
        return None
    
    def _save_to_cache(self, key, content):
        """保存数据到缓存"""
        cache_path = self._get_cache_path(key)
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': time.time(),
                    'content': content
                }, f)
        except:
            pass
    
    def get_repo_info(self, owner, repo_name):
        """获取仓库基本信息"""
        cache_key = f"repo_{owner}_{repo_name}"
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        try:
            self._wait_for_rate_limit()
            repo = self.github.get_repo(f"{owner}/{repo_name}")
            
            # 检查仓库大小
            repo_size_mb = repo.size / 1024  # GitHub API返回的size单位是KB
            if repo_size_mb > Config.MAX_REPO_SIZE_MB:
                raise GitHubError(f"仓库大小 {repo_size_mb:.1f}MB 超过限制 {Config.MAX_REPO_SIZE_MB}MB")
            
            result = {
                'name': repo.name,
                'full_name': repo.full_name,
                'size_kb': repo.size,
                'size_mb': repo_size_mb,
                'default_branch': repo.default_branch,
                'private': repo.private
            }
            
            self._save_to_cache(cache_key, result)
            return result
            
        except GithubException as e:
            if e.status == 404:
                raise GitHubError("仓库不存在或无法访问")
            elif e.status == 403:
                raise GitHubError("API限制或权限不足，请设置GitHub Token或稍后重试")
            else:
                raise GitHubError(f"获取仓库信息失败：{e.data.get('message', str(e))}")
        except Exception as e:
            raise GitHubError(f"网络或其他错误：{str(e)}")
    
    def get_repository_tree(self, owner, repo_name, branch=None):
        """使用树API一次性获取所有文件信息"""
        cache_key = f"tree_{owner}_{repo_name}_{branch}"
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        try:
            self._wait_for_rate_limit()
            repo = self.github.get_repo(f"{owner}/{repo_name}")
            
            if not branch:
                branch = repo.default_branch
            
            # 使用树API递归获取所有文件
            tree = repo.get_git_tree(branch, recursive=True)
            
            files = []
            for item in tree.tree:
                if item.type == 'blob':  # 只要文件，不要目录
                    files.append({
                        'path': item.path,
                        'name': os.path.basename(item.path),
                        'size': item.size,
                        'sha': item.sha,
                        'type': 'file'
                    })
            
            # 检查文件数量限制
            if len(files) > Config.MAX_FILE_COUNT:
                raise GitHubError(f"仓库文件数量 {len(files)} 超过限制 {Config.MAX_FILE_COUNT}")
            
            self._save_to_cache(cache_key, files)
            return files
            
        except GithubException as e:
            if e.status == 404:
                raise GitHubError("仓库不存在或分支不存在")
            else:
                raise GitHubError(f"获取仓库内容失败：{e.data.get('message', str(e))}")
        except Exception as e:
            raise GitHubError(f"处理仓库内容时出错：{str(e)}")
    
    def get_file_content_batch(self, owner, repo_name, file_paths, branch=None):
        """批量获取文件内容"""
        try:
            repo = self.github.get_repo(f"{owner}/{repo_name}")
            
            if not branch:
                branch = repo.default_branch
            
            results = []
            
            for i, file_path in enumerate(file_paths):
                # 检查缓存
                cache_key = f"file_{owner}_{repo_name}_{branch}_{file_path.replace('/', '_')}"
                cached = self._get_from_cache(cache_key)
                if cached:
                    results.append(cached)
                    continue
                
                try:
                    # 添加延迟避免触发限制
                    if i > 0:  # 第一个文件不需要延迟
                        time.sleep(self.request_delay)
                    
                    self._wait_for_rate_limit()
                    content = repo.get_contents(file_path, ref=branch)
                    
                    # 检查文件大小
                    if content.size > Config.MAX_SINGLE_FILE_SIZE_MB * 1024 * 1024:
                        result = {
                            'path': file_path,
                            'content': f"[文件过大: {content.size / (1024*1024):.1f}MB > {Config.MAX_SINGLE_FILE_SIZE_MB}MB]",
                            'size': content.size,
                            'is_binary': False,
                            'is_oversized': True
                        }
                    else:
                        # 尝试解码文件内容
                        try:
                            if content.encoding == 'base64':
                                decoded_content = base64.b64decode(content.content).decode('utf-8')
                            else:
                                decoded_content = content.content
                            
                            result = {
                                'path': file_path,
                                'content': decoded_content,
                                'size': content.size,
                                'is_binary': False,
                                'is_oversized': False
                            }
                        except UnicodeDecodeError:
                            result = {
                                'path': file_path,
                                'content': f"[二进制文件或编码无法识别: {file_path}]",
                                'size': content.size,
                                'is_binary': True,
                                'is_oversized': False
                            }
                    
                    # 保存到缓存
                    self._save_to_cache(cache_key, result)
                    results.append(result)
                    
                except GithubException as e:
                    if e.status == 403 and 'abuse detection' in str(e):
                        # 触发恶意检测，等待更长时间
                        print(f"触发API限制，等待30秒后重试 {file_path}")
                        time.sleep(30)
                        # 重试一次
                        try:
                            content = repo.get_contents(file_path, ref=branch)
                            # ... 重复解码逻辑
                        except:
                            # 如果重试仍然失败，记录错误并继续
                            result = {
                                'path': file_path,
                                'content': f"[获取文件内容失败: API限制]",
                                'size': 0,
                                'is_binary': False,
                                'is_oversized': False
                            }
                    else:
                        result = {
                            'path': file_path,
                            'content': f"[获取文件内容失败: {str(e)}]",
                            'size': 0,
                            'is_binary': False,
                            'is_oversized': False
                        }
                    results.append(result)
                
                except Exception as e:
                    result = {
                        'path': file_path,
                        'content': f"[处理文件时出错: {str(e)}]",
                        'size': 0,
                        'is_binary': False,
                        'is_oversized': False
                    }
                    results.append(result)
            
            return results
            
        except Exception as e:
            raise GitHubError(f"批量获取文件失败：{str(e)}")
    
    def get_file_content(self, owner, repo_name, file_path, branch='main'):
        """获取单个文件内容（兼容性方法）"""
        results = self.get_file_content_batch(owner, repo_name, [file_path], branch)
        return results[0] if results else None
    
    def list_repository_contents(self, owner, repo_name, branch=None):
        """递归获取仓库所有文件列表（使用树API优化）"""
        return self.get_repository_tree(owner, repo_name, branch)
    
    def clear_cache(self):
        """清理缓存"""
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json'):
                    os.remove(os.path.join(self.cache_dir, filename))
        except:
            pass 