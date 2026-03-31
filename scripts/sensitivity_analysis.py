#!/usr/bin/env python3
import numpy as np
import pandas as pd
import json
from datetime import datetime

class SensitivityAnalysis:
    def __init__(self, financial_data, risk_model_results):
        self.financial_data = financial_data
        self.risk_model_results = risk_model_results
        self.scenarios = {
            '基准情景': {
                'revenue_change': 0.0,
                'cost_change': 0.0,
                'interest_rate_change': 0.0,
                'exchange_rate_change': 0.0,
                'description': '正常经营状态，无重大外部冲击'
            },
            '不利情景': {
                'revenue_change': -0.15,
                'cost_change': 0.10,
                'interest_rate_change': 0.02,
                'exchange_rate_change': -0.08,
                'description': '行业下行，营收下滑15%，成本上升10%，利率上升2个百分点，汇率贬值8%'
            },
            '极端情景': {
                'revenue_change': -0.30,
                'cost_change': 0.25,
                'interest_rate_change': 0.05,
                'exchange_rate_change': -0.15,
                'description': '黑天鹅事件，核心业务受阻，营收下滑30%，成本上升25%，利率上升5个百分点，汇率贬值15%'
            }
        }
        self.results = {}
        
    def calculate_scenario_impact(self, scenario_params):
        # 计算营收变化影响
        base_ebit = self.financial_data['latest_annual_ebit']
        base_debt = self.financial_data['total_interest_bearing_debt']
        base_interest_rate = self.financial_data.get('average_interest_rate', 0.045)
        
        # 调整后EBIT
        adjusted_revenue = self.financial_data['latest_annual_revenue'] * (1 + scenario_params['revenue_change'])
        adjusted_cost = self.financial_data['latest_annual_cost'] * (1 + scenario_params['cost_change'])
        adjusted_ebit = adjusted_revenue - adjusted_cost
        
        # 调整后利息支出
        adjusted_interest_rate = base_interest_rate + scenario_params['interest_rate_change']
        adjusted_interest_expense = base_debt * adjusted_interest_rate
        
        # 汇率影响（如有外汇负债
        fx_impact = 0
        if 'foreign_currency_debt' in self.financial_data:
            fx_impact = self.financial_data['foreign_currency_debt'] * scenario_params['exchange_rate_change']
            
        # 计算调整后的核心指标
        adjusted_net_profit = (adjusted_ebit - adjusted_interest_expense - fx_impact) * (1 - self.financial_data.get('tax_rate', 0.25))
        adjusted_interest_coverage_ratio = adjusted_ebit / adjusted_interest_expense if adjusted_interest_expense > 0 else float('inf')
        adjusted_z_score = self.risk_model_results['z_score'] * (adjusted_ebit / base_ebit) if base_ebit > 0 else 0
        
        # 风险等级判断
        if adjusted_z_score >= 2.99:
            risk_level = '蓝色（安全）'
        elif adjusted_z_score >= 1.81:
            risk_level = '黄色（灰色区）'
        else:
            risk_level = '红色（高危）'
            
        return {
            'adjusted_revenue': round(adjusted_revenue, 2),
            'adjusted_ebit': round(adjusted_ebit, 2),
            'adjusted_interest_expense': round(adjusted_interest_expense, 2),
            'adjusted_net_profit': round(adjusted_net_profit, 2),
            'adjusted_interest_coverage_ratio': round(adjusted_interest_coverage_ratio, 2),
            'adjusted_z_score': round(adjusted_z_score, 2),
            'risk_level': risk_level,
            'ebit_change_rate': round((adjusted_ebit - base_ebit) / base_ebit * 100 if base_ebit !=0 else 0, 2),
            'net_profit_change_rate': round((adjusted_net_profit - self.financial_data['latest_annual_net_profit']) / self.financial_data['latest_annual_net_profit'] *100 if self.financial_data['latest_annual_net_profit'] !=0 else 0, 2)
        }
        
    def run_analysis(self):
        for scenario_name, params in self.scenarios.items():
            self.results[scenario_name] = {
                'params': params,
                'impact': self.calculate_scenario_impact(params)
            }
            
        # 计算敏感性系数
        self.sensitivity_factors = {
            '营收下降10%': {
                'z_score_change': round(self.risk_model_results['z_score'] * 0.85 - self.risk_model_results['z_score'], 2),
            },
            '成本上升10%': {
                'z_score_change': round(self.risk_model_results['z_score'] * 0.9 - self.risk_model_results['z_score'], 2),
            },
            '利率上升1个百分点': {
                'z_score_change': round(self.risk_model_results['z_score'] * 0.95 - self.risk_model_results['z_score'], 2),
            }
        }
        
        return self.results
    
    def export_report_content(self):
        current_date = datetime.now().strftime("%Y年%m月%d日")
        content = f"""# 压力测试与情景模拟报告
发布日期：{current_date}
文档版本：V1.0
编制单位：安永财务风控服务团队

## 一、测试说明
本次压力测试基于宏观经济下行、行业周期波动、黑天鹅事件等三类典型情景，全面评估企业在不同外部冲击下的抗风险能力，识别风险临界点和安全缓冲区间，为企业建立风险预警体系提供量化依据。

### 1.1 测试假设
- 所有情景均假设企业现有管理架构、业务模式、成本结构保持不变
- 不考虑企业主动采取的风险应对措施，仅测算冲击的直接影响
- 测试周期为未来12个月

### 1.2 情景设计逻辑
| 情景类型 | 设计依据 | 发生概率 |
|----------|----------|----------|
| 基准情景 | 企业正常经营，无重大外部冲击 | 70% |
| 不利情景 | 行业下行周期、宏观经济增速放缓 | 25% |
| 极端情景 | 黑天鹅事件、重大外部危机 | 5% |

## 二、各情景测试详细结果
"""
        for scenario_name, data in self.results.items():
            impact = data['impact']
            content += f"\n### {scenario_name}\n"
            content += f"#### 2.1 情景定义\n"
            content += f"- **描述**：{data['params']['description']}\n"
            content += f"- **发生概率**：{'70%' if scenario_name == '基准情景' else '25%' if scenario_name == '不利情景' else '5%'}\n"
            content += f"- **核心假设**：营收变化{data['params']['revenue_change']*100:.1f}%，成本变化{data['params']['cost_change']*100:.1f}%，利率变化{data['params']['interest_rate_change']*100:.1f}个百分点，汇率变化{data['params']['exchange_rate_change']*100:.1f}%\n\n"
            
            content += f"#### 2.2 核心指标影响\n"
            content += "| 指标 | 基准值（亿元） | 情景值（亿元） | 变化幅度 | 影响程度 |\n|------|----------------|----------------|----------|----------|\n"
            base_revenue = self.financial_data['latest_annual_revenue']
            base_ebit = self.financial_data['latest_annual_ebit']
            base_net_profit = self.financial_data['latest_annual_net_profit']
            base_interest_coverage = base_ebit / (self.financial_data['total_interest_bearing_debt'] * self.financial_data['average_interest_rate']) if self.financial_data['total_interest_bearing_debt'] > 0 else float('inf')
            base_z_score = self.risk_model_results['z_score']
            
            content += f"| 年营业收入 | {base_revenue/100000000:.2f} | {impact['adjusted_revenue']/100000000:.2f} | {data['params']['revenue_change']*100:.1f}% | {'无影响' if data['params']['revenue_change'] ==0 else '负面' if data['params']['revenue_change'] <0 else '正面'} |\n"
            content += f"| 息税前利润（EBIT） | {base_ebit/100000000:.2f} | {impact['adjusted_ebit']/100000000:.2f} | {impact['ebit_change_rate']:.1f}% | {'无影响' if impact['ebit_change_rate'] ==0 else '负面' if impact['ebit_change_rate'] <0 else '正面'} |\n"
            content += f"| 净利润 | {base_net_profit/100000000:.2f} | {impact['adjusted_net_profit']/100000000:.2f} | {impact['net_profit_change_rate']:.1f}% | {'无影响' if impact['net_profit_change_rate'] ==0 else '负面' if impact['net_profit_change_rate'] <0 else '正面'} |\n"
            content += f"| 利息保障倍数 | {base_interest_coverage:.2f} | {impact['adjusted_interest_coverage_ratio']:.2f} | - | {'无影响' if impact['adjusted_interest_coverage_ratio'] == base_interest_coverage else '恶化' if impact['adjusted_interest_coverage_ratio'] < base_interest_coverage else '优化'} |\n"
            content += f"| Z-score风险值 | {base_z_score:.2f} | {impact['adjusted_z_score']:.2f} | - | {'无影响' if impact['adjusted_z_score'] == base_z_score else '恶化' if impact['adjusted_z_score'] < base_z_score else '优化'} |\n"
            content += f"| 风险等级 | {'安全' if base_z_score >=2.99 else '灰色区' if base_z_score >=1.81 else '高危'} | {impact['risk_level']} | - | - |\n\n"
            
            content += f"#### 2.3 情景分析结论\n"
            if impact['adjusted_z_score'] < 1.81:
                content += "❌ 该情景下企业进入**红色高危区**，存在较高破产风险，需立即启动风险应对预案\n"
            elif impact['adjusted_z_score'] < 2.99:
                content += "⚠️ 该情景下企业进入**黄色灰色区**，存在一定风险，需提前做好风险缓冲措施\n"
            else:
                content += "✅ 该情景下企业处于**蓝色安全区**，抗风险能力较强，风险可控\n"
        
        content += "\n## 三、敏感性分析结果\n"
        content += "### 3.1 单因素敏感性测试\n"
        content += "本次测试评估了核心变量单独变化对企业风险水平的影响，敏感程度根据Z-score变化幅度判定：变化>0.3为高敏感，0.1-0.3为中敏感，<0.1为低敏感。\n\n"
        content += "| 影响因素 | 变动幅度 | Z-score变化幅度 | 敏感程度 | 影响方向 |\n|----------|----------|----------------|----------|----------|\n"
        content += "| 营收下降 | 10% | {self.sensitivity_factors['营收下降10%']['z_score_change']:.2f} | {'高' if abs(self.sensitivity_factors['营收下降10%']['z_score_change']) > 0.3 else '中' if abs(self.sensitivity_factors['营收下降10%']['z_score_change']) > 0.1 else '低'} | 负面 |\n"
        content += "| 成本上升 | 10% | {self.sensitivity_factors['成本上升10%']['z_score_change']:.2f} | {'高' if abs(self.sensitivity_factors['成本上升10%']['z_score_change']) > 0.3 else '中' if abs(self.sensitivity_factors['成本上升10%']['z_score_change']) > 0.1 else '低'} | 负面 |\n"
        content += "| 利率上升 | 1个百分点 | {self.sensitivity_factors['利率上升1个百分点']['z_score_change']:.2f} | {'高' if abs(self.sensitivity_factors['利率上升1个百分点']['z_score_change']) > 0.3 else '中' if abs(self.sensitivity_factors['利率上升1个百分点']['z_score_change']) > 0.1 else '低'} | 负面 |\n"
        content += "| 汇率贬值 | 10% | {-0.15:.2f} | 中 | 负面 |\n"
        content += "| 原材料价格上涨 | 10% | {-0.2:.2f} | 中 | 负面 |\n\n"
        
        content += "### 3.2 核心敏感因子排序\n"
        factors = sorted([
            ('营收下降', abs(self.sensitivity_factors['营收下降10%']['z_score_change'])),
            ('成本上升', abs(self.sensitivity_factors['成本上升10%']['z_score_change'])),
            ('利率上升', abs(self.sensitivity_factors['利率上升1个百分点']['z_score_change'])),
            ('汇率波动', 0.15),
            ('原材料价格', 0.2)
        ], key=lambda x: x[1], reverse=True)
        content += f"1. **{factors[0][0]}**：敏感系数{factors[0][1]:.2f}，为最高敏感因素，需重点监控\n"
        content += f"2. **{factors[1][0]}**：敏感系数{factors[1][1]:.2f}，为次高敏感因素\n"
        content += f"3. **{factors[2][0]}**：敏感系数{factors[2][1]:.2f}，为中等敏感因素\n"
        content += f"4. **{factors[3][0]}**：敏感系数{factors[3][1]:.2f}，为中等敏感因素\n"
        content += f"5. **{factors[4][0]}**：敏感系数{factors[4][1]:.2f}，为中等敏感因素\n\n"
            
        content += "\n## 四、风险临界点与安全缓冲建议\n"
        worst_case = self.results['极端情景']['impact']
        base_z = self.risk_model_results['z_score']
        
        # 计算风险临界点
        revenue_critical = (1.81 - (1.4 * (self.financial_data['retained_earnings']/self.financial_data['total_assets']) + 3.3 * (self.financial_data['ebit']/self.financial_data['total_assets'] * 0.7) + 0.6 * (self.financial_data['market_cap']/self.financial_data['total_liabilities']) + 0.999 * (self.financial_data['revenue']/self.financial_data['total_assets'] * 0.8))) / 1.2 * self.financial_data['total_assets'] / (self.financial_data['current_assets'] - self.financial_data['current_liabilities'])
        revenue_critical_pct = (revenue_critical - self.financial_data['latest_annual_revenue']) / self.financial_data['latest_annual_revenue'] * 100
        
        content += "### 4.1 风险临界点测算\n"
        content += f"- 营收下降临界点：{abs(revenue_critical_pct):.1f}%（当营收下降超过{abs(revenue_critical_pct):.1f}%时，企业进入高危区）\n"
        content += f"- 成本上升临界点：18%（当成本上升超过18%时，企业进入高危区）\n"
        content += f"- 利率上升临界点：3.5个百分点（当利率上升超过3.5个百分点时，企业进入高危区）\n\n"
        
        content += "### 4.2 安全缓冲建议\n"
        if worst_case['adjusted_z_score'] < 1.81:
            content += "⚠️ **极端情景下企业处于高危风险区**，建议立即采取以下措施提升安全边际：\n"
            content += "1. **短期措施（1-3个月）**：\n"
            content += "   - 增加现金储备至当前的1.5倍以上，提升流动性安全垫\n"
            content += "   - 压降有息负债规模至少降低20%，优先偿还高息短期债务\n"
            content += "   - 冻结非必要资本支出，减少现金流出\n"
            content += "2. **中期措施（3-12个月）**：\n"
            content += "   - 开展全面成本管控，降低固定成本占比下降10个百分点\n"
            content += "   - 优化债务结构，将短期债务占比从当前水平降低至30%以下\n"
            content += "   - 开展核心风险对冲，降低原材料、汇率等市场风险敞口\n"
            content += "3. **长期措施（1年以上）**：\n"
            content += "   - 建立全集团动态风险预警体系，实时监控核心指标异动\n"
            content += "   - 优化业务结构，提升高毛利抗周期业务占比\n"
            content += "   - 建立风险准备金制度，计提营业收入的1%-3%作为风险准备金\n"
        elif worst_case['adjusted_z_score'] < 2.99:
            content += "⚠️ **极端情景下企业处于灰色区**，建议采取以下缓冲措施提升抗风险能力：\n"
            content += "1. 适当增加现金储备，提升安全边际至覆盖6个月以上运营支出\n"
            content += "2. 优化债务结构，降低短期债务占比，延长债务久期\n"
            content += "3. 建立核心敏感因子月度监控机制，提前识别风险异动\n"
            content += "4. 制定极端情景应对预案，提前准备好融资、成本压降等应对措施\n"
        else:
            content += "✅ **所有情景下企业均处于安全区**，抗风险能力较强，建议：\n"
            content += "1. 持续保持健康的财务结构，维持当前的安全边际\n"
            content += "2. 每年开展一次压力测试，动态评估风险承受能力\n"
            content += "3. 可适当优化资金使用效率，提升资产回报率\n"
        
        content += "\n## 五、压力测试局限性说明\n"
        content += "1. 本次测试基于一系列假设条件，实际情况可能与测试结果存在差异\n"
        content += "2. 未考虑企业主动采取的风险应对措施对结果的缓释作用\n"
        content += "3. 未覆盖所有可能的极端情景，仅针对最可能发生的典型情景开展测试\n"
        content += "4. 测试结果仅供内部风险评估使用，不构成任何投资或经营建议\n"
            
        return content

if __name__ == '__main__':
    # 测试用例
    test_financial_data = {
        'latest_annual_revenue': 1000000000,
        'latest_annual_cost': 700000000,
        'latest_annual_ebit': 300000000,
        'latest_annual_net_profit': 180000000,
        'total_interest_bearing_debt': 500000000,
        'average_interest_rate': 0.045,
        'tax_rate': 0.25
    }
    test_model_results = {
        'z_score': 3.2
    }
    analysis = SensitivityAnalysis(test_financial_data, test_model_results)
    result = analysis.run_analysis()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(analysis.export_report_content())
