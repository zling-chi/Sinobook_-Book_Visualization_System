<div align="center">

# 📚 高校教材网图书数据可视化分析系统

**University Textbook Data Visualization & Analysis System**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3.3-000000?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?style=flat-square&logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Scrapy](https://img.shields.io/badge/Scrapy-2.11-60A839?style=flat-square&logo=scrapy&logoColor=white)](https://scrapy.org/)
[![ECharts](https://img.shields.io/badge/ECharts-5.4.3-AA344D?style=flat-square)](https://echarts.apache.org/)

以[高校教材网](https://www.sinobook.com.cn)为数据来源，基于 Scrapy + Flask + ECharts 构建的教材数据全链路分析平台，覆盖**数据采集 → 清洗存储 → 可视化分析 → 检索推荐**完整流程。

</div>

---

## 项目简介

高校教材网积累了大量教材数据，包括书名、作者、出版社、适用专业、定价、年度等多维字段，但平台本身缺乏系统性的统计分析能力。本项目通过爬虫自动采集约 **9661 页**教材数据，构建可视化大屏与检索推荐系统，帮助教材管理人员快速掌握教材分布规律，也为师生提供便捷的教材查询服务。

---

## 主要功能

### 📊 数据可视化大屏
登录后默认展示数据大屏，通过 ECharts 呈现六类交互式图表：

- **出版社分布** — TOP 10 柱状图
- **适用专业分布** — TOP 10 柱状图  
- **教材类别占比** — 饼图
- **年度教材数量趋势** — 折线图
- **价格区间分布** — 按 0-20 / 20-40 / 40-60 / 60-80 / 80-100 / 100元以上六档统计
- **书名关键词词云** — 基于 jieba 分词，过滤无意义通用词后取高频词 150 个

> 未注册用户也可直接浏览全部图表。

---

### 🔍 图书检索
注册用户可通过关键词对以下字段进行模糊查询：

```
书名 / 作者 / 出版社 / ISBN / 适用专业
```

支持多字段同时命中，每次最多返回 50 条结果。

---

### 🎯 智能推荐
根据用户输入的**专业方向**和**教材级别**，系统通过四维加权打分模型计算推荐系数 R，推荐最匹配的 20 本教材。

| 维度 | 权重 | 说明 |
|------|------|------|
| 教材分级匹配 | 40% | 用户指定级别与教材分级字段完全匹配 |
| 价格适中度 | 20% | 35~65 元区间满分，偏离越多得分越低 |
| 出版年份新旧 | 20% | 2024 年及以后满分，越早出版得分越低 |
| 文本相似度 | 20% | 专业名称出现在书名或适用专业字段中得分 |

---

### ⭐ 图书收藏
注册用户可在检索或浏览时收藏感兴趣的教材，支持随时查看和取消收藏，收藏记录持久化保存。

---

### 👤 用户系统
支持用户注册与登录，密码经 Werkzeug 哈希加密存储。未登录用户可浏览可视化大屏，登录后解锁检索、收藏和推荐功能。

---

## 技术栈

| 层次 | 技术 |
|------|------|
| 数据采集 | Scrapy 2.11（全量爬虫 + 增量爬虫） |
| 数据处理 | Pandas 2.0、jieba 0.42 |
| 数据存储 | MySQL 8.0 |
| 后端服务 | Python Flask 2.3、pymysql、Werkzeug |
| 前端展示 | HTML5 / CSS3 / JavaScript、ECharts 5.4.3 |

---

<div align="center">

广州科技职业技术大学 · 人工智能与大数据学院 · 大数据工程技术专业 · 2026 届毕业设计

</div>
