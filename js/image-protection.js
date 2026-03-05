/**
 * 图片保护脚本 - 禁止保存图片到本地
 * 功能：禁用右键菜单、禁用拖拽、禁用快捷键保存
 */

(function() {
    'use strict';

    // 禁用右键菜单
    document.addEventListener('contextmenu', function(e) {
        // 检查是否点击了图片
        if (e.target.tagName === 'IMG' || 
            e.target.closest('img') ||
            e.target.classList.contains('character-avatar') ||
            e.target.classList.contains('gallery-image') ||
            e.target.classList.contains('faction-emblem') ||
            e.target.classList.contains('branch-icon')) {
            e.preventDefault();
            e.stopPropagation();
            return false;
        }
    }, true);

    // 禁用拖拽图片
    document.addEventListener('dragstart', function(e) {
        if (e.target.tagName === 'IMG' || 
            e.target.closest('img') ||
            e.target.classList.contains('character-avatar') ||
            e.target.classList.contains('gallery-image') ||
            e.target.classList.contains('faction-emblem') ||
            e.target.classList.contains('branch-icon')) {
            e.preventDefault();
            e.stopPropagation();
            return false;
        }
    }, true);

    // 禁用鼠标中键点击（新标签页打开图片）
    document.addEventListener('auxclick', function(e) {
        if (e.button === 1) { // 鼠标中键
            if (e.target.tagName === 'IMG' || e.target.closest('img')) {
                e.preventDefault();
                e.stopPropagation();
                return false;
            }
        }
    }, true);

    // 禁用快捷键保存
    document.addEventListener('keydown', function(e) {
        // Ctrl+S / Cmd+S - 保存页面
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            e.preventDefault();
            e.stopPropagation();
            return false;
        }

        // Ctrl+Shift+S / Cmd+Shift+S - 另存为
        if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'S') {
            e.preventDefault();
            e.stopPropagation();
            return false;
        }

        // Ctrl+U / Cmd+U - 查看源代码
        if ((e.ctrlKey || e.metaKey) && e.key === 'u') {
            e.preventDefault();
            e.stopPropagation();
            return false;
        }

        // F12 - 开发者工具
        if (e.key === 'F12') {
            e.preventDefault();
            e.stopPropagation();
            return false;
        }

        // Ctrl+Shift+I / Cmd+Shift+I - 开发者工具
        if ((e.ctrlKey || e.metaKey) && e.shiftKey && (e.key === 'I' || e.key === 'i')) {
            e.preventDefault();
            e.stopPropagation();
            return false;
        }

        // Ctrl+Shift+J / Cmd+Shift+J - 控制台
        if ((e.ctrlKey || e.metaKey) && e.shiftKey && (e.key === 'J' || e.key === 'j')) {
            e.preventDefault();
            e.stopPropagation();
            return false;
        }

        // Ctrl+Shift+C / Cmd+Shift+C - 检查元素
        if ((e.ctrlKey || e.metaKey) && e.shiftKey && (e.key === 'C' || e.key === 'c')) {
            e.preventDefault();
            e.stopPropagation();
            return false;
        }
    }, true);

    // 禁用打印
    document.addEventListener('keydown', function(e) {
        // Ctrl+P / Cmd+P - 打印
        if ((e.ctrlKey || e.metaKey) && e.key === 'p') {
            e.preventDefault();
            e.stopPropagation();
            return false;
        }
    }, true);

    // 禁用复制图片
    document.addEventListener('copy', function(e) {
        if (e.target.tagName === 'IMG' || e.target.closest('img')) {
            e.preventDefault();
            e.stopPropagation();
            return false;
        }
    }, true);

    // 禁用剪切图片
    document.addEventListener('cut', function(e) {
        if (e.target.tagName === 'IMG' || e.target.closest('img')) {
            e.preventDefault();
            e.stopPropagation();
            return false;
        }
    }, true);

    // 保护图片 - 动态添加的图片也需要保护
    function protectImages() {
        const images = document.querySelectorAll('img, .character-avatar, .gallery-image, .faction-emblem, .branch-icon, [class*="avatar"], [class*="image"]');
        images.forEach(function(img) {
            // 禁用右键
            img.oncontextmenu = function() { return false; };
            // 禁用拖拽
            img.ondragstart = function() { return false; };
            // 禁用选择
            img.onselectstart = function() { return false; };
            // 禁用触摸长按（移动端）
            img.ontouchstart = function() { return false; };
        });
    }

    // 页面加载完成后执行
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', protectImages);
    } else {
        protectImages();
    }

    // 使用 MutationObserver 监视动态添加的图片
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            mutation.addedNodes.forEach(function(node) {
                if (node.nodeType === 1) { // Element node
                    if (node.tagName === 'IMG' || 
                        node.classList.contains('character-avatar') ||
                        node.classList.contains('gallery-image') ||
                        node.classList.contains('faction-emblem') ||
                        node.classList.contains('branch-icon')) {
                        node.oncontextmenu = function() { return false; };
                        node.ondragstart = function() { return false; };
                        node.onselectstart = function() { return false; };
                    }
                    // 检查子元素
                    if (node.querySelectorAll) {
                        const images = node.querySelectorAll('img, .character-avatar, .gallery-image, .faction-emblem, .branch-icon');
                        images.forEach(function(img) {
                            img.oncontextmenu = function() { return false; };
                            img.ondragstart = function() { return false; };
                            img.onselectstart = function() { return false; };
                        });
                    }
                }
            });
        });
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true
    });

    // 控制台警告
    console.log('%c⚠️ 图片保护已启用', 'color: #22d3ee; font-size: 14px; font-weight: bold;');
    console.log('%c本页面的图片受版权保护，禁止未经授权的保存和使用。', 'color: #fbbf24; font-size: 12px;');

})();
