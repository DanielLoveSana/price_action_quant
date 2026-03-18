# Price Action Quant - 价格行为学量化分析系统

## 📊 项目状态
**当前阶段**: Phase 1 - 基础因子开发  
**最后更新**: 2026-03-18 10:57 (GMT+8)

## ✅ 已完成
1. **环境搭建** - Python 3.11.13 + 虚拟环境
2. **依赖安装** - 所有核心量化分析库
3. **项目结构** - 模块化目录布局

## 🚀 技术栈
- **Python**: 3.11.13 (从3.6.8升级)
- **数据源**: yfinance, akshare, ccxt
- **分析库**: pandas, numpy, ta, scipy
- **可视化**: matplotlib, plotly, mplfinance, seaborn
- **机器学习**: scikit-learn, statsmodels

## 📁 项目结构
```
price_action_quant/
├── src/                    # 源代码
│   ├── data/              # 数据接入层
│   ├── factors/           # 因子计算层
│   ├── visualization/     # 可视化模块
│   └── utils/             # 工具函数
├── tests/                 # 测试用例
├── docs/                  # 文档
├── venv/                  # Python 3.11虚拟环境
├── requirements_3.11_fixed.txt  # 依赖列表
└── test_environment.py    # 环境测试脚本
```

## 🔧 快速开始
```bash
# 激活虚拟环境
source venv/bin/activate

# 测试环境
python test_environment.py

# 运行示例
python -c "import yfinance as yf; ticker = yf.Ticker('AAPL'); print(f'AAPL: ${ticker.history(period=\"1d\")[\"Close\"].iloc[-1]:.2f}')"
```

## 📋 Phase 1 任务清单
- [x] 1.1 环境搭建 (Python升级+依赖安装)
- [ ] 1.2 数据接入模块 (src/data/)
- [ ] 1.3 市场结构因子 (支撑阻力、趋势线)
- [ ] 1.4 关键价位因子 (高低点、斐波那契)
- [ ] 1.5 基础可视化 (价格图表+因子标记)
- [ ] 1.6 自测验收

## 🎯 核心功能规划
1. **多市场数据接入** (股票、期货、加密货币)
2. **价格行为因子计算** (6大类量化因子)
3. **智能图表分析** (自动标记关键价位)
4. **策略回测框架** (信号生成+绩效评估)
5. **实时监控预警** (价格突破、形态识别)

## 📞 开发日志
- **02:22**: 项目启动，需求分析完成
- **10:57**: Python升级到3.11.13，依赖安装完成
- **11:03**: 开始数据接入模块开发
- **11:10**: 数据模块核心代码完成（基础类、yfinance、akshare、管理器）
- **11:18**: Git仓库初始化完成，准备GitHub同步
- **11:41**: 成功推送到GitHub仓库 `DanielLoveSana/price_action_quant`
- **11:46**: 开始Phase 1.3市场结构因子开发
- **12:03**: Phase 1.3完成！市场结构因子模块实现完成

## 🗂️ 数据模块架构
```
src/data/
├── __init__.py          # 模块导出
├── base.py              # 数据获取基类（缓存、标准化）
├── yfinance_fetcher.py  # 美股/港股/全球市场数据
├── akshare_fetcher.py   # A股市场数据
└── manager.py           # 统一数据管理器
```

### 核心功能
1. **多市场支持**: 自动识别标的类型，选择合适的数据源
2. **智能缓存**: 自动缓存数据，减少API调用
3. **数据标准化**: 统一数据格式，方便后续处理
4. **错误处理**: 完善的异常处理和日志记录
5. **批量操作**: 支持批量获取多个标的的数据

### 使用示例
```python
from src.data.manager import DataManager

# 创建数据管理器
manager = DataManager()

# 获取数据（自动选择数据源）
df = manager.fetch_data("AAPL", "2024-01-01", "2024-01-31")

# 获取实时数据
realtime = manager.fetch_realtime("AAPL")

# 批量获取
symbols = ["AAPL", "MSFT", "GOOGL"]
all_data = manager.fetch_multiple_symbols(symbols, start_date, end_date)
```

### 运行示例
```bash
# 激活虚拟环境
source venv/bin/activate

# 运行数据演示
python examples/data_demo.py

# 运行测试
python -m pytest tests/test_data_module.py -v

# Git工作流
./scripts/git_workflow.sh
```

## 🔄 GitHub同步 ✅ 已完成

### 当前状态
- ✅ Git仓库已初始化
- ✅ 初始提交完成 (Phase 1.2 - 数据模块)
- ✅ .gitignore配置完成
- ✅ 成功推送到 `DanielLoveSana/price_action_quant`

### 仓库信息
- **URL**: https://github.com/DanielLoveSana/price_action_quant
- **分支**: main
- **提交**: 4个 (Phase 1.2 + Phase 1.3完整代码)
- **最新提交**: 0d0f178 - Phase 1.3: Market structure factors complete

### 克隆项目
```bash
git clone https://github.com/DanielLoveSana/price_action_quant.git
cd price_action_quant
python -m venv venv
source venv/bin/activate
pip install -r requirements_3.11_fixed.txt
```

### 阶段提交策略
```
Phase 1.2: 数据模块 ✅ (已推送)
Phase 1.3: 市场结构因子 ✅ (已推送)
Phase 1.4: 关键价位因子 🔄 (开发中)
Phase 1.5: 基础可视化 🔄 (等待)
Phase 1.6: 自测验收 🔄 (等待)
```

---
*项目负责人: 丹尼尔 (超级程序员)*  
*最后验证: 环境测试通过 ✅*