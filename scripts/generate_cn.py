"""Generate the CN-Scenarios dataset (Chinese preference / temporal /
code-evolution / sensitivity) as questions.jsonl.

Each question is self-contained: entries[] are the memories to ingest,
query is what to ask, gold is the set of entry indices that must be
retrieved. We generate it locally so no third-party download is needed.
"""
from __future__ import annotations

import json
import os
import random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "datasets", "cn", "questions.jsonl")

random.seed(20261024)  # deterministic


def q(user_id: str, entries: list[str], query: str, gold: list[int]) -> dict:
    return {
        "user_id": user_id,
        "entries": [
            {"content": c, "observation_date": "2026-09-01"} for c in entries
        ],
        "query": query,
        "gold": [str(i) for i in gold],
    }


def build() -> list[dict]:
    out: list[dict] = []

    # --- 1. cross-session preference flip (conflict resolution) -------
    out.append(q(
        "u_pref",
        [
            "用户说：我喜欢用浅色的界面主题。",
            "用户说：我更喜欢用 Vim 快捷键。",
            "用户说：我讨厌自动补全，总是干扰我。",
            "用户后来改口：算了，浅色主题看久了眼睛累，还是深色舒服。",
            "用户说：我的笔记本是 14 寸的。",
        ],
        "用户现在偏好的界面主题是什么？",
        [0, 3],
    ))

    # --- 2. long-document key-point recall ----------------------------
    out.append(q(
        "u_doc",
        [
            "会议纪要：Q3 营收目标是 8000 万，实际完成 8200 万，超出 2.5%。",
            "技术债清单：数据库连接池上限从 50 调到 200，灰度 5% 流量。",
            "会议纪要：下季度重点做东南亚市场，优先越南。",
            "技术债清单：鉴权模块迁移到统一网关，排期到 11 月。",
            "会议纪要：客户 A 的续约金额 320 万，签了三年。",
        ],
        "客户 A 的续约金额是多少，签了几年？",
        [4],
    ))

    # --- 3. temporal memory ("that thing I mentioned last week") ------
    out.append(q(
        "u_time",
        [
            "（2026-09-02）用户说：我们周五要上线那个新支付渠道。",
            "（2026-09-09）用户说：那个支付渠道上线后报错率 0.3%。",
            "（2026-09-16）用户说：上次说的支付渠道，现在稳定了。",
        ],
        "用户上周提到的那个功能上线后的状态是什么？",
        [1, 2],
    ))

    # --- 4. sensitive-data tiering (sensitivity governance) -----------
    out.append(q(
        "u_secret",
        [
            "用户说：我家猫叫花生，养了三年了。",
            "用户说：我的手机号是 13800001234。",
            "用户说：我住在北京海淀区。",
            "用户说：我的车牌是京A88888。",
        ],
        "哪些条目包含需要脱敏的敏感信息？",
        [1, 3],
    ))

    # --- 5. code evolution (five changes to the same file) -----------
    out.append(q(
        "u_code",
        [
            "修改 auth.py：把同步登录改成异步，去掉线程池。",
            "修改 auth.py：加了一个 token 刷新间隔，默认 30 分钟。",
            "修改 auth.py：发现刷新间隔导致偶发 401，改成 25 分钟。",
            "修改 auth.py：加了 token 黑名单，登出后立即失效。",
            "修改 auth.py：黑名单用内存实现，重启会丢，改到 SQLite。",
        ],
        "auth.py 的 token 刷新间隔现在是多久？黑名单存在哪里？",
        [2, 4],
    ))

    # --- 6. multi-hop fact chaining -----------------------------------
    out.append(q(
        "u_multi",
        [
            "用户说他负责支付模块。",
            "支付模块的 owner 是老王。",
            "老王的工号是 1024。",
            "1024 号工位在 12 楼东区。",
        ],
        "负责支付模块的人的工位在哪？",
        [1, 2, 3],
    ))

    return out


def main() -> None:
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    qs = build()
    with open(OUT, "w", encoding="utf-8") as f:
        for item in qs:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"wrote {len(qs)} questions -> {OUT}")


if __name__ == "__main__":
    main()
