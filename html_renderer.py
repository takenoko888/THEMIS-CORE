"""
Themis-Core — HTML Renderer
サイバーパンク調ターミナルUI風HTMLを生成する。
"""

import os
import html as html_lib
import markdown as md_lib
import re


def _get_css() -> str:
    """全ページ共通のCSS"""
    return """
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;700&family=Noto+Sans+JP:wght@300;400;700&display=swap');

    :root {
      --bg-primary: #050510;
      --bg-secondary: #0a0a1a;
      --bg-panel: rgba(10, 15, 30, 0.85);
      --cyan: #00e5ff;
      --magenta: #ff00e5;
      --gold: #ffd700;
      --green: #00ff41;
      --red: #ff3e3e;
      --text: #c8d0e0;
      --text-dim: #5a6580;
      --border: #1a2040;
      --glow-cyan: 0 0 15px rgba(0, 229, 255, 0.4);
      --glow-magenta: 0 0 15px rgba(255, 0, 229, 0.4);
      --glow-gold: 0 0 15px rgba(255, 215, 0, 0.4);
    }

    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      background: var(--bg-primary);
      color: var(--text);
      font-family: 'JetBrains Mono', 'Noto Sans JP', monospace;
      font-size: 14px;
      line-height: 1.8;
      min-height: 100vh;
      overflow-x: hidden;
    }

    /* === Scanline Overlay === */
    body::before {
      content: '';
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: repeating-linear-gradient(
        0deg,
        transparent,
        transparent 2px,
        rgba(0, 0, 0, 0.08) 2px,
        rgba(0, 0, 0, 0.08) 4px
      );
      pointer-events: none;
      z-index: 9999;
    }

    /* === Background Grid === */
    body::after {
      content: '';
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background-image:
        linear-gradient(rgba(0, 229, 255, 0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0, 229, 255, 0.03) 1px, transparent 1px);
      background-size: 40px 40px;
      pointer-events: none;
      z-index: -1;
    }

    /* === Container === */
    .container {
      max-width: 900px;
      margin: 0 auto;
      padding: 30px 20px;
    }

    /* === System Header === */
    .system-header {
      text-align: center;
      padding: 40px 20px;
      margin-bottom: 40px;
      border: 1px solid var(--border);
      background: linear-gradient(180deg, rgba(0, 229, 255, 0.05) 0%, transparent 100%);
      position: relative;
    }

    .system-header::before {
      content: '── CLASSIFIED ── CLASSIFIED ── CLASSIFIED ── CLASSIFIED ──';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      font-size: 10px;
      color: var(--red);
      opacity: 0.4;
      letter-spacing: 2px;
      padding: 4px;
      background: rgba(255, 62, 62, 0.05);
      overflow: hidden;
      white-space: nowrap;
    }

    .system-title {
      font-size: 28px;
      font-weight: 700;
      color: var(--cyan);
      text-shadow: var(--glow-cyan);
      letter-spacing: 6px;
      margin-bottom: 8px;
    }

    .system-subtitle {
      font-size: 12px;
      color: var(--text-dim);
      letter-spacing: 4px;
    }

    .day-badge {
      display: inline-block;
      margin-top: 16px;
      padding: 6px 24px;
      border: 1px solid var(--gold);
      color: var(--gold);
      font-size: 18px;
      font-weight: 700;
      letter-spacing: 4px;
      text-shadow: var(--glow-gold);
    }

    /* === Section Panels === */
    .panel {
      margin-bottom: 32px;
      border: 1px solid var(--border);
      background: var(--bg-panel);
      backdrop-filter: blur(8px);
      overflow: hidden;
    }

    .panel-header {
      padding: 12px 20px;
      font-size: 13px;
      font-weight: 700;
      letter-spacing: 3px;
      text-transform: uppercase;
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .panel-header .icon {
      font-size: 16px;
    }

    .panel-body {
      padding: 20px;
      word-wrap: break-word;
      font-size: 13px;
      line-height: 1.9;
    }

    /* === Markdown Rendered Elements === */
    .panel-body h1, .panel-body h2, .panel-body h3, .panel-body h4 {
      color: inherit;
      margin: 1.2em 0 0.5em 0;
      line-height: 1.4;
    }
    .panel-body h1 { font-size: 1.3em; }
    .panel-body h2 { font-size: 1.15em; }
    .panel-body h3 { font-size: 1.05em; }
    .panel-body h4 { font-size: 1em; opacity: 0.9; }

    .panel-body p {
      margin: 0.6em 0;
    }

    .panel-body strong {
      color: #fff;
      font-weight: 700;
    }

    .panel-body em {
      font-style: italic;
      opacity: 0.9;
    }

    .panel-body ul, .panel-body ol {
      margin: 0.5em 0 0.5em 1.5em;
      padding: 0;
    }

    .panel-body li {
      margin: 0.3em 0;
    }

    .panel-body table {
      width: 100%;
      border-collapse: collapse;
      margin: 1em 0;
      font-size: 12px;
    }

    .panel-body th {
      background: rgba(255, 255, 255, 0.06);
      border: 1px solid rgba(255, 255, 255, 0.15);
      padding: 8px 12px;
      text-align: left;
      font-weight: 700;
      color: #fff;
    }

    .panel-body td {
      border: 1px solid rgba(255, 255, 255, 0.08);
      padding: 8px 12px;
    }

    .panel-body tr:nth-child(even) {
      background: rgba(255, 255, 255, 0.02);
    }

    .panel-body hr {
      border: none;
      border-top: 1px solid rgba(255, 255, 255, 0.1);
      margin: 1.5em 0;
    }

    .panel-body code {
      background: rgba(255, 255, 255, 0.08);
      padding: 2px 6px;
      border-radius: 3px;
      font-size: 0.9em;
    }

    .panel-body pre {
      background: rgba(0, 0, 0, 0.3);
      padding: 12px;
      border-radius: 4px;
      overflow-x: auto;
      margin: 1em 0;
    }

    .panel-body blockquote {
      border-left: 3px solid rgba(255, 255, 255, 0.2);
      padding-left: 16px;
      margin: 1em 0;
      opacity: 0.85;
    }

    /* Module-specific strong colors */
    .panel.module-a .panel-body strong { color: var(--cyan); }
    .panel.module-b .panel-body strong { color: var(--magenta); }
    .panel.judge .panel-body strong { color: var(--gold); }
    .panel.case-file .panel-body strong { color: var(--green); }

    /* Module A — Cyan */
    .panel.module-a { border-color: rgba(0, 229, 255, 0.3); }
    .panel.module-a .panel-header {
      background: linear-gradient(90deg, rgba(0, 229, 255, 0.15), transparent);
      color: var(--cyan);
      border-bottom: 1px solid rgba(0, 229, 255, 0.2);
    }

    /* Module B — Magenta */
    .panel.module-b { border-color: rgba(255, 0, 229, 0.3); }
    .panel.module-b .panel-header {
      background: linear-gradient(90deg, rgba(255, 0, 229, 0.15), transparent);
      color: var(--magenta);
      border-bottom: 1px solid rgba(255, 0, 229, 0.2);
    }

    /* Judge — Gold */
    .panel.judge { border-color: rgba(255, 215, 0, 0.3); }
    .panel.judge .panel-header {
      background: linear-gradient(90deg, rgba(255, 215, 0, 0.15), transparent);
      color: var(--gold);
      border-bottom: 1px solid rgba(255, 215, 0, 0.2);
    }

    /* Case — Green */
    .panel.case-file { border-color: rgba(0, 255, 65, 0.3); }
    .panel.case-file .panel-header {
      background: linear-gradient(90deg, rgba(0, 255, 65, 0.15), transparent);
      color: var(--green);
      border-bottom: 1px solid rgba(0, 255, 65, 0.2);
    }

    /* === Separator === */
    .separator {
      text-align: center;
      color: var(--text-dim);
      font-size: 11px;
      letter-spacing: 6px;
      margin: 32px 0;
      opacity: 0.5;
    }

    /* === Footer === */
    .system-footer {
      text-align: center;
      padding: 24px;
      border-top: 1px solid var(--border);
      color: var(--text-dim);
      font-size: 11px;
      letter-spacing: 2px;
      margin-top: 40px;
    }

    /* === Cursor Blink === */
    @keyframes blink {
      0%, 100% { opacity: 1; }
      50% { opacity: 0; }
    }
    .cursor {
      display: inline-block;
      width: 8px;
      height: 16px;
      background: var(--cyan);
      animation: blink 1s step-end infinite;
      vertical-align: text-bottom;
      margin-left: 4px;
    }

    /* === Index Page Specific === */
    .day-grid {
      display: grid;
      grid-template-columns: 1fr;
      gap: 16px;
      margin-top: 32px;
    }

    .day-card {
      display: block;
      padding: 20px 24px;
      border: 1px solid var(--border);
      background: var(--bg-panel);
      text-decoration: none;
      color: var(--text);
      transition: all 0.3s ease;
      position: relative;
      overflow: hidden;
    }

    .day-card:hover {
      border-color: var(--cyan);
      box-shadow: var(--glow-cyan);
      transform: translateX(4px);
    }

    .day-card::before {
      content: '';
      position: absolute;
      left: 0;
      top: 0;
      bottom: 0;
      width: 3px;
    }

    .day-card.phase-initial::before { background: var(--cyan); }
    .day-card.phase-learning::before { background: var(--magenta); }
    .day-card.phase-mature::before { background: var(--gold); }
    .day-card.phase-final::before { background: var(--green); }

    .day-card .day-number {
      font-size: 20px;
      font-weight: 700;
      letter-spacing: 3px;
    }

    .day-card.phase-initial .day-number { color: var(--cyan); }
    .day-card.phase-learning .day-number { color: var(--magenta); }
    .day-card.phase-mature .day-number { color: var(--gold); }
    .day-card.phase-final .day-number { color: var(--green); }

    .day-card .case-title {
      font-size: 12px;
      color: var(--text-dim);
      margin-top: 6px;
    }

    /* === Phase Labels === */
    .phase-label {
      display: inline-block;
      padding: 3px 10px;
      font-size: 10px;
      letter-spacing: 2px;
      border: 1px solid;
      margin-top: 8px;
    }

    .phase-label.initial { color: var(--cyan); border-color: rgba(0, 229, 255, 0.4); }
    .phase-label.learning { color: var(--magenta); border-color: rgba(255, 0, 229, 0.4); }
    .phase-label.mature { color: var(--gold); border-color: rgba(255, 215, 0, 0.4); }
    .phase-label.final { color: var(--green); border-color: rgba(0, 255, 65, 0.4); }

    /* === Progress Bar === */
    .progress-container {
      margin: 32px 0;
      padding: 20px;
      border: 1px solid var(--border);
      background: var(--bg-panel);
    }

    .progress-title {
      font-size: 11px;
      color: var(--text-dim);
      letter-spacing: 3px;
      margin-bottom: 12px;
    }

    .progress-bar {
      display: flex;
      height: 4px;
      background: var(--border);
      overflow: hidden;
      gap: 2px;
    }

    .progress-segment {
      height: 100%;
      transition: all 0.5s ease;
    }

    .progress-segment.active.initial { background: var(--cyan); box-shadow: var(--glow-cyan); }
    .progress-segment.active.learning { background: var(--magenta); box-shadow: var(--glow-magenta); }
    .progress-segment.active.mature { background: var(--gold); box-shadow: var(--glow-gold); }
    .progress-segment.active.final { background: var(--green); }

    /* === Navigation === */
    .nav-links {
      display: flex;
      justify-content: space-between;
      margin-top: 32px;
      gap: 16px;
    }

    .nav-link {
      display: inline-block;
      padding: 10px 20px;
      border: 1px solid var(--border);
      color: var(--cyan);
      text-decoration: none;
      font-size: 12px;
      letter-spacing: 2px;
      transition: all 0.3s ease;
    }

    .nav-link:hover {
      border-color: var(--cyan);
      box-shadow: var(--glow-cyan);
    }

    .nav-link.disabled {
      color: var(--text-dim);
      pointer-events: none;
      opacity: 0.3;
    }
    """


def _escape(text: str) -> str:
    """HTMLエスケープ"""
    return html_lib.escape(text)


def _render_markdown(text: str) -> str:
    """MarkdownテキストをHTMLに変換"""
    # 表の直前に空行がないとレンダリングされない問題を修正
    text = re.sub(r'([^\n])\n(\s*\|.*\|)', r'\1\n\n\2', text)
    
    extensions = ['tables', 'fenced_code', 'nl2br', 'sane_lists']
    return md_lib.markdown(text, extensions=extensions)


def _get_phase(day: int) -> tuple:
    """Day番号からフェーズ名とラベルを返す"""
    if day <= 2:
        return "initial", "INITIAL — 二極化"
    elif day <= 4:
        return "learning", "LEARNING — 揺らぎ"
    elif day <= 6:
        return "mature", "MATURE — 逆転と交差"
    else:
        return "final", "CONVERGENCE — 共生"


def render_day_html(day: int, case_info: dict, module_a: str, module_b: str, verdict: str) -> str:
    """1日分の審議記録HTMLを生成"""

    phase_class, phase_label = _get_phase(day)

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>THEMIS-CORE — Day {day} Judicial Proceedings</title>
  <meta name="description" content="統合司法AI Themis-Core 第{day}日審議記録">
  <style>{_get_css()}</style>
</head>
<body>
  <div class="container">

    <!-- System Header -->
    <header class="system-header">
      <div class="system-title">THEMIS-CORE</div>
      <div class="system-subtitle">INTEGRATED JUDICIAL AI SYSTEM v1.0</div>
      <div class="day-badge">DAY {day:02d} / 07</div>
      <div style="margin-top: 12px;">
        <span class="phase-label {phase_class}">{phase_label}</span>
      </div>
    </header>

    <!-- Case File -->
    <section class="panel case-file" id="case-file">
      <div class="panel-header">
        <span class="icon">📂</span>
        CASE FILE — TC-{day:03d}
      </div>
      <div class="panel-body">{_render_markdown(case_info['text'])}</div>
    </section>

    <div class="separator">═══════════ DELIBERATION START ═══════════</div>

    <!-- Module A: PSYCHE -->
    <section class="panel module-a" id="module-a">
      <div class="panel-header">
        <span class="icon">🧠</span>
        MODULE-A : PSYCHE — 読心AI分析レポート
      </div>
      <div class="panel-body">{_render_markdown(module_a)}</div>
    </section>

    <!-- Module B: ORACLE -->
    <section class="panel module-b" id="module-b">
      <div class="panel-header">
        <span class="icon">📊</span>
        MODULE-B : ORACLE — 予測AI分析レポート
      </div>
      <div class="panel-body">{_render_markdown(module_b)}</div>
    </section>

    <div class="separator">═══════════ VERDICT ═══════════</div>

    <!-- Judge: THEMIS -->
    <section class="panel judge" id="verdict">
      <div class="panel-header">
        <span class="icon">⚖️</span>
        MAIN SYSTEM : THEMIS — 最終判決
      </div>
      <div class="panel-body">{_render_markdown(verdict)}</div>
    </section>

    <!-- Navigation -->
    <nav class="nav-links">
      <a href="{'day' + str(day - 1) + '.html' if day > 1 else '#'}"
         class="nav-link {'disabled' if day == 1 else ''}">
        {'&lt;&lt; DAY ' + f'{day - 1:02d}' if day > 1 else '—'}
      </a>
      <a href="index.html" class="nav-link">INDEX</a>
      <a href="{'day' + str(day + 1) + '.html' if day < 7 else '#'}"
         class="nav-link {'disabled' if day == 7 else ''}">
        {'DAY ' + f'{day + 1:02d}' + ' &gt;&gt;' if day < 7 else '—'}
      </a>
    </nav>

    <!-- Footer -->
    <footer class="system-footer">
      THEMIS-CORE JUDICIAL AI SYSTEM — CONFIDENTIAL<br>
      RECORD DATE: DAY {day:02d} | STATUS: AUTHENTICATED | CLEARANCE: LEVEL-5
    </footer>

  </div>
</body>
</html>"""


def render_index_html(days_data: list) -> str:
    """全日程の一覧ページHTMLを生成"""

    day_cards = ""
    for d in days_data:
        phase_class, phase_label = _get_phase(d["day"])
        summary = d.get("case_summary", "記録なし")
        day_cards += f"""
    <a href="day{d['day']}.html" class="day-card phase-{phase_class}">
      <div class="day-number">DAY {d['day']:02d}</div>
      <div class="case-title">{_escape(summary)}</div>
      <span class="phase-label {phase_class}">{phase_label}</span>
    </a>"""

    # Progress bar segments
    progress_segments = ""
    for i in range(1, 8):
        phase_class, _ = _get_phase(i)
        active = "active" if i <= len(days_data) else ""
        progress_segments += f'<div class="progress-segment {active} {phase_class}" style="flex:1;"></div>'

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>THEMIS-CORE — 7-Day Judicial Proceedings Archive</title>
  <meta name="description" content="統合司法AI Themis-Core 7日間審議記録アーカイブ">
  <style>{_get_css()}</style>
</head>
<body>
  <div class="container">

    <header class="system-header">
      <div class="system-title">THEMIS-CORE</div>
      <div class="system-subtitle">INTEGRATED JUDICIAL AI SYSTEM v1.0</div>
      <div style="margin-top: 16px; color: var(--text-dim); font-size: 12px; letter-spacing: 3px;">
        7-DAY JUDICIAL PROCEEDINGS ARCHIVE
      </div>
    </header>

    <!-- System Evolution Progress -->
    <div class="progress-container">
      <div class="progress-title">SYSTEM EVOLUTION PROGRESS</div>
      <div class="progress-bar">
        {progress_segments}
      </div>
      <div style="display: flex; justify-content: space-between; margin-top: 8px; font-size: 10px; color: var(--text-dim);">
        <span>INITIAL</span>
        <span>LEARNING</span>
        <span>MATURE</span>
        <span>CONVERGENCE</span>
      </div>
    </div>

    <!-- Day Cards -->
    <div class="day-grid">
      {day_cards}
    </div>

    <footer class="system-footer">
      THEMIS-CORE JUDICIAL AI SYSTEM — COMPLETE ARCHIVE<br>
      TOTAL PROCEEDINGS: {len(days_data)} | STATUS: {'COMPLETE' if len(days_data) == 7 else 'IN PROGRESS'}
    </footer>

  </div>
</body>
</html>"""


def save_html(content: str, filepath: str):
    """HTMLファイルを保存"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  💾 HTML保存完了: {filepath}")
