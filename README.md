# NEON CYBER DASH // Retro Arcade Action

A high-energy, retro-style arcade game featuring smooth vector movement, dynamic combo scoring, an EMP dash ability, 15-second difficulty surges, and persistent arcade leaderboards.

---

## 🎮 How to Play Immediately

### Option A: Browser (Zero Installation, Recommended)
Simply **double-click** `index.html` in any modern web browser (Google Chrome, Microsoft Edge, Mozilla Firefox, Safari) or run a local web server:
```bash
# Double-click index.html or open via terminal
start index.html
```
- 100% self-contained: Built with HTML5 Canvas and procedural Web Audio API.
- Zero external libraries or internet downloads needed. Works completely offline.

### Option B: Python / Pygame
If Python 3 and Pygame are installed on your machine:
```bash
pip install pygame
python neon_cyber_dash.py
```

---

## 🕹️ Controls

| Control | Action |
|---|---|
| **W, A, S, D** or **Arrow Keys** | Smooth 8-Directional Vector Movement |
| **Spacebar** | EMP Dash & Clear-Screen Shockwave (3.5s cooldown) |
| **R** | Instant Quick Restart (on Game Over or during play) |
| **M** | Toggle Synthesizer Audio / Music On/Off |
| **Esc** | Exit (Python version) |

---

## ⚡ Game Rules & Mechanics

1. **60-Second Match Countdown**: Score as many points as possible before the timer expires.
2. **Energy Cores (+100 Points)**: Collect the glowing green diamond cores scattered throughout the grid.
3. **Combo Multiplier (Up to 5x)**: Collect cores back-to-back within **3.0 seconds** to build your combo multiplier:
   - `x1` $\to$ `x2` $\to$ `x3` $\to$ `x4` $\to$ `x5 MAX`!
4. **3 Lives & Invulnerability Flash**:
   - Colliding with a Hunter or Sweeper Drone deducts 1 life.
   - Triggers a **1.5-second invulnerability flash** with screen shake and particle bursts.
5. **Twist for Competition (Every 15 Seconds)**:
   - At 45s, 30s, and 15s remaining, a **Surge Alert** activates!
   - Enemy speed and drone spawn rate increase by **+20%**.
   - A high-stakes **Golden Risk/Reward Bonus Orb** spawns for 8 seconds. Grabbing it rewards **+500 $\times$ Combo Multiplier** and instantly maxes your combo to **5x**!
6. **EMP Dash & Clear-Screen Shockwave (Spacebar)**:
   - Grants a burst of speed and invulnerability.
   - Unleashes an expanding cyan shockwave ring that vaporizes nearby drones for bonus points (+150 $\times$ Multiplier).
7. **Arcade Initials & High Scores**:
   - Save your 3-letter pilot initials (e.g. `ACE`, `NEO`) to the persistent High Score Hall of Legends (`localStorage` in browser / `neon_scores.json` in Python).

