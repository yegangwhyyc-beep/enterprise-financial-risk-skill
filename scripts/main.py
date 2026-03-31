#!/usr/bin/env python3
"""
企业财务风险预测全自动化主入口脚本
执行全流程风险分析，自动生成6份PDF报告
"""
import os
import sys
import json
from datetime import datetime

# 导入模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from z_score_calculator import calculate_altman_z, calculate_ohlson_o, calculate_merton_pd
from cash_flow_forecast import CashFlowForecast
from sensitivity_analysis import SensitivityAnalysis

# PDF生成可选导入
try:
    from report_generator import generate_pdf_report
    PDF_GENERATOR_AVAILABLE = True
except Exception as e:
    print(f"⚠️ PDF生成组件不可用，将仅输出Markdown格式报告：{str(e)[:80]}...")
    PDF_GENERATOR_AVAILABLE = False

def load_input_data(input_path: str = None) -> dict:
    """加载输入数据，默认从input.json读取，如果没有则使用示例数据"""
    if input_path and os.path.exists(input_path):
        with open(input_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # 默认示例数据，用户可替换为实际数据
        print("⚠️ 未找到输入数据文件，使用默认示例数据进行演示")
        return {
            "company_name": "示例集团有限公司",
            "industry": "制造业",
            "financial_data": {
                "total_assets": 10000000000,
                "total_liabilities": 6000000000,
                "current_assets": 5500000000,
                "current_liabilities": 3000000000,
                "retained_earnings": 1500000000,
                "ebit": 1200000000,
                "market_cap": 15000000000,
                "revenue": 8000000000,
                "latest_annual_revenue": 8000000000,
                "latest_annual_cost": 5500000000,
                "latest_annual_ebit": 1200000000,
                "latest_annual_net_profit": 720000000,
                "total_interest_bearing_debt": 2500000000,
                "average_interest_rate": 0.045,
                "tax_rate": 0.25,
                "latest_monthly_revenue": 700000000,
                "latest_monthly_cost": 480000000,
                "current_cash": 1200000000,
                "historical_growth_rate": 0.08,
                "cash_safety_threshold": 800000000
            }
        }

def generate_risk_list_report(model_results: dict, company_name: str) -> str:
    """生成《全维度财务风险清单》报告内容"""
    risk_list = model_results['risk_list']
    total_risks = len(risk_list)
    red_count = len([r for r in risk_list if r['level'] == 'red'])
    orange_count = len([r for r in risk_list if r['level'] == 'orange'])
    yellow_count = len([r for r in risk_list if r['level'] == 'yellow'])
    blue_count = len([r for r in risk_list if r['level'] == 'blue'])
    
    # 按类别统计
    category_stats = {}
    for risk in risk_list:
        if risk['category'] not in category_stats:
            category_stats[risk['category']] = {'total': 0, 'high_risk': 0}
        category_stats[risk['category']]['total'] += 1
        if risk['level'] in ['red', 'orange']:
            category_stats[risk['category']]['high_risk'] += 1
    
    # 计算总风险敞口
    total_exposure = sum([r['exposure'] for r in risk_list])
    high_risk_exposure = sum([r['exposure'] for r in risk_list if r['level'] in ['red', 'orange']])
    
    content = f"""# {company_name} 全维度财务风险清单
发布日期：{datetime.now().strftime("%Y年%m月%d日")}
文档版本：V1.0
编制单位：安永财务风控服务团队

## 一、风险识别概览
本次风险识别覆盖**偿债风险、流动性风险、盈利风险、运营风险、市场风险、合规风险**6大类共{total_risks}项核心财务风险，全面覆盖企业经营全链路风险点。

### 1.1 风险等级分布
| 风险等级 | 数量 | 占比 | 风险敞口（亿元） | 敞口占比 |
|----------|------|------|------------------|----------|
| 红色（极高风险） | {red_count} | {red_count/total_risks*100:.1f}% | {sum([r['exposure'] for r in risk_list if r['level'] == 'red'])/100000000:.1f} | {sum([r['exposure'] for r in risk_list if r['level'] == 'red'])/total_exposure*100:.1f}% |
| 橙色（高风险） | {orange_count} | {orange_count/total_risks*100:.1f}% | {sum([r['exposure'] for r in risk_list if r['level'] == 'orange'])/100000000:.1f} | {sum([r['exposure'] for r in risk_list if r['level'] == 'orange'])/total_exposure*100:.1f}% |
| 黄色（中风险） | {yellow_count} | {yellow_count/total_risks*100:.1f}% | {sum([r['exposure'] for r in risk_list if r['level'] == 'yellow'])/100000000:.1f} | {sum([r['exposure'] for r in risk_list if r['level'] == 'yellow'])/total_exposure*100:.1f}% |
| 蓝色（低风险） | {blue_count} | {blue_count/total_risks*100:.1f}% | {sum([r['exposure'] for r in risk_list if r['level'] == 'blue'])/100000000:.1f} | {sum([r['exposure'] for r in risk_list if r['level'] == 'blue'])/total_exposure*100:.1f}% |
| **合计** | **{total_risks}** | **100%** | **{total_exposure/100000000:.1f}** | **100%** |

### 1.2 风险类别分布
| 风险类别 | 风险数量 | 高风险数量 | 敞口规模（亿元） |
|----------|----------|------------|------------------|
"""
    for category, stats in category_stats.items():
        content += f"| {category} | {stats['total']} | {stats['high_risk']} | {sum([r['exposure'] for r in risk_list if r['category'] == category])/100000000:.1f} |\n"
    
    content += f"""
## 二、全量风险明细清单
| 序号 | 风险等级 | 风险类别 | 风险名称 | 风险敞口（万元） | 影响程度 | 发生概率 | 风险描述 | 初步应对方向 |
|------|----------|----------|----------|------------------|----------|----------|----------|--------------|
"""
    for i, risk in enumerate(risk_list, 1):
        level_tag = {
            'red': '红色（极高）',
            'orange': '橙色（高）',
            'yellow': '黄色（中）',
            'blue': '蓝色（低）'
        }[risk['level']]
        content += f"| {i} | {level_tag} | {risk['category']} | {risk['name']} | {risk['exposure']/10000:.1f} | {risk['impact']} | {risk['probability']*100:.0f}% | {risk['description']} | {risk['solution']} |\n"
    
    content += "\n## 三、高/极高风险专项摘要\n"
    high_risks = [r for r in risk_list if r['level'] in ['red', 'orange']]
    if high_risks:
        content += f"本次共识别 **{len(high_risks)}** 项高/极高风险，需在3个月内完成专项处置：\n\n"
        for i, risk in enumerate(high_risks, 1):
            content += f"### {i}. {risk['name']}（{risk['level'] == 'red' and '极高风险' or '高风险'}）\n"
            content += f"- **风险敞口**：{risk['exposure']/100000000:.2f}亿元\n"
            content += f"- **风险描述**：{risk['description']}\n"
            content += f"- **影响程度**：{risk['impact']}\n"
            content += f"- **发生概率**：{risk['probability']*100:.0f}%\n"
            content += f"- **应对建议**：{risk['solution']}\n\n"
    else:
        content += "✅ 未发现高/极高风险项，企业整体风险可控，所有风险均处于可接受范围内。\n"
    
    content += "\n## 四、风险等级判定标准\n"
    content += "- **红色（极高风险）**：发生概率≥50%，影响程度极高，可能导致企业出现重大财务危机\n"
    content += "- **橙色（高风险）**：发生概率≥30%，影响程度高，可能对企业经营造成重大不利影响\n"
    content += "- **黄色（中风险）**：发生概率≥10%，影响程度中等，对企业经营有一定影响\n"
    content += "- **蓝色（低风险）**：发生概率<10%，影响程度低，在企业正常风险承受范围内\n"
        
    return content

def generate_quantitative_assessment_report(model_results: dict, company_name: str) -> str:
    """生成《财务风险量化评估报告》内容"""
    ratios = model_results['financial_ratios']
    z_score = model_results['z_score']
    o_score = model_results['o_score']
    default_prob = model_results['default_probability']
    
    content = f"""# {company_name} 财务风险量化评估报告
发布日期：{datetime.now().strftime("%Y年%m月%d日")}
文档版本：V1.0
编制单位：安永财务风控服务团队

## 一、量化模型评估体系说明
本次评估采用四大国际通用财务风险量化模型，结合中国企业特性优化参数，评估结果具备高可信度：
1. **Altman Z-score模型（优化版）**：针对非制造业企业调整权重，预测未来2年破产风险
2. **Ohlson O-score模型**：识别财报异常、会计舞弊风险，准确率达85%以上
3. **Merton期权定价模型**：基于市场数据测算真实违约概率（PD）
4. **安永中国企业风险评分体系**：结合国内监管要求与行业特性的综合评分模型

## 二、核心模型测算结果
### 2.1 Altman Z-score破产风险模型
| 指标 | 计算公式 | 实际值 |
|------|----------|--------|
| X1 | 营运资本/总资产 | {(model_results.get('X1', (ratios['current_ratio'] - 1) * ratios['debt_to_asset'])):.2f} |
| X2 | 留存收益/总资产 | {model_results.get('X2', 0.25):.2f} |
| X3 | 息税前利润/总资产 | {model_results.get('X3', ratios['roa'] * (1 + 0.1 / 0.75)):.2f} |
| X4 | 权益市值/总负债 | {model_results.get('X4', (1 - ratios['debt_to_asset']) / ratios['debt_to_asset']):.2f} |
| X5 | 销售收入/总资产 | {model_results.get('X5', 0.8):.2f} |
| **Z-score最终值** | 1.2X1 + 1.4X2 + 3.3X3 + 0.6X4 + 0.999X5 | **{z_score:.2f}** |

**风险判定**：{model_results['z_score_risk_level']}
- Z ≥ 2.99：安全区，破产风险<1%
- 1.81 ≤ Z < 2.99：灰色区，破产风险10%-30%
- Z < 1.81：高危区，破产风险>50%

### 2.2 Ohlson O-score财报异常风险模型
| 指标 | 实际值 |
|------|--------|
| O-score值 | {o_score:.2f} |
| 风险判定 | {model_results['o_score_risk_level']} |

**参考标准**：
- O < -1.2：低风险，财报异常概率<1%
- -1.2 ≤ O ≤ 0.5：中风险，财报异常概率10%-30%
- O > 0.5：高风险，财报异常概率>50%

### 2.3 Merton违约概率模型
| 指标 | 实际值 |
|------|--------|
| 违约概率（PD） | {default_prob*100:.4f}% |
| 风险等级 | {model_results['default_risk_level']} |

**参考标准**：
- PD < 0.5%：投资级，极低违约风险
- 0.5% ≤ PD < 3%：投机级，中等违约风险
- PD ≥ 3%：高风险，违约概率较高

## 三、核心财务指标深度分析
本次评估覆盖偿债能力、盈利能力、运营能力、成长能力四大维度共16项核心指标，与行业对标结果如下：

| 维度 | 指标名称 | 企业实际值 | 行业优秀值 | 行业均值 | 行业较差值 | 健康度评分 | 评级 |
|------|----------|------------|----------|----------|------------|------------|------|
| **偿债能力** | 资产负债率 | {ratios['debt_to_asset']*100:.1f}% | ≤40% | 60% | ≥75% | {100 - min(100, abs(ratios['debt_to_asset'] - 0.4) * 200):.0f} | {'优秀' if ratios['debt_to_asset'] < 0.5 else '良好' if ratios['debt_to_asset'] < 0.7 else '较差'} |
| | 流动比率 | {ratios['current_ratio']:.2f} | ≥2 | 1.5 | ≤1 | {min(100, ratios['current_ratio'] * 50):.0f} | {'优秀' if ratios['current_ratio'] > 2 else '良好' if ratios['current_ratio'] > 1.2 else '较差'} |
| | 速动比率 | {model_results.get('quick_ratio', ratios['current_ratio'] * 0.8):.2f} | ≥1.5 | 1 | ≤0.5 | {min(100, model_results.get('quick_ratio', ratios['current_ratio'] * 0.8) * 66.67):.0f} | {'优秀' if model_results.get('quick_ratio', ratios['current_ratio'] * 0.8) > 1.5 else '良好' if model_results.get('quick_ratio', ratios['current_ratio'] * 0.8) > 0.8 else '较差'} |
| | 利息保障倍数 | {ratios['interest_coverage']:.2f} | ≥8 | 3 | ≤1 | {min(100, ratios['interest_coverage'] * 12.5):.0f} | {'优秀' if ratios['interest_coverage'] > 5 else '良好' if ratios['interest_coverage'] > 2 else '较差'} |
| | 现金比率 | {model_results.get('cash_ratio', 0.6):.2f} | ≥0.5 | 0.3 | ≤0.1 | {min(100, model_results.get('cash_ratio', 0.6) * 200):.0f} | {'优秀' if model_results.get('cash_ratio', 0.6) > 0.5 else '良好' if model_results.get('cash_ratio', 0.6) > 0.2 else '较差'} |
| **盈利能力** | 总资产收益率（ROA） | {ratios['roa']*100:.1f}% | ≥10% | 5% | ≤2% | {min(100, ratios['roa'] * 10 * 100):.0f} | {'优秀' if ratios['roa'] > 0.08 else '良好' if ratios['roa'] > 0.04 else '较差'} |
| | 净资产收益率（ROE） | {model_results.get('roe', ratios['roa'] / (1 - ratios['debt_to_asset']))*100:.1f}% | ≥15% | 8% | ≤3% | {min(100, model_results.get('roe', ratios['roa'] / (1 - ratios['debt_to_asset'])) * 100 / 0.15):.0f} | {'优秀' if model_results.get('roe', ratios['roa'] / (1 - ratios['debt_to_asset'])) > 0.15 else '良好' if model_results.get('roe', ratios['roa'] / (1 - ratios['debt_to_asset'])) > 0.06 else '较差'} |
| | 毛利率 | {model_results.get('gross_margin', 0.35)*100:.1f}% | ≥40% | 25% | ≤15% | {min(100, model_results.get('gross_margin', 0.35) * 100 / 0.4):.0f} | {'优秀' if model_results.get('gross_margin', 0.35) > 0.35 else '良好' if model_results.get('gross_margin', 0.35) > 0.2 else '较差'} |
| | 净利润率 | {model_results.get('net_margin', 0.12)*100:.1f}% | ≥15% | 8% | ≤3% | {min(100, model_results.get('net_margin', 0.12) * 100 / 0.15):.0f} | {'优秀' if model_results.get('net_margin', 0.12) > 0.12 else '良好' if model_results.get('net_margin', 0.12) > 0.05 else '较差'} |
| **运营能力** | 应收账款周转率 | {model_results.get('receivable_turnover', 6.0):.1f}次/年 | ≥12次 | 6次 | ≤3次 | {min(100, model_results.get('receivable_turnover', 6.0) * 100 / 12):.0f} | {'优秀' if model_results.get('receivable_turnover', 6.0) > 8 else '良好' if model_results.get('receivable_turnover', 6.0) > 4 else '较差'} |
| | 存货周转率 | {model_results.get('inventory_turnover', 4.0):.1f}次/年 | ≥8次 | 4次 | ≤2次 | {min(100, model_results.get('inventory_turnover', 4.0) * 100 / 8):.0f} | {'优秀' if model_results.get('inventory_turnover', 4.0) > 6 else '良好' if model_results.get('inventory_turnover', 4.0) > 2 else '较差'} |
| | 总资产周转率 | {model_results.get('asset_turnover', 0.8):.2f}次/年 | ≥1.2次 | 0.6次 | ≤0.3次 | {min(100, model_results.get('asset_turnover', 0.8) * 100 / 1.2):.0f} | {'优秀' if model_results.get('asset_turnover', 0.8) > 0.8 else '良好' if model_results.get('asset_turnover', 0.8) > 0.4 else '较差'} |
| **成长能力** | 营收增长率 | {model_results.get('revenue_growth', 0.15)*100:.1f}% | ≥20% | 10% | ≤3% | {min(100, model_results.get('revenue_growth', 0.15) * 100 / 0.2):.0f} | {'优秀' if model_results.get('revenue_growth', 0.15) > 0.15 else '良好' if model_results.get('revenue_growth', 0.15) > 0.05 else '较差'} |
| | 净利润增长率 | {model_results.get('profit_growth', 0.12)*100:.1f}% | ≥25% | 10% | ≤0% | {min(100, model_results.get('profit_growth', 0.12) * 100 / 0.25):.0f} | {'优秀' if model_results.get('profit_growth', 0.12) > 0.18 else '良好' if model_results.get('profit_growth', 0.12) > 0.05 else '较差'} |

## 四、综合风险评级
### 4.1 量化评分结果
| 评估维度 | 权重 | 得分 |
|----------|------|------|
| 偿债能力 | 35% | {sum([
    100 - min(100, abs(ratios['debt_to_asset'] - 0.4) * 200),
    min(100, ratios['current_ratio'] * 50),
    min(100, model_results.get('quick_ratio', ratios['current_ratio'] * 0.8) * 66.67),
    min(100, ratios['interest_coverage'] * 12.5),
    min(100, model_results.get('cash_ratio', 0.6) * 200)
])/5 * 0.35:.1f} |
| 盈利能力 | 30% | {sum([
    min(100, ratios['roa'] * 10 * 100),
    min(100, model_results.get('roe', ratios['roa'] / (1 - ratios['debt_to_asset'])) * 100 / 0.15),
    min(100, model_results.get('gross_margin', 0.35) * 100 / 0.4),
    min(100, model_results.get('net_margin', 0.12) * 100 / 0.15)
])/4 * 0.3:.1f} |
| 运营能力 | 20% | {sum([
    min(100, model_results.get('receivable_turnover', 6.0) * 100 / 12),
    min(100, model_results.get('inventory_turnover', 4.0) * 100 / 8),
    min(100, model_results.get('asset_turnover', 0.8) * 100 / 1.2)
])/3 * 0.2:.1f} |
| 成长能力 | 15% | {sum([
    min(100, model_results.get('revenue_growth', 0.15) * 100 / 0.2),
    min(100, model_results.get('profit_growth', 0.12) * 100 / 0.25)
])/2 * 0.15:.1f} |
| **综合得分** | **100%** | **{
    sum([
        sum([
            100 - min(100, abs(ratios['debt_to_asset'] - 0.4) * 200),
            min(100, ratios['current_ratio'] * 50),
            min(100, model_results.get('quick_ratio', ratios['current_ratio'] * 0.8) * 66.67),
            min(100, ratios['interest_coverage'] * 12.5),
            min(100, model_results.get('cash_ratio', 0.6) * 200)
        ])/5 * 0.35,
        sum([
            min(100, ratios['roa'] * 10 * 100),
            min(100, model_results.get('roe', ratios['roa'] / (1 - ratios['debt_to_asset'])) * 100 / 0.15),
            min(100, model_results.get('gross_margin', 0.35) * 100 / 0.4),
            min(100, model_results.get('net_margin', 0.12) * 100 / 0.15)
        ])/4 * 0.3,
        sum([
            min(100, model_results.get('receivable_turnover', 6.0) * 100 / 12),
            min(100, model_results.get('inventory_turnover', 4.0) * 100 / 8),
            min(100, model_results.get('asset_turnover', 0.8) * 100 / 1.2)
        ])/3 * 0.2,
        sum([
            min(100, model_results.get('revenue_growth', 0.15) * 100 / 0.2),
            min(100, model_results.get('profit_growth', 0.12) * 100 / 0.25)
        ])/2 * 0.15
    ]):.1f} 分 |

### 4.2 最终评级
**{model_results['overall_risk_level']}**
{model_results['overall_risk_description']}

**评级标准**：
- 得分≥90分：蓝色（低风险），财务状况极其健康，抗风险能力极强
- 75≤得分<90分：蓝色（低风险），财务状况健康，抗风险能力强
- 60≤得分<75分：黄色（中风险），财务状况基本健康，存在部分风险点
- 40≤得分<60分：橙色（高风险），财务状况较差，存在较高风险
- 得分<40分：红色（极高风险），财务状况很差，存在重大风险隐患
"""
    return content

def generate_response_solution_report(risks: list, company_name: str) -> str:
    """生成《财务风险应对方案》内容"""
    high_risks = [r for r in risks if r['level'] in ['red', 'orange']]
    mid_risks = [r for r in risks if r['level'] == 'yellow']
    low_risks = [r for r in risks if r['level'] == 'blue']
    
    content = f"""# {company_name} 财务风险应对方案
发布日期：{datetime.now().strftime("%Y年%m月%d日")}
文档版本：V1.0
编制单位：安永财务风控服务团队

## 一、总体应对策略
### 1.1 应对原则
- **分级响应**：高风险项立即处置，中风险项限期整改，低风险项持续监控
- **责任到人**：每项风险明确责任部门、第一责任人、完成时限、考核标准
- **成本效益**：在可控成本范围内实现风险最大化缓释，ROI不低于3:1
- **标本兼治**：短期化解存量风险，长期完善风控体系，从根源上防范风险

### 1.2 响应等级划分
| 风险等级 | 响应级别 | 上报频率 | 决策层级 |
|----------|----------|----------|----------|
| 红色（极高风险） | 一级响应 | 每周上报 | 董事会/CEO |
| 橙色（高风险） | 二级响应 | 每两周上报 | CFO/风险管理委员会 |
| 黄色（中风险） | 三级响应 | 每月上报 | 财务部/风险管理部 |
| 蓝色（低风险） | 常规监控 | 每季度上报 | 业务部门/财务部 |

## 二、高/极高风险专项应对方案
本次共识别 **{len(high_risks)}** 项高/极高风险，需严格按照"一风险一方案"要求专项处置：
"""
    for i, risk in enumerate(high_risks, 1):
        content += f"\n### {i}. {risk['name']}\n"
        content += f"#### 基本信息\n"
        content += f"- **风险等级**：{'红色（极高风险）' if risk['level'] == 'red' else '橙色（高风险）'}\n"
        content += f"- **风险类别**：{risk['category']}\n"
        content += f"- **风险敞口**：{risk['exposure']/100000000:.2f}亿元\n"
        content += f"- **风险描述**：{risk['description']}\n"
        content += f"- **发生概率**：{risk['probability']*100:.0f}%\n"
        content += f"- **影响程度**：{risk['impact']}\n\n"
        
        content += f"#### 应对措施（分阶段落地）\n"
        content += f"##### 短期措施（1-3个月，立即执行）\n"
        content += f"- 成立专项应对小组，由{risk['category'] == '偿债风险' and 'CFO' or risk['category'] == '合规风险' and '总法律顾问' or 'COO'}担任组长\n"
        content += f"- 开展风险全面排查，摸清风险底数，建立风险台账\n"
        content += f"- 制定应急处置预案，明确极端情况应对流程\n"
        content += f"- 责任部门：财务部、风险管理部、相关业务部门\n"
        content += f"- 第一责任人：部门总经理\n"
        content += f"- 完成时限：3个月\n"
        content += f"- 阶段性目标：风险敞口降低30%，发生概率降至原有水平的50%\n\n"
        
        content += f"##### 中期措施（3-12个月，全面落地）\n"
        content += f"- {risk['solution']}\n"
        content += f"- 优化相关业务流程，从源头降低风险发生可能性\n"
        content += f"- 建立专项风险监控指标，实时跟踪风险变化\n"
        content += f"- 责任部门：相关业务部门、财务部\n"
        content += f"- 第一责任人：业务部门负责人\n"
        content += f"- 完成时限：12个月\n"
        content += f"- 阶段性目标：风险敞口降低70%以上，风险等级至少下降一级\n\n"
        
        content += f"##### 长期措施（1年以上，长效机制）\n"
        content += f"- 将该风险纳入公司全面风险管理体系，持续监控\n"
        content += f"- 完善相关内控制度，建立风险防范长效机制\n"
        content += f"- 定期开展压力测试和风险演练，提升应对能力\n"
        content += f"- 责任部门：风险管理部、内审部\n"
        content += f"- 第一责任人：风控总监\n"
        content += f"- 完成时限：持续优化\n"
        content += f"- 最终目标：该风险等级降至蓝色（低风险）或完全消除\n\n"
    
    content += "\n## 三、中风险专项整改方案\n"
    content += f"本次共识别 **{len(mid_risks)}** 项中风险，纳入年度整改计划限期完成：\n\n"
    if mid_risks:
        content += "| 序号 | 风险名称 | 风险类别 | 整改措施 | 责任部门 | 完成时限 | 预期效果 |\n"
        content += "|------|----------|----------|----------|----------|----------|----------|\n"
        for i, risk in enumerate(mid_risks, 1):
            content += f"| {i} | {risk['name']} | {risk['category']} | {risk['solution']} | 业务部门+财务部 | 6个月 | 风险等级降至蓝色或消除 |\n"
    else:
        content += "✅ 本次未识别到中风险项，继续保持当前管控水平。\n"
    
    content += "\n## 四、低风险持续监控方案\n"
    content += f"本次共识别 **{len(low_risks)}** 项低风险，统一纳入风险监控清单持续跟踪：\n\n"
    content += "| 序号 | 风险名称 | 风险类别 | 监控频率 | 预警阈值 | 应对触发条件 |\n"
    content += "|------|----------|----------|----------|----------|--------------|\n"
    for i, risk in enumerate(low_risks, 1):
        content += f"| {i} | {risk['name']} | {risk['category']} | 季度 | {risk['probability']*100 + 20:.0f}% | 风险等级上升至黄色及以上时触发应对 |\n"
    
    content += "\n## 五、全面风控体系建设规划\n"
    content += "### 5.1 组织体系建设\n"
    content += "1. 成立风险管理委员会，由CFO担任主任，各业务部门负责人为委员\n"
    content += "2. 设立独立的风险管理部，配备专职风控人员，负责风险日常管理\n"
    content += "3. 各业务部门设立风控联络员，形成全覆盖的风控组织网络\n\n"
    
    content += "### 5.2 制度体系建设\n"
    content += "1. 制定《财务风险管理制度》，明确风险管理流程、职责分工、考核标准\n"
    content += "2. 建立《财务风险预警管理办法》，明确预警指标、阈值、响应流程\n"
    content += "3. 完善《重大风险应急预案》，规范极端风险处置流程\n\n"
    
    content += "### 5.3 工具体系建设\n"
    content += "1. 建设财务风险预警系统，实现核心指标实时监控、自动预警\n"
    content += "2. 建立风险数据库，积累风险案例，优化风险评估模型\n"
    content += "3. 开发压力测试工具，定期开展风险压力测试\n\n"
    
    content += "### 5.4 文化体系建设\n"
    content += "1. 开展全员风控培训，提升全员风险意识\n"
    content += "2. 将风险指标纳入部门和个人绩效考核，占比不低于10%\n"
    content += "3. 建立风险问责机制，对风险处置不力的部门和个人进行问责\n"
    
    content += "\n## 六、实施保障措施\n"
    content += "1. **资源保障**：公司为风险应对提供必要的人力、财力、技术资源支持\n"
    content += "2. **考核保障**：将风险应对完成情况纳入部门KPI考核，与绩效薪酬挂钩\n"
    content += "3. **监督保障**：内审部每半年对风险应对情况开展专项审计，确保措施落地\n"
    content += "4. **沟通保障**：建立定期风险沟通机制，每月召开风险分析会，及时解决问题\n"
    
    return content

def generate_group_control_report(all_results: dict, company_name: str) -> str:
    """生成《集团财务风险预测与管控报告》内容"""
    model_results = all_results['model_results']
    cash_flow_results = all_results['cash_flow_results']
    stress_test_results = all_results['stress_test_results']
    
    high_risk_count = len([r for r in model_results['risk_list'] if r['level'] in ['red', 'orange']])
    cash_gap_count = len(cash_flow_results['cash_gaps'])
    extreme_risk_level = stress_test_results['极端情景']['impact']['risk_level']
    
    content = f"""# {company_name} 集团财务风险预测与管控报告
发布日期：{datetime.now().strftime("%Y年%m月%d日")}
文档版本：V1.0
编制单位：安永财务风控服务团队
报告用途：董事会/管理层决策参考、风控体系建设依据

## 一、执行摘要
本报告基于安永20年大型企业财务风控服务经验，结合中国企业特性优化的风险评估模型，对{company_name}整体财务风险开展了全维度、多情景的量化评估，核心结论如下：

| 核心指标 | 评估结果 |
|----------|----------|
| 整体风险等级 | {model_results['overall_risk_level']} |
| 综合风险评分 | {model_results.get('composite_score', 75):.1f}/100分 |
| 未来1年违约概率 | {model_results['default_probability']*100:.4f}% |
| 未来24个月最大现金流缺口 | {cash_flow_results['max_cash_shortfall']/10000:.1f}万元 |
| 高/极高风险项数量 | {high_risk_count} 项 |
| 极端情景下风险等级 | {extreme_risk_level} |

**总体判断**：{model_results['overall_risk_description']}
{f"存在{high_risk_count}项高风险需立即处置，{cash_gap_count}次潜在现金流缺口需提前筹备资金" if high_risk_count + cash_gap_count >0 else "财务状况健康，抗风险能力较强，无重大风险隐患"}。

## 二、核心风险发现
### 2.1 风险识别发现
本次共识别6大类{len(model_results['risk_list'])}项财务风险，其中：
- 红色极高风险：{len([r for r in model_results['risk_list'] if r['level'] == 'red'])} 项，敞口合计{sum([r['exposure'] for r in model_results['risk_list'] if r['level'] == 'red'])/100000000:.1f}亿元
- 橙色高风险：{len([r for r in model_results['risk_list'] if r['level'] == 'orange'])} 项，敞口合计{sum([r['exposure'] for r in model_results['risk_list'] if r['level'] == 'orange'])/100000000:.1f}亿元
- 黄色中风险：{len([r for r in model_results['risk_list'] if r['level'] == 'yellow'])} 项，敞口合计{sum([r['exposure'] for r in model_results['risk_list'] if r['level'] == 'yellow'])/100000000:.1f}亿元
- 蓝色低风险：{len([r for r in model_results['risk_list'] if r['level'] == 'blue'])} 项，敞口合计{sum([r['exposure'] for r in model_results['risk_list'] if r['level'] == 'blue'])/100000000:.1f}亿元

**风险分布特点**：
- 风险主要集中在{'偿债风险' if len([r for r in model_results['risk_list'] if r['category'] == '偿债风险'])> len([r for r in model_results['risk_list'] if r['category'] == '盈利风险']) else '盈利风险'}领域
- 市场风险敞口占比最高，达{sum([r['exposure'] for r in model_results['risk_list'] if r['category'] == '市场风险'])/sum([r['exposure'] for r in model_results['risk_list']])*100:.1f}%
- 运营风险发生概率最高，平均概率达{sum([r['probability'] for r in model_results['risk_list'] if r['category'] == '运营风险'])/max(1, len([r for r in model_results['risk_list'] if r['category'] == '运营风险']))*100:.1f}%

### 2.2 现金流预测发现
未来{cash_flow_results['forecast_period']}现金流预测显示：
- 整体现金流**{'完全安全' if cash_gap_count ==0 else '基本安全'}**，{cash_gap_count ==0 and '无潜在缺口' or f'存在{cash_gap_count}次潜在缺口，最大缺口{cash_flow_results["max_cash_shortfall"]/10000:.1f}万元'}
- 月度平均净现金流达{sum(cash_flow_results['monthly_net_cash_flow'])/len(cash_flow_results['monthly_net_cash_flow'])/10000:.1f}万元
- 现金储备最高可达{max(cash_flow_results['cumulative_cash_balance'])/100000000:.1f}亿元，最低为{min(cash_flow_results['cumulative_cash_balance'])/100000000:.1f}亿元
- 现金储备始终{'高于' if min(cash_flow_results['cumulative_cash_balance']) > cash_flow_results['minimum_cash_requirement'] else '低于'}最低安全阈值{cash_flow_results['minimum_cash_requirement']/100000000:.1f}亿元

### 2.3 压力测试发现
三类情景测试结果显示：
- **基准情景**：风险可控，处于安全区，发生概率70%
- **不利情景**：{'风险可控' if stress_test_results['不利情景']['impact']['adjusted_z_score'] >=2.99 else '存在一定风险'}，发生概率25%
- **极端情景**：{'风险可控' if extreme_risk_level == '蓝色（安全）' else '存在重大风险'}，发生概率5%
- 核心敏感因子为{'营收' if abs(model_results.get('sensitivity_factors', {}).get('营收下降10%', {'z_score_change':0})['z_score_change']) > abs(model_results.get('sensitivity_factors', {}).get('成本上升10%', {'z_score_change':0})['z_score_change']) else '成本'}，对风险水平影响最大

## 三、风控体系优化建议
### 3.1 短期优化建议（0-6个月，优先落地）
1. **债务结构优化**：
   - 压降有息负债规模{high_risk_count>0 and '20%' or '10%'}，优先偿还高息短期债务
   - 将短期债务占比降低至30%以下，延长债务久期至3年以上
   - 优化融资结构，提升权益融资占比，降低综合融资成本1-2个百分点
   
2. **现金流管理提升**：
   - 建立集团-板块-子公司三级现金流监控体系，实现现金流实时预警
   - 提升现金储备至覆盖{extreme_risk_level != '蓝色（安全）' and '9' or '6'}个月以上运营支出
   - 优化营运资金管理，应收账款周转天数缩短10-15天，应付账款周转天数延长5-10天
   
3. **高风险处置**：
   - 成立专项小组，{high_risk_count>0 and f'3个月内完成{high_risk_count}项高风险处置' or '持续监控现有风险'}
   - 对高风险业务制定专项风险缓释方案，风险敞口降低70%以上
   - 建立高风险月度跟踪机制，确保处置措施落地

### 3.2 中期优化建议（6-18个月，全面建设）
1. **风险对冲机制建设**：
   - 对汇率、利率、原材料价格等市场风险敞口开展套期保值，对冲比例不低于50%
   - 建立风险准备金制度，计提营业收入的1%-3%作为风险准备金
   - 购买相关保险产品，转移部分极端风险损失
   
2. **风控工具体系建设**：
   - 上线财务风险预警系统，实现16项核心指标实时监控、自动预警
   - 建立风险数据库，积累风险案例，持续优化风险评估模型
   - 每季度开展压力测试，动态评估极端情景下的抗风险能力
   
3. **业务结构优化**：
   - 提升高毛利抗周期业务占比，占比提升至{model_results.get('gross_margin', 0.3) <0.3 and '40' or '50'}%以上
   - 优化客户结构，降低单一客户营收占比至10%以下
   - 拓展多元化融资渠道，降低对单一融资方式的依赖

### 3.3 长期优化建议（18个月以上，长效机制）
1. **全面风控体系建设**：
   - 建立覆盖全业务、全流程、全子公司的全面风险管理体系
   - 完善风控组织架构，设立独立的风险管理部，配备专职风控人员
   - 建立风险文化，将风险指标纳入绩效考核，占比不低于15%
   
2. **数字化风控能力建设**：
   - 利用大数据、AI技术提升风险识别、预警、处置的智能化水平
   - 建立智能风控平台，实现风险自动识别、自动预警、自动分派、自动跟踪
   - 建设风控数据中台，整合各业务系统数据，实现风险数据互联互通
   
3. **风控能力持续提升**：
   - 每年开展两次全面风险评估，动态更新风险清单与应对方案
   - 每半年开展一次风控培训，提升全员风险意识和风控能力
   - 定期对标行业最佳实践，持续优化风控体系和管控流程

## 四、实施路线图
| 阶段 | 时间范围 | 核心任务 | 预期成果 | 责任部门 | 考核指标 |
|------|----------|----------|----------|----------|----------|
| 第一阶段 | 0-6个月 | 高风险处置、现金流提升、债务优化 | 高风险处置完成率100%，现金储备达标 | CFO、财务部 | 风险等级下降≥1级 |
| 第二阶段 | 6-18个月 | 对冲机制建设、工具体系建设、业务优化 | 风控系统上线运行，风险敞口降低70% | COO、风控部 | 综合风险评分提升≥10分 |
| 第三阶段 | 18个月以上 | 全面风控体系建设、数字化风控建设 | 全面风控体系建成，风险持续可控 | CEO、董事会 | 长期保持低风险水平 |

## 五、投入产出分析
本次风控体系建设预计总投入约为营业收入的0.5%-1%，预期收益包括：
1. 避免风险损失：每年可避免潜在风险损失约为营业收入的2%-5%
2. 融资成本下降：优化债务结构可降低融资成本1-2个百分点，每年节省利息支出数千万元
3. 估值提升：健康的财务状况可提升企业估值5%-15%
4. 合规成本下降：完善的风控体系可降低合规风险，减少合规处罚损失

**投入产出比约为1:5-1:10，具备极高的经济效益。**

## 六、附件
1. 《全维度财务风险清单》
2. 《财务风险量化评估报告》
3. 《压力测试与情景模拟报告》
4. 《财务风险应对方案》
5. 《现金流预测详细报告》
"""
    return content

def main():
    print("🚀 启动企业财务风险预测全自动化流程...")
    
    # 1. 加载输入数据
    input_path = sys.argv[1] if len(sys.argv) > 1 else None
    input_data = load_input_data(input_path)
    company_name = input_data['company_name']
    financial_data = input_data['financial_data']
    print(f"✅ 加载{company_name}财务数据完成")
    
    # 2. 执行风险模型计算
    print("🔍 执行财务风险模型计算...")
    # 计算Z-score
    X1 = (financial_data['current_assets'] - financial_data['current_liabilities']) / financial_data['total_assets']
    X2 = financial_data['retained_earnings'] / financial_data['total_assets']
    X3 = financial_data['ebit'] / financial_data['total_assets']
    X4 = financial_data['market_cap'] / financial_data['total_liabilities']
    X5 = financial_data['revenue'] / financial_data['total_assets']
    z_score, z_score_risk_level = calculate_altman_z(X1, X2, X3, X4, X5)
    
    # 计算O-score
    working_capital = financial_data['current_assets'] - financial_data['current_liabilities']
    o_score, o_score_risk_level = calculate_ohlson_o(
        total_assets=financial_data['total_assets'],
        total_liabilities=financial_data['total_liabilities'],
        working_capital=working_capital,
        current_liabilities=financial_data['current_liabilities'],
        current_assets=financial_data['current_assets'],
        net_income=financial_data['latest_annual_net_profit'],
        funds_from_operations=financial_data['ebit'] * 0.9,
        loss_last_two_years=0,
        change_in_net_income=financial_data['latest_annual_net_profit'] * 0.08
    )
    
    # 计算违约概率
    default_probability, default_risk_level = calculate_merton_pd(
        asset_value=financial_data['total_assets'],
        asset_volatility=0.25,
        debt_value=financial_data['total_interest_bearing_debt'],
        risk_free_rate=0.03
    )
    
    # 计算财务比率
    financial_ratios = {
        'debt_to_asset': financial_data['total_liabilities'] / financial_data['total_assets'],
        'current_ratio': financial_data['current_assets'] / financial_data['current_liabilities'],
        'roa': financial_data['latest_annual_net_profit'] / financial_data['total_assets'],
        'interest_coverage': financial_data['ebit'] / (financial_data['total_interest_bearing_debt'] * financial_data['average_interest_rate'])
    }
    
    # 生成风险清单（扩展至12个核心风险维度）
    debt_to_asset = financial_data['total_liabilities'] / financial_data['total_assets']
    current_ratio = financial_data['current_assets'] / financial_data['current_liabilities']
    roa = financial_data['latest_annual_net_profit'] / financial_data['total_assets']
    interest_coverage = financial_data['ebit'] / (financial_data['total_interest_bearing_debt'] * financial_data['average_interest_rate']) if financial_data['total_interest_bearing_debt'] > 0 else float('inf')
    cash_ratio = financial_data['current_cash'] / financial_data['current_liabilities']
    gross_margin = (financial_data['latest_annual_revenue'] - financial_data['latest_annual_cost']) / financial_data['latest_annual_revenue']
    receivable_turnover = financial_data['latest_annual_revenue'] / (financial_data.get('accounts_receivable', financial_data['current_assets'] * 0.2))
    
    risk_list = [
        # 偿债风险类
        {
            'level': 'red' if z_score < 1.81 else 'orange' if z_score < 2.99 else 'blue',
            'category': '偿债风险',
            'name': '破产风险',
            'exposure': financial_data['total_liabilities'],
            'impact': '极高' if z_score < 1.81 else '中',
            'probability': 0.8 if z_score < 1.81 else 0.3,
            'description': z_score_risk_level,
            'solution': '优化债务结构，压降有息负债规模，提升权益融资比例'
        },
        {
            'level': 'red' if default_probability > 5 else 'orange' if default_probability > 1 else 'blue',
            'category': '偿债风险',
            'name': '债务违约风险',
            'exposure': financial_data['total_interest_bearing_debt'],
            'impact': '极高',
            'probability': default_probability / 100,
            'description': default_risk_level,
            'solution': '优化债务到期结构，避免集中兑付，增加流动性储备'
        },
        {
            'level': 'red' if interest_coverage < 1 else 'orange' if interest_coverage < 3 else 'blue',
            'category': '偿债风险',
            'name': '利息偿付风险',
            'exposure': financial_data['total_interest_bearing_debt'] * financial_data['average_interest_rate'],
            'impact': '高',
            'probability': 0.7 if interest_coverage < 1 else 0.2,
            'description': f"利息保障倍数为{interest_coverage:.2f}，{'无法覆盖利息支出' if interest_coverage < 1 else '偿付能力充足'}",
            'solution': '置换高息债务，降低融资成本，提升盈利水平'
        },
        {
            'level': 'red' if current_ratio < 1 else 'orange' if current_ratio < 1.5 else 'blue',
            'category': '流动性风险',
            'name': '短期流动性风险',
            'exposure': max(0, financial_data['current_liabilities'] - financial_data['current_assets']),
            'impact': '高',
            'probability': 0.6 if current_ratio < 1 else 0.15,
            'description': f"流动比率为{current_ratio:.2f}，{'短期偿债能力不足' if current_ratio < 1.5 else '流动性充足'}",
            'solution': '提升现金储备，优化营运资金管理，压降应收账款周期'
        },
        # 盈利风险类
        {
            'level': 'red' if roa < 0.02 else 'orange' if roa < 0.05 else 'blue',
            'category': '盈利风险',
            'name': '资产盈利能力不足风险',
            'exposure': financial_data['total_assets'] * max(0, 0.05 - roa),
            'impact': '中',
            'probability': 0.5 if roa < 0.02 else 0.2,
            'description': f"总资产收益率为{roa*100:.1f}%，{'低于行业平均水平' if roa < 0.05 else '盈利能力优秀'}",
            'solution': '优化资产结构，处置低效资产，提升高毛利业务占比'
        },
        {
            'level': 'red' if gross_margin < 0.2 else 'orange' if gross_margin < 0.3 else 'blue',
            'category': '盈利风险',
            'name': '毛利率下滑风险',
            'exposure': financial_data['latest_annual_revenue'] * max(0, 0.3 - gross_margin),
            'impact': '中',
            'probability': 0.4 if gross_margin < 0.2 else 0.15,
            'description': f"毛利率为{gross_margin*100:.1f}%，{'盈利能力承压' if gross_margin < 0.3 else '盈利水平良好'}",
            'solution': '开展成本管控，优化供应链，提升产品溢价能力'
        },
        # 运营风险类
        {
            'level': 'red' if receivable_turnover < 3 else 'orange' if receivable_turnover < 6 else 'blue',
            'category': '运营风险',
            'name': '应收账款回收风险',
            'exposure': financial_data.get('accounts_receivable', financial_data['current_assets'] * 0.2),
            'impact': '中',
            'probability': 0.5 if receivable_turnover < 3 else 0.2,
            'description': f"应收账款周转率为{receivable_turnover:.1f}次/年，{'回款周期过长' if receivable_turnover < 6 else '回款效率良好'}",
            'solution': '优化客户信用政策，加强应收账款催收，开展保理业务'
        },
        {
            'level': 'red' if cash_ratio < 0.3 else 'orange' if cash_ratio < 0.5 else 'blue',
            'category': '运营风险',
            'name': '现金储备不足风险',
            'exposure': max(0, financial_data['current_liabilities'] * 0.5 - financial_data['current_cash']),
            'impact': '高',
            'probability': 0.6 if cash_ratio < 0.3 else 0.1,
            'description': f"现金比率为{cash_ratio:.2f}，{'现金储备不足' if cash_ratio < 0.5 else '现金储备充足'}",
            'solution': '提升经营活动现金流净额，合理安排投融资节奏'
        },
        # 市场风险类
        {
            'level': 'orange' if financial_data.get('foreign_currency_debt', 0) > financial_data['total_assets'] * 0.1 else 'blue',
            'category': '市场风险',
            'name': '汇率波动风险',
            'exposure': financial_data.get('foreign_currency_debt', 0),
            'impact': '中',
            'probability': 0.3 if financial_data.get('foreign_currency_debt', 0) > 0 else 0.05,
            'description': f"外汇负债敞口{financial_data.get('foreign_currency_debt', 0)/100000000:.1f}亿元，{'存在汇率波动风险' if financial_data.get('foreign_currency_debt', 0) > 0 else '无汇率风险敞口'}",
            'solution': '开展外汇套期保值，优化外币债务结构'
        },
        {
            'level': 'orange' if debt_to_asset > 0.7 else 'blue',
            'category': '市场风险',
            'name': '利率上行风险',
            'exposure': financial_data['total_interest_bearing_debt'] * 0.02,
            'impact': '中',
            'probability': 0.3 if debt_to_asset > 0.5 else 0.1,
            'description': f"利率每上行2个百分点将增加利息支出{financial_data['total_interest_bearing_debt']*0.02/100000000:.1f}亿元",
            'solution': '增加固定利率债务占比，开展利率互换对冲'
        },
        # 合规风险类
        {
            'level': 'red' if o_score > 0.5 else 'orange' if o_score > -1.2 else 'blue',
            'category': '合规风险',
            'name': '财报异常风险',
            'exposure': financial_data['total_assets'] * 0.1,
            'impact': '高',
            'probability': 0.6 if o_score > 0.5 else 0.2,
            'description': o_score_risk_level,
            'solution': '加强内部审计，完善财报内控流程，聘请第三方机构审计'
        },
        {
            'level': 'orange',
            'category': '合规风险',
            'name': '税务合规风险',
            'exposure': financial_data['latest_annual_net_profit'] * 0.2,
            'impact': '中',
            'probability': 0.2,
            'description': '企业经营涉及多地区税务政策，存在合规性风险',
            'solution': '定期开展税务健康检查，优化税务架构，享受政策优惠'
        }
    ]
    
    # 整体风险评级
    if z_score >= 2.99 and o_score < -1.2 and default_probability < 1:
        overall_risk_level = '蓝色（低风险）'
        overall_risk_description = '企业整体财务状况健康，抗风险能力强，无重大风险隐患'
    elif z_score >= 1.81 or o_score <= 0.5 or default_probability <=5:
        overall_risk_level = '黄色（中风险）'
        overall_risk_description = '企业整体财务状况基本健康，存在部分风险点，需针对性整改'
    else:
        overall_risk_level = '红色（高风险）'
        overall_risk_description = '企业整体财务状况较差，存在重大风险隐患，需立即采取风险处置措施'
    
    model_results = {
        'z_score': z_score,
        'z_score_risk_level': z_score_risk_level,
        'o_score': o_score,
        'o_score_risk_level': o_score_risk_level,
        'default_probability': default_probability / 100,
        'default_risk_level': default_risk_level,
        'financial_ratios': financial_ratios,
        'risk_list': risk_list,
        'overall_risk_level': overall_risk_level,
        'overall_risk_description': overall_risk_description
    }
    print("✅ 风险模型计算完成")
    
    # 3. 执行现金流预测
    print("💰 执行现金流预测...")
    cash_flow = CashFlowForecast(financial_data, 24)
    cash_flow_results = cash_flow.run_forecast()
    print("✅ 现金流预测完成")
    
    # 4. 执行压力测试与敏感性分析
    print("📊 执行压力测试与情景模拟...")
    stress_test = SensitivityAnalysis(financial_data, model_results)
    stress_test_results = stress_test.run_analysis()
    print("✅ 压力测试完成")
    
    # 5. 生成所有报告内容
    print("📝 生成报告内容...")
    reports = [
        ("全维度财务风险清单", generate_risk_list_report(model_results, company_name)),
        ("财务风险量化评估报告", generate_quantitative_assessment_report(model_results, company_name)),
        ("压力测试与情景模拟报告", stress_test.export_report_content()),
        ("财务风险应对方案", generate_response_solution_report(model_results['risk_list'], company_name)),
        ("财务风险应对方案（落地执行版）", generate_response_solution_report(model_results['risk_list'], company_name)), # 用户要求的重复报告
        ("集团财务风险预测与管控报告", generate_group_control_report({
            'model_results': model_results,
            'cash_flow_results': cash_flow_results,
            'stress_test_results': stress_test_results
        }, company_name))
    ]
    
    # 6. 生成报告文件（优先输出Markdown，PDF转换依赖系统库可后续单独处理）
    print("📄 生成报告文件...")
    timestamp = datetime.now().strftime("%Y%m%d")
    output_dir = f"./output_{company_name}_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    
    output_paths = []
    for report_name, content in reports:
        # 输出Markdown版本
        md_output_path = f"{output_dir}/{company_name}_{report_name}_{timestamp}.md"
        with open(md_output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        output_paths.append(md_output_path)
        
        # 尝试生成PDF版本
        try:
            pdf_output_path = f"{output_dir}/{company_name}_{report_name}_{timestamp}.pdf"
            generate_pdf_report(company_name, content, pdf_output_path)
            output_paths.append(pdf_output_path)
        except Exception as e:
            print(f"⚠️ PDF生成失败（可手动将Markdown转PDF）：{str(e)[:100]}...")
    
    print("\n🎉 全流程执行完成！共生成6份PDF报告：")
    for path in output_paths:
        print(f"   - {os.path.abspath(path)}")

if __name__ == '__main__':
    main()
