"""
個人持倉分析與預測模型
帳戶：98625627
總值：$117,383.15（截至 2026-06-01）
今日：-$2,817.04 (-2.34%)
購買力：$21,472.13

持倉清單（來源：截圖）：
  AMD   1 股     成本 $242.70
  DUOL  10 股    成本 $192.33/股
  GFS   10 股    成本 $70.51/股
  GOOGL 20.01 股 成本 $318.07/股
  INTC  200 股   成本 $68.66/股
  META  0.006 股 成本 $663.65/股（零股，可忽略）
  NVDA  70.01 股 成本 $177.95/股
  O     29.04 股 成本 $62.25/股
  ONL   0.594 股 成本 $18.38/股（零股，可忽略）
  QQQ   1.00 股  成本 $608.16/股
  TSLA  110 股   成本 $396.25/股  ← 最大部位，高度集中！
  VT    0.838 股 成本 $110.96/股（零股，可忽略）
"""

from dataclasses import dataclass, field
from enum import Enum


# ──────────────────────────────────────────
# 資料結構
# ──────────────────────────────────────────

class Signal(Enum):
    STRONG_BUY  = "★★★★★ 強力買入"
    BUY         = "★★★★☆ 買入"
    HOLD        = "★★★☆☆ 持有"
    REDUCE      = "★★☆☆☆ 減碼"
    SELL        = "★☆☆☆☆ 賣出"

class RiskLevel(Enum):
    LOW    = "低"
    MEDIUM = "中"
    HIGH   = "高"
    EXTREME = "極高"


@dataclass
class Holding:
    ticker: str
    shares: float
    avg_cost: float          # 平均成本（美元/股）
    current_price: float     # 當前市價（需定期更新）
    category: str            # 分類

    # 多因子評分輸入（0–10 分）
    fundamental_score: float    # 基本面（營收成長、毛利率、訂單）
    ai_capex_score: float       # AI CapEx 受益程度
    trump_risk_score: float     # 川普政策風險（越高越危險）
    technical_score: float      # 技術面（RSI、均線）
    sentiment_score: float      # 市場情緒、分析師看法

    # 補充資訊
    trump_exposure: str = ""    # 與川普相關的主要風險
    key_catalyst: str = ""      # 近期最重要催化因子
    key_risk: str = ""          # 最大風險

    @property
    def total_cost(self) -> float:
        return self.shares * self.avg_cost

    @property
    def current_value(self) -> float:
        return self.shares * self.current_price

    @property
    def unrealized_pnl(self) -> float:
        return self.current_value - self.total_cost

    @property
    def unrealized_pct(self) -> float:
        return (self.unrealized_pnl / self.total_cost) * 100 if self.total_cost else 0

    def composite_score(self) -> float:
        """
        綜合評分（0–100）
        權重：基本面25% + AI CapEx 30% + 技術面20% + 情緒10% - 川普風險15%
        """
        raw = (
            self.fundamental_score * 2.5 +
            self.ai_capex_score    * 3.0 +
            self.technical_score   * 2.0 +
            self.sentiment_score   * 1.0 -
            self.trump_risk_score  * 1.5   # 風險扣分
        )
        return max(0.0, min(100.0, raw))

    def signal(self) -> Signal:
        s = self.composite_score()
        if s >= 75: return Signal.STRONG_BUY
        if s >= 60: return Signal.BUY
        if s >= 45: return Signal.HOLD
        if s >= 30: return Signal.REDUCE
        return Signal.SELL

    def trump_risk_level(self) -> RiskLevel:
        r = self.trump_risk_score
        if r <= 2:  return RiskLevel.LOW
        if r <= 4:  return RiskLevel.MEDIUM
        if r <= 7:  return RiskLevel.HIGH
        return RiskLevel.EXTREME


# ──────────────────────────────────────────
# 持倉資料（2026-06-01 快照）
# ★ 請每週更新 current_price ★
# ──────────────────────────────────────────

PORTFOLIO: list[Holding] = [

    Holding(
        ticker="TSLA", shares=110, avg_cost=396.25,
        current_price=426.0,          # 更新：2026-06 約 $420–445
        category="EV/AI機器人/自動駕駛",
        fundamental_score=5.0,        # FSD 用戶 +51% YoY；但車輛毛利率偏低
        ai_capex_score=6.0,           # Dojo 超級電腦 + FSD 算力需求
        trump_risk_score=9.5,         # 川普-馬斯克決裂後補貼威脅；最高風險
        technical_score=5.5,          # 從高峰-50%後反彈至 $420 附近
        sentiment_score=6.0,          # Robotaxi 正式商用（達拉斯、休士頓）
        trump_exposure="川普威脅撤銷 Tesla 政府補貼；EV 補貼已廢止（2025/9/30）",
        key_catalyst="Robotaxi 商用規模化 + FSD 中國監管批准",
        key_risk="★ 最大風險：持倉過度集中（53% 成本佔比）+ 川普政策不確定",
    ),

    Holding(
        ticker="INTC", shares=200, avg_cost=68.66,
        current_price=125.0,          # 估算：政府入股後 2026 大漲，約 $100–135
        category="半導體/AI晶圓代工",
        fundamental_score=5.5,        # 營收回暖，18A 製程量產
        ai_capex_score=7.5,           # 川普政府直接入股 10%（$89億 CHIPS 投資）
        trump_risk_score=4.0,         # 高度依賴政府補貼（若川普政策轉向有風險）
        technical_score=7.5,          # 2026 年 YTD 漲幅巨大（估 +80% 以上）
        sentiment_score=8.0,          # 蘋果晶片代工傳聞 + 政府背書
        trump_exposure="CHIPS 法案受益者；川普若削減補貼則有下行風險",
        key_catalyst="蘋果晶片代工合約落地 + 18A 良率提升",
        key_risk="製程落後 TSMC/三星；補貼依賴度高達 40%",
    ),

    Holding(
        ticker="NVDA", shares=70.01, avg_cost=177.95,
        current_price=211.0,          # 來源：2026-06-01 pre-market $215.91
        category="AI晶片/GPU/CUDA生態",
        fundamental_score=9.5,        # FY26 資料中心收入 $1,973億（+71% YoY）
        ai_capex_score=10.0,          # AI CapEx 最直接受益者，無可撼動龍頭
        trump_risk_score=5.5,         # 中國 AI 晶片出口禁令反覆（禁→解禁→再禁）
        technical_score=6.5,          # 已在高位，RSI 偏高
        sentiment_score=9.0,          # 62 Buy / 1 Hold / 0 Sell（分析師共識）
        trump_exposure="川普對中 AI 晶片出口政策反覆；H20 禁令風險持續",
        key_catalyst="Blackwell/GB300 超級晶片週期；Hyperscaler CapEx 持續加碼",
        key_risk="中國出口禁令永久化；AMD/Broadcom ASIC 蠶食份額",
    ),

    Holding(
        ticker="GOOGL", shares=20.01, avg_cost=318.07,
        current_price=190.0,          # 估算：2026-06 後分割調整後約 $185–210
        category="AI平台/雲端/廣告",
        fundamental_score=7.0,        # Google Cloud +35% YoY；AI Overviews 廣告衝擊
        ai_capex_score=7.5,           # 2026 CapEx $1,750–1,850億（AI 佔 75%）
        trump_risk_score=3.0,         # 反壟斷調查；但與川普無直接衝突
        technical_score=4.0,          # 成本 $318（分割調整前）vs 現價 ~$190，帳面虧損
        sentiment_score=6.5,          # Gemini AI 競爭力強，但廣告市場壓力
        trump_exposure="司法部反壟斷訴訟；廣告市場受關稅通膨間接衝擊",
        key_catalyst="Gemini 2.0 滲透率提升 + Google Cloud 加速成長",
        key_risk="成本基礎（分割前）$318 → 現價約 $190，帳面虧損 ~40%",
    ),

    Holding(
        ticker="DUOL", shares=10, avg_cost=192.33,
        current_price=109.0,          # 來源：分析師目標 $104.55（-4.2% from current）
        category="AI教育科技",
        fundamental_score=7.0,        # Q1 2026 營收 $292M 超預期；DAU +21% YoY
        ai_capex_score=5.0,           # AI 用於內容生成（Q1 產出 20,500 課程單元）
        trump_risk_score=1.5,         # 幾乎無川普直接風險
        technical_score=3.5,          # 成本 $192.33 vs 現價 $109，帳面虧損 ~43%
        sentiment_score=5.0,          # 23 分析師評為 Hold；平均目標 $104.55
        trump_exposure="無直接川普政策風險",
        key_catalyst="AI 驅動內容規模化；DUOL Max 訂閱滲透率提升",
        key_risk="成本遠高於現價（-43%）；教育科技估值仍然偏高",
    ),

    Holding(
        ticker="GFS", shares=10, avg_cost=70.51,
        current_price=40.0,           # 估算：GFS 近年 $30–50 區間
        category="半導體晶圓代工",
        fundamental_score=4.5,        # Q2 2025 營收 $1.69B；毛利率 25.2%（偏低）
        ai_capex_score=4.0,           # 成熟製程受益有限（非 AI 前沿製程）
        trump_risk_score=3.0,         # CHIPS 法案次要受益者；關稅可能影響客戶
        technical_score=3.5,          # 成本 $70.51 vs 現價 ~$40，帳面虧損 ~43%
        sentiment_score=4.5,          # IBM 和解 + 德勒斯頓擴廠利多，但分析師謹慎
        trump_exposure="美國製造政策次要受益；客戶受關稅衝擊間接影響",
        key_catalyst="Renesas 擴大合作；GaN 技術（Navitas 合作）",
        key_risk="成本遠高於現價（-43%）；與台積電、三星競爭激烈",
    ),

    Holding(
        ticker="AMD", shares=1, avg_cost=242.70,
        current_price=115.0,          # 估算：2026-06 約 $110–125
        category="AI晶片/GPU/CPU",
        fundamental_score=6.0,        # MI300X 有競爭力；但市占率遠低於 NVDA
        ai_capex_score=6.5,           # 受益 AI 投資浪潮，但為第二選擇
        trump_risk_score=5.0,         # 中國出口禁令同樣影響 AMD（MI308 禁令）
        technical_score=3.0,          # 成本 $242.70 vs 現價 ~$115，帳面虧損 ~53%
        sentiment_score=5.5,          # 分析師普遍積極但目標低於 NVDA 溢價
        trump_exposure="中國 AI 晶片出口禁令（MI308 反覆）",
        key_catalyst="MI350/MI400 系列競爭力提升",
        key_risk="成本 $242.70 已嚴重落後（-53%）；NVDA 護城河難以撼動",
    ),

    Holding(
        ticker="O", shares=29.04, avg_cost=62.25,
        current_price=55.0,           # 估算：REIT 在利率下降環境約 $53–58
        category="月配息REIT",
        fundamental_score=6.5,        # 第 114 次連續季度提高股息；AFFO $4.28/股
        ai_capex_score=1.0,           # 與 AI 基礎建設無直接關聯
        trump_risk_score=2.0,         # 利率政策間接影響；川普要求降息有利
        technical_score=5.0,          # 聯準會降息週期支撐，但仍低於成本
        sentiment_score=6.0,          # 5.07% 股息殖利率具吸引力；信用評等穩定
        trump_exposure="川普要求降息 → 利率下行有利 REIT",
        key_catalyst="聯準會持續降息；月配息防禦性質",
        key_risk="成本 $62.25 vs 現價 ~$55，小幅虧損；辦公室空置率壓力",
    ),

    Holding(
        ticker="QQQ", shares=1.00, avg_cost=608.16,
        current_price=545.0,          # 估算：2026-06 Nasdaq 100 ETF
        category="那斯達克100 ETF",
        fundamental_score=7.5,        # 追蹤那斯達克 100，AI 股高佔比
        ai_capex_score=8.0,           # NVDA、MSFT、META、AMZN 等 AI 重股
        trump_risk_score=4.0,         # 科技股整體承受川普關稅 + Fed 風險
        technical_score=5.0,          # 成本 $608.16，現價 ~$545，小幅虧損
        sentiment_score=7.5,          # AI 牛市主要受益指數
        trump_exposure="整體科技股受川普關稅 + 聯準會政策影響",
        key_catalyst="AI 牛市持續；Hyperscaler 財報強勁",
        key_risk="估值集中於少數科技巨頭；與個別持股高度重疊",
    ),

    # 微小零股部位（實際影響力可忽略）
    Holding(
        ticker="META", shares=0.00553, avg_cost=663.65,
        current_price=700.0,          # META 2026 年在 AI 廣告業務帶動下強勁
        category="AI社群平台（零股）",
        fundamental_score=8.5,
        ai_capex_score=8.0,
        trump_risk_score=2.0,
        technical_score=7.0,
        sentiment_score=8.0,
        trump_exposure="廣告市場受關稅通膨間接影響",
        key_catalyst="AI 廣告精準化 + Llama AI 開源生態",
        key_risk="部位過小（$3.67），無實質影響",
    ),

    Holding(
        ticker="ONL", shares=0.594, avg_cost=18.38,
        current_price=9.5,            # 辦公室 REIT 持續承壓
        category="辦公室REIT（零股）",
        fundamental_score=2.0,
        ai_capex_score=0.5,
        trump_risk_score=2.0,
        technical_score=2.0,
        sentiment_score=2.0,
        trump_exposure="WFH 政策 + 辦公室空置率挑戰",
        key_catalyst="資產出售策略",
        key_risk="部位過小（$10.92），且辦公室 REIT 基本面惡化",
    ),

    Holding(
        ticker="VT", shares=0.838, avg_cost=110.96,
        current_price=115.0,
        category="全球股票ETF（零股）",
        fundamental_score=6.0,
        ai_capex_score=4.0,
        trump_risk_score=3.0,
        technical_score=6.0,
        sentiment_score=6.0,
        trump_exposure="全球關稅戰影響全球股市",
        key_catalyst="美股以外市場估值修復",
        key_risk="部位過小（$93），無實質影響",
    ),
]


# ──────────────────────────────────────────
# 分析引擎
# ──────────────────────────────────────────

class PortfolioAnalyzer:

    def __init__(self, holdings: list[Holding], account_value: float):
        self.holdings = holdings
        self.account_value = account_value

    # ── 持倉集中度 ──────────────────────────
    def concentration_report(self) -> str:
        total_value = sum(h.current_value for h in self.holdings)
        rows = sorted(self.holdings, key=lambda h: h.current_value, reverse=True)
        lines = [
            "=" * 65,
            "【持倉集中度分析】",
            f"{'代號':<6} {'現值':>10} {'佔比':>7} {'成本佔比':>9} {'風險'}",
            "-" * 65,
        ]
        for h in rows:
            pct_value = h.current_value / total_value * 100
            pct_cost  = h.total_cost / sum(x.total_cost for x in self.holdings) * 100
            risk = h.trump_risk_level().value
            lines.append(
                f"{h.ticker:<6} ${h.current_value:>9,.0f} {pct_value:>6.1f}% "
                f"{pct_cost:>8.1f}%  川普風險:{risk}"
            )
        lines.append("=" * 65)
        return "\n".join(lines)

    # ── 損益分析 ──────────────────────────
    def pnl_report(self) -> str:
        lines = [
            "=" * 65,
            "【各持倉損益狀況】",
            f"{'代號':<6} {'持股':<8} {'成本':>8} {'現價':>8} {'損益':>10} {'損益%':>8}",
            "-" * 65,
        ]
        total_pnl = 0.0
        for h in sorted(self.holdings, key=lambda x: x.unrealized_pnl, reverse=True):
            total_pnl += h.unrealized_pnl
            marker = "▲" if h.unrealized_pnl >= 0 else "▼"
            lines.append(
                f"{h.ticker:<6} {h.shares:<8.3f} ${h.avg_cost:>7.2f} ${h.current_price:>7.2f} "
                f"{marker}${abs(h.unrealized_pnl):>8,.0f} {h.unrealized_pct:>+7.1f}%"
            )
        lines += [
            "-" * 65,
            f"{'合計未實現損益':>40} ${total_pnl:>+10,.0f}",
            "=" * 65,
        ]
        return "\n".join(lines)

    # ── 多因子評分 ──────────────────────────
    def scoring_report(self) -> str:
        lines = [
            "=" * 65,
            "【多因子評分與操作建議】",
            f"{'代號':<6} {'綜合分':>6} {'基本':>5} {'CapEx':>6} {'川普風險':>9} {'技術':>5} {'情緒':>5}  訊號",
            "-" * 65,
        ]
        for h in sorted(self.holdings, key=lambda x: x.composite_score(), reverse=True):
            lines.append(
                f"{h.ticker:<6} {h.composite_score():>6.1f} "
                f"{h.fundamental_score:>5.1f} {h.ai_capex_score:>6.1f} "
                f"{h.trump_risk_score:>9.1f} {h.technical_score:>5.1f} "
                f"{h.sentiment_score:>5.1f}  {h.signal().value}"
            )
        lines.append("=" * 65)
        return "\n".join(lines)

    # ── 川普風險地圖 ──────────────────────────
    def trump_risk_map(self) -> str:
        lines = [
            "=" * 65,
            "【川普言論風險地圖】",
            f"{'代號':<6} {'風險等級':<8} {'主要暴露'}",
            "-" * 65,
        ]
        for h in sorted(self.holdings, key=lambda x: x.trump_risk_score, reverse=True):
            lines.append(f"{h.ticker:<6} [{h.trump_risk_level().value:<4}]   {h.trump_exposure[:45]}")
        lines.append("=" * 65)
        return "\n".join(lines)

    # ── 關鍵警示 ──────────────────────────
    def alerts(self) -> str:
        total_cost = sum(h.total_cost for h in self.holdings)
        total_value = sum(h.current_value for h in self.holdings)
        tsla = next(h for h in self.holdings if h.ticker == "TSLA")

        lines = ["=" * 65, "【⚠️  關鍵警示與建議】", ""]

        # 集中度警示
        tsla_pct = tsla.current_value / total_value * 100
        if tsla_pct > 35:
            lines.append(
                f"🔴 極度危險：TSLA 佔總持倉 {tsla_pct:.1f}%！\n"
                f"   單一事件（川普推文/馬斯克爭議/FSD 事故）可導致帳戶單日 -5% 以上。\n"
                f"   建議：分批減碼至 20–25% 以下，設定停損線 $380（成本 $396 下方 4%）。"
            )
        lines.append("")

        # 虧損部位警示
        losers = [h for h in self.holdings if h.unrealized_pct < -20]
        if losers:
            lines.append("🟡 帳面虧損超過 20% 的部位：")
            for h in sorted(losers, key=lambda x: x.unrealized_pct):
                lines.append(f"   {h.ticker}: {h.unrealized_pct:+.1f}%（成本 ${h.avg_cost:.2f} vs 現價 ${h.current_price:.2f}）")
                lines.append(f"   → {h.key_risk}")
        lines.append("")

        # 正面催化
        winners = [h for h in self.holdings if h.composite_score() >= 60]
        if winners:
            lines.append("🟢 強力持有部位（評分 ≥ 60）：")
            for h in sorted(winners, key=lambda x: x.composite_score(), reverse=True):
                lines.append(f"   {h.ticker}（{h.composite_score():.0f}分）：{h.key_catalyst}")
        lines.append("")

        # 購買力建議
        lines.append(
            f"💰 購買力 $21,472 建議用途：\n"
            f"   優先補充：NVDA（評分最高，現有部位可加碼）\n"
            f"   次選考慮：INTC（政府背書、蘋果合約催化）\n"
            f"   避免加碼：TSLA（集中度已過高）、DUOL/GFS/AMD（帳面虧損深）"
        )
        lines.append("=" * 65)
        return "\n".join(lines)

    # ── 完整報告 ──────────────────────────
    def full_report(self) -> str:
        total_cost  = sum(h.total_cost for h in self.holdings)
        total_value = sum(h.current_value for h in self.holdings)
        total_pnl   = total_value - total_cost

        header = "\n".join([
            "=" * 65,
            "  個人持倉分析報告  |  帳戶：98625627  |  2026-06-01",
            "=" * 65,
            f"  帳戶估算總值  ：${total_value:>12,.2f}",
            f"  總成本基礎    ：${total_cost:>12,.2f}",
            f"  未實現損益    ：${total_pnl:>+12,.2f}（{total_pnl/total_cost*100:+.1f}%）",
            f"  購買力        ：$ 21,472.13",
            "=" * 65,
        ])

        return "\n\n".join([
            header,
            self.concentration_report(),
            self.pnl_report(),
            self.scoring_report(),
            self.trump_risk_map(),
            self.alerts(),
        ])


# ──────────────────────────────────────────
# 主程式
# ──────────────────────────────────────────

if __name__ == "__main__":
    analyzer = PortfolioAnalyzer(
        holdings=PORTFOLIO,
        account_value=117_383.15,
    )
    report = analyzer.full_report()
    print(report)

    # 匯出簡要 JSON
    import json
    summary = []
    for h in PORTFOLIO:
        summary.append({
            "ticker": h.ticker,
            "shares": h.shares,
            "avg_cost": h.avg_cost,
            "current_price": h.current_price,
            "total_cost": round(h.total_cost, 2),
            "current_value": round(h.current_value, 2),
            "unrealized_pnl": round(h.unrealized_pnl, 2),
            "unrealized_pct": round(h.unrealized_pct, 1),
            "composite_score": round(h.composite_score(), 1),
            "signal": h.signal().value,
            "trump_risk": h.trump_risk_level().value,
        })
    summary.sort(key=lambda x: x["composite_score"], reverse=True)

    with open("my_portfolio_snapshot.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("\n✅ JSON 已匯出至 my_portfolio_snapshot.json")
    print("\n📌 更新方式：")
    print("   每週將各持股的 current_price 更新為最新收盤價，重新執行即可獲得最新建議。")
