/**
 * Fluent2 Design Dialog Component
 * 用于替代浏览器原生的 confirm() 和 alert()
 */

// 注入对话框样式
(function() {
    if (document.getElementById('fluent2-dialog-styles')) return;
    const style = document.createElement('style');
    style.id = 'fluent2-dialog-styles';
    style.textContent = `
        .fluent2-dialog-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.4);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10000;
            opacity: 0;
            transition: opacity 0.2s ease;
            padding: 20px;
        }
        
        .fluent2-dialog-overlay.visible {
            opacity: 1;
        }
        
        .fluent2-dialog {
            background: #ffffff;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.14);
            max-width: 400px;
            width: 100%;
            transform: scale(0.95) translateY(10px);
            transition: transform 0.2s ease;
            overflow: hidden;
        }
        
        .fluent2-dialog-overlay.visible .fluent2-dialog {
            transform: scale(1) translateY(0);
        }
        
        .fluent2-dialog-body {
            padding: 24px 24px 16px;
        }
        
        .fluent2-dialog-title {
            font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
            font-size: 18px;
            font-weight: 600;
            color: #1a1a1a;
            margin: 0 0 12px 0;
            line-height: 1.3;
        }
        
        .fluent2-dialog-content {
            font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
            font-size: 14px;
            color: #424242;
            margin: 0;
            line-height: 1.5;
        }
        
        .fluent2-dialog-footer {
            display: flex;
            justify-content: flex-end;
            gap: 8px;
            padding: 16px 24px 24px;
        }
        
        .fluent2-dialog-btn {
            font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
            font-size: 14px;
            font-weight: 500;
            padding: 8px 20px;
            border-radius: 6px;
            border: none;
            cursor: pointer;
            transition: background-color 0.1s ease, transform 0.1s ease;
            min-width: 64px;
        }
        
        .fluent2-dialog-btn:active {
            transform: scale(0.98);
        }
        
        .fluent2-dialog-btn-primary {
            background: #0078d4;
            color: white;
        }
        
        .fluent2-dialog-btn-primary:hover {
            background: #106ebe;
        }
        
        .fluent2-dialog-btn-secondary {
            background: #f5f5f5;
            color: #424242;
        }
        
        .fluent2-dialog-btn-secondary:hover {
            background: #e0e0e0;
        }
        
        .fluent2-dialog-btn-danger {
            background: #d13438;
            color: white;
        }
        
        .fluent2-dialog-btn-danger:hover {
            background: #a4262c;
        }
        
        /* 暗色主题支持 */
        @media (prefers-color-scheme: dark) {
            .fluent2-dialog {
                background: #2d2d2d;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.28);
            }
            
            .fluent2-dialog-title {
                color: #ffffff;
            }
            
            .fluent2-dialog-content {
                color: #d1d1d1;
            }
            
            .fluent2-dialog-btn-secondary {
                background: #404040;
                color: #ffffff;
            }
            
            .fluent2-dialog-btn-secondary:hover {
                background: #505050;
            }
        }
    `;
    document.head.appendChild(style);
})();

/**
 * 显示确认对话框
 * @param {string} message - 提示信息
 * @param {string} title - 标题（可选，默认"确认"）
 * @param {object} options - 配置选项
 * @returns {Promise<boolean>} 用户选择的结果
 */
function fluentConfirm(message, title = '确认', options = {}) {
    return new Promise((resolve) => {
        const overlay = document.createElement('div');
        overlay.className = 'fluent2-dialog-overlay';
        
        const confirmText = options.confirmText || '确定';
        const cancelText = options.cancelText || '取消';
        const dangerMode = options.dangerMode || false;
        
        const confirmBtnClass = dangerMode ? 'fluent2-dialog-btn fluent2-dialog-btn-danger' : 'fluent2-dialog-btn fluent2-dialog-btn-primary';
        
        overlay.innerHTML = `
            <div class="fluent2-dialog">
                <div class="fluent2-dialog-body">
                    <h2 class="fluent2-dialog-title">${escapeDialogHtml(title)}</h2>
                    <p class="fluent2-dialog-content">${escapeDialogHtml(message)}</p>
                </div>
                <div class="fluent2-dialog-footer">
                    <button class="fluent2-dialog-btn fluent2-dialog-btn-secondary" data-action="cancel">${escapeDialogHtml(cancelText)}</button>
                    <button class="${confirmBtnClass}" data-action="confirm">${escapeDialogHtml(confirmText)}</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(overlay);
        
        // 动画显示
        requestAnimationFrame(() => {
            overlay.classList.add('visible');
        });
        
        function close(result) {
            overlay.classList.remove('visible');
            setTimeout(() => {
                overlay.remove();
                resolve(result);
            }, 200);
        }
        
        overlay.querySelector('[data-action="cancel"]').addEventListener('click', () => close(false));
        overlay.querySelector('[data-action="confirm"]').addEventListener('click', () => close(true));
        
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) close(false);
        });
        
        document.addEventListener('keydown', function handler(e) {
            if (e.key === 'Escape') {
                document.removeEventListener('keydown', handler);
                close(false);
            }
        });
    });
}

/**
 * 显示提示对话框
 * @param {string} message - 提示信息
 * @param {string} title - 标题（可选，默认"提示"）
 * @returns {Promise<void>}
 */
function fluentAlert(message, title = '提示') {
    return new Promise((resolve) => {
        const overlay = document.createElement('div');
        overlay.className = 'fluent2-dialog-overlay';
        
        overlay.innerHTML = `
            <div class="fluent2-dialog">
                <div class="fluent2-dialog-body">
                    <h2 class="fluent2-dialog-title">${escapeDialogHtml(title)}</h2>
                    <p class="fluent2-dialog-content">${escapeDialogHtml(message)}</p>
                </div>
                <div class="fluent2-dialog-footer">
                    <button class="fluent2-dialog-btn fluent2-dialog-btn-primary" data-action="ok">确定</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(overlay);
        
        requestAnimationFrame(() => {
            overlay.classList.add('visible');
        });
        
        function close() {
            overlay.classList.remove('visible');
            setTimeout(() => {
                overlay.remove();
                resolve();
            }, 200);
        }
        
        overlay.querySelector('[data-action="ok"]').addEventListener('click', close);
        
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) close();
        });
        
        document.addEventListener('keydown', function handler(e) {
            if (e.key === 'Enter' || e.key === 'Escape') {
                document.removeEventListener('keydown', handler);
                close();
            }
        });
    });
}

/**
 * 显示输入对话框
 * @param {string} message - 提示信息
 * @param {string} title - 标题（可选，默认"输入"）
 * @param {string} defaultValue - 默认值（可选）
 * @returns {Promise<string|null>} 用户输入的值，取消返回 null
 */
function fluentPrompt(message, title = '输入', defaultValue = '') {
    return new Promise((resolve) => {
        const overlay = document.createElement('div');
        overlay.className = 'fluent2-dialog-overlay';
        
        overlay.innerHTML = `
            <div class="fluent2-dialog">
                <div class="fluent2-dialog-body">
                    <h2 class="fluent2-dialog-title">${escapeDialogHtml(title)}</h2>
                    <p class="fluent2-dialog-content">${escapeDialogHtml(message)}</p>
                    <input type="text" class="fluent2-dialog-input" value="${escapeDialogHtml(defaultValue)}" style="
                        width: 100%;
                        margin-top: 12px;
                        padding: 10px 12px;
                        border: 1px solid #d1d1d1;
                        border-radius: 6px;
                        font-size: 14px;
                        font-family: inherit;
                        outline: none;
                        transition: border-color 0.2s;
                        box-sizing: border-box;
                    ">
                </div>
                <div class="fluent2-dialog-footer">
                    <button class="fluent2-dialog-btn fluent2-dialog-btn-secondary" data-action="cancel">取消</button>
                    <button class="fluent2-dialog-btn fluent2-dialog-btn-primary" data-action="confirm">确定</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(overlay);
        
        const input = overlay.querySelector('.fluent2-dialog-input');
        
        requestAnimationFrame(() => {
            overlay.classList.add('visible');
            input.focus();
            input.select();
        });
        
        input.addEventListener('focus', () => {
            input.style.borderColor = '#0078d4';
        });
        
        input.addEventListener('blur', () => {
            input.style.borderColor = '#d1d1d1';
        });
        
        function close(result) {
            overlay.classList.remove('visible');
            setTimeout(() => {
                overlay.remove();
                resolve(result);
            }, 200);
        }
        
        overlay.querySelector('[data-action="cancel"]').addEventListener('click', () => close(null));
        overlay.querySelector('[data-action="confirm"]').addEventListener('click', () => close(input.value));
        
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') close(input.value);
            if (e.key === 'Escape') close(null);
        });
        
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) close(null);
        });
    });
}

/**
 * HTML 转义（对话框内部使用）
 */
function escapeDialogHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
