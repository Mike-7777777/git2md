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
import uuid
from threading import Thread
import shutil

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

# 任务存储
tasks = {}

def process_export_task(task_id, params, logger):
    """在后台线程中处理导出任务"""
    try:
        tasks[task_id]['status'] = 'processing'
        tasks[task_id]['progress'] = 0
        tasks[task_id]['stage'] = '初始化'
        
        github_handler = GitHubHandler()
        
        def progress_callback(processed, total):
            progress = int((processed / total) * 100)
            tasks[task_id]['progress'] = progress
            if progress < 100:
                tasks[task_id]['stage'] = f'下载文件 {processed}/{total}'
            else:
                tasks[task_id]['stage'] = '合并文件'

        # 获取文件列表
        tasks[task_id]['stage'] = '获取文件列表'
        files = github_handler.list_repository_contents(
            params['owner'], params['repo'], params['branch']
        )
        
        # 过滤
        file_processor = FileProcessor(
            file_types=params['file_types'],
            exclude_names=params['exclude_names'],
            exclude_dirs=params['exclude_dirs'],
            use_default_filters=params.get('use_default_filters', False)
        )
        filtered_files = file_processor.filter_files(files)
        
        if not filtered_files:
            raise Exception("没有符合条件的文件")

        # 获取文件内容
        file_paths = [f['path'] for f in filtered_files]
        files_content = github_handler.get_file_content_batch(
            params['owner'], params['repo'], file_paths, params['branch'], progress_callback
        )
        
        output_mode = params.get('output_mode', 'single')

        if output_mode == 'split' and params['output_format'] == 'md':
            tasks[task_id]['stage'] = '切分并保存文件'
            saved_file_info = file_processor.save_split_files(
                files_content, params['repo'], params['output_format']
            )
            
            # 将文件夹打包成zip
            tasks[task_id]['stage'] = '压缩文件'
            folder_to_zip = saved_file_info['file_path']
            zip_filename = f"{saved_file_info['file_name']}.zip"
            zip_filepath = os.path.join(Config.DOWNLOAD_FOLDER, zip_filename)
            
            shutil.make_archive(os.path.join(Config.DOWNLOAD_FOLDER, saved_file_info['file_name']), 'zip', folder_to_zip)
            
            # 删除原文件夹
            shutil.rmtree(folder_to_zip)

            tasks[task_id]['status'] = 'success'
            tasks[task_id]['result'] = {
                'file_count': saved_file_info['file_count'],
                'download_url': f'/download_folder/{zip_filename}',
                'file_size': os.path.getsize(zip_filepath),
                'output_mode': 'split'
            }
        else:
            # 合并
            tasks[task_id]['stage'] = '合并内容'
            merged_content, total_size = file_processor.merge_files_content(
                files_content, params['output_format'], params['repo']
            )

            # 保存
            tasks[task_id]['stage'] = '保存文件'
            output_filename = file_processor.generate_output_filename(
                params['repo'], params['output_format']
            )
            saved_file_info = file_processor.save_merged_file(merged_content, output_filename)
            
            tasks[task_id]['status'] = 'success'
            tasks[task_id]['result'] = {
                'download_url': f'/files/{output_filename}',
                'file_size': saved_file_info['file_size'],
                'file_count': len(files_content),
                'output_mode': 'single'
            }

    except Exception as e:
        logger.exception(f"任务 {task_id} 失败")
        tasks[task_id]['status'] = 'error'
        tasks[task_id]['message'] = str(e)


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
    """开始一个导出任务"""
    start_time = time.time()
    
    try:
        params = request.json
        if not params:
            return jsonify({'status': 'error', 'message': '无效的请求'}), 400
        
        logger.info(f"收到下载请求: {params}")

        # 参数校验
        try:
            validated_params = Validator.validate_all_params(params)
        except ValidationError as e:
            logger.warning(f"参数校验失败: {str(e)}")
            return jsonify({'status': 'error', 'message': str(e)}), 400

        # 获取仓库信息以确定默认分支
        github_handler = GitHubHandler()
        try:
            repo_info = github_handler.get_repo_info(validated_params['owner'], validated_params['repo'])
            validated_params['branch'] = repo_info['default_branch']

            if repo_info['private']:
                return jsonify({
                    'status': 'error',
                    'message': '不支持私有仓库'
                }), 400

        except GitHubError as e:
            logger.error(f"获取仓库信息失败: {str(e)}")
            return jsonify({'status': 'error', 'message': str(e)}), 400

        task_id = str(uuid.uuid4())
        tasks[task_id] = {'status': 'pending'}
        
        thread = Thread(target=process_export_task, args=(task_id, validated_params, logger))
        thread.start()
        
        return jsonify({'status': 'processing', 'task_id': task_id})

    except Exception as e:
        logger.error(f"启动任务时发生错误: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': '启动任务失败'
        }), 500

@app.route('/status/<task_id>')
def task_status(task_id):
    """获取任务状态"""
    task = tasks.get(task_id)
    if not task:
        return jsonify({'status': 'error', 'message': '任务不存在'}), 404
    
    return jsonify(task)

@app.route('/files/<path:filename>')
def download_file(filename):
    """下载单个文件"""
    file_path = os.path.join(Config.DOWNLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        abort(404, description="文件未找到或已过期")
    return send_file(file_path, as_attachment=True)


@app.route('/download_folder/<path:filename>')
def download_folder(filename):
    """下载打包的文件夹"""
    file_path = os.path.join(Config.DOWNLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        abort(404, description="文件未找到或已过期")
    return send_file(file_path, as_attachment=True, mimetype='application/zip')


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