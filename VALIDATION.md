# 实际验收记录

执行环境：Python 3.12、Node.js 24；2026-10-27。

- `PYTHONPATH=/tmp/logcat-deps:. python -m pytest -q`：7 passed，1.01s。一个上游 TestClient/httpx 弃用提示。
- `cd frontend && npm test`：2 passed，Vitest 3.2.7。
- `cd frontend && npm run build`：TypeScript 检查和 Vite 生产构建通过；ECharts 包大于 500 KB 的体积提示。
- `PYTHONPATH=/tmp/logcat-deps:. python tests/benchmark.py`：生成两份 100000 / 40000 行数据，140000 条记录完整聚合；导入 77.451 秒，聚合 1.206 秒，1936 点。这是分桶上限修复之前的测量；最终算法增加基数检查，不可直接将该聚合耗时当作最终版本保证。

## 三个独立核心环节

1. 解析：验证子模块开头提取、点号名称、首组括号、中间括号、未分类、非法日期、堆栈保留、年份和时区换算。
2. 筛选：验证单/多 Tag，多个子模块、未分类、空选择、同名交叉、Level 与关键词；前端验证父级部分/全选和不同 Tag 的同名子模块独立。
3. 时间线：验证 1ms/1s/1min 聚合总数，分桶时间范围回查，原始同毫秒记录和乱序记录完整保留；API 验证分页查询、原文上下文和 JSON 导出。

浏览器实际点击、拖动缩放和视觉效果尚未做自动化端到端验收，不能把 API 范围测试当作浏览器交互通过。未测试百万行、高基数轨道或所有浏览器。
