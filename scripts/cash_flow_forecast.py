#!/usr/bin/env python3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

class CashFlowForecast:
    def __init__(self, financial_data, forecast_months=24):
        self.financial_data = financial_data
        self.forecast_months = forecast_months
        self.growth_rate = financial_data.get('historical_growth_rate', 0.05)
        self.cash_inflow_ratio = financial_data.get('cash_inflow_ratio', 0.85)
        self.cash_outflow_ratio = financial_data.get('cash_outflow_ratio', 0.75)
        self.results = {}
        
    def run_forecast(self):
        # 生成预测日期序列
        start_date = datetime.now()
        dates = [start_date + timedelta(days=30*i) for i in range(self.forecast_months)]
        
        # 基础现金流预测
        base_revenue = self.financial_data['latest_monthly_revenue']
        revenues = [base_revenue * (1 + self.growth_rate) ** (i/12) for i in range(self.forecast_months)]
        
        # 现金流入：营收*流入比例 + 融资收入 + 投资收益
        cash_inflows = []
        for i, rev in enumerate(revenues):
            inflow = rev * self.cash_inflow_ratio
            # 添加季节性调整
            if i % 12 in [11, 0]: # 12月、1月回款高峰
                inflow *= 1.2
            cash_inflows.append(inflow)
            
        # 现金流出：成本*流出比例 + 资本支出 + 税费 + 债务偿还
        cash_outflows = []
        base_cost = self.financial_data['latest_monthly_cost']
        for i, rev in enumerate(revenues):
            outflow = base_cost * self.cash_outflow_ratio
            # 季度付款调整
            if i % 3 == 2:
                outflow *= 1.3
            cash_outflows.append(outflow)
            
        # 计算净现金流和累计现金流
        net_cash_flows = [inflow - outflow for inflow, outflow in zip(cash_inflows, cash_outflows)]
        cumulative_cash = [self.financial_data['current_cash']]
        for ncf in net_cash_flows:
            cumulative_cash.append(cumulative_cash[-1] + ncf)
            
        # 识别现金流缺口
        gaps = []
        for i, cash in enumerate(cumulative_cash[1:]):
            if cash < self.financial_data.get('cash_safety_threshold', 10000000):
                gaps.append({
                    'month': i+1,
                    'date': dates[i].strftime('%Y-%m'),
                    'cash_balance': round(cash, 2),
                    'gap_amount': round(self.financial_data['cash_safety_threshold'] - cash, 2),
                    'risk_level': 'red' if cash < 0 else 'orange'
                })
                
        self.results = {
            'forecast_period': f"{start_date.strftime('%Y-%m')} 至 {(start_date + timedelta(days=30*self.forecast_months)).strftime('%Y-%m')}",
            'dates': [d.strftime('%Y-%m') for d in dates],
            'monthly_revenue': [round(r, 2) for r in revenues],
            'monthly_cash_inflow': [round(ci, 2) for ci in cash_inflows],
            'monthly_cash_outflow': [round(co, 2) for co in cash_outflows],
            'monthly_net_cash_flow': [round(ncf, 2) for ncf in net_cash_flows],
            'cumulative_cash_balance': [round(cc, 2) for cc in cumulative_cash[1:]],
            'cash_gaps': gaps,
            'max_cash_shortfall': round(max([0] + [g['gap_amount'] for g in gaps]), 2),
            'minimum_cash_requirement': self.financial_data.get('cash_safety_threshold', 10000000)
        }
        
        return self.results
    
    def export_report_content(self):
        content = f"""# 三级联动现金流预测报告
## 预测范围
{self.results['forecast_period']}（共{self.forecast_months}个月）

## 核心假设
- 营收年增长率：{self.growth_rate*100:.1f}%
- 营收现金流入比例：{self.cash_inflow_ratio*100:.1f}%
- 成本现金流出比例：{self.cash_outflow_ratio*100:.1f}%
- 最低现金安全阈值：{self.results['minimum_cash_requirement']:,} 元

## 预测结果
| 月份 | 月度营收（万元） | 现金流入（万元） | 现金流出（万元） | 净现金流（万元） | 累计现金余额（万元） |
|------|------------------|------------------|------------------|------------------|----------------------|
"""
        for i in range(min(12, self.forecast_months)):
            content += f"| {self.results['dates'][i]} | {self.results['monthly_revenue'][i]/10000:.1f} | {self.results['monthly_cash_inflow'][i]/10000:.1f} | {self.results['monthly_cash_outflow'][i]/10000:.1f} | {self.results['monthly_net_cash_flow'][i]/10000:.1f} | {self.results['cumulative_cash_balance'][i]/10000:.1f} |\n"
        
        content += f"\n## 风险预警\n"
        if len(self.results['cash_gaps']) == 0:
            content += "✅ 预测期内现金流充足，无缺口风险\n"
        else:
            content += f"⚠️ 预测期内共发现 {len(self.results['cash_gaps'])} 次现金流缺口，最大缺口金额：{self.results['max_cash_shortfall']/10000:.1f} 万元\n"
            for gap in self.results['cash_gaps']:
                content += f"- {gap['date']}：现金余额 {gap['cash_balance']/10000:.1f} 万元，缺口 {gap['gap_amount']/10000:.1f} 万元，风险等级：{gap['risk_level']}\n"
                
        return content

if __name__ == '__main__':
    # 测试用例
    test_data = {
        'latest_monthly_revenue': 50000000,
        'latest_monthly_cost': 35000000,
        'current_cash': 200000000,
        'historical_growth_rate': 0.08,
        'cash_safety_threshold': 150000000
    }
    forecast = CashFlowForecast(test_data, 24)
    result = forecast.run_forecast()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(forecast.export_report_content())
