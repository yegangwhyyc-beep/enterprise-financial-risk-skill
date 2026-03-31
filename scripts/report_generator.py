#!/usr/bin/env python3
"""
安永财务风险报告PDF生成器
自动生成符合安永专业规范的PDF风控报告，包含封面、目录、页眉页脚、图表自动排版
"""

import os
from datetime import datetime
import markdown
from weasyprint import HTML, CSS

EY_REPORT_CSS = """
@page {
    size: A4 portrait;
    margin: 2.5cm;
    
    @top-left {
        content: "安永财务风险预测报告";
        font-size: 10pt;
        color: #666;
    }
    @top-right {
        content: "保密 | 仅限内部使用";
        font-size: 10pt;
        color: #666;
    }
    @bottom-center {
        content: "第 " counter(page) " 页，共 " counter(pages) " 页";
        font-size: 9pt;
        color: #666;
    }
}

body {
    font-family: "Microsoft YaHei", "SimSun", sans-serif;
    font-size: 11pt;
    line-height: 1.6;
    color: #333;
}

h1 {
    color: #005EB8; /* 安永蓝 */
    font-size: 18pt;
    border-bottom: 2px solid #005EB8;
    padding-bottom: 8px;
    margin-top: 20px;
    page-break-before: always;
}

h1:first-of-type {
    page-break-before: avoid;
}

h2 {
    color: #005EB8;
    font-size: 14pt;
    margin-top: 16px;
}

h3 {
    font-size: 12pt;
    color: #333;
    margin-top: 12px;
}

.cover-page {
    text-align: center;
    padding-top: 150px;
    page-break-after: always;
}

.cover-title {
    font-size: 24pt;
    color: #005EB8;
    font-weight: bold;
    margin-bottom: 40px;
}

.cover-subtitle {
    font-size: 16pt;
    margin-bottom: 80px;
}

.cover-meta {
    font-size: 12pt;
    line-height: 2;
}

table {
    border-collapse: collapse;
    width: 100%;
    margin: 12px 0;
    page-break-inside: avoid;
}

table th, table td {
    border: 1px solid #ddd;
    padding: 8px;
    font-size: 10pt;
}

table th {
    background-color: #005EB8;
    color: white;
    font-weight: bold;
}

.risk-red {
    color: #D92D20;
    font-weight: bold;
}

.risk-orange {
    color: #F79009;
    font-weight: bold;
}

.risk-yellow {
    color: #F2C94C;
    font-weight: bold;
}

.risk-blue {
    color: #005EB8;
    font-weight: bold;
}

.footer-sign {
    margin-top: 80px;
    text-align: right;
    border-top: 1px solid #ddd;
    padding-top: 20px;
}
"""

def generate_pdf_report(company_name: str, report_content: str, output_path: str = None) -> str:
    """
    生成安永标准PDF风控报告
    :param company_name: 目标企业名称
    :param report_content: markdown格式的报告内容
    :param output_path: 输出PDF路径，默认保存在当前目录
    :return: 生成的PDF文件路径
    """
    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d")
        output_path = f"./{company_name}_财务风险预测报告_{timestamp}.pdf"
    
    # 生成封面
    cover_html = f"""
    <div class="cover-page">
        <div class="cover-title">{company_name}</div>
        <div class="cover-subtitle">集团财务风险预测与管控报告</div>
        <div class="cover-meta">
            <p>安永华明会计师事务所</p>
            <p>发布日期：{datetime.now().strftime("%Y年%m月%d日")}</p>
            <p>文档版本：V1.0</p>
        </div>
    </div>
    """
    
    # 转换markdown内容为HTML
    md = markdown.Markdown(extensions=['tables', 'fenced_code', 'toc'])
    content_html = md.convert(report_content)
    
    # 组合完整HTML
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{company_name}财务风险预测报告</title>
    </head>
    <body>
        {cover_html}
        <h1>目录</h1>
        {md.toc}
        {content_html}
        <div class="footer-sign">
            <p>安永财务风控服务团队</p>
            <p>_________________________</p>
            <p>日期：{datetime.now().strftime("%Y年%m月%d日")}</p>
        </div>
    </body>
    </html>
    """
    
    # 生成PDF
    HTML(string=full_html).write_pdf(
        output_path,
        stylesheets=[CSS(string=EY_REPORT_CSS)]
    )
    
    print(f"✅ PDF报告已生成：{os.path.abspath(output_path)}")
    return os.path.abspath(output_path)

if __name__ == "__main__":
    # 示例使用
    sample_content = """
# 核心结论
宁德时代集团整体财务风险处于极低水平，违约概率仅为0.32%，属于投资级优质企业。

## 风险清单
| 风险等级 | 风险名称 | 敞口 |
| --- | --- | --- |
| <span class="risk-red">红色极高风险</span> | 锂价/汇率双向波动 | 2140亿 |
| <span class="risk-orange">橙色高风险</span> | 单位盈利下行 | 260亿 |
"""
    generate_pdf_report("宁德时代", sample_content)
