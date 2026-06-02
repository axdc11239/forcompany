#!/usr/bin/env python3
"""
川普言論與財務自動監控系統
Trump Truth Social + Financial Disclosure Routine Monitor

排程：
  - 每 12 小時：抓取 Truth Social 最新發文，分析市場影響
  - 每 3 天   ：檢查 OGE 財務揭露，比對已知持股清單

使用方式：
  python trump_monitor.py            # 啟動排程（持續執行）
  python trump_monitor.py --now      # 立即執行一次（測試用）
  python trump_monitor.py --finance  # 只執行財務檢查
"""

import sys
import json
import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from apscheduler.schedulers.blocking import BlockingScheduler

# ──────────────────────────────────────────────
# 設定區
# ──────────────────────────────────────────────

DATA_DIR    = Path("monitor_data")
REPORT_DIR  = Path("monitor_reports")
STATE_FILE  = DATA_DIR / "seen_posts.json"
FINANCE_FILE = DATA_DIR / "finance_snapshots.json"

DATA_DIR.mkdir(exist_ok=True)
REPORT_DIR.mkdir(exist_ok=True)

# Truth Social：Trump 帳號 Mastodon 相容 API
TRUTH_SOCIAL_API = (
    "https://truthsocial.com/api/v1/accounts/"
    "107780257626128497/statuses?limit=20"
)

# OGE 財務揭露搜尋（ProPublica 整理版）
OGE_TRUMP_URL = (
    "https://efts.usda.gov/EFTS/fulltext/search"  # fallback
)
WHITEHOUSE_FINANCE = (
    "https://www.whitehouse.gov/briefing-room/"
    "presidential-actions/"
)

# ── 關鍵字分類字典（正/負面，按個股/產業） ──────────
KEYWORD_MAP = {
    # ── 正面關鍵字 ──
    "positive": {
        "NVDA":  ["nvidia", "nvda", "ai chip", "artificial intelligence", "war fighting", "military ai"],
        "INTC":  ["intel", "intc", "chips act", "american semiconductor", "american manufacturing"],
        "TSLA":  ["tesla", "elon", "musk", "electric vehicle", "robotaxi", "fsd"],
        "AAPL":  ["apple", "tim cook", "iphone", "american made"],
        "AVGO":  ["broadcom", "avgo", "custom chip", "asic"],
        "PLTR":  ["palantir", "pltr", "defense tech", "war technology"],
        "GS":    ["goldman sachs", "goldman", "wall street", "deregulation"],
        "BAC":   ["bank of america", "american banks", "banking"],
        "ORCL":  ["oracle", "tiktok deal", "cloud"],
        "GFS":   ["globalfoundries", "foundry", "semiconductor"],
        "MARKET":["stock market", "markets", "dow jones", "nasdaq", "s&p",
                  "great economy", "best economy", "record high", "buy", "great time"],
        "CRYPTO":["bitcoin", "crypto", "digital assets", "btc", "strategic reserve"],
        "DEFENSE":["lockheed", "raytheon", "northrop", "military", "defense",
                   "weapons", "missile", "lmt", "rtx", "noc"],
        "ENERGY_UP":["drill", "oil production", "energy independence", "lng"],
    },
    # ── 負面關鍵字 ──
    "negative": {
        "TSLA":  ["musk subsidy", "tesla subsidy", "revoke", "off the rails",
                  "elon off", "musk wrong", "deportation musk"],
        "PHARMA":["drug company", "pharma", "drug price", "pfizer", "lilly",
                  "novo nordisk", "tariff drugs", "100% tariff"],
        "RETAIL":["walmart", "target", "amazon price", "eat the tariff",
                  "price gouging", "raising prices"],
        "CHINA": ["china tariff", "chinese imports", "100%", "125%", "145%",
                  "china hostile", "rare earth", "chip ban"],
        "FED":   ["powell", "federal reserve", "major loser", "too late powell",
                  "fire powell", "terminate"],
        "ENERGY_DOWN":["iran deal", "hormuz open", "oil flooding",
                       "energy prices falling", "opec"],
        "TECH":  ["antitrust", "monopoly", "break up", "google antitrust",
                  "amazon antitrust"],
        "AUTO":  ["usmca", "auto tariff", "american content", "mexico cars",
                  "canada cars", "25% auto"],
    }
}

# ── 受影響個股對照（用於你的持倉） ──────────────────
YOUR_PORTFOLIO = {
    "TSLA": 110,
    "INTC": 200,
    "NVDA": 70.01,
    "GOOGL": 20.01,
    "DUOL": 10,
    "GFS": 10,
    "AMD": 1,
    "O": 29.04,
    "QQQ": 1.00,
    "META": 0.006,
}

COST_BASIS = {
    "TSLA": 396.25, "INTC": 68.66, "NVDA": 177.95,
    "GOOGL": 318.07, "DUOL": 192.33, "GFS": 70.51,
    "AMD": 242.70, "O": 62.25, "QQQ": 608.16, "META": 663.65,
}


# ──────────────────────────────────────────────
# 狀態管理（避免重複分析同一篇帖文）
# ──────────────────────────────────────────────

def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"seen_ids": [], "last_run": None}

def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))

def load_finance_state() -> dict:
    if FINANCE_FILE.exists():
        return json.loads(FINANCE_FILE.read_text())
    return {"snapshots": [], "known_holdings": {}, "last_check": None}

def save_finance_state(state: dict):
    FINANCE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))


# ──────────────────────────────────────────────
# Truth Social 抓取
# ──────────────────────────────────────────────

def fetch_truth_social_posts() -> list[dict]:
    """
    透過 Truth Social Mastodon 相容 API 取得川普最新發文。
    若 API 不可用，改抓 RSS/備用來源。
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; TrumpMonitor/1.0)",
        "Accept": "application/json",
    }
    posts = []

    # 方法一：官方 Mastodon API
    try:
        resp = requests.get(TRUTH_SOCIAL_API, headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            for item in data:
                text = BeautifulSoup(
                    item.get("content", ""), "html.parser"
                ).get_text()
                posts.append({
                    "id":        str(item.get("id", "")),
                    "created_at": item.get("created_at", ""),
                    "text":      text.strip(),
                    "url":       item.get("url", ""),
                    "source":    "truthsocial_api",
                })
            return posts
    except Exception as e:
        print(f"  [!] Truth Social API 失敗：{e}")

    # 方法二：RSS（第三方鏡像，如 truthsocial.com RSS）
    rss_urls = [
        "https://trumpstruth.org/rss",
        "https://rss.politico.com/trump",
    ]
    for rss_url in rss_urls:
        try:
            resp = requests.get(rss_url, headers=headers, timeout=10)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "xml")
                for item in soup.find_all("item")[:20]:
                    posts.append({
                        "id":        hashlib.md5(
                            item.find("link").text.encode()
                        ).hexdigest()[:16],
                        "created_at": item.find("pubDate").text
                                      if item.find("pubDate") else "",
                        "text":      BeautifulSoup(
                            item.find("description").text, "html.parser"
                        ).get_text().strip(),
                        "url":       item.find("link").text,
                        "source":    "rss",
                    })
                if posts:
                    return posts
        except Exception:
            continue

    # 方法三：模擬資料（測試/API 封鎖時）
    print("  [!] 所有 API 均失敗，使用模擬資料進行測試")
    posts = [
        {
            "id": "test_001",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "text": (
                "NVIDIA (NVDA) is the greatest AI company in the world. "
                "They are MAKING AMERICA GREAT AGAIN with their chips! "
                "The best military AI technology. BUY AMERICAN!"
            ),
            "url": "https://truthsocial.com/@realDonaldTrump/test001",
            "source": "simulated",
        },
        {
            "id": "test_002",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "text": (
                "Iran wants to make a DEAL. It will be the greatest deal "
                "ever made. Nobody makes deals like Trump! "
                "The Strait of Hormuz will be OPEN very soon!"
            ),
            "url": "https://truthsocial.com/@realDonaldTrump/test002",
            "source": "simulated",
        },
    ]
    return posts


# ──────────────────────────────────────────────
# 川普帖文情緒分析
# ──────────────────────────────────────────────

def analyze_post(post: dict) -> dict:
    """
    對單篇帖文進行多維度分析：
    - 正/負面關鍵字比對
    - 受影響個股識別
    - 市場影響評估
    - 對持倉的具體影響
    """
    text_lower = post["text"].lower()
    result = {
        "post_id":    post["id"],
        "timestamp":  post["created_at"],
        "text":       post["text"][:200] + ("..." if len(post["text"]) > 200 else ""),
        "url":        post.get("url", ""),
        "hits":       [],          # 命中的關鍵字
        "affected_tickers": [],    # 受影響個股
        "direction":  "NEUTRAL",   # BULLISH / BEARISH / NEUTRAL / MIXED
        "urgency":    "LOW",       # HIGH / MEDIUM / LOW
        "portfolio_impact": [],    # 對你持倉的直接影響
        "recommended_action": "",
    }

    pos_hits, neg_hits = [], []

    # ── 掃描正面關鍵字 ─────────────────────
    for ticker, keywords in KEYWORD_MAP["positive"].items():
        for kw in keywords:
            if kw in text_lower:
                pos_hits.append({"keyword": kw, "ticker": ticker, "direction": "+"})
                if ticker not in result["affected_tickers"] and ticker in YOUR_PORTFOLIO:
                    result["affected_tickers"].append(ticker)

    # ── 掃描負面關鍵字 ─────────────────────
    for ticker, keywords in KEYWORD_MAP["negative"].items():
        for kw in keywords:
            if kw in text_lower:
                neg_hits.append({"keyword": kw, "ticker": ticker, "direction": "-"})
                if ticker not in result["affected_tickers"] and ticker in YOUR_PORTFOLIO:
                    result["affected_tickers"].append(ticker)

    result["hits"] = pos_hits + neg_hits

    # ── 判斷方向 ──────────────────────────
    if pos_hits and neg_hits:
        result["direction"] = "MIXED"
    elif pos_hits:
        result["direction"] = "BULLISH"
    elif neg_hits:
        result["direction"] = "BEARISH"

    # ── 緊急程度（影響你持倉的幣種數量 + 市場整體關鍵字） ──
    market_keywords = ["stock market", "buy", "sell", "record", "crash",
                       "tariff", "deal", "iran", "china"]
    market_hit = any(kw in text_lower for kw in market_keywords)
    portfolio_tickers_hit = len(result["affected_tickers"])

    if portfolio_tickers_hit >= 2 or (market_hit and result["direction"] != "NEUTRAL"):
        result["urgency"] = "HIGH"
    elif portfolio_tickers_hit == 1 or market_hit:
        result["urgency"] = "MEDIUM"

    # ── 對持倉的具體影響分析 ──────────────
    for ticker in result["affected_tickers"]:
        shares = YOUR_PORTFOLIO.get(ticker, 0)
        cost   = COST_BASIS.get(ticker, 0)
        if shares == 0:
            continue

        # 方向判斷
        ticker_pos = any(h["ticker"] == ticker for h in pos_hits)
        ticker_neg = any(h["ticker"] == ticker for h in neg_hits)

        if ticker_pos and not ticker_neg:
            est_chg = +0.04   # 正面：預估 +4%
            direction_str = "▲ 利多"
            action = "可考慮持有或加碼"
        elif ticker_neg and not ticker_pos:
            est_chg = -0.05   # 負面：預估 -5%
            direction_str = "▼ 利空"
            action = ("⚠️ 注意停損！建議確認是否需要減碼"
                      if ticker == "TSLA" else "注意動向，考慮停損")
        else:
            est_chg = 0.0
            direction_str = "⟺ 混合"
            action = "觀望"

        est_pnl = shares * cost * est_chg
        result["portfolio_impact"].append({
            "ticker":     ticker,
            "shares":     shares,
            "direction":  direction_str,
            "est_impact": f"${est_pnl:+,.0f}（預估 {est_chg:+.0%}）",
            "action":     action,
        })

    # ── 綜合建議 ──────────────────────────
    if result["direction"] == "BEARISH" and "TSLA" in result["affected_tickers"]:
        result["recommended_action"] = (
            "🔴 緊急：TSLA 相關負面言論！"
            "當前持倉 110 股，建議立即評估是否觸及停損線 $380"
        )
    elif result["direction"] == "BULLISH" and result["urgency"] == "HIGH":
        tickers = ", ".join(result["affected_tickers"])
        result["recommended_action"] = (
            f"🟢 利多訊號：{tickers} 受益，"
            "開盤後注意確認是否需要加碼"
        )
    elif result["direction"] == "NEUTRAL":
        result["recommended_action"] = "市場中性，無需操作"
    else:
        result["recommended_action"] = "持續觀察，暫無緊急操作需求"

    return result


# ──────────────────────────────────────────────
# Truth Social 12 小時例行任務
# ──────────────────────────────────────────────

def job_truth_social():
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"\n{'='*60}")
    print(f"[{now_str}] 🔍 Truth Social 檢查開始")
    print(f"{'='*60}")

    state   = load_state()
    seen_ids = set(state.get("seen_ids", []))

    # 抓取最新帖文
    posts = fetch_truth_social_posts()
    print(f"  取得 {len(posts)} 篇帖文")

    # 只處理新帖文
    new_posts = [p for p in posts if p["id"] not in seen_ids]
    print(f"  其中 {len(new_posts)} 篇為新帖文")

    if not new_posts:
        print("  ✓ 無新帖文，本次無需操作")
        state["last_run"] = now_str
        save_state(state)
        return

    # 分析每篇新帖文
    analyses = [analyze_post(p) for p in new_posts]

    # 生成報告
    report_lines = [
        f"# Truth Social 監控報告",
        f"**產生時間：** {now_str}",
        f"**新帖文數量：** {len(new_posts)} 篇",
        "",
    ]

    high_urgency = [a for a in analyses if a["urgency"] == "HIGH"]
    if high_urgency:
        report_lines += [
            "## ⚠️ 高緊急度警報",
            "",
        ]
        for a in high_urgency:
            report_lines += [
                f"### [{a['direction']}] {a['timestamp'][:16]}",
                f"> {a['text']}",
                "",
                f"**受影響個股：** {', '.join(a['affected_tickers']) or '無'}",
                f"**建議操作：** {a['recommended_action']}",
                "",
            ]
            if a["portfolio_impact"]:
                report_lines.append("**你的持倉影響：**")
                for imp in a["portfolio_impact"]:
                    report_lines.append(
                        f"- {imp['ticker']}（{imp['shares']} 股）"
                        f"：{imp['direction']} {imp['est_impact']} → {imp['action']}"
                    )
                report_lines.append("")

    report_lines += ["---", "## 所有新帖文摘要", ""]
    for a in analyses:
        emoji = {"BULLISH": "📈", "BEARISH": "📉",
                 "MIXED": "↕️", "NEUTRAL": "➡️"}.get(a["direction"], "")
        urgency_label = {"HIGH": "🔴", "MEDIUM": "🟡",
                         "LOW": "🟢"}.get(a["urgency"], "")
        report_lines.append(
            f"- {urgency_label}{emoji} `{a['timestamp'][:16]}` "
            f"[{a['direction']}] {a['text'][:80]}..."
        )
        if a["affected_tickers"]:
            report_lines.append(
                f"  → 影響：{', '.join(a['affected_tickers'])}"
            )

    report_content = "\n".join(report_lines)

    # 儲存報告
    report_filename = (
        REPORT_DIR
        / f"truth_social_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
    )
    report_filename.write_text(report_content, encoding="utf-8")
    print(f"\n  📄 報告已儲存：{report_filename}")

    # 印出關鍵摘要
    if high_urgency:
        print(f"\n  🚨 發現 {len(high_urgency)} 則高緊急度帖文！")
        for a in high_urgency:
            print(f"     [{a['direction']}] {a['text'][:100]}")
            print(f"     → {a['recommended_action']}")
    else:
        print("  ✓ 無高緊急度事件")

    # 更新已處理 ID
    seen_ids.update(p["id"] for p in new_posts)
    state["seen_ids"] = list(seen_ids)[-200:]   # 只保留最近 200 個
    state["last_run"] = now_str
    save_state(state)

    print(f"\n  完成。下次執行：12 小時後")


# ──────────────────────────────────────────────
# 財務揭露 3 天例行任務
# ──────────────────────────────────────────────

# 川普已知持股清單（根據 Q1 2026 OGE 揭露）
KNOWN_TRUMP_HOLDINGS = {
    "NVDA":  {"range": "100萬–500萬", "last_seen": "2026-Q1", "status": "持有"},
    "AAPL":  {"range": "100萬–500萬", "last_seen": "2026-Q1", "status": "持有"},
    "PLTR":  {"range": "25萬–63萬",   "last_seen": "2026-Q1", "status": "持有（已讚美）"},
    "AVGO":  {"range": "中等",        "last_seen": "2026-Q1", "status": "持有"},
    "GS":    {"range": "中等",        "last_seen": "2026-Q1", "status": "持有"},
    "BAC":   {"range": "中等",        "last_seen": "2026-Q1", "status": "持有"},
    "ORCL":  {"range": "中等",        "last_seen": "2026-Q1", "status": "持有"},
    "MSFT":  {"range": "部分已賣出",  "last_seen": "2026-Q1", "status": "減碼"},
    "AMZN":  {"range": "500萬以上已賣出","last_seen": "2026-Q1", "status": "已賣出"},
    "META":  {"range": "混合（買賣）","last_seen": "2026-Q1", "status": "混合"},
    "SPY":   {"range": "100萬–500萬", "last_seen": "2026-Q1", "status": "持有"},
    "BA":    {"range": "100萬–600萬", "last_seen": "2025-Q3", "status": "持有"},
}

# OGE 財務揭露來源（按優先順序）
OGE_SOURCES = [
    "https://efts.usda.gov/EFTS/fulltext/search?q=Trump&type=278&year=2026",
    "https://www.citizensforethics.org/trump-financial-disclosures/",
    "https://projects.propublica.org/trump-conflicts/",
]


def fetch_oge_disclosures() -> dict:
    """
    嘗試抓取 OGE 最新財務揭露。
    實際部署時應對接 OGE EFTS API 或 ProPublica API。
    """
    headers = {"User-Agent": "Mozilla/5.0 (compatible; TrumpMonitor/1.0)"}
    result = {
        "source": "unknown",
        "fetch_time": datetime.now().isoformat(),
        "new_trades": [],
        "raw_html_snippet": "",
    }

    for url in OGE_SOURCES:
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                # 抓取包含股票代號的文字段落
                text_blocks = soup.get_text()
                # 找可能的股票代號（大寫 2-5 字母）
                tickers_found = re.findall(r'\b([A-Z]{2,5})\b', text_blocks)
                # 過濾成常見股票代號
                known_tickers = {
                    "NVDA","AAPL","MSFT","AMZN","META","GOOGL","TSLA",
                    "PLTR","AVGO","GS","BAC","ORCL","JPM","BAC","V","MA",
                    "NFLX","AMD","INTC","SPY","QQQ","BA","RTX","LMT","NOC",
                    "XOM","CVX","GLD","BTC","COIN","MSTR",
                }
                found = [t for t in set(tickers_found) if t in known_tickers]
                result["source"] = url
                result["raw_html_snippet"] = text_blocks[:500]
                result["detected_tickers"] = found
                break
        except Exception as e:
            print(f"  [!] OGE 來源失敗 {url}：{e}")
            continue

    return result


def job_financial_disclosure():
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"\n{'='*60}")
    print(f"[{now_str}] 💰 財務揭露檢查開始（3 天週期）")
    print(f"{'='*60}")

    fin_state = load_finance_state()
    oge_data  = fetch_oge_disclosures()

    # 偵測新持股（與已知清單比較）
    detected  = set(oge_data.get("detected_tickers", []))
    known     = set(KNOWN_TRUMP_HOLDINGS.keys())
    new_tickers = detected - known

    # 生成財務報告
    report_lines = [
        f"# 川普財務揭露監控報告",
        f"**產生時間：** {now_str}",
        f"**資料來源：** {oge_data['source']}",
        "",
        "## 已知川普持股清單（Q1 2026 揭露）",
        "",
        f"| 代號 | 持倉規模 | 狀態 | 最後揭露 | 未來炒作風險 |",
        f"|------|---------|------|---------|-------------|",
    ]

    for ticker, info in KNOWN_TRUMP_HOLDINGS.items():
        in_your_portfolio = "✅ 你持有" if ticker in YOUR_PORTFOLIO else ""
        promoted = "⚠️ 已讚美過" if "已讚美" in info["status"] else "🎯 尚未讚美"
        report_lines.append(
            f"| {ticker} | {info['range']} | {info['status']} "
            f"| {info['last_seen']} | {promoted} {in_your_portfolio} |"
        )

    report_lines += [
        "",
        "## 🎯 炒作優先級排序",
        "根據「已買入但尚未讚美」邏輯，川普最可能讚美的標的：",
        "",
        "1. **NVDA** ⭐⭐⭐⭐⭐ — 軍事 AI + 持倉最大 → **你也持有！**",
        "2. **AAPL** ⭐⭐⭐⭐ — 美國製造故事 + Tim Cook 關係",
        "3. **AVGO** ⭐⭐⭐ — 美國 AI 晶片製造代表",
        "4. **GS/BAC** ⭐⭐⭐ — 金融去管制化成果展示",
        "5. **ORCL** ⭐⭐⭐ — TikTok 合作故事",
        "",
    ]

    if new_tickers:
        report_lines += [
            f"## 🆕 偵測到潛在新持股（需人工確認）",
            f"發現以下代號在最新揭露中出現，但不在已知清單：",
            "",
        ]
        for t in new_tickers:
            in_portfolio = "⚠️ 你持有此股！" if t in YOUR_PORTFOLIO else ""
            report_lines.append(f"- **{t}** {in_portfolio}")
        report_lines.append("")

    # 對你持倉的影響分析
    overlap = [t for t in KNOWN_TRUMP_HOLDINGS if t in YOUR_PORTFOLIO]
    report_lines += [
        "## 你的持倉與川普持股重疊分析",
        "",
        f"| 代號 | 你持有股數 | 川普持倉狀態 | 風險/機會 |",
        f"|------|-----------|------------|---------|",
    ]
    for t in overlap:
        info = KNOWN_TRUMP_HOLDINGS[t]
        risk = ""
        if "已賣出" in info["status"]:
            risk = "⚠️ 川普已清倉，留意負面言論"
        elif "尚未讚美" in (
            "⚠️ 已讚美過" if "已讚美" in info["status"] else "尚未讚美"
        ):
            risk = "🎯 等待川普讚美潛力"
        else:
            risk = "✅ 已讚美，風險降低"

        report_lines.append(
            f"| {t} | {YOUR_PORTFOLIO[t]} 股 | {info['status']} | {risk} |"
        )

    report_lines += [
        "",
        "## 下次人工確認建議",
        "- 登入 https://efts.usda.gov 搜尋最新 Form 278",
        "- 確認 NVDA、AAPL、AVGO 是否出現在最新季度揭露",
        "- 留意任何新出現、且尚未公開讚美的持股",
    ]

    report_content = "\n".join(report_lines)
    report_filename = (
        REPORT_DIR
        / f"financial_disclosure_{datetime.now().strftime('%Y%m%d')}.md"
    )
    report_filename.write_text(report_content, encoding="utf-8")
    print(f"  📄 財務報告已儲存：{report_filename}")

    # 更新狀態
    fin_state["last_check"]      = now_str
    fin_state["known_holdings"]  = KNOWN_TRUMP_HOLDINGS
    fin_state["snapshots"].append({
        "date": now_str,
        "detected_tickers": list(detected),
        "new_tickers": list(new_tickers),
    })
    fin_state["snapshots"] = fin_state["snapshots"][-30:]  # 保留最近 30 次
    save_finance_state(fin_state)

    # 印出摘要
    print("\n  川普已買入但尚未讚美的高風險股：")
    for ticker, info in KNOWN_TRUMP_HOLDINGS.items():
        if "已讚美" not in info["status"] and "賣出" not in info["status"]:
            in_port = "← 你持有！" if ticker in YOUR_PORTFOLIO else ""
            print(f"    {ticker:6s}  {info['range']:12s}  {in_port}")

    if new_tickers:
        print(f"\n  🆕 偵測到潛在新持股：{new_tickers}")

    print(f"\n  完成。下次執行：3 天後")


# ──────────────────────────────────────────────
# 主排程器
# ──────────────────────────────────────────────

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""

    if mode == "--now":
        print("【立即執行所有任務（測試模式）】")
        job_truth_social()
        job_financial_disclosure()
        return

    if mode == "--truth":
        job_truth_social()
        return

    if mode == "--finance":
        job_financial_disclosure()
        return

    # 正常排程模式
    print("=" * 60)
    print("  川普言論 & 財務監控系統 啟動")
    print("  Truth Social：每 12 小時")
    print("  財務揭露　　：每 3 天")
    print("=" * 60)

    # 啟動時立即執行一次
    print("\n[初始化] 立即執行一次確認系統正常...")
    job_truth_social()
    job_financial_disclosure()

    scheduler = BlockingScheduler(timezone="America/New_York")

    # 每 12 小時：Truth Social（美東 9:00 / 21:00）
    scheduler.add_job(
        job_truth_social,
        "cron",
        hour="9,21",
        minute=0,
        id="truth_social",
        name="Truth Social 12小時檢查",
        misfire_grace_time=300,
    )

    # 每 3 天：財務揭露（每週一、四 早上 8:30 美東）
    scheduler.add_job(
        job_financial_disclosure,
        "cron",
        day_of_week="mon,thu",
        hour=8,
        minute=30,
        id="financial_disclosure",
        name="財務揭露 3天檢查",
        misfire_grace_time=3600,
    )

    print("\n✅ 排程器已啟動，按 Ctrl+C 停止")
    print("  下次 Truth Social 檢查：每日 09:00 & 21:00 (美東)")
    print("  下次財務揭露檢查　　：每週一 & 週四 08:30 (美東)")

    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("\n\n監控系統已停止")


if __name__ == "__main__":
    main()
