#!/usr/bin/env python3
"""
安永财务风险量化模型计算器
支持：Altman Z-score（优化版）、Ohlson O-score、Merton违约概率测算
"""

import math

def calculate_altman_z(X1: float, X2: float, X3: float, X4: float, X5: float) -> tuple[float, str]:
    """
    计算优化版Altman Z-score（制造业适用）
    X1: 营运资本/总资产
    X2: 留存收益/总资产
    X3: 息税前利润/总资产
    X4: 权益市值/总负债
    X5: 销售收入/总资产
    返回：z值，风险等级
    """
    z = 1.2 * X1 + 1.4 * X2 + 3.3 * X3 + 0.6 * X4 + 0.999 * X5
    if z > 2.99:
        level = "安全区，破产风险极低"
    elif 1.81 <= z <= 2.99:
        level = "灰色区，存在一定破产风险"
    else:
        level = "高危区，破产风险较高"
    return round(z, 2), level

def calculate_ohlson_o(
    total_assets: float, 
    total_liabilities: float, 
    working_capital: float, 
    current_liabilities: float, 
    current_assets: float,
    net_income: float,
    funds_from_operations: float,
    loss_last_two_years: int,
    change_in_net_income: float
) -> tuple[float, str]:
    """
    计算Ohlson O-score，识别财报异常风险
    返回：o值，风险等级
    """
    SIZE = math.log(total_assets / 1000000)  # 资产以美元计价，单位百万
    TLTA = total_liabilities / total_assets
    WCTA = working_capital / total_assets
    CLCA = current_liabilities / current_assets
    OENEG = 1 if total_liabilities > total_assets else 0
    NITA = net_income / total_assets
    FUTL = funds_from_operations / total_liabilities
    INTWO = loss_last_two_years  # 过去两年是否亏损，是为1，否为0
    CHIN = change_in_net_income / (abs(net_income) + abs(change_in_net_income))
    
    o = -1.32 - 0.407 * SIZE + 6.03 * TLTA - 1.43 * WCTA + 0.0757 * CLCA - 1.72 * OENEG - 2.37 * NITA - 1.83 * FUTL + 0.285 * INTWO - 0.521 * CHIN
    
    if o < -1.2:
        level = "低风险，财报异常概率<1%"
    elif -1.2 <= o <= 0.5:
        level = "中风险，财报异常概率10%-30%"
    else:
        level = "高风险，财报异常概率>50%"
    return round(o, 2), level

def calculate_merton_pd(
    asset_value: float, 
    asset_volatility: float, 
    debt_value: float, 
    risk_free_rate: float, 
    time_horizon: float = 1.0
) -> tuple[float, str]:
    """
    计算Merton模型违约概率PD
    返回：pd（百分比），风险等级
    """
    d1 = (math.log(asset_value / debt_value) + (risk_free_rate + 0.5 * asset_volatility**2) * time_horizon) / (asset_volatility * math.sqrt(time_horizon))
    d2 = d1 - asset_volatility * math.sqrt(time_horizon)
    pd = round(norm_cdf(-d2) * 100, 2)
    
    if pd < 0.5:
        level = "投资级，极低违约风险"
    elif 0.5 <= pd <= 3:
        level = "投机级，中等违约风险"
    else:
        level = "高风险，违约概率较高"
    return pd, level

def norm_cdf(x: float) -> float:
    """标准正态分布累积分布函数近似计算"""
    return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0

if __name__ == "__main__":
    # 示例：宁德时代2023年核心参数测算
    z, z_level = calculate_altman_z(0.32, 0.28, 0.15, 1.8, 0.85)
    print(f"Altman Z-score: {z}, {z_level}")
    
    pd, pd_level = calculate_merton_pd(12000, 0.25, 4800, 0.03)
    print(f"Merton违约概率: {pd}%, {pd_level}")
