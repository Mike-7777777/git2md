class GitHubExporter {
    constructor() {
        this.form = document.getElementById('exportForm');
        this.exportBtn = document.getElementById('exportBtn');
        this.statusArea = document.getElementById('statusArea');
        this.loadingStatus = document.getElementById('loadingStatus');
        this.successStatus = document.getElementById('successStatus');
        this.errorStatus = document.getElementById('errorStatus');
        this.retryBtn = document.getElementById('retryBtn');
        
        this.init();
    }
    
    init() {
        // 绑定事件
        this.form.addEventListener('submit', async (e) => {
            e.preventDefault();

            this.hideAllStatus();
            this.statusArea.style.display = 'block';
            this.loadingStatus.style.display = 'block';
            this.exportBtn.disabled = true;
            this.exportBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 处理中...';

            this.updateProgress(0, '正在初始化...');

            const formData = new FormData(this.form);
            const data = Object.fromEntries(formData.entries());

            try {
                const response = await fetch('/download', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });

                const result = await response.json();

                if (response.ok && result.task_id) {
                    this.pollTaskStatus(result.task_id);
                } else {
                    this.showError(result.message || '启动任务失败');
                }
            } catch (error) {
                this.showError('请求失败，请检查网络连接');
            }
        });
        this.retryBtn.addEventListener('click', this.handleRetry.bind(this));
        
        // 表单重置时隐藏状态区域
        this.form.addEventListener('reset', () => {
            this.hideAllStatus();
        });

        // 默认过滤模板复选框处理
        const useDefaultFilters = document.getElementById('use_default_filters');
        const defaultFiltersInfo = document.getElementById('defaultFiltersInfo');
        
        useDefaultFilters.addEventListener('change', () => {
            if (useDefaultFilters.checked) {
                defaultFiltersInfo.style.display = 'block';
            } else {
                defaultFiltersInfo.style.display = 'none';
            }
        });
    }
    
    async handleSubmit(e) {
        e.preventDefault();
        
        // 获取表单数据
        const formData = new FormData(this.form);
        const data = {
            repo_url: formData.get('repo_url'),
            file_types: formData.get('file_types'),
            exclude_names: formData.get('exclude_names'),
            exclude_dirs: formData.get('exclude_dirs'),
            output_format: formData.get('output_format'),
            output_mode: formData.get('output_mode'),
            use_default_filters: formData.get('use_default_filters') === 'on'
        };
        
        // 验证必填字段
        if (!data.repo_url) {
            this.showError('请输入GitHub仓库URL');
            return;
        }
        
        // 开始处理
        this.showLoading('正在验证仓库信息...');
        this.disableForm();
        
        try {
            const response = await fetch('/download', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (response.ok) {
                if (result.task_id) {
                    this.pollTaskStatus(result.task_id);
                } else {
                     this.showError(result.message || '启动任务失败');
                     this.enableForm();
                }
            } else {
                this.showError(result.message || '处理失败，请稍后重试');
                this.enableForm();
            }
        } catch (error) {
            console.error('Error:', error);
            this.showError('网络错误，请检查网络连接后重试');
            this.enableForm();
        }
    }
    
    handleRetry() {
        this.hideAllStatus();
        this.form.querySelector('#repo_url').focus();
    }
    
    showLoading(message = '正在处理中...') {
        this.hideAllStatus();
        this.statusArea.style.display = 'block';
        this.loadingStatus.style.display = 'block';
        
        const loadingMessage = document.getElementById('loadingMessage');
        loadingMessage.textContent = message;
        
        // 模拟进度消息
        this.simulateProgress();
    }
    
    simulateProgress() {
        const messages = [
            '正在验证仓库信息...',
            '正在获取文件列表...',
            '正在过滤文件...',
            '正在下载文件内容...',
            '正在生成合并文件...',
            '即将完成...'
        ];
        
        let index = 0;
        const loadingMessage = document.getElementById('loadingMessage');
        
        const interval = setInterval(() => {
            if (index < messages.length - 1) {
                index++;
                loadingMessage.textContent = messages[index];
            } else {
                clearInterval(interval);
            }
        }, 1500);
        
        // 保存interval引用，以便在成功或失败时清除
        this.progressInterval = interval;
    }

    pollTaskStatus(taskId) {
        const interval = setInterval(async () => {
            try {
                const response = await fetch(`/status/${taskId}`);
                const result = await response.json();

                if (result.status === 'processing') {
                    this.showLoading(result.stage, result.progress);
                } else {
                    clearInterval(interval);
                    this.enableForm();
                    if (result.status === 'success') {
                        this.showSuccess(result.result);
                    } else {
                        this.showError(result.message);
                    }
                }
            } catch (error) {
                clearInterval(interval);
                this.showError('无法获取任务状态');
                this.enableForm();
            }
        }, 2000);
    }

    updateProgress(percentage, message) {
        const progressFill = this.loadingStatus.querySelector('.progress-fill');
        const loadingMessage = document.getElementById('loadingMessage');
        
        progressFill.style.width = `${percentage}%`;
        loadingMessage.textContent = message;
    }
    
    showSuccess(result) {
        let content;
        const fileSize = (result.file_size / (1024 * 1024)).toFixed(2);

        if (result.output_mode === 'split') {
            content = `
                <h4><i class="fas fa-check-circle"></i> 多文件导出成功 (ZIP压缩包)</h4>
                <p>共处理 ${result.file_count} 个文件，压缩包大小 ${fileSize} MB。</p>
                <a href="${result.download_url}" class="btn btn-success" download>
                    <i class="fas fa-download"></i> 下载ZIP压缩包
                </a>
                <p class="help-text">文件将在30分钟后被删除。</p>
            `;
        } else {
            content = `
                <h4><i class="fas fa-check-circle"></i> 导出成功</h4>
                <p>共处理 ${result.file_count} 个文件，合计 ${fileSize} MB。</p>
                <a href="${result.download_url}" class="btn btn-success" download>
                    <i class="fas fa-download"></i> 下载文件
                </a>
                <p class="help-text">文件将在30分钟后被删除。</p>
            `;
        }
        
        this.resultDiv.innerHTML = `<div class="status-success">${content}</div>`;
        this.resultDiv.style.display = 'block';
    }
    
    showError(message) {
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
        }
        
        this.hideAllStatus();
        this.statusArea.style.display = 'block';
        this.errorStatus.style.display = 'block';
        
        document.getElementById('errorMessage').textContent = message;
        
        // 滚动到错误区域
        this.statusArea.scrollIntoView({ behavior: 'smooth', block: 'center' });
        this.exportBtn.disabled = false;
        this.exportBtn.innerHTML = '<i class="fas fa-download"></i> 开始导出';
    }
    
    hideAllStatus() {
        this.statusArea.style.display = 'none';
        this.loadingStatus.style.display = 'none';
        this.successStatus.style.display = 'none';
        this.errorStatus.style.display = 'none';
    }
    
    disableForm() {
        this.exportBtn.disabled = true;
        this.exportBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 处理中...';
        
        // 禁用所有输入字段
        const inputs = this.form.querySelectorAll('input, button');
        inputs.forEach(input => {
            if (input !== this.exportBtn) {
                input.disabled = true;
            }
        });
    }
    
    enableForm() {
        this.exportBtn.disabled = false;
        this.exportBtn.innerHTML = '<i class="fas fa-download"></i> 开始导出';
        
        // 启用所有输入字段
        const inputs = this.form.querySelectorAll('input, button');
        inputs.forEach(input => input.disabled = false);
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
    }
    
    showDownloadTip() {
        // 显示下载完成提示
        const tip = document.createElement('div');
        tip.className = 'download-tip';
        tip.innerHTML = `
            <div class="tip-content">
                <i class="fas fa-check-circle"></i>
                <span>文件下载完成！请妥善保存。</span>
            </div>
        `;
        
        // 添加样式
        tip.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #28a745;
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            z-index: 1000;
            animation: slideInRight 0.3s ease;
        `;
        
        document.body.appendChild(tip);
        
        // 3秒后自动移除
        setTimeout(() => {
            tip.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => {
                if (tip.parentNode) {
                    tip.parentNode.removeChild(tip);
                }
            }, 300);
        }, 3000);
    }
}

// 表单验证增强
class FormValidator {
    constructor() {
        this.init();
    }
    
    init() {
        // 实时验证URL格式
        const repoUrlInput = document.getElementById('repo_url');
        repoUrlInput.addEventListener('input', this.validateRepoUrl.bind(this));
        repoUrlInput.addEventListener('blur', this.validateRepoUrl.bind(this));
        
        // 验证其他字段长度
        const textInputs = ['file_types', 'exclude_names', 'exclude_dirs'];
        textInputs.forEach(id => {
            const input = document.getElementById(id);
            input.addEventListener('input', () => this.validateLength(input, 128));
        });
    }
    
    validateRepoUrl(e) {
        const input = e.target;
        const value = input.value.trim();
        
        // 移除之前的错误样式
        input.classList.remove('error');
        this.removeErrorMessage(input);
        
        if (value && !this.isValidGitHubUrl(value)) {
            input.classList.add('error');
            this.showFieldError(input, '请输入有效的GitHub仓库URL');
        }
    }
    
    validateLength(input, maxLength) {
        const value = input.value;
        
        // 移除之前的错误样式
        input.classList.remove('error');
        this.removeErrorMessage(input);
        
        if (value.length > maxLength) {
            input.classList.add('error');
            this.showFieldError(input, `输入内容过长，最多${maxLength}个字符`);
        }
    }
    
    isValidGitHubUrl(url) {
        const githubPattern = /^https:\/\/github\.com\/[\w\-\.]+\/[\w\-\.]+\/?$/;
        return githubPattern.test(url);
    }
    
    showFieldError(input, message) {
        const errorElement = document.createElement('div');
        errorElement.className = 'field-error';
        errorElement.textContent = message;
        errorElement.style.cssText = `
            color: #e74c3c;
            font-size: 14px;
            margin-top: 5px;
            display: block;
        `;
        
        input.parentNode.appendChild(errorElement);
    }
    
    removeErrorMessage(input) {
        const errorElement = input.parentNode.querySelector('.field-error');
        if (errorElement) {
            errorElement.parentNode.removeChild(errorElement);
        }
    }
}

// 添加动画CSS
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    .form-control.error {
        border-color: #e74c3c !important;
        box-shadow: 0 0 0 3px rgba(231, 76, 60, 0.1) !important;
    }
    
    .tip-content {
        display: flex;
        align-items: center;
        gap: 10px;
    }
`;
document.head.appendChild(style);

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    new GitHubExporter();
    new FormValidator();
    
    // 添加一些交互增强
    
    // 表单重置确认
    const resetBtn = document.querySelector('button[type="reset"]');
    resetBtn.addEventListener('click', (e) => {
        if (!confirm('确定要重置表单吗？')) {
            e.preventDefault();
        }
    });
    
    // 快捷键支持
    document.addEventListener('keydown', (e) => {
        // Ctrl/Cmd + Enter 提交表单
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            document.getElementById('exportForm').dispatchEvent(new Event('submit'));
        }
        
        // ESC 键隐藏状态区域
        if (e.key === 'Escape') {
            const statusArea = document.getElementById('statusArea');
            if (statusArea.style.display !== 'none') {
                statusArea.style.display = 'none';
            }
        }
    });
    
    // 添加工具提示
    const helpTexts = document.querySelectorAll('.help-text');
    helpTexts.forEach(helpText => {
        helpText.addEventListener('click', () => {
            helpText.style.backgroundColor = '#f0f8ff';
            setTimeout(() => {
                helpText.style.backgroundColor = '';
            }, 1000);
        });
    });
}); 