import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import threading
import os
import pandas as pd

# Importando nossos novos módulos
import io_system
import geo_core

# --- CONFIGURAÇÕES VISUAIS ---
BG_COLOR = "black"
FG_COLOR = "#00FF00"
FG_WHITE = "white"
FONT_MAIN = ("Consolas", 10)
FONT_BOLD = ("Consolas", 10, "bold")
FONT_HEADER = ("Consolas", 16, "bold")

class GeoSystemApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SISTEMA GEO-TERRITORIAL v3.0 [MODULAR]")
        self.root.geometry("850x750")
        self.root.configure(bg=BG_COLOR)
        
        self.file_path_localidades = ""
        self.file_path_contas = ""
        self.geo_service = None # Será inicializado depois

        # --- LAYOUT (Mesmo da v2.9) ---
        self._setup_ui()

    def _setup_ui(self):
        # Cabeçalho
        header = tk.Frame(self.root, bg=BG_COLOR)
        header.pack(pady=10)
        tk.Label(header, text="*** SISTEMA DE GESTAO TERRITORIAL ***", font=FONT_HEADER, bg=BG_COLOR, fg=FG_COLOR).pack()
        tk.Label(header, text="MODULO DE ALTA PERFORMANCE (V3.0)", font=("Consolas", 11), bg=BG_COLOR, fg=FG_WHITE).pack()

        # Bloco 1: Dados
        fr_dados = tk.LabelFrame(self.root, text=" [ 1. CONFIGURAÇÃO ] ", font=FONT_BOLD, bg=BG_COLOR, fg=FG_WHITE, bd=2)
        fr_dados.pack(pady=5, padx=20, fill="x")
        
        tk.Label(fr_dados, text="> API KEY:", font=FONT_BOLD, bg=BG_COLOR, fg=FG_COLOR).grid(row=0, column=0, sticky="w", padx=10)
        self.entry_api = tk.Entry(fr_dados, font=FONT_MAIN, bg="#111", fg=FG_WHITE, show="*")
        self.entry_api.grid(row=0, column=1, sticky="ew", padx=10)
        
        tk.Label(fr_dados, text="> LOCALIDADES:", font=FONT_BOLD, bg=BG_COLOR, fg=FG_COLOR).grid(row=1, column=0, sticky="w", padx=10)
        self.btn_f1 = tk.Button(fr_dados, text="[ CSV ]", command=self.select_file1, bg="#222", fg=FG_WHITE)
        self.btn_f1.grid(row=1, column=1, sticky="w", padx=10)
        self.lbl_f1 = tk.Label(fr_dados, text="...", bg=BG_COLOR, fg="gray")
        self.lbl_f1.grid(row=1, column=2, sticky="w")

        tk.Label(fr_dados, text="> CONTAS:", font=FONT_BOLD, bg=BG_COLOR, fg=FG_COLOR).grid(row=2, column=0, sticky="w", padx=10)
        self.btn_f2 = tk.Button(fr_dados, text="[ CSV ]", command=self.select_file2, bg="#222", fg=FG_WHITE)
        self.btn_f2.grid(row=2, column=1, sticky="w", padx=10)
        self.lbl_f2 = tk.Label(fr_dados, text="...", bg=BG_COLOR, fg="gray")
        self.lbl_f2.grid(row=2, column=2, sticky="w")

        # Bloco 2: Parâmetros
        fr_action = tk.LabelFrame(self.root, text=" [ 2. PARÂMETROS ] ", font=FONT_BOLD, bg=BG_COLOR, fg=FG_WHITE, bd=2)
        fr_action.pack(pady=5, padx=20, fill="x")
        
        self.escopo_var = tk.StringVar(value="MUNICIPAL")
        self.combo_escopo = ttk.Combobox(fr_action, textvariable=self.escopo_var, values=["MUNICIPAL", "ESTADUAL"], width=10)
        self.combo_escopo.grid(row=0, column=0, padx=10)
        self.entry_local = tk.Entry(fr_action, width=25, bg="#111", fg=FG_WHITE)
        self.entry_local.insert(0, "SAO JOSE DO RIO PRETO")
        self.entry_local.grid(row=0, column=1, padx=10)
        
        self.btn_run = tk.Button(fr_action, text=">>> INICIAR <<<", command=self.start_thread, font=("Consolas", 12, "bold"), bg="#004400", fg=FG_WHITE)
        self.btn_run.grid(row=0, column=2, padx=20, pady=10)

        # Bloco 3: Cache Info
        fr_cache = tk.LabelFrame(self.root, text=" [ 3. STATUS CACHE ] ", font=FONT_BOLD, bg=BG_COLOR, fg=FG_WHITE, bd=2)
        fr_cache.pack(pady=5, padx=20, fill="x")
        self.lbl_cache = tk.Label(fr_cache, text="Inicialize para ver dados...", font=("Consolas", 9), bg=BG_COLOR, fg=FG_COLOR)
        self.lbl_cache.pack(side="left", padx=10)
        tk.Button(fr_cache, text="[ VER ESTATÍSTICAS ]", command=self.show_stats, font=FONT_MAIN, bg="#222", fg=FG_WHITE).pack(side="right", padx=10)

        # Log
        self.log = scrolledtext.ScrolledText(self.root, width=90, height=12, font=("Consolas", 9), bg="#050505", fg="#00CC00")
        self.log.pack(pady=5, padx=20, fill="both", expand=True)

    # --- MÉTODOS AUXILIARES ---
    def log_msg(self, msg):
        self.root.after(0, lambda: self.log.insert(tk.END, f"{msg}\n") or self.log.see(tk.END))

    def update_cache_ui(self):
        if self.geo_service:
            stats = self.geo_service.cache.obter_estatisticas()
            val = (stats['total'] * 0.005) * 5.80
            txt = f"📦 ITENS: {stats['total']} | 💰 ECONOMIA: R$ {val:.2f}"
            self.lbl_cache.config(text=txt)

    def show_stats(self):
        if self.geo_service:
            stats = self.geo_service.cache.obter_estatisticas()
            msg = f"Total: {stats['total']}\nHits: {stats['hits']}\nMisses: {stats['misses']}"
            messagebox.showinfo("Cache Stats", msg)
        else:
            messagebox.showwarning("Aviso", "Processe algo primeiro.")

    def select_file1(self):
        f = filedialog.askopenfilename(); 
        if f: self.file_path_localidades = f; self.lbl_f1.config(text=os.path.basename(f))
    
    def select_file2(self):
        f = filedialog.askopenfilename(); 
        if f: self.file_path_contas = f; self.lbl_f2.config(text=os.path.basename(f))

    def start_thread(self):
        threading.Thread(target=self.run_process, daemon=True).start()

    # --- LÓGICA PRINCIPAL (ORQUESTRAÇÃO) ---
    def run_process(self):
        key = self.entry_api.get().strip()
        local = self.entry_local.get().strip().upper()
        modo = self.escopo_var.get()

        if not key or not self.file_path_localidades or not self.file_path_contas:
            self.root.after(0, lambda: messagebox.showerror("ERRO", "Preencha tudo!"))
            return

        self.root.after(0, lambda: self.btn_run.config(state="disabled", text="RODANDO..."))
        
        try:
            # 1. INICIALIZA SERVIÇO GEO
            self.log_msg("> INICIALIZANDO GEO SERVICE...")
            self.geo_service = geo_core.GeoService(key, local, modo)
            self.root.after(0, self.update_cache_ui)

            # 2. CARREGA ARQUIVOS (USANDO MÓDULO IO)
            self.log_msg("> LENDO ARQUIVOS...")
            df_locais = io_system.IOSystem.ler_csv_inteligente(self.file_path_localidades)
            df_contas = io_system.IOSystem.ler_csv_inteligente(self.file_path_contas)

            # 3. IDENTIFICA COLUNAS (USANDO MÓDULO IO)
            col_end_loc = io_system.IOSystem.achar_coluna(df_locais, ['ENDERECO_COMPLETO', 'ENDERECO', 'LOGRADOURO'])
            col_nome_loc = io_system.IOSystem.achar_coluna(df_locais, ['LOCALIDADE', 'NOME', 'UNIDADE'])
            col_sec_loc = io_system.IOSystem.achar_coluna(df_locais, ['SECRETARIA', 'SETOR'])
            
            col_end_conta = io_system.IOSystem.achar_coluna(df_contas, ['ENDERECO_CONTA', 'ENDERECO'])
            col_id_conta = io_system.IOSystem.achar_coluna(df_contas, ['ID_MEDIDOR', 'MEDIDOR', 'INSTALACAO'])
            col_tipo_conta = io_system.IOSystem.achar_coluna(df_contas, ['TIPO', 'SERVICO'])

            if not col_end_loc or not col_end_conta: raise Exception("Colunas de endereço não encontradas.")

            # 4. REMOVE DUPLICATAS
            if col_id_conta:
                df_contas, removidos = io_system.IOSystem.remover_duplicatas(df_contas, col_id_conta)
                if removidos > 0: self.log_msg(f"⚠ REMOVIDOS {removidos} DUPLICADOS.")

            # 5. MAPEIA LOCALIDADES
            self.log_msg("> MAPEANDO LOCALIDADES...")
            locais_validos = []
            for idx, row in df_locais.iterrows():
                geo = self.geo_service.geocodificar(row[col_end_loc])
                if geo:
                    locais_validos.append({
                        'Secretaria': row[col_sec_loc] if col_sec_loc else "GERAL",
                        'Localidade': row[col_nome_loc] if col_nome_loc else "SEM NOME",
                        'coords': (geo['lat'], geo['lng'])
                    })
            
            self.log_msg(f"> SEDES VALIDAS: {len(locais_validos)}")
            self.geo_service.construir_kdtree(locais_validos)

            # 6. CRUZA DADOS
            self.log_msg("> CRUZANDO CONTAS...")
            relatorio = []
            matches = 0
            
            for idx, row in df_contas.iterrows():
                if idx % 20 == 0: self.log_msg(f"  Processando {idx}...")
                
                # Dados Brutos
                end_c = str(row[col_end_conta])
                geo = self.geo_service.geocodificar(end_c)
                
                # Dados Padrão (Vazio)
                m_sec, m_loc = "NAO IDENTIFICADO", "LOCAL NAO CADASTRADO"
                log, num, bai, cep, cid = end_c, "S/N", "", "", ""

                if geo:
                    # Busca Vizinho
                    m_sec, m_loc, dist = self.geo_service.buscar_vizinho_proximo(
                        geo['lat'], geo['lng'], raio_max_metros=50
                    )
                    if m_sec != "NAO IDENTIFICADO": matches += 1
                    
                    # Preenche Endereço do Google
                    log = geo['logradouro'] if geo['logradouro'] else end_c
                    num, bai, cep, cid = geo['numero'], geo['bairro'], geo['cep'], geo['cidade']

                # Refinamento Regex (se Google falhou em separar numero)
                if "," in log and any(char.isdigit() for char in log):
                    log, num, bai = geo_core.GeoService.refinar_endereco_regex(log)

                relatorio.append({
                    'Secretaria': m_sec, 'Localidade': m_loc, 
                    'Medidor': str(row[col_id_conta]) if col_id_conta else "",
                    'Tipo': str(row[col_tipo_conta]).upper() if col_tipo_conta else "",
                    'CNPJ': '', 'Logradouro': log, 'Nº': num, 'Complemento': '', 
                    'Bairro': bai, 'CEP': cep, 'Cidade': cid, 
                    'Fornecedor': '', 'SubGrupo': '', 'Modelo Tarifário': ''
                })

            # 7. SALVA
            self.geo_service.cache.salvar_cache()
            df_final = pd.DataFrame(relatorio)
            
            # Ordenar colunas
            cols_final = ['Secretaria', 'Localidade', 'Medidor', 'Tipo', 'CNPJ', 'Logradouro', 'Nº', 'Complemento', 'Bairro', 'CEP', 'Cidade', 'Fornecedor', 'SubGrupo', 'Modelo Tarifário']
            df_final = df_final[cols_final]

            def salvar_final():
                nome_padrao = f"Relatorio_{modo}_{local}.xlsx".replace(" ", "_")
                f = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile=nome_padrao)
                if f:
                    io_system.IOSystem.salvar_excel(df_final, f)
                    self.log_msg(f"\n>>> SUCESSO! MATCHES: {matches}")
                    self.log_msg(f"> ARQUIVO: {os.path.basename(f)}")
                    self.update_cache_ui()
                    messagebox.showinfo("Sucesso", "Relatório gerado!")
            
            self.root.after(0, salvar_final)

        except Exception as e:
            self.log_msg(f"ERRO: {e}")
            self.root.after(0, lambda: messagebox.showerror("ERRO", str(e)))
        finally:
            self.root.after(0, lambda: self.btn_run.config(state="normal", text=">>> INICIAR <<<"))

if __name__ == "__main__":
    root = tk.Tk()
    app = GeoSystemApp(root)
    root.mainloop()