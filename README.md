# Logcat Analyzer

本地 Android threadtime 日志分析工具。FastAPI + SQLite，React + TypeScript + Vite + ECharts。开发计划见 PLAN.md。

## 安装与运行

需要 Python 3.11+、Node.js 20.19+，建议 Node.js 22。

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd frontend
npm ci
cd ..
./start.sh
```

打开 http://127.0.0.1:5173 。API 文档：http://127.0.0.1:8000/docs 。默认数据库为启动目录的 `logcat.sqlite`，首次查询自动初始化；可用 `LOGCAT_DB=/absolute/path.sqlite` 指定。服务仅绑定本机。

## 使用

1. 输入日志的明确年份和 IANA 时区（例如 Asia/Shanghai），导入一个或多个 .log/.txt。示例见 examples/sample.log。
2. 勾选来源文件；树中 Tag 全选包含未分类，子模块可跨 Tag 多选。清空选择表示零条匹配。
3. 输入关键词、Level、UTC ISO 时间范围。表格、统计、密度与轨道共用后端筛选。
4. 图表支持拖动和滑块缩放，点击桶筛选该时间范围；重置时间恢复范围。表格点击行查看前后各十行原文。
5. 查看文件失败行，或导出全部当前匹配结果为 CSV / JSON。

## 数据与契约

`POST /api/import` multipart: file/year/timezone；`GET /api/files`；`POST /api/tree`：file_ids；`POST /api/logs`、`/api/timeline`、`/api/stats`、`/api/export/{csv|json}` 共用 JSON：

```json
{"file_ids":["文件UUID"],"filters":[{"tag":"GameAssist","submodules":["TileHost",null]},{"tag":"GCloud","submodules":null}],"start":null,"end":null,"levels":[],"keyword":"","offset":0,"limit":100}
```

时间为 UTC epoch 毫秒、区间两端包含。null 子模块列表表示全部，列表内 null 表示未分类；空列表不匹配。SQL 参数绑定，Tag 与子模块组合 OR。分页最大 200。时间排序相同时按文件 UUID、源序号稳定排序；UUID 排序不代表跨文件因果关系。

基础解析先于子模块提取，只提取开头第一组非空方括号；message 完整保存，message_body 移除前缀，raw_line 保存去掉换行符的源行。错误/堆栈行完整保留，可通过 `/api/errors/{file_id}?offset=0` 分页访问。上下文 `/api/context/{record_id}` 不受筛选影响。

流式读取与每 2000 行批量 SQL，在单个事务中原子导入。重复导入独立 UUID，重复记录不去重；同名文件独立。数据库索引覆盖文件/时间、文件/Tag/子模块/时间和源位置。聚合在数据库执行，自动放大分桶避免大多数情况下超过 2000 点；极端高基数子模块时最少每组一项，可能超过此阈值。

年份不自动猜测或跨年递增；跨年文件需拆分并分别指定年份。DST 歧义/不存在时间保留为失败行。UTF-8 解码损坏字节替换为 U+FFFD。文件末尾若字段完整但消息被截断，无法可靠判断，不擅自报错。

## 验证

```bash
python -m pytest -v
cd frontend
npm test
npm run build
cd ..
python tests/benchmark.py  # 运行时请设置 PYTHONPATH=.
```

实际测试和性能结果见 VALIDATION.md。没有找到需求中两份真实日志，使用提供的 fixture 和生成数据。

## 当前限制

- 导入显示进行中及最终报告，尚无逐行百分比/取消导入；同步请求不适合极慢存储。
- 轨道可切换 Tag 聚合和子模块展开，但尚不能在同一图中逐 Tag 独立折叠；合并日志序列在下方表格查看。
- 时间差是当前分页内相邻记录之差，第一页首行不查询前一页。
- 失败行界面目前只显示前 100 行，API 支持分页。
- 前端目前主要组件集中在 main.tsx，仍需要进一步拆分职责；尚无浏览器端端到端自动化测试。
- CSV 导出保留原始文本；在电子表格软件打开不可信日志时应使用文本导入以避免公式解释。
- 深分页使用 OFFSET；百万行、高基数组合的 UI 流畅性尚未验收。
- ECharts 完整包造成构建体积提示；不影响本地使用。

本版不含 AI、账号、云存储、自定义解析规则或因果推断。
