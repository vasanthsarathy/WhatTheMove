🧠 WhatTheMove — Streamlit Visual + UX Design Spec
Purpose: PGN-based chess analyzer that explains your thought process per move in a calm, clean, minimal interface.

🧩 Core UX Principles
🕊️ Minimalistic white aesthetic

🧭 Three panels: Move List | Live Chessboard | Thought Analysis

🎯 Simple interaction: upload, click, reflect

🧠 Structured thought model with rich yet technical language

🖼️ Visual Layout: 3-Panel Grid
pgsql
Copy
Edit
+-------------------------------------------------------------------+
|                  [ Upload PGN ]   [ ⬅ Prev | ➡ Next ]            |
+-------------------+-------------------+---------------------------+
|                   |                   |                           |
|   MOVE LIST       |   LIVE BOARD      |  THOUGHT ANALYSIS         |
|   (scrollable)    |   (current move)  |  (ORIENT step shown)      |
|                   |                   |                           |
|   > 1. e4          |                   |  🧠 Move 1: White plays e4 |
|     1... c5        |                   |  • Kings: …               |
|     2. Nf3         |                   |  • Things: …              |
|                   |                   |  • Strings: …             |
+-------------------+-------------------+---------------------------+
🧰 Panel Breakdown
🧾 1. Move List (Left Column)
Feature	Type
Scrollable list	st.radio() or st.selectbox() (styled slim)
Clickable move jumps	Clicking moves updates board + analysis
Highlight current move	Light gray background or bolded
Minimal design	No borders, monospace or slim serif font
♟️ 2. Live Chessboard (Center Column)
Feature	Description
Board rendering	Use python-chess SVG → PNG → st.image() or embed HTML chessboard.js
Navigation buttons	⬅️ Prev / ➡️ Next buttons at the top
Highlight last move	Arrow or color highlight on move played
Minimal style	White background, no grid lines, subtle border
Optional future enhancement	Animate transitions
🧠 3. Thought Analysis (Right Column)
Section	Content
Move header	🧠 Move 4: Black plays ...
ORIENT Step	- Kings: open files, checks, mate threats
markdown
Copy
Edit
            - **Things:** hanging, loose, overloaded, weak pawns  
            - **Strings:** pins, discoveries |
| Visual style | Use st.markdown() with light emoji accents, bold headings, clear bulleting | | Consistency | Uniform phrasing across moves, using technical but plain language |

🎨 Styling & Aesthetic Details
Element	Style
Theme	White with soft gray accents
Fonts	System sans-serif or minimal serif
Colors	Neutral palette; light blue for selection, subtle red/green for threat severity
Icons	Use emojis very sparingly (🧠, ♟️, ❗) to hint tone
No distractions	No animations, ads, or visual noise
Spacing	Balanced white space between sections, light borders only when needed
⏯️ Controls
Button	Action
⬅ Prev	Step one move back
Next ➡	Step forward
Upload PGN	Open file browser
Future: Play ▶	Auto-play through game
✅ MVP Feature Summary
Feature	Include
Upload PGN	✅ Yes
Clickable move list	✅ Yes
Live updating board	✅ Yes
Orientation-based analysis	✅ Yes
Responsive layout	✅ Yes
Dark mode	🚫 No
Fancy animations	🚫 No
Engine evaluations	🚫 No (future)
🧪 Optional Future UX Enhancements
Show material count or imbalance

Annotated graph view of threats

Multiple steps: add “Direction”, “Candidates” after ORIENT

Shareable analysis link or PDF export

🚀 Want to Build It?
If you’re ready, I can scaffold a working Streamlit app using this spec. It will:

Use 3 columns via st.columns([1, 1.2, 2])

Parse PGNs and render SVG boards

Show full ORIENT output for each move