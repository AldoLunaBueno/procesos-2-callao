import os
import sys

if hasattr(sys, "_MEIPASS"):
    base_path = sys._MEIPASS
else:
    base_path = sys.base_prefix  # o sys._MEIPASS en modo ejecutable
os.environ["TCL_LIBRARY"] = os.path.join(base_path, "tcl", "tcl8.6")
os.environ["TK_LIBRARY"] = os.path.join(base_path, "tcl", "tk8.6")

print("TCL path:", os.environ.get("TCL_LIBRARY"))
print("TK path:", os.environ.get("TK_LIBRARY"))
try:
    import tkinter as tk
except ImportError as e:
    print("ERROR AL IMPORTAR TKINTER:", e)
    import traceback; traceback.print_exc()
    input("Presiona Enter para salir.")
    sys.exit(1)


import tkinter as tk
from tkinter import messagebox
import pandas as pd
from main import liq_liq_n_etapas, establecer_tkinter, NUMERO_ETAPAS
from typing import Dict

# Ventana principal
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Extracción Líquido-Líquido")
        self.entries: Dict[str, tk.Entry] = {}
        
        self.etiquetas = {
            "F_masa": "Flujo de alimentación (kg/s)",
            "F_xf": "Fracción en peso de ácido oleico (%)",
            "F_nf": "Pureza en la alimentación (%)",
            "S_masa": "Flujo de solvente (kg/s)",
            "A_aceite": "Fracción en peso de aceite (%)",
            "B_propano": "Fracción en peso de propano (%)",
            "C_oleico": "Fracción en peso de ácido oleico (%)",
            "E_compuesto": "Extracto total (kg/s)",
            "y_compuesto": "Fracción del compuesto del extracto (%)"
        }

        # === Grupo: Aceite ===
        grupo_aceite = tk.LabelFrame(root, text="Alimentación: Aceite", padx=10, pady=5)
        grupo_aceite.grid(row=0, column=0, columnspan=2, pady=5, sticky="ew")
        
        valores_defecto_aceite = {
            "F_masa": 100,
            "F_xf": 0.5,
            "F_nf": 0
        }
        
        for i, campo in enumerate({"F_masa", "F_xf", "F_nf"}):
            tk.Label(grupo_aceite, text=self.etiquetas[campo]).grid(row=i, column=0, sticky="e")
            entry = tk.Entry(grupo_aceite)
            entry.grid(row=i, column=1)
            entry.insert(0, str(valores_defecto_aceite[campo]))
            self.entries[campo] = entry

        # === Grupo: Solvente ===
        grupo_solvente = tk.LabelFrame(root, text="Solvente: Propano", padx=10, pady=5)
        grupo_solvente.grid(row=1, column=0, columnspan=2, pady=5, sticky="ew")

        valores_defecto_solvente = {
            "S_masa": 1500
        }
        campo = "S_masa"
        tk.Label(grupo_solvente, text=self.etiquetas[campo]).grid(row=0, column=0, sticky="e")
        entry = tk.Entry(grupo_solvente)
        entry.grid(row=0, column=1)
        entry.insert(0, str(valores_defecto_solvente[campo]))
        self.entries[campo] = entry

        # === Grupo: Composición del solvente ===
        grupo_comp = tk.LabelFrame(root, text="Composición del solvente", padx=10, pady=5)
        grupo_comp.grid(row=2, column=0, columnspan=2, pady=5, sticky="ew")

        valores_defecto_comp = {
            "A_aceite": 0.018,
            "B_propano": 0.98,
            "C_oleico": 0.002
        }        
        
        for i, campo in enumerate(["A_aceite", "B_propano", "C_oleico"]):
            tk.Label(grupo_comp, text=self.etiquetas[campo]).grid(row=i, column=0, sticky="e")
            entry = tk.Entry(grupo_comp)
            entry.grid(row=i, column=1)
            entry.insert(0, str(valores_defecto_comp[campo]))
            self.entries[campo] = entry

        # === Número de etapas ===
        tk.Label(root, text="Número de etapas").grid(row=4, column=0, sticky="e")
        self.etapas_entry = tk.Entry(root)
        self.etapas_entry.insert(0, str(NUMERO_ETAPAS))
        self.etapas_entry.grid(row=4, column=1)

        # === Frame para botones ===
        frame_botones = tk.Frame(root)
        frame_botones.grid(row=5, column=0, columnspan=2, pady=10)

        # === Botón calcular ===
        calcular_btn = tk.Button(frame_botones, text="Calcular", command=self.calcular, fg="white", bg="green")
        calcular_btn.pack(side="left", padx=5)
        
        # === Botón limpiar ===
        limpiar_btn = tk.Button(frame_botones, text="Limpiar", command=self.limpiar, fg="white", bg="red")
        limpiar_btn.pack(side="left", padx=5)
        
        
        # === Frame para resultados ===
        self.grupo_resultados = tk.LabelFrame(root, text="Resultados", padx=10, pady=5)
        self.grupo_resultados.grid(row=0, column=2, rowspan=6, padx=10, pady=5, sticky="ns")

        self.resultados_labels = {
            "E_compuesto": tk.StringVar(),
            "y_compuesto": tk.StringVar()
        }

        for i, (k, var) in enumerate(self.resultados_labels.items()):
            tk.Label(self.grupo_resultados, text=self.etiquetas[k]).grid(row=i, column=0, sticky="e")
            entry = tk.Entry(self.grupo_resultados, textvariable=var, state="readonly", fg="red")
            entry.grid(row=i, column=1)


    def calcular(self):
        try:
            # validación
            if not all(self.entries.values()):
                raise ValueError
            if not self.etapas_entry.get():
                raise ValueError
            
            # Extraer datos
            valores = {k: float(self.entries[k].get()) for k in self.entries}
            etapas = int(self.etapas_entry.get())

            F = {
                "masa": float(valores["F_masa"]),
                "xf": float(valores["F_xf"]),
                "nf": float(valores["F_nf"]),
            }
            S_masa = valores["S_masa"]

            solvente = {
                "A": float(valores["A_aceite"]),
                "B": float(valores["B_propano"]),
                "C": float(valores["C_oleico"]),
            }

            # Ejecutar
            establecer_tkinter()
            E_comp, y_comp = liq_liq_n_etapas(etapas, F=F, S_masa=S_masa, solvente=solvente)

            self.resultados_labels["E_compuesto"].set(f"{E_comp:.3f}")
            self.resultados_labels["y_compuesto"].set(f"{y_comp:.4f}")

        except ValueError as e:
            messagebox.showerror("Error", "Falta llenar uno o más campos")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            
    def limpiar(self):
        for entry in self.entries.values():
            entry.delete(0, tk.END)

        self.etapas_entry.delete(0, tk.END)

        self.resultados_labels["E_compuesto"].set("")
        self.resultados_labels["y_compuesto"].set("")


if __name__ == "__main__":
    establecer_tkinter()
    root = tk.Tk()
    app = App(root)
    root.mainloop()
