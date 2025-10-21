# Afunda ou Bóia — Simulador + Jogo (fórmulas fixas ao lado)
# - Mantém seu simulador (fundo branco, grade, snap, água preenchida, setas após "Analisar (IA)")
# - Adiciona aba "Jogo (5 fases)" com verificação de certo/errado
# - As FÓRMULAS ficam FIXAS no painel da direita nas duas abas

import tkinter as tk
from tkinter import ttk

# ---------------- Cores e constantes (iguais ao seu simulador) ----------------
COL_BG     = "#ffffff"   # fundo branco
COL_GRID   = "#e5e7eb"   # grade
COL_LINE   = "#0b84d8"   # linha d'água
COL_WATER  = "#e6f5ff"   # água preenchida
COL_SHAPE  = "#111827"   # contorno das formas
COL_E      = "#059669"   # empuxo
COL_P      = "#ef4444"   # peso

GRID    = 20
WATER_Y = 360
SNAP    = True

SIZE        = 120
RECT_RATIO  = 1.6
PERSON_WF   = 0.60
PERSON_HF   = 2.00

SHAPES = ["Quadrado", "Retângulo", "Círculo", "Pessoa"]

FORMULAS_FIXAS = [
    "E = peso do fluido deslocado",
    "E = ρ_f · g · V_deslocado",
    "P = m · g",
    "ρ = m / V",
    "γ = ρ · g",
    "p = p_atm + ρ · g · h",
    "Δp = ρ · g · Δh",
    "P_aparente = P − E",
    "Boia se E ≥ P; afunda se P > E",
]

# ---------------- Utilidades p/ Jogo ----------------
def pct(x, p):  # tolerância absoluta
    return abs(x) * p

def parse_num(txt):
    try:
        return float(str(txt).replace(",", ".").strip())
    except:
        return None

def dentro(x, alvo, tol):
    return (x is not None) and (abs(x - alvo) <= tol)

# ---------------- Fases do jogo (gabarito) ----------------
FASES = [
    {   # Fase 1
        "titulo": "Fase 1 — Bloco em água e em óleo",
        "texto": (
            "Um bloco de madeira flutua em água doce com 2/3 do volume V submerso e, em óleo, com 0,90·V submerso.\n"
            "Determine a massa específica (densidade): (a) da madeira e (b) do óleo."
        ),
        "campos": [
            {"rotulo": "ρ_madeira (kg/m³)", "chave": "rho_mad",  "esperado": 666.7, "tol": pct(666.7, 0.02)},
            {"rotulo": "ρ_óleo (kg/m³)",    "chave": "rho_oleo", "esperado": 740.7, "tol": pct(740.7, 0.02)},
        ]
    },
    {   # Fase 2
        "titulo": "Fase 2 — Cubo suspenso em líquido",
        "texto": (
            "Cubo: aresta L = 0,600 m, massa 450 kg. Líquido: ρ = 1030 kg/m³. Tanque aberto, p_atm = 1,00 atm.\n"
            "Topo do cubo a h = L/2 abaixo da superfície (0,30 m). Determine:\n"
            "(a) força na face superior (N), (b) força na face inferior (N), (c) tração na corda (N), (d) empuxo (N).\n"
            "Dica: F_inferior − F_superior = Empuxo."
        ),
        "campos": [
            {"rotulo": "(a) F_superior (N)", "chave": "Ftop",   "esperado": 37560, "tol": 0.03*37560},
            {"rotulo": "(b) F_inferior (N)", "chave": "Fbot",   "esperado": 39740, "tol": 0.03*39740},
            {"rotulo": "(c) Tração T (N)",   "chave": "T",      "esperado": 2230,  "tol": 0.05*2230},
            {"rotulo": "(d) Empuxo E (N)",   "chave": "E",      "esperado": 2180,  "tol": 0.05*2180},
        ]
    },
    {   # Fase 3
        "titulo": "Fase 3 — Âncora no ar e na água",
        "texto": (
            "Uma âncora de ferro (ρ = 7870 kg/m³) parece ser 200 N mais leve na água do que no ar.\n"
            "(a) Qual é o volume da âncora? (b) Quanto ela pesa no ar?"
        ),
        "campos": [
            {"rotulo": "(a) Volume (m³)",    "chave": "V",    "esperado": 0.0204, "tol": 0.03*0.0204},
            {"rotulo": "(b) Peso no ar (N)", "chave": "Wair", "esperado": 1573,   "tol": 0.05*1573},
        ]
    },
    {   # Fase 4
        "titulo": "Fase 4 — Esfera oca de ferro flutuando",
        "texto": (
            "Esfera de ferro oca flutua quase totalmente submersa em água. Diâmetro EXTERNO = 60,0 cm.\n"
            "ρ_ferro = 7,87 g/cm³. Determine o DIÂMETRO INTERNO."
        ),
        "campos": [
            {"rotulo": "Diâmetro interno (cm)", "chave": "Dint_cm", "esperado": 57.4, "tol": 0.02*57.4},
        ],
        "normalizador": "cm"  # aceita também ~0,574 m
    },
    {   # Fase 5
        "titulo": "Fase 5 — Bloco + lastro de chumbo (duas variações)",
        "texto": (
            "Bloco de madeira: m = 3,67 kg, ρ = 600 kg/m³. Deseja-se flutuar com 0,900·V do bloco submerso.\n"
            "Chumbo: ρ = 1,14×10⁴ kg/m³. Determine a massa de chumbo necessária se colado:\n"
            "(a) NO TOPO do bloco (acima da água); (b) NA BASE do bloco (submerso)."
        ),
        "campos": [
            {"rotulo": "(a) m_chumbo no topo (kg)", "chave": "mtopo", "esperado": 1.835, "tol": 0.03*1.835},
            {"rotulo": "(b) m_chumbo na base (kg)", "chave": "mbase", "esperado": 2.011, "tol": 0.03*2.011},
        ]
    },
]

# ---------------- Simulador (igual ao seu, só organizado em classe de aba) ----------------
class SimuladorFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=COL_BG)
        self.bodies = []
        self.drag = {"idx": None, "dx": 0, "dy": 0}
        self.analysis = None
        self.frozen = False
        self._build_ui()

    class Body:
        def __init__(self, shape, x=100, y=100):
            self.shape = shape
            self.x, self.y = x, y
        def bbox(self):
            if self.shape == "Quadrado":
                w = h = SIZE
            elif self.shape == "Retângulo":
                w = SIZE; h = int(SIZE/RECT_RATIO)
            elif self.shape == "Círculo":
                w = h = SIZE
            elif self.shape == "Pessoa":
                w = int(SIZE*PERSON_WF); h = int(SIZE*PERSON_HF)
            return self.x, self.y, self.x+w, self.y+h

    def _build_ui(self):
        # layout em 2 colunas: esquerda (canvas/controles) | direita (fórmulas fixas)
        left = tk.Frame(self, bg=COL_BG)
        left.pack(side="left", fill="both", expand=True)
        right = tk.Frame(self, bg=COL_BG)
        right.pack(side="right", fill="y", padx=(6,10), pady=(8,10))

        # barra de controles
        top = tk.Frame(left, bg=COL_BG)
        top.pack(side="top", fill="x", padx=10, pady=6)

        tk.Label(top, text="Forma:", bg=COL_BG).pack(side="left")
        self.shape_var = tk.StringVar(value=SHAPES[0])
        tk.OptionMenu(top, self.shape_var, *SHAPES).pack(side="left", padx=6)
        tk.Button(top, text="Adicionar", command=self.add_body).pack(side="left", padx=6)
        tk.Button(top, text="Limpar tudo", command=self.clear_all).pack(side="left", padx=6)
        self.btn_ai = tk.Button(top, text="Analisar (IA)", bg="#22c55e", fg="white", command=self.analyze)
        self.btn_ai.pack(side="left", padx=6)
        self.btn_reset = tk.Button(top, text="Reiniciar", bg="#9333ea", fg="white",
                                   command=self.reset, state="disabled")
        self.btn_reset.pack(side="left", padx=6)

        # canvas
        self.canvas = tk.Canvas(left, bg=COL_BG, highlightthickness=1, highlightbackground=COL_GRID)
        self.canvas.pack(fill="both", expand=True, padx=12, pady=12)

        self.canvas.bind("<Button-1>", self.on_down)
        self.canvas.bind("<B1-Motion>", self.on_move)
        self.canvas.bind("<ButtonRelease-1>", self.on_up)

        tk.Label(left, text="Monte → Analisar (IA) → Congela  •  Reiniciar p/ novo",
                 bg=COL_BG, fg="#64748b").pack(anchor="w", padx=12, pady=(0,10))

        # fórmulas fixas (painel lateral)
        tk.Label(right, text="Fórmulas (Arquimedes/Hidrostática)", bg=COL_BG,
                 font=("Arial", 12, "bold")).pack(anchor="w", pady=(0,6))
        self.formulas = tk.Listbox(right, width=36, height=28, bd=0, highlightthickness=0)
        self.formulas.pack(fill="y")
        for f in FORMULAS_FIXAS:
            self.formulas.insert(tk.END, f)

    # ações simulador
    def add_body(self):
        if self.frozen: return
        self.bodies.append(self.Body(self.shape_var.get(), 100, 100))
        self.draw()

    def clear_all(self):
        if self.frozen: return
        self.bodies.clear(); self.draw()

    def analyze(self):
        if self.frozen: return
        self.analysis = []
        for b in self.bodies:
            _, y0, _, y1 = b.bbox()
            self.analysis.append({"E": y1 > WATER_Y, "P": True})
        self.frozen = True
        self.btn_ai.config(state="disabled"); self.btn_reset.config(state="normal")
        self.draw()

    def reset(self):
        self.bodies.clear(); self.analysis = None; self.frozen = False
        self.btn_ai.config(state="normal"); self.btn_reset.config(state="disabled")
        self.draw()

    # arrasto
    def on_down(self, e):
        if self.frozen: return
        for i in range(len(self.bodies)-1, -1, -1):
            x0,y0,x1,y1 = self.bodies[i].bbox()
            if x0 <= e.x <= x1 and y0 <= e.y <= y1:
                self.drag = {"idx": i, "dx": e.x - self.bodies[i].x, "dy": e.y - self.bodies[i].y}
                break

    def on_move(self, e):
        if self.frozen: return
        i = self.drag["idx"]
        if i is None: return
        nx = e.x - self.drag["dx"]; ny = e.y - self.drag["dy"]
        if SNAP:
            nx = round(nx/GRID)*GRID; ny = round(ny/GRID)*GRID
        self.bodies[i].x, self.bodies[i].y = nx, ny
        self.draw()

    def on_up(self, e):
        self.drag = {"idx": None, "dx": 0, "dy": 0}

    # desenho
    def draw(self):
        c = self.canvas
        c.delete("all")
        W = c.winfo_width() or 800
        H = c.winfo_height() or 520

        # água + linha
        c.create_rectangle(0, WATER_Y, W, H, fill=COL_WATER, outline="")
        c.create_line(0, WATER_Y, W, WATER_Y, fill=COL_LINE, width=2)

        # grade
        for x in range(0, W, GRID): c.create_line(x, 0, x, H, fill=COL_GRID)
        for y in range(0, H, GRID): c.create_line(0, y, W, y, fill=COL_GRID)

        # corpos
        for b in self.bodies:
            x0,y0,x1,y1 = b.bbox()
            if b.shape in ("Quadrado","Retângulo"):
                c.create_rectangle(x0,y0,x1,y1, outline=COL_SHAPE, width=2)
            elif b.shape == "Círculo":
                c.create_oval(x0,y0,x1,y1, outline=COL_SHAPE, width=2)
            elif b.shape == "Pessoa":
                self.draw_person(x0,y0,x1,y1)

        # setas após IA
        if self.analysis:
            for b, flags in zip(self.bodies, self.analysis):
                x0,y0,x1,y1 = b.bbox()
                mid = (y0+y1)//2
                if flags["E"]:
                    self.arrow(c, x0-16, mid+6, x0-16, mid-54, COL_E)   # empuxo ↑
                if flags["P"]:
                    self.arrow(c, x1+16, mid-6, x1+16, mid+54, COL_P)   # peso ↓

        # moldura
        c.create_rectangle(1,1,W-1,H-1, outline=COL_GRID)

    def draw_person(self,c,x0,y0,x1,y1):
        cx=(x0+x1)/2; w=x1-x0; h=y1-y0
        r=max(8,min(w,h)*0.18); head=y0+r+3
        c.create_oval(cx-r, head-r, cx+r, head+r, outline=COL_SHAPE, width=2)
        neck=head+r; torso=h*0.4; hip=neck+torso
        c.create_line(cx, neck, cx, hip, fill=COL_SHAPE, width=2)
        arm=w*0.5; ay=neck+torso*0.3
        c.create_line(cx-arm, ay, cx+arm, ay, fill=COL_SHAPE, width=2)
        leg=h*0.3
        c.create_line(cx, hip, cx-w*0.2, hip+leg, fill=COL_SHAPE, width=2)
        c.create_line(cx, hip, cx+w*0.2, hip+leg, fill=COL_SHAPE, width=2)

    def arrow(self,c,x0,y0,x1,y1,color):
        c.create_line(x0,y0,x1,y1, fill=color, width=3)
        s=7
        if y1<y0:
            c.create_polygon(x1,y1, x1-s,y1+s*1.4, x1+s,y1+s*1.4, fill=color, outline=color)
        else:
            c.create_polygon(x1,y1, x1-s,y1-s*1.4, x1+s,y1-s*1.4, fill=color, outline=color)

# ---------------- Jogo (com fórmulas fixas à direita) ----------------
class JogoFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=COL_BG)
        self.fase_idx = 0
        self.entradas = {}  # chave -> tk.Entry
        self._build_ui()

    def _build_ui(self):
        # layout em 2 colunas: esquerda (enunciado e respostas) | direita (fórmulas fixas)
        left = tk.Frame(self, bg=COL_BG)
        left.pack(side="left", fill="both", expand=True)
        right = tk.Frame(self, bg=COL_BG)
        right.pack(side="right", fill="y", padx=(6,10), pady=(8,10))

        # conteúdo esquerdo
        self.titulo = tk.Label(left, text="", bg=COL_BG, font=("Arial", 14, "bold"))
        self.titulo.pack(anchor="w", padx=12, pady=(12,6))

        self.enunciado = tk.Message(left, text="", bg=COL_BG, width=820, font=("Arial", 11))
        self.enunciado.pack(anchor="w", padx=12)

        self.form = tk.Frame(left, bg=COL_BG)
        self.form.pack(anchor="w", padx=12, pady=8)

        self.msg = tk.Label(left, text="", bg=COL_BG, fg="#444")
        self.msg.pack(anchor="w", padx=12, pady=(4,8))

        btns = tk.Frame(left, bg=COL_BG)
        btns.pack(anchor="w", padx=12, pady=6)
        self.btn_check = tk.Button(btns, text="Verificar", command=self.verificar, bg="#22c55e", fg="white")
        self.btn_check.pack(side="left")
        self.btn_next = tk.Button(btns, text="Próxima fase ▶", command=self.next_fase, state="disabled")
        self.btn_next.pack(side="left", padx=8)

        # fórmulas fixas (painel à direita)
        tk.Label(right, text="Fórmulas (Arquimedes/Hidrostática)", bg=COL_BG,
                 font=("Arial", 12, "bold")).pack(anchor="w", pady=(0,6))
        self.formulas = tk.Listbox(right, width=36, height=28, bd=0, highlightthickness=0)
        self.formulas.pack(fill="y")
        for f in FORMULAS_FIXAS:
            self.formulas.insert(tk.END, f)

        self.load_fase()

    def load_fase(self):
        self.entradas.clear()
        for w in self.form.winfo_children(): w.destroy()
        fase = FASES[self.fase_idx]
        self.titulo.config(text=fase["titulo"])
        self.enunciado.config(text=fase["texto"])
        for item in fase["campos"]:
            row = tk.Frame(self.form, bg=COL_BG); row.pack(anchor="w", pady=3)
            tk.Label(row, text=item["rotulo"] + ": ", bg=COL_BG).pack(side="left")
            e = tk.Entry(row, width=18); e.pack(side="left", padx=6)
            self.entradas[item["chave"]] = e
        self.msg.config(text="Dica: use ponto OU vírgula nos decimais. Tolerância ~2–5%.")

        self.btn_check.config(state="normal")
        self.btn_next.config(state="disabled")

    def verificar(self):
        fase = FASES[self.fase_idx]
        acertos = 0; total = len(fase["campos"]); mensagens = []
        for item in fase["campos"]:
            raw = self.entradas[item["chave"]].get()
            v = parse_num(raw)
            alvo = item["esperado"]; tol = item["tol"]

            # Fase 4 aceita cm ou m
            if fase.get("normalizador") == "cm":
                if v is not None and v < 5:  # se digitar em metros (~0,574), converte para cm
                    v = v * 100

            ok = dentro(v, alvo, tol)
            if ok:
                acertos += 1
                mensagens.append(f"✓ {item['rotulo']}: correto")
            else:
                if v is None:
                    mensagens.append(f"✗ {item['rotulo']}: valor inválido")
                else:
                    mensagens.append(f"✗ {item['rotulo']}: esperado ≈ {alvo:.3g} (±{tol:.2g})")

        if acertos == total:
            self.msg.config(text="✅ Tudo certo! Fase concluída.", fg="#16a34a")
            self.btn_next.config(state=("normal" if self.fase_idx < len(FASES)-1 else "disabled"))
            self.btn_check.config(state="disabled")
        else:
            self.msg.config(text="\n".join(mensagens), fg="#b91c1c")

    def next_fase(self):
        if self.fase_idx < len(FASES)-1:
            self.fase_idx += 1
            self.load_fase()

# ---------------- App com abas ----------------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FluydQuest — Simulador + Jogo")
        self.geometry("1200x760")
        self.configure(bg=COL_BG)

        tabs = ttk.Notebook(self)
        tabs.pack(fill="both", expand=True)

        self.sim_tab = SimuladorFrame(tabs)
        self.jogo_tab = JogoFrame(tabs)

        tabs.add(self.sim_tab, text="Simulador")
        tabs.add(self.jogo_tab, text="Jogo (5 fases)")

if __name__ == "__main__":
    App().mainloop()
