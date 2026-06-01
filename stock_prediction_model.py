"""
美股預測模型框架：川普言論 × AI 基礎建設雙因子模型
US Stock Prediction Model: Trump Sentiment × AI Infrastructure Multi-Factor Model

資料來源整合：
- 川普 Truth Social 發文情緒（NLP）
- 超大規模業者 CapEx 公告
- AI 基礎建設供應鏈層級指標
- 半導體出口政策狀態
"""

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ─────────────────────────────────────────────
# 資料結構定義
# ─────────────────────────────────────────────

class PolicyStatus(Enum):
    POSITIVE = "positive"    # 利多（解禁、補貼、豁免）
    NEUTRAL = "neutral"
    NEGATIVE = "negative"   # 利空（禁令、威脅、制裁）


class SupplyChainLayer(Enum):
    L1_CHIP = "L1_晶片"
    L2_SERVER = "L2_伺服器/冷卻"
    L3_NETWORK = "L3_網路設備"
    L4_POWER = "L4_電力供應"
    L5_REIT = "L5_資料中心REIT"
    L6_CLOUD = "L6_雲端算力"


@dataclass
class TrumpSignal:
    """川普發言對個股的即時訊號"""
    date: str
    statement: str
    sentiment_score: float          # -1.0 (極負面) ~ +1.0 (極正面)
    affected_tickers: list[str]
    policy_status: PolicyStatus
    expected_impact_pct: float      # 預期股價影響百分比
    historical_similar_impact: float  # 歷史相似事件平均影響
    source: str = ""

    def net_signal(self) -> float:
        """綜合訊號強度"""
        policy_weight = {
            PolicyStatus.POSITIVE: 1.0,
            PolicyStatus.NEUTRAL: 0.0,
            PolicyStatus.NEGATIVE: -1.0,
        }[self.policy_status]
        return (self.sentiment_score * 0.4 + policy_weight * 0.6) * abs(self.expected_impact_pct)


@dataclass
class AICapexIndicator:
    """AI 資本支出領先指標"""
    quarter: str                    # e.g. "2026Q2"
    company: str                    # Hyperscaler 名稱
    capex_billion_usd: float        # 季度 CapEx（億美元）
    yoy_growth_pct: float           # 年增率
    ai_capex_ratio: float           # AI 基礎建設佔 CapEx 比例（0–1）
    guidance_tone: str              # "raised" / "maintained" / "lowered"

    def ai_capex(self) -> float:
        return self.capex_billion_usd * self.ai_capex_ratio


@dataclass
class StockFeatures:
    """個股特徵向量（用於預測模型輸入）"""
    ticker: str
    supply_chain_layer: SupplyChainLayer

    # 基本面因子（權重 25%）
    revenue_growth_yoy: float       # 營收年增率
    revenue_growth_qoq: float       # 營收季增率（加速度更重要）
    backlog_to_bill: float          # 訂單積壓/Book-to-Bill
    gross_margin: float             # 毛利率

    # CapEx 領先指標（權重 30%）
    hyperscaler_capex_growth: float  # 超大規模業者 CapEx 年增率
    customer_concentration: float    # 前三大客戶佔比（高集中 = 高風險）

    # 政策風險（權重 15%）
    china_export_policy: PolicyStatus  # 對中晶片出口政策狀態
    trump_sentiment: float           # 川普對該股/產業的情緒分數（-1 ~ +1）
    subsidy_dependency: float        # 政府補貼依賴度（0–1）

    # 技術分析（權重 20%）
    rsi_14: float                   # RSI 14 日（>70 超買，<30 超賣）
    price_vs_ma200: float           # 與 200 日均線乖離率（%）
    short_interest_pct: float       # 空頭部位比率

    # 市場情緒（權重 10%）
    analyst_target_upside: float    # 分析師目標價上行空間（%）
    news_sentiment_30d: float       # 近 30 日新聞情緒（-1 ~ +1）

    def compute_score(self) -> dict:
        """多因子評分（0–100分）"""

        # 1. 基本面評分（25分滿分）
        fundamental = min(25, (
            self.revenue_growth_yoy * 0.10 +
            self.revenue_growth_qoq * 0.15 +       # 季增率權重更高
            (self.backlog_to_bill - 1.0) * 5 +     # >1 為利多
            (self.gross_margin - 0.3) * 20
        ))

        # 2. CapEx 領先指標評分（30分滿分）
        capex_score = min(30, (
            self.hyperscaler_capex_growth * 0.20 +
            (1 - self.customer_concentration) * 15   # 分散度越高越好
        ))

        # 3. 政策風險評分（15分滿分）
        policy_map = {PolicyStatus.POSITIVE: 15, PolicyStatus.NEUTRAL: 7.5, PolicyStatus.NEGATIVE: 0}
        policy = policy_map[self.china_export_policy]
        trump_adj = self.trump_sentiment * 5  # ±5 分的川普情緒調整
        policy_score = max(0, min(15, policy + trump_adj - self.subsidy_dependency * 5))

        # 4. 技術面評分（20分滿分）
        rsi_score = 10 - abs(self.rsi_14 - 50) / 5  # RSI 接近 50 = 最高分
        ma_score = min(10, max(0, 10 - abs(self.price_vs_ma200) / 5))
        short_penalty = -self.short_interest_pct * 10
        technical = max(0, min(20, rsi_score + ma_score + short_penalty))

        # 5. 市場情緒評分（10分滿分）
        sentiment = min(10, max(0,
            self.analyst_target_upside * 0.05 +
            self.news_sentiment_30d * 5 + 5
        ))

        total = fundamental + capex_score + policy_score + technical + sentiment

        return {
            "ticker": self.ticker,
            "total_score": round(total, 2),
            "breakdown": {
                "fundamental_25": round(fundamental, 2),
                "capex_lead_30": round(capex_score, 2),
                "policy_risk_15": round(policy_score, 2),
                "technical_20": round(technical, 2),
                "sentiment_10": round(sentiment, 2),
            },
            "signal": "強力買入" if total >= 75 else "買入" if total >= 60 else "持有" if total >= 45 else "減碼" if total >= 30 else "賣出"
        }


# ─────────────────────────────────────────────
# 歷史川普訊號資料庫
# ─────────────────────────────────────────────

TRUMP_SIGNAL_DATABASE: list[TrumpSignal] = [
    TrumpSignal(
        date="2024-11-06",
        statement="川普當選，市場預期去管制化與企業減稅",
        sentiment_score=0.9,
        affected_tickers=["JPM", "GS", "BAC", "BTCUSD"],
        policy_status=PolicyStatus.POSITIVE,
        expected_impact_pct=3.5,
        historical_similar_impact=3.2,
    ),
    TrumpSignal(
        date="2025-01-17",
        statement="發行 $TRUMP 迷因幣",
        sentiment_score=0.5,
        affected_tickers=["SOL", "BTCUSD", "COIN"],
        policy_status=PolicyStatus.POSITIVE,
        expected_impact_pct=12.0,
        historical_similar_impact=8.0,
    ),
    TrumpSignal(
        date="2025-03-15",
        statement="宣布國家戰略加密貨幣儲備（含比特幣）",
        sentiment_score=0.85,
        affected_tickers=["BTCUSD", "COIN", "MSTR"],
        policy_status=PolicyStatus.POSITIVE,
        expected_impact_pct=8.2,
        historical_similar_impact=6.5,
    ),
    TrumpSignal(
        date="2025-04-02",
        statement="宣布解放日互惠關稅（幾乎所有國家）",
        sentiment_score=-0.95,
        affected_tickers=["NKE", "AAPL", "AMZN", "SPY", "QQQ"],
        policy_status=PolicyStatus.NEGATIVE,
        expected_impact_pct=-12.0,
        historical_similar_impact=-10.5,
    ),
    TrumpSignal(
        date="2025-04-09",
        statement="Truth Social「THIS IS A GREAT TIME TO BUY!!!」→ 隨即宣布 90 天關稅暫停",
        sentiment_score=0.98,
        affected_tickers=["SPY", "QQQ", "AAPL", "NKE"],
        policy_status=PolicyStatus.POSITIVE,
        expected_impact_pct=9.5,
        historical_similar_impact=8.8,
    ),
    TrumpSignal(
        date="2025-04-21",
        statement="稱鮑威爾為「重大失敗者」，暗示解雇",
        sentiment_score=-0.8,
        affected_tickers=["SPY", "DJI", "QQQ", "GLD", "UUP"],
        policy_status=PolicyStatus.NEGATIVE,
        expected_impact_pct=-2.4,
        historical_similar_impact=-2.1,
    ),
    TrumpSignal(
        date="2025-04-23",
        statement="聲稱「無意解雇鮑威爾」",
        sentiment_score=0.75,
        affected_tickers=["SPY", "DJI"],
        policy_status=PolicyStatus.POSITIVE,
        expected_impact_pct=1.5,
        historical_similar_impact=1.3,
    ),
    TrumpSignal(
        date="2025-04-12",
        statement="豁免手機、電腦、晶片免受關稅",
        sentiment_score=0.85,
        affected_tickers=["AAPL", "DELL", "NVDA", "AMD"],
        policy_status=PolicyStatus.POSITIVE,
        expected_impact_pct=2.5,
        historical_similar_impact=2.2,
    ),
    TrumpSignal(
        date="2025-07-04",
        statement="大美麗法案廢除 7,500 美元 EV 補貼（2025/9/30 截止）",
        sentiment_score=-0.7,
        affected_tickers=["RIVN", "GM", "F", "TSLA"],
        policy_status=PolicyStatus.NEGATIVE,
        expected_impact_pct=-5.0,
        historical_similar_impact=-4.2,
    ),
    TrumpSignal(
        date="2025-08-22",
        statement="政府取得 Intel 10% 股權（89 億美元 CHIPS 投資）",
        sentiment_score=0.9,
        affected_tickers=["INTC"],
        policy_status=PolicyStatus.POSITIVE,
        expected_impact_pct=6.0,
        historical_similar_impact=5.5,
    ),
    TrumpSignal(
        date="2025-09-24",
        statement="稱烏克蘭可收復全部領土",
        sentiment_score=0.7,
        affected_tickers=["LMT", "RTX", "NOC"],
        policy_status=PolicyStatus.POSITIVE,
        expected_impact_pct=1.2,
        historical_similar_impact=1.0,
    ),
    TrumpSignal(
        date="2025-07-01",
        statement="川普 Truth Social 警告撤銷 Tesla 政府補貼，稱馬斯克「不合規」",
        sentiment_score=-0.9,
        affected_tickers=["TSLA"],
        policy_status=PolicyStatus.NEGATIVE,
        expected_impact_pct=-7.0,
        historical_similar_impact=-6.5,
    ),
    TrumpSignal(
        date="2025-07-25",
        statement="川普稱太陽能「愚蠢且醜陋」",
        sentiment_score=-0.85,
        affected_tickers=["FSLR", "ENPH", "SUNRUN"],
        policy_status=PolicyStatus.NEGATIVE,
        expected_impact_pct=-5.5,
        historical_similar_impact=-5.0,
    ),
]


# ─────────────────────────────────────────────
# AI 基礎建設 CapEx 追蹤資料（2025–2026）
# ─────────────────────────────────────────────

AI_CAPEX_DATA: list[AICapexIndicator] = [
    AICapexIndicator("2025Q1", "Microsoft",  210, 78, 0.75, "raised"),
    AICapexIndicator("2025Q1", "Alphabet",   170, 65, 0.70, "raised"),
    AICapexIndicator("2025Q1", "Amazon",     250, 55, 0.65, "maintained"),
    AICapexIndicator("2025Q1", "Meta",       140, 90, 0.80, "raised"),
    AICapexIndicator("2025Q2", "Microsoft",  230, 84, 0.78, "raised"),
    AICapexIndicator("2025Q2", "Alphabet",   185, 72, 0.72, "raised"),
    AICapexIndicator("2026Q1", "Microsoft",  300, 43, 0.80, "raised"),
    AICapexIndicator("2026Q1", "Alphabet",   220, 35, 0.75, "maintained"),
    AICapexIndicator("2026Q1", "Amazon",     340, 36, 0.70, "raised"),
    AICapexIndicator("2026Q1", "Meta",       175, 25, 0.82, "raised"),
]


# ─────────────────────────────────────────────
# 個股特徵範例資料（2026 年 6 月快照）
# ─────────────────────────────────────────────

STOCK_SNAPSHOT_2026Q2: list[StockFeatures] = [
    StockFeatures(
        ticker="NVDA",
        supply_chain_layer=SupplyChainLayer.L1_CHIP,
        revenue_growth_yoy=0.65, revenue_growth_qoq=0.18,
        backlog_to_bill=2.5, gross_margin=0.74,
        hyperscaler_capex_growth=0.45, customer_concentration=0.55,
        china_export_policy=PolicyStatus.NEGATIVE,
        trump_sentiment=0.1, subsidy_dependency=0.1,
        rsi_14=62, price_vs_ma200=18, short_interest_pct=0.02,
        analyst_target_upside=25, news_sentiment_30d=0.7,
    ),
    StockFeatures(
        ticker="AVGO",
        supply_chain_layer=SupplyChainLayer.L1_CHIP,
        revenue_growth_yoy=0.50, revenue_growth_qoq=0.22,
        backlog_to_bill=3.0, gross_margin=0.68,
        hyperscaler_capex_growth=0.45, customer_concentration=0.45,
        china_export_policy=PolicyStatus.NEUTRAL,
        trump_sentiment=0.2, subsidy_dependency=0.05,
        rsi_14=58, price_vs_ma200=12, short_interest_pct=0.018,
        analyst_target_upside=30, news_sentiment_30d=0.75,
    ),
    StockFeatures(
        ticker="VRT",
        supply_chain_layer=SupplyChainLayer.L2_SERVER,
        revenue_growth_yoy=0.46, revenue_growth_qoq=0.15,
        backlog_to_bill=3.0, gross_margin=0.36,
        hyperscaler_capex_growth=0.45, customer_concentration=0.40,
        china_export_policy=PolicyStatus.NEUTRAL,
        trump_sentiment=0.3, subsidy_dependency=0.05,
        rsi_14=55, price_vs_ma200=25, short_interest_pct=0.03,
        analyst_target_upside=35, news_sentiment_30d=0.8,
    ),
    StockFeatures(
        ticker="ANET",
        supply_chain_layer=SupplyChainLayer.L3_NETWORK,
        revenue_growth_yoy=0.35, revenue_growth_qoq=0.12,
        backlog_to_bill=2.0, gross_margin=0.64,
        hyperscaler_capex_growth=0.45, customer_concentration=0.48,
        china_export_policy=PolicyStatus.NEUTRAL,
        trump_sentiment=0.2, subsidy_dependency=0.02,
        rsi_14=52, price_vs_ma200=8, short_interest_pct=0.025,
        analyst_target_upside=20, news_sentiment_30d=0.65,
    ),
    StockFeatures(
        ticker="CEG",
        supply_chain_layer=SupplyChainLayer.L4_POWER,
        revenue_growth_yoy=0.15, revenue_growth_qoq=0.04,
        backlog_to_bill=1.5, gross_margin=0.28,
        hyperscaler_capex_growth=0.45, customer_concentration=0.35,
        china_export_policy=PolicyStatus.NEUTRAL,
        trump_sentiment=0.4, subsidy_dependency=0.20,
        rsi_14=48, price_vs_ma200=5, short_interest_pct=0.02,
        analyst_target_upside=22, news_sentiment_30d=0.6,
    ),
    StockFeatures(
        ticker="INTC",
        supply_chain_layer=SupplyChainLayer.L1_CHIP,
        revenue_growth_yoy=0.08, revenue_growth_qoq=0.05,
        backlog_to_bill=1.2, gross_margin=0.42,
        hyperscaler_capex_growth=0.45, customer_concentration=0.30,
        china_export_policy=PolicyStatus.NEGATIVE,
        trump_sentiment=0.8,  # 川普政府直接入股，高正面情緒
        subsidy_dependency=0.40,  # 高度依賴 CHIPS 法案補助
        rsi_14=70, price_vs_ma200=35, short_interest_pct=0.04,
        analyst_target_upside=15, news_sentiment_30d=0.7,
    ),
    StockFeatures(
        ticker="SMCI",
        supply_chain_layer=SupplyChainLayer.L2_SERVER,
        revenue_growth_yoy=0.30, revenue_growth_qoq=0.08,
        backlog_to_bill=1.8, gross_margin=0.14,
        hyperscaler_capex_growth=0.45, customer_concentration=0.55,
        china_export_policy=PolicyStatus.NEGATIVE,  # 走私醜聞
        trump_sentiment=-0.5,  # 走私調查為負面
        subsidy_dependency=0.05,
        rsi_14=35, price_vs_ma200=-35, short_interest_pct=0.18,
        analyst_target_upside=40,  # 高潛在反彈，但風險極高
        news_sentiment_30d=-0.4,
    ),
    StockFeatures(
        ticker="TSLA",
        supply_chain_layer=SupplyChainLayer.L2_SERVER,  # FSD/AI 計算基礎建設
        revenue_growth_yoy=-0.05, revenue_growth_qoq=-0.02,
        backlog_to_bill=1.0, gross_margin=0.18,
        hyperscaler_capex_growth=0.10, customer_concentration=0.20,
        china_export_policy=PolicyStatus.NEUTRAL,
        trump_sentiment=-0.8,  # 川普-馬斯克決裂
        subsidy_dependency=0.15,  # EV 補貼廢止影響
        rsi_14=38, price_vs_ma200=-30, short_interest_pct=0.10,
        analyst_target_upside=30,
        news_sentiment_30d=-0.3,
    ),
]


# ─────────────────────────────────────────────
# 預測引擎
# ─────────────────────────────────────────────

class StockPredictionEngine:
    """
    多因子股票預測引擎
    整合川普言論風險 + AI 基礎建設 CapEx 領先指標
    """

    def __init__(
        self,
        stocks: list[StockFeatures],
        trump_signals: list[TrumpSignal],
        capex_data: list[AICapexIndicator],
    ):
        self.stocks = stocks
        self.trump_signals = trump_signals
        self.capex_data = capex_data

    def get_latest_capex_growth(self) -> float:
        """取得最新超大規模業者平均 CapEx 年增率"""
        if not self.capex_data:
            return 0.0
        latest_quarter = sorted(self.capex_data, key=lambda x: x.quarter)[-4:]
        return sum(c.yoy_growth_pct for c in latest_quarter) / len(latest_quarter) / 100

    def get_trump_impact(self, ticker: str) -> float:
        """
        取得近期川普訊號對特定個股的綜合影響分數
        只考慮最近 90 天的訊號
        """
        relevant = [s for s in self.trump_signals if ticker in s.affected_tickers]
        if not relevant:
            return 0.0
        # 加權平均（越近期權重越高，簡化為等權重）
        return sum(s.net_signal() for s in relevant[-3:]) / max(1, len(relevant[-3:]))

    def rank_stocks(self) -> list[dict]:
        """對所有股票評分並排名"""
        results = []
        for stock in self.stocks:
            score_data = stock.compute_score()
            trump_adj = self.get_trump_impact(stock.ticker)
            final_score = min(100, max(0, score_data["total_score"] + trump_adj))

            results.append({
                **score_data,
                "trump_signal_adj": round(trump_adj, 2),
                "final_score": round(final_score, 2),
                "layer": stock.supply_chain_layer.value,
                "final_signal": (
                    "強力買入" if final_score >= 75 else
                    "買入"    if final_score >= 60 else
                    "持有"    if final_score >= 45 else
                    "減碼"    if final_score >= 30 else
                    "賣出"
                )
            })

        return sorted(results, key=lambda x: x["final_score"], reverse=True)

    def generate_report(self) -> str:
        """生成預測報告"""
        rankings = self.rank_stocks()
        capex_growth = self.get_latest_capex_growth()

        lines = [
            "=" * 60,
            "美股預測模型：川普言論 × AI 基礎建設雙因子報告",
            f"超大規模業者平均 CapEx 年增率：{capex_growth:.1%}",
            "=" * 60,
            f"{'排名':<4} {'代號':<8} {'層級':<16} {'綜合分數':<10} {'川普調整':<10} {'訊號'}",
            "-" * 60,
        ]

        for i, r in enumerate(rankings, 1):
            lines.append(
                f"{i:<4} {r['ticker']:<8} {r['layer']:<16} "
                f"{r['final_score']:<10.1f} {r['trump_signal_adj']:+<10.2f} {r['final_signal']}"
            )

        lines += [
            "=" * 60,
            "分項評分詳情：",
        ]
        for r in rankings:
            b = r["breakdown"]
            lines.append(
                f"  {r['ticker']}: 基本面={b['fundamental_25']:.1f}/25 "
                f"CapEx領先={b['capex_lead_30']:.1f}/30 "
                f"政策={b['policy_risk_15']:.1f}/15 "
                f"技術={b['technical_20']:.1f}/20 "
                f"情緒={b['sentiment_10']:.1f}/10"
            )

        return "\n".join(lines)


# ─────────────────────────────────────────────
# 主程式
# ─────────────────────────────────────────────

if __name__ == "__main__":
    engine = StockPredictionEngine(
        stocks=STOCK_SNAPSHOT_2026Q2,
        trump_signals=TRUMP_SIGNAL_DATABASE,
        capex_data=AI_CAPEX_DATA,
    )

    report = engine.generate_report()
    print(report)

    # 匯出 JSON 供後續機器學習使用
    rankings = engine.rank_stocks()
    with open("stock_predictions_2026Q2.json", "w", encoding="utf-8") as f:
        json.dump(rankings, f, ensure_ascii=False, indent=2)

    print("\n✅ 預測結果已匯出至 stock_predictions_2026Q2.json")
    print("\n📌 模型使用說明：")
    print("  1. 更新 STOCK_SNAPSHOT_2026Q2 中各股的即時財務指標")
    print("  2. 在 TRUMP_SIGNAL_DATABASE 加入最新川普發言事件")
    print("  3. 在 AI_CAPEX_DATA 加入最新超大規模業者財報數字")
    print("  4. 執行此腳本獲取最新排名與建議")
