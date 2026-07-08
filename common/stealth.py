"""Playwright 反检测 — 隐藏无头浏览器自动化痕迹。

page.add_init_script() 在页面任何脚本执行前注入 JS，
重写被检测的属性，使无头浏览器被识别为正常 Chrome。
"""

# 覆盖最常见的 4 个检测点
STEALTH_JS = """
// 1. 隐藏 webdriver 标记
Object.defineProperty(navigator, 'webdriver', { get: () => false });

// 2. 伪造 chrome 对象
window.chrome = { runtime: {}, loadTimes: function() {}, csi: function() {} };

// 3. 伪造 plugins（正常 Chrome 最少有 3 个内置插件）
Object.defineProperty(navigator, 'plugins', {
    get: () => {
        const plugins = [
            { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
            { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
            { name: 'Native Client', filename: 'internal-nacl-plugin' },
        ];
        plugins.item = (i) => plugins[i];
        plugins.namedItem = (n) => plugins.find(p => p.name === n);
        plugins.refresh = () => {};
        Object.setPrototypeOf(plugins, PluginArray.prototype);
        return plugins;
    }
});

// 4. 伪造 languages
Object.defineProperty(navigator, 'languages', {
    get: () => ['zh-CN', 'zh', 'en-US', 'en']
});

// 5. 伪造 permissions（防止权限检测）
const origQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (parameters) => (
    parameters.name === 'notifications' ?
        Promise.resolve({ state: Notification.permission }) :
        origQuery(parameters)
);
"""


def apply_stealth(page):
    """对 Playwright Page 对象应用反检测脚本。

    必须在 page.goto() 之前调用。

    Args:
        page: Playwright Page 对象
    """
    page.add_init_script(STEALTH_JS)
