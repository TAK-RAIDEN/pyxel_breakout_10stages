# BRICK RAIDERS - 10 Stages + UFO Boss + Title + Continue + LifeUp + Anti-Stuck
# + Boss Auto-AllClear + 2-line Clear Banner + SpeedUp & Shake + BossHit+10
# + High-Speed Substep Collision + Auto Next Stage After Clear
# + Random 30 Patterns by Difficulty + Title Grid BG + ESC Quit + R BackToTitle (2025-11)
# + Stage-Based Grid Color (1-3 / 4-6 / 7-9 / Boss)

import random
import math
import pyxel

# ==== 定数 =========================================================
W, H = 160, 120
BAR_W, BAR_H = 32, 6
BALL_R = 2
SPEED = 2.2
FOOTER_H = 10  # 紺帯を1段だけにして下げる
MIN_V = 0.25                      # 角度クランプ用の最小成分
MIN_VY_KICK = max(1.0, SPEED * 1.1)  # 上下ヒット後の最低縦速度
STUCK_STREAK = 3
JITTER_SMALL = 0.08
JITTER_STRONG = 0.18
ROTATE_STRONG = 0.22

# ---- 高速時だけサブステップ用 ----
SUBSTEP_SPEED_THRESHOLD = 3.0   # この速度を超えたら多段ステップ
SUBSTEP_MULTIPLIER = 2.0        # 分割数 = speed * これ
SUBSTEP_MAX_STEPS = 12          # 分割上限（負荷対策）

# スプライトのブロックサイズ
BRICK_W, BRICK_H, BRICK_GAP = 14, 6, 2
BRICK_OFFSET_Y = 16

# ==== IMG0 改訂レイアウト ==========================================
# Paddle: (0,0) 32x8 / Ball: (34,0) 4x4
PADDLE_U, PADDLE_V, PADDLE_W, PADDLE_H = 0, 0, 32, 8
BALL_U,   BALL_V,   BALL_W,   BALL_H   = 34, 0, 4, 4

# ブロック 14x6
BRK_W, BRK_H = 14, 6

# HP1（3色）: (0,12), (48,12), (64,12)
BRK1_FRAMES = [
    (0, 12),
    (48, 12),
    (64, 12),
]

# HP2（3色）: (16,12), (80,12), (96,12)
BRK2_FRAMES = [
    (16, 12),
    (80, 12),
    (96, 12),
]

# Unbreakable（1色）: (32,12)
BRKX_U, BRKX_V = 32, 12

# ==== タイトル画像（IMG0） ========================================
# あなたが作成したロゴ: (11,48)〜(116,78) → 105x30
TITLE_U, TITLE_V = 11, 48
TITLE_W, TITLE_H = 116 - 11, 78 - 48  # 105 x 30

# ==== 3x5 極小フォント =============================================
SMALL_FONT = {
    "A": ["010","101","111","101","101"],
    "B": ["110","101","110","101","110"],
    "C": ["011","100","100","100","011"],
    "D": ["110","101","101","101","110"],
    "E": ["111","100","110","100","111"],
    "I": ["010","010","010","010","010"],
    "L": ["100","100","100","100","111"],
    "N": ["101","111","111","111","101"],
    "R": ["110","101","110","101","101"],
    "T": ["111","010","010","010","010"],
    "Y": ["101","101","010","010","010"],
    " ": ["000","000","000","000","000"],
}

def draw_small_char(x, y, ch, col):
    pat = SMALL_FONT.get(ch.upper(), SMALL_FONT[" "])
    for ry, row in enumerate(pat):
        for rx, c in enumerate(row):
            if c == "1":
                pyxel.pset(x + rx, y + ry, col)

def small_text_width(s: str) -> int:
    n = len(s)
    return 0 if n == 0 else n * 4 - 1

def draw_small_text(x, y, s, col):
    cx = x
    for i, ch in enumerate(s):
        draw_small_char(cx, y, ch, col)
        cx += 4

# ==== 難易度別レイアウトプール（各10パターン） =====================
# 1行 = 10文字 / 4行で1面
# ' ' 空白, '1' HP1, '2' HP2, '#' 壊れない

PATTERNS_EASY = [
    ["1111111111"," 11111111 ","  111111  ","   1111   "],
    ["1 1 1 1 1"," 1 1 1 1 ","1 1 1 1 1"," 1 1 1 1 "],
    ["111    111","1111  1111"," 111  111 ","  11  11  "],
    ["          ","1111111111","1111111111","          "],
    ["1111111111","  111111  ","    111   ","     1    "],
    ["1010101010".replace('0',' '),"0101010101".replace('0',' '),"1010101010".replace('0',' '),"0101010101".replace('0',' ')],
    [" 11111111 ","11      11","11 1111 11","  111111  "],
    ["1111111111","1        1","1        1","1111111111"],
    ["1111111111","          ","1111111111","          "],
    ["   1111   ","  111111  "," 11111111 ","1111111111"],
]

PATTERNS_MEDIUM = [
    ["  222222  "," 21212121 ","1111111111"," 21212121 "],
    ["2020202020".replace('0','1'),"0202020202".replace('0','1'),"2020202020".replace('0','1'),"0202020202".replace('0','1')],
    ["1111111111","2222222222","1111111111","  111111  "],
    ["2222222222","2 111111 2","2 111111 2","2222222222"],
    ["  111111  "," 11222211 "," 11222211 ","  111111  "],
    ["2 1111111 "," 2 1111111","  2 111111","   2 11111"],
    ["2222222222","1111111111","2222222222","1111111111"],
    ["1111111111","  222222  ","  222222  ","1111111111"],
    ["111 22 111","111 22 111","1111111111","  111111  "],
    ["   2222   ","   2222   ","2222222222","   2222   "],
]

PATTERNS_HARD = [
    ["11##11##11","2211##1122","11##11##11","2211##1122"],
    ["###11 11##","#  22  1 #","## 11 22 #","###11 11##"],
    ["#1#1#1#1#1","2#2#2#2#2#".rstrip('#'),"#1#1#1#1#1","2#2#2#2#2#".rstrip('#')],
    ["##########","#22222222#","#21111112#","##########"],
    ["2##2222##2"," 21111112 "," 2##222##2"," 21111112 "],
    ["####  ####","#22#  #22#","#11#  #11#","####  ####"],
    ["1111111111","11 #### 11","11 #### 11","1111111111"],
    ["#11111111 ","2#1111111 ","22#111111 ","222#11111 "],
    ["## 2222 ##","## 1111 ##","## 2222 ##","## 1111 ##"],
    ["##########","#2#1#2#1#2","#1#2#1#2#1","##########"],
]

def pick_layout_for_stage(stage: int):
    """ステージ番号から難易度を決め、30パターンからランダム選択。10面はボスで空レイアウト。"""
    if stage == 10:
        return []
    if 1 <= stage <= 3:
        pool = PATTERNS_EASY
    elif 4 <= stage <= 6:
        pool = PATTERNS_MEDIUM
    else:
        pool = PATTERNS_HARD
    return random.choice(pool)

# ==== UFO（ユーザー作成スプライト） ================================
# 通常: (0,24,48,16) / 被弾: (48,24,48,16)
# 追加: 中ダメージ(96,24,48,16) / 瀕死(144,24,48,16)
UFO_W, UFO_H = 48, 16
UFO_PHASES = [
    (0, 24),     # HP > 10
    (96, 24),    # 10 >= HP > 5
    (144, 24),   # HP <= 5
]
UFO_HIT = (48, 24)  # 被弾フレーム

# ==== UFO Boss ====================================================
class BossUFO:
    def __init__(self):
        self.w, self.h = UFO_W, UFO_H
        self.x = W // 2 - self.w // 2
        self.y = 26
        self.vx = 1.3
        self.hp = 20
        self.hit_flash = 0
        self.t = 0
        self.exploding = False
        self.particles = []
        self.speed_max = 6.0  # 上限

    def take_damage(self, amount=1):
        self.hp -= amount
        sign = 1 if self.vx >= 0 else -1
        speed = min(abs(self.vx) + 0.5, self.speed_max)
        self.vx = sign * speed
        self.hit_flash = 6

    def update(self):
        if self.exploding:
            alive = []
            for p in self.particles:
                p["x"] += p["vx"]
                p["y"] += p["vy"]
                p["vy"] += 0.02
                p["life"] -= 1
                if p["life"] > 0:
                    alive.append(p)
            self.particles = alive
            return

        self.t += 1
        self.x += self.vx

        # HPが減るほど上下揺れが強くなる
        shake_amp = 2 + (20 - max(self.hp, 0)) * 0.3
        self.y = 24 + int(math.sin(self.t * 0.08) * shake_amp)

        if self.x <= 6 or self.x + self.w >= W - 6:
            self.vx *= -1

        if self.hit_flash > 0:
            self.hit_flash -= 1

    def draw(self):
        if self.exploding:
            for p in self.particles:
                pyxel.pset(int(p["x"]), int(p["y"]), p["c"])
            return

        # HPに応じて通常フレームを選択
        if self.hp > 10:
            u, v = UFO_PHASES[0]
        elif self.hp > 5:
            u, v = UFO_PHASES[1]
        else:
            u, v = UFO_PHASES[2]

        # 被弾中はヒットフレームを優先（点滅）
        if self.hit_flash % 2 == 1:
            u, v = UFO_HIT

        pyxel.blt(int(self.x), int(self.y), 0, u, v, UFO_W, UFO_H, 0)

        # HP表示は非表示（要望反映）
        # pyxel.text(W // 2 - 16, 16, f"UFO HP:{self.hp:02}", 7)

    def start_explosion(self):
        self.exploding = True
        self.particles = []
        for _ in range(60):
            ang = random.random() * math.tau
            spd = random.uniform(0.5, 2.2)
            self.particles.append({
                "x": self.x + self.w / 2,
                "y": self.y + self.h / 2,
                "vx": math.cos(ang) * spd,
                "vy": math.sin(ang) * spd,
                "life": random.randint(20, 40),
                "c": random.choice([7, 10, 8, 9, 2])
            })

    def is_hit_ball(self, bx, by, br):
        x, y, w, h = self.x, self.y, self.w, self.h
        nx = max(x, min(bx, x + w))
        ny = max(y, min(by, y + h))
        dx, dy = bx - nx, by - ny
        return (dx * dx + dy * dy) <= (br * br)

# ==== Game ========================================================
class Game:
    def __init__(self):
        pyxel.init(W, H, title="BRICK RAIDERS")
        # 同じフォルダに breakout_assets.pyxres を置く
        pyxel.load("breakout_assets.pyxres")

        self.make_sounds()
        self.goto_title()
        pyxel.run(self.update, self.draw)

    def make_sounds(self):
        pyxel.sounds[0].set(notes="C3", tones="P", volumes="6", effects="N", speed=6)           # 反射
        pyxel.sounds[1].set(notes="C3E3G3", tones="T", volumes="764", effects="N", speed=4)     # 破壊
        pyxel.sounds[2].set(notes="G2F2E2D2", tones="N", volumes="7643", effects="N", speed=6)  # ミス
        pyxel.sounds[3].set(notes="E3G3C4", tones="T", volumes="764", effects="N", speed=6)     # ボス被弾
        pyxel.sounds[4].set(notes="C3D3E3G3", tones="T", volumes="7777", effects="N", speed=6)  # クリア
        pyxel.sounds[5].set(notes="C4E4G4C4", tones="T", volumes="7777", effects="N", speed=6)  # 1UP
        pyxel.sounds[6].set(notes="C4G3E3C3", tones="N", volumes="7776", effects="N", speed=3)  # 爆発
        # ★ STARTジングル（短め・即開始）
        pyxel.sounds[7].set(notes="C3G3C4", tones="TTT", volumes="777", effects="NNN", speed=6)

    def goto_title(self):
        self.state = "TITLE"   # TITLE / READY / PLAY / CLEAR / ALLCLEAR / GAMEOVER / BOSS_EXPLODE
        self.stage = 1
        self.score = 0
        self.lives = 3
        self.next_life = 200
        self.bar_x = W // 2 - BAR_W // 2
        self.bar_y = H - FOOTER_H - 8
        self.ball_x = self.bar_x + BAR_W / 2
        self.ball_y = self.bar_y - BALL_R - 0.1
        self.ball_vx = 0
        self.ball_vy = 0
        self.boss = None
        self.bricks = []
        self.cool = 0
        self.last_unbreak_id = None
        self.unbreak_hit_streak = 0
        self.explode_timer = 0
        self.clear_timer = 0
        self.title_timer = 0      # 点滅用タイマー

    def reset(self, all_reset=False):
        if all_reset:
            self.stage = 1
            self.score = 0
            self.lives = 3
            self.next_life = 200
        self.bar_x = W // 2 - BAR_W // 2
        self.bar_y = H - FOOTER_H - 8
        self.is_boss = (self.stage == 10)
        self.boss = BossUFO() if self.is_boss else None
        # ★ ランダムレイアウト選択
        self.bricks = [] if self.is_boss else self.build_bricks(self.stage)
        self.state = "READY"
        self.cool = 0
        self.reset_ball_on_paddle()
        self.last_unbreak_id = None
        self.unbreak_hit_streak = 0
        self.explode_timer = 0
        self.clear_timer = 0

    def continue_stage(self):
        self.score = 0
        self.lives = 3
        self.next_life = 200
        self.is_boss = (self.stage == 10)
        self.boss = BossUFO() if self.is_boss else None
        # ★ ランダムレイアウト選択
        self.bricks = [] if self.is_boss else self.build_bricks(self.stage)
        self.state = "READY"
        self.cool = 0
        self.reset_ball_on_paddle()
        self.last_unbreak_id = None
        self.unbreak_hit_streak = 0
        self.explode_timer = 0
        self.clear_timer = 0

    def next_stage(self):
        self.stage += 1
        if self.stage > 10:
            self.state = "ALLCLEAR"
            pyxel.play(2, 4)
            return
        if self.stage == 10:
            self.is_boss = True
            self.boss = BossUFO()
            self.bricks = []
            self.state = "READY"
            self.cool = 0
            self.reset_ball_on_paddle()
            pyxel.play(2, 4)
            return
        self.reset()
        pyxel.play(2, 4)

    def build_bricks(self, stage):
        layout = pick_layout_for_stage(stage)
        bricks = []
        cols_max = max(len(row) for row in layout) if layout else 0
        total_w = cols_max * BRK_W + (cols_max - 1) * BRICK_GAP if cols_max > 0 else 0
        start_x = (W - total_w) // 2 if cols_max > 0 else 0

        for r, row in enumerate(layout):
            for c, ch in enumerate(row):
                if ch == " ":
                    continue
                x = start_x + c * (BRK_W + BRICK_GAP)
                y = BRICK_OFFSET_Y + r * (BRK_H + BRICK_GAP)

                if ch == "1":
                    hp, unbreak, score = 1, False, 10
                    style = (c + stage) % len(BRK1_FRAMES)  # HP1は3色ローテ
                    kind = "hp1"
                elif ch == "2":
                    hp, unbreak, score = 2, False, 20
                    style = (r + stage) % len(BRK2_FRAMES)  # HP2も3色ローテ
                    kind = "hp2"
                elif ch == "#":
                    hp, unbreak, score = 999, True, 0
                    style = 0
                    kind = "x"
                else:
                    continue

                bricks.append({
                    "x": x, "y": y,
                    "hp": hp, "unbreak": unbreak, "score": score,
                    "style": style, "kind": kind
                })
        return bricks

    # ---- ボール初期化（真上に発射）----
    def reset_ball_on_paddle(self):
        self.ball_x = self.bar_x + BAR_W / 2
        self.ball_y = self.bar_y - BALL_R - 0.1
        self.ball_vx = 0
        self.ball_vy = -abs(SPEED * 1.2)

    # ---- 角ハマり対策 ----
    def rotate_vel(self, vx, vy, theta):
        c, s = math.cos(theta), math.sin(theta)
        return vx * c - vy * s, vx * s + vy * c

    def anti_stuck(self, strong=False):
        jitter = JITTER_STRONG if strong else JITTER_SMALL
        self.ball_vx += (random.random() - 0.5) * 2 * jitter
        self.ball_vy += (random.random() - 0.5) * 2 * jitter
        if strong:
            theta = random.choice([-1, 1]) * ROTATE_STRONG
            self.ball_vx, self.ball_vy = self.rotate_vel(self.ball_vx, self.ball_vy, theta)
        self.clamp_angle()

    def clamp_angle(self):
        if abs(self.ball_vx) < MIN_V:
            self.ball_vx = MIN_V if self.ball_vx >= 0 else -MIN_V
        if abs(self.ball_vy) < MIN_V:
            self.ball_vy = MIN_V if self.ball_vy >= 0 else -MIN_V

    # ---- ライフアップ ----
    def check_lifeup(self):
        while self.score >= self.next_life:
            self.lives += 1
            self.next_life += 200
            pyxel.play(2, 5)

    # ==== グリッド色決定 & 描画 ====================================
    def get_grid_color(self):
        """ステージ帯に応じたグリッド色を返す"""
        if getattr(self, "is_boss", False) or self.stage == 10:
            return 8   # 赤（ボス）
        if self.stage <= 3:
            return 5   # 明るい青
        if self.stage <= 6:
            return 11  # ライトグリーン
        return 4      # オレンジ

    def draw_grid(self, color, step=16): # stepの数字を8，12，16,24に変える
        """フッターの上までグリッドを描画"""
        for x in range(0, W, step):
            pyxel.line(x, 0, x, H - FOOTER_H, color)
        for y in range(0, H - FOOTER_H, step):
            pyxel.line(0, y, W, y, color)

    # ==== 共通：中央揃えフッター描画 ==============================
    def draw_footer_bar(self, msg: str):
        pyxel.rect(0, H - FOOTER_H, W, FOOTER_H, 1)
        pyxel.rectb(0, H - FOOTER_H, W, FOOTER_H, 0)
        x = W // 2 - len(msg) * 2  # 文字幅4px→×2で中央
        y = H - FOOTER_H + 2
        pyxel.text(x, y, msg, 13)

    # ---- 更新 -----------------------------------------------------
    def update(self):
        # === グローバル操作 ===
        # ESCでゲーム終了（非表示ショートカット）
        if pyxel.btnp(pyxel.KEY_ESCAPE):
            pyxel.quit()

        # Rでどこからでもタイトルへ（タイトル画面では無効）
        if pyxel.btnp(pyxel.KEY_R) and self.state != "TITLE":
            self.goto_title()
            return

        # ===== タイトル =====
        if self.state == "TITLE":
            self.title_timer += 1

            # 隠し：1〜9で各面、Bでボス
            digit_to_stage = {
                pyxel.KEY_1: 1, pyxel.KEY_2: 2, pyxel.KEY_3: 3, pyxel.KEY_4: 4, pyxel.KEY_5: 5,
                pyxel.KEY_6: 6, pyxel.KEY_7: 7, pyxel.KEY_8: 8, pyxel.KEY_9: 9,
            }
            for k, stage_no in digit_to_stage.items():
                if pyxel.btnp(k):
                    self.stage = stage_no
                    self.score = 0
                    self.lives = 100
                    self.next_life = 200
                    self.reset(all_reset=False)
                    return
            if pyxel.btnp(pyxel.KEY_B):
                self.stage = 10
                self.score = 0
                self.lives = 100
                self.next_life = 200
                self.reset(all_reset=False)
                return

            # ★ ENTERで開始SEを鳴らしつつ即ゲーム開始（READYへ）
            if pyxel.btnp(pyxel.KEY_RETURN):
                pyxel.play(2, 7)      # スタートSE（チャンネル2）
                self.reset(all_reset=True)
            return

        # ===== ALL CLEAR =====
        if self.state == "ALLCLEAR":
            if pyxel.btnp(pyxel.KEY_R):
                self.goto_title()
            return

        # ===== CLEAR（通常ステージ・自動で次へ）=====
        if self.state == "CLEAR":
            if self.clear_timer == 0:
                self.clear_timer = 60  # 約1秒
            if pyxel.btnp(pyxel.KEY_R):
                self.clear_timer = 1
            self.clear_timer -= 1
            if self.clear_timer <= 0:
                self.next_stage()
            return

        # ===== BOSS爆発中 → 爆発終了で自動ALL CLEAR =====
        if self.state == "BOSS_EXPLODE":
            if self.boss:
                self.boss.update()
            self.explode_timer -= 1
            if self.explode_timer <= 0 or (self.boss and len(self.boss.particles) == 0):
                self.state = "ALLCLEAR"
                pyxel.play(2, 4)
            return

        # ===== GAME OVER =====
        if self.state == "GAMEOVER":
            if pyxel.btnp(pyxel.KEY_C):
                self.continue_stage()
            return

        # ===== READY/PLAY =====
        if pyxel.btn(pyxel.KEY_LEFT):
            self.bar_x -= 3
        if pyxel.btn(pyxel.KEY_RIGHT):
            self.bar_x += 3
        self.bar_x = max(0, min(W - BAR_W, self.bar_x))

        if self.state == "READY":
            self.ball_x = self.bar_x + BAR_W / 2
            self.ball_y = self.bar_y - BALL_R - 0.1
            if pyxel.btnp(pyxel.KEY_SPACE):
                self.state = "PLAY"
            return

        # ==== プレイ中の移動＆衝突（高速時だけサブステップ）====
        boss_rect = None
        if getattr(self, "is_boss", False) and self.boss:
            self.boss.update()
            boss_rect = (self.boss.x, self.boss.y, self.boss.w, self.boss.h)

        speed = math.sqrt(self.ball_vx * self.ball_vx + self.ball_vy * self.ball_vy)
        if speed > SUBSTEP_SPEED_THRESHOLD:
            steps = min(int(speed * SUBSTEP_MULTIPLIER), SUBSTEP_MAX_STEPS)
        else:
            steps = 1

        for _ in range(steps):
            prev_x, prev_y = self.ball_x, self.ball_y

            self.ball_x += self.ball_vx / steps
            self.ball_y += self.ball_vy / steps

            # 壁反射
            if self.ball_x - BALL_R <= 0:
                self.ball_x = BALL_R
                self.ball_vx *= -1
                pyxel.play(0, 0)
            if self.ball_x + BALL_R >= W:
                self.ball_x = W - BALL_R
                self.ball_vx *= -1
                pyxel.play(0, 0)
            if self.ball_y - BALL_R <= 0:
                self.ball_y = BALL_R
                self.ball_vy = +max(abs(self.ball_vy), MIN_VY_KICK)
                self.ball_vx += (random.random() - 0.5) * 0.20
                self.clamp_angle()
                pyxel.play(0, 0)

            # バー反射
            if self.ball_vy > 0 and self.hit_bar():
                hit = (self.ball_x - (self.bar_x + BAR_W / 2)) / (BAR_W / 2)
                self.ball_vx = SPEED * 1.2 * hit
                self.ball_vy = -abs(self.ball_vy)
                self.clamp_angle()
                pyxel.play(0, 0)
                self.cool = 3
                continue

            # ブロック or ボス
            if getattr(self, "is_boss", False):
                if boss_rect and self.cool == 0:
                    x, y, w, h = boss_rect
                    nx = max(x, min(self.ball_x, x + w))
                    ny = max(y, min(self.ball_y, y + h))
                    dx, dy = self.ball_x - nx, self.ball_y - ny
                    if dx * dx + dy * dy <= BALL_R * BALL_R:
                        coming_from_top    = prev_y <= y
                        coming_from_bottom = prev_y >= y + h
                        coming_from_left   = prev_x <= x
                        coming_from_right  = prev_x >= x + w

                        if coming_from_top or coming_from_bottom:
                            self.ball_vy = -self.ball_vy
                            self.ball_vy = (-MIN_VY_KICK if coming_from_top else +MIN_VY_KICK)
                            self.ball_y = (y - BALL_R - 1.0) if coming_from_top else (y + h + BALL_R + 1.0)
                            self.ball_vx += (random.random() - 0.5) * 0.20
                            self.cool = 6
                        else:
                            self.ball_vx = -self.ball_vx
                            self.ball_x = (x - BALL_R - 1.0) if coming_from_left else (x + w + BALL_R + 1.0)
                            self.ball_vx += (random.random() - 0.5) * 0.10
                            self.cool = 4

                        self.clamp_angle()

                        # ボスヒット +10点
                        self.score += 10
                        self.check_lifeup()

                        self.boss.take_damage(1)
                        pyxel.play(0, 3)

                        if self.boss.hp <= 0 and not self.boss.exploding:
                            self.boss.start_explosion()
                            self.state = "BOSS_EXPLODE"
                            self.ball_vx = 0
                            self.ball_vy = 0
                            self.explode_timer = 60
                            pyxel.play(2, 6)
                            break
            else:
                self.hit_bricks(prev_x, prev_y)
                if all(b["unbreak"] or b["hp"] <= 0 for b in self.bricks):
                    self.state = "CLEAR"
                    self.clear_timer = 60
                    self.ball_vx = 0
                    self.ball_vy = 0
                    break

        # cool はフレーム単位で減衰
        if self.cool > 0:
            self.cool -= 1

        # 落下
        if self.ball_y - BALL_R > H:
            self.lives -= 1
            pyxel.play(2, 2)
            if self.lives <= 0:
                self.state = "GAMEOVER"
            else:
                self.state = "READY"
                self.cool = 0
                self.reset_ball_on_paddle()

        self.clamp_angle()

    def hit_bar(self):
        bx1, by1 = self.bar_x, self.bar_y
        bx2, by2 = self.bar_x + BAR_W, self.bar_y + BAR_H
        nx = max(bx1, min(self.ball_x, bx2))
        ny = max(by1, min(self.ball_y, by2))
        dx, dy = self.ball_x - nx, self.ball_y - ny
        return dx * dx + dy * dy <= BALL_R * BALL_R

    def hit_bricks(self, prev_x, prev_y):
        if self.cool > 0:
            return
        for b in self.bricks:
            if b["hp"] <= 0:
                continue
            nx = max(b["x"], min(self.ball_x, b["x"] + BRK_W))
            ny = max(b["y"], min(self.ball_y, b["y"] + BRK_H))
            dx, dy = self.ball_x - nx, self.ball_y - ny
            if dx * dx + dy * dy <= BALL_R * BALL_R:
                was_left  = prev_x < b["x"]
                was_right = prev_x > b["x"] + BRK_W
                was_above = prev_y < b["y"]
                was_below = prev_y > b["y"] + BRK_H

                if (was_above and not was_below) or (was_below and not was_above):
                    self.ball_vy *= -1
                    self.ball_vy = (-MIN_VY_KICK if was_above else +MIN_VY_KICK)
                    self.ball_vx += (random.random() - 0.5) * 0.18
                    self.ball_y = (b["y"] - BALL_R - 0.8) if was_above else (b["y"] + BRK_H + BALL_R + 0.8)
                    self.cool = 3
                elif (was_left and not was_right) or (was_right and not was_left):
                    self.ball_vx *= -1
                    self.ball_vx += (random.random() - 0.5) * 0.12
                    self.ball_x = (b["x"] - BALL_R - 0.8) if was_left else (b["x"] + BRK_W + BALL_R + 0.8)
                    self.cool = 2

                if not b.get("unbreak", False):
                    b["hp"] -= 1
                    if b["hp"] <= 0:
                        self.score += b["score"]
                        self.check_lifeup()
                        pyxel.play(1, 1)
                    else:
                        pyxel.play(0, 0)
                    self.last_unbreak_id = None
                    self.unbreak_hit_streak = 0
                else:
                    pyxel.play(0, 0)
                    bid = id(b)
                    if self.last_unbreak_id == bid:
                        self.unbreak_hit_streak += 1
                    else:
                        self.last_unbreak_id = bid
                        self.unbreak_hit_streak = 1
                    if self.unbreak_hit_streak >= STUCK_STREAK:
                        self.anti_stuck(True)
                        self.unbreak_hit_streak = 0
                    else:
                        self.anti_stuck(False)

                self.clamp_angle()
                return

    # ==== 描画 -----------------------------------------------------
    def draw(self):
        pyxel.cls(0)

        if self.state == "TITLE":
            self.draw_title()
            return

        # 背景グリッド（フッターより上）— ステージ帯に応じた色
        grid_color = self.get_grid_color()
        self.draw_grid(grid_color, step=16)

        # ブロック or ボス
        if getattr(self, "is_boss", False):
            if self.boss:
                self.boss.draw()
        else:
            for b in self.bricks:
                if b["hp"] <= 0:
                    continue
                if b["kind"] == "x":  # unbreakable
                    u, v = BRKX_U, BRKX_V
                elif b["kind"] == "hp2":
                    u, v = BRK2_FRAMES[b.get("style", 0)]
                else:  # hp1
                    u, v = BRK1_FRAMES[b.get("style", 0)]
                pyxel.blt(int(b["x"]), int(b["y"]), 0, u, v, BRK_W, BRK_H, 0)

        # バー & ボール（スプライト）
        pyxel.blt(int(self.bar_x), int(self.bar_y) - (PADDLE_H - BAR_H),
                  0, PADDLE_U, PADDLE_V, PADDLE_W, PADDLE_H, 0)
        pyxel.blt(int(self.ball_x - BALL_W / 2), int(self.ball_y - BALL_H / 2),
                  0, BALL_U, BALL_V, BALL_W, BALL_H, 0)

        # ヘッダー
        pyxel.text(4, 4, f"SCORE: {self.score}", 7)
        pyxel.text(W // 2 - 20, 4, f"LIVES: {self.lives}", 7)
        st = "BOSS" if getattr(self, "is_boss", False) else f"{self.stage}/10"
        pyxel.text(W - 56, 4, f"STAGE: {st}", 7)

        # フッター帯（常に1行・中央揃え）
        self.draw_footer_bar("ARROWS: MOVE    R: BACK TO TITLE")

        # READY中だけ中央に「スペースで開始」を表示（PLAYになったら自然に消える）
        if self.state == "READY":
            msg = "PRESS SPACE TO LAUNCH"
            pyxel.text(W // 2 - len(msg) * 2, H // 2 - 4, msg, 10)

        # バナー（矩形なし）
        if self.state == "GAMEOVER":
            self.banner("GAME OVER\nPress C to Continue\nPress R to Title")
        elif self.state == "CLEAR":
            self.banner("STAGE CLEAR")
        elif self.state == "ALLCLEAR":
            self.banner(f"ALL STAGE CLEARED!\nSCORE: {self.score}\nPress R to Title")

    def draw_title(self):
        pyxel.cls(0)

        # タイトル背景もグリッド（穏やかな色: 1）
        self.draw_grid(color=1, step=16)

        # タイトル画像を中央表示（フッターは除外して縦中央寄せ）
        x = (W - TITLE_W) // 2
        y = (H - FOOTER_H - TITLE_H) // 2 - 12  # 微調整
        pyxel.blt(x, y, 0, TITLE_U, TITLE_V, TITLE_W, TITLE_H, 0)

        # クレジット（下段へ）
        credit = "Created by RAIDEN LLC"
        cx = (W - small_text_width(credit)) // 2
        draw_small_text(cx, H - FOOTER_H - 16, credit, 7)

        # 点滅する「PRESS ENTER TO START」
        msg = "PRESS ENTER TO START"
        if (pyxel.frame_count // 20) % 2 == 0:  # 20f間隔で点滅
            mx = W // 2 - len(msg) * 2
            pyxel.text(mx, y + TITLE_H + 18, msg, 10)

        # 下部：タイトルでは「ENTER: START」のみ表示
        self.draw_footer_bar("ENTER: START")

    def banner(self, message):
        lines = message.split("\n")
        for i, line in enumerate(lines):
            x = W // 2 - len(line) * 2
            y = H // 2 - len(lines) * 4 + i * 8
            pyxel.text(x, y, line, 10)

if __name__ == "__main__":
    Game()
