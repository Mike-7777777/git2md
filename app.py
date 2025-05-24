import os
import time
import logging
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, send_file, abort
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from config import Config
from utils.validator import Validator, ValidationError
from utils.github_handler import GitHubHandler, GitHubError
from utils.file_processor import FileProcessor
import requests

# 加载.env文件
load_dotenv()

# 创建Flask应用
app = Flask(__name__)
app.config.from_object(Config)
Config.init_app(app)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 初始化定时任务调度器
scheduler = BackgroundScheduler()
scheduler.start()

def cleanup_old_files():
    """清理过期的下载文件"""
    try:
        if not os.path.exists(Config.DOWNLOAD_FOLDER):
            return
        
        cutoff_time = datetime.now() - timedelta(minutes=Config.FILE_RETENTION_MINUTES)
        
        for filename in os.listdir(Config.DOWNLOAD_FOLDER):
            file_path = os.path.join(Config.DOWNLOAD_FOLDER, filename)
            if os.path.isfile(file_path):
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                if file_time < cutoff_time:
                    try:
                        os.remove(file_path)
                        logger.info(f"清理过期文件: {filename}")
                    except Exception as e:
                        logger.error(f"清理文件失败 {filename}: {str(e)}")
    except Exception as e:
        logger.error(f"清理任务执行失败: {str(e)}")

# 添加定时清理任务（每5分钟执行一次）
scheduler.add_job(
    func=cleanup_old_files,
    trigger="interval",
    minutes=5,
    id='cleanup_files'
)

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    """处理下载请求"""
    start_time = time.time()
    
    try:
        # 获取请求参数
        if request.is_json:
            params = request.get_json()
        else:
            params = request.form.to_dict()
        
        logger.info(f"收到下载请求: {params}")
        
        # 参数校验
        try:
            validated_params = Validator.validate_all_params(params)
        except ValidationError as e:
            logger.warning(f"参数校验失败: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 400
        
        # 初始化GitHub处理器
        github_handler = GitHubHandler()
        
        # 获取仓库信息
        try:
            repo_info = github_handler.get_repo_info(
                validated_params['owner'], 
                validated_params['repo']
            )
            logger.info(f"仓库信息: {repo_info}")
            
            if repo_info['private']:
                return jsonify({
                    'status': 'error',
                    'message': '不支持私有仓库'
                }), 400
                
        except GitHubError as e:
            logger.error(f"获取仓库信息失败: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 400
        
        # 获取文件列表
        try:
            files = github_handler.list_repository_contents(
                validated_params['owner'],
                validated_params['repo'],
                repo_info['default_branch']
            )
            logger.info(f"获取到 {len(files)} 个文件")
            
        except GitHubError as e:
            logger.error(f"获取文件列表失败: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 400
        
        # 过滤文件
        file_processor = FileProcessor(
            file_types=validated_params['file_types'],
            exclude_names=validated_params['exclude_names'],
            exclude_dirs=validated_params['exclude_dirs'],
            use_default_filters=validated_params.get('use_default_filters', False)
        )
        
        filtered_files = file_processor.filter_files(files)
        logger.info(f"过滤后剩余 {len(filtered_files)} 个文件")
        
        if not filtered_files:
            return jsonify({
                'status': 'error',
                'message': '没有符合条件的文件，请检查过滤条件'
            }), 400
        
        # 获取文件内容
        files_content = []
        total_processed_size = 0
        
        # 使用批量处理获取文件内容
        file_paths = [file_info['path'] for file_info in filtered_files]
        
        try:
            logger.info(f"开始批量获取 {len(file_paths)} 个文件的内容")
            files_content = github_handler.get_file_content_batch(
                validated_params['owner'],
                validated_params['repo'],
                file_paths,
                repo_info['default_branch']
            )
            
            # 计算总大小
            for file_content in files_content:
                total_processed_size += file_content.get('size', 0)
                
            logger.info(f"批量处理完成，总文件大小: {total_processed_size} 字节")
            
        except GitHubError as e:
            logger.error(f"批量获取文件内容失败: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 400
        
        # 合并文件内容
        merged_content, _ = file_processor.merge_files_content(
            files_content,
            validated_params['output_format'],
            validated_params['repo']
        )
        
        # 生成文件名并保存
        output_filename = file_processor.generate_output_filename(
            validated_params['repo'],
            validated_params['output_format']
        )
        
        try:
            saved_file_info = file_processor.save_merged_file(merged_content, output_filename)
            
            processing_time = time.time() - start_time
            
            logger.info(f"处理完成: {output_filename}, 耗时: {processing_time:.2f}秒")
            
            return jsonify({
                'status': 'success',
                'download_url': f'/files/{output_filename}',
                'file_size': saved_file_info['file_size'],
                'file_count': len(files_content),
                'processing_time': round(processing_time, 2),
                'message': '导出成功'
            })
            
        except Exception as e:
            logger.error(f"保存文件失败: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': f'保存文件失败: {str(e)}'
            }), 500
    
    except Exception as e:
        logger.error(f"处理请求时发生未知错误: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': '服务器内部错误，请稍后重试'
        }), 500

@app.route('/files/<filename>')
def download_file(filename):
    """下载文件"""
    try:
        file_path = os.path.join(Config.DOWNLOAD_FOLDER, filename)
        
        if not os.path.exists(file_path):
            logger.warning(f"文件不存在: {filename}")
            abort(404)
        
        logger.info(f"下载文件: {filename}")
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/octet-stream'
        )
        
    except Exception as e:
        logger.error(f"下载文件失败 {filename}: {str(e)}")
        abort(500)

@app.route('/admin')
def admin():
    """管理页面"""
    # 获取缓存统计信息
    cache_stats = {
        'cache_size': 0,
        'cache_files': 0,
        'github_token_set': bool(Config.get_github_token())
    }
    
    try:
        cache_dir = Config.CACHE_FOLDER
        if os.path.exists(cache_dir):
            cache_files = [f for f in os.listdir(cache_dir) if f.endswith('.json')]
            cache_stats['cache_files'] = len(cache_files)
            
            total_size = 0
            for filename in cache_files:
                file_path = os.path.join(cache_dir, filename)
                total_size += os.path.getsize(file_path)
            cache_stats['cache_size'] = total_size
    except:
        pass
    
    return render_template('admin.html', cache_stats=cache_stats)

@app.route('/admin/clear-cache', methods=['POST'])
def clear_cache():
    """清理缓存"""
    try:
        github_handler = GitHubHandler()
        github_handler.clear_cache()
        
        logger.info("缓存清理成功")
        return jsonify({
            'status': 'success',
            'message': '缓存清理成功'
        })
    except Exception as e:
        logger.error(f"清理缓存失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'清理缓存失败: {str(e)}'
        }), 500

@app.route('/health')
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'github_token_configured': bool(Config.get_github_token())
    })

@app.route('/settings')
def settings():
    """设置页面"""
    # 获取当前token状态
    current_token = Config.get_github_token()
    if current_token:
        # 脱敏显示token
        current_token_masked = current_token[:8] + '*' * (len(current_token) - 12) + current_token[-4:]
        token_status_class = 'valid'
        token_status_icon = 'fa-check-circle'
        token_status_message = 'Token已配置'
    else:
        current_token_masked = ''
        token_status_class = 'empty'
        token_status_icon = 'fa-exclamation-triangle'
        token_status_message = '未配置Token，API限制为60次/小时'
    
    # 获取API限制信息
    api_limits = get_api_limits(current_token)
    
    # 获取系统统计信息
    system_stats = get_system_stats()
    
    return render_template('settings.html',
                         current_token_masked=current_token_masked,
                         token_status_class=token_status_class,
                         token_status_icon=token_status_icon,
                         token_status_message=token_status_message,
                         api_limits=api_limits,
                         system_stats=system_stats)

@app.route('/settings/token', methods=['POST'])
def save_token():
    """保存GitHub Token"""
    try:
        data = request.get_json()
        token = data.get('token', '').strip()
        
        if token:
            # 验证token有效性
            if not validate_github_token(token):
                return jsonify({
                    'status': 'error',
                    'message': 'Token无效或已过期，请检查权限设置'
                }), 400
        
        # 保存token
        if Config.save_token_to_file(token):
            message = 'Token保存成功' if token else 'Token已清除'
            
            # 获取token信息
            token_info = get_token_info(token) if token else {'valid': False}
            
            return jsonify({
                'status': 'success',
                'message': message,
                'token_info': token_info
            })
        else:
            return jsonify({
                'status': 'error',
                'message': '保存失败，请检查文件权限'
            }), 500
            
    except Exception as e:
        logger.error(f"保存token失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'保存失败: {str(e)}'
        }), 500

@app.route('/settings/token', methods=['DELETE'])
def clear_token():
    """清除GitHub Token"""
    try:
        if Config.save_token_to_file(None):
            return jsonify({
                'status': 'success',
                'message': 'Token已清除'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': '清除失败'
            }), 500
            
    except Exception as e:
        logger.error(f"清除token失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'清除失败: {str(e)}'
        }), 500

@app.route('/settings/test-token', methods=['POST'])
def test_token():
    """测试GitHub Token"""
    try:
        data = request.get_json()
        token = data.get('token', '').strip()
        
        if not token:
            return jsonify({
                'status': 'error',
                'message': '请输入Token'
            }), 400
        
        token_info = get_token_info(token)
        
        if token_info['valid']:
            return jsonify({
                'status': 'success',
                'message': 'Token验证成功',
                'remaining': token_info['remaining'],
                'limit': token_info['limit']
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Token无效或已过期'
            }), 400
            
    except Exception as e:
        logger.error(f"测试token失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'测试失败: {str(e)}'
        }), 500

@app.route('/settings/clear-downloads', methods=['POST'])
def clear_downloads():
    """清理下载文件"""
    try:
        if not os.path.exists(Config.DOWNLOAD_FOLDER):
            return jsonify({
                'status': 'success',
                'message': '下载目录不存在，无需清理'
            })
        
        file_count = 0
        for filename in os.listdir(Config.DOWNLOAD_FOLDER):
            file_path = os.path.join(Config.DOWNLOAD_FOLDER, filename)
            if os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                    file_count += 1
                except Exception as e:
                    logger.warning(f"删除文件失败 {filename}: {str(e)}")
        
        logger.info(f"清理下载文件成功，删除 {file_count} 个文件")
        return jsonify({
            'status': 'success',
            'message': f'清理完成，删除 {file_count} 个文件'
        })
        
    except Exception as e:
        logger.error(f"清理下载文件失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'清理失败: {str(e)}'
        }), 500

def validate_github_token(token):
    """验证GitHub Token是否有效"""
    try:
        headers = {'Authorization': f'token {token}'}
        response = requests.get('https://api.github.com/user', headers=headers, timeout=10)
        return response.status_code == 200
    except Exception:
        return False

def get_token_info(token):
    """获取token信息"""
    if not token:
        return {'valid': False, 'limit': 60, 'remaining': 0}
    
    try:
        headers = {'Authorization': f'token {token}'}
        response = requests.get('https://api.github.com/rate_limit', headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            core = data['rate']
            return {
                'valid': True,
                'limit': core['limit'],
                'remaining': core['remaining'],
                'reset': core['reset']
            }
        else:
            return {'valid': False, 'limit': 60, 'remaining': 0}
    except Exception:
        return {'valid': False, 'limit': 60, 'remaining': 0}

def get_api_limits(token):
    """获取API限制信息"""
    token_info = get_token_info(token)
    
    if token_info['valid']:
        reset_time = datetime.fromtimestamp(token_info['reset']).strftime('%H:%M')
        return {
            'current': token_info['limit'],
            'remaining': token_info['remaining'],
            'reset_time': reset_time
        }
    else:
        return {
            'current': 60,
            'remaining': '未知',
            'reset_time': '每小时'
        }

def get_system_stats():
    """获取系统统计信息"""
    stats = {
        'cache_files': 0,
        'cache_size_mb': 0,
        'download_files': 0
    }
    
    try:
        # 缓存统计
        if os.path.exists(Config.CACHE_FOLDER):
            cache_files = [f for f in os.listdir(Config.CACHE_FOLDER) if f.endswith('.json')]
            stats['cache_files'] = len(cache_files)
            
            total_size = 0
            for filename in cache_files:
                file_path = os.path.join(Config.CACHE_FOLDER, filename)
                total_size += os.path.getsize(file_path)
            stats['cache_size_mb'] = round(total_size / (1024 * 1024), 2)
        
        # 下载文件统计
        if os.path.exists(Config.DOWNLOAD_FOLDER):
            download_files = [f for f in os.listdir(Config.DOWNLOAD_FOLDER) if os.path.isfile(os.path.join(Config.DOWNLOAD_FOLDER, f))]
            stats['download_files'] = len(download_files)
            
    except Exception as e:
        logger.warning(f"获取系统统计失败: {str(e)}")
    
    return stats

@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return jsonify({
        'status': 'error',
        'message': '页面未找到'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    return jsonify({
        'status': 'error',
        'message': '服务器内部错误'
    }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 