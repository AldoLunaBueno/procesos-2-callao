import argparse
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.ticker import MaxNLocator
from scipy.interpolate import interp1d
from scipy.optimize import bisect

import os
import sys

NUMERO_ETAPAS = 4
MUESTREO_APROXIMACION = 20

def resource_path(relative_path):
    """Devuelve la ruta absoluta a un recurso, compatible con PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def establecer_tkinter():
    os.environ["TCL_LIBRARY"] = os.path.join(sys.base_prefix, "tcl", "tcl8.6")
    os.environ["TK_LIBRARY"] = os.path.join(sys.base_prefix, "tcl", "tk8.6")


def ingesta_datos():
    fase_oleica = pd.read_table(resource_path("fase_oleica.txt"), decimal=",")
    fase_propano = pd.read_table(resource_path("fase_propano.txt"), decimal=",")
    
    return fase_oleica, fase_propano


def cargar_parametros(path="parametros_liq_liq.txt"):
    df = pd.read_csv(resource_path(path))
    params = dict(zip(df["clave"], df["valor"]))

    # reconstruir los diccionarios originales
    F = {
        "masa": float(params["F_masa"]),
        "xf": float(params["F_xf"]),
        "nf": float(params["F_nf"]),
    }
    S_masa = params["S_masa"]
    
    solvente = {
        "A": float(params["A_aceite"]),
        "B": float(params["B_propano"]),
        "C": float(params["C_oleico"]),
    }
    return F, S_masa, solvente


def graficar(X_N, Y_N, M_acum, R_acum, E_acum, n):  
    fig = plt.gcf()  # obtener figura actual
    plt.clf()  # limpiar gráficos
    fig.canvas.manager.set_window_title("Diagramas")  # cambiar título
    
    # graficar X vs N y Y vs N
    plt.subplot(2, 1, 1)
    plt.plot(X_N["X"], X_N["N"], "m.-", label="X vs Nr")
    plt.plot(Y_N["Y"], Y_N["N"], "b.-", label="Y vs Ne")
    for i in range(n):
        plt.plot([R_acum[i][0], E_acum[i][0]], [R_acum[i][1], E_acum[i][1]], "go-")
        plt.plot(M_acum[i][0], M_acum[i][1], "ro")
        plt.text(R_acum[i][0] + 0.01, R_acum[i][1], f"$R_{{{i+1}}}$")
        plt.text(E_acum[i][0] + 0.01, E_acum[i][1], f"$E_{{{i+1}}}$")
        plt.text(M_acum[i][0] + 0.01, M_acum[i][1], f"$M_{{{i+1}}}$")
    plt.xlabel("Fracción molar")
    plt.ylabel("N")
    plt.tick_params(axis='both', labelsize=6)
    plt.legend()
    # número de ticks en los ejes
    plt.gca().xaxis.set_major_locator(MaxNLocator(nbins=12))
    plt.gca().yaxis.set_major_locator(MaxNLocator(nbins=12))

    # graficar X vs Y
    plt.subplot(2, 1, 2)
    plt.plot(X_N["X"], Y_N["Y"], "c.-", label="X vs Y")
    plt.xlabel("X")
    plt.ylabel("Y")
    plt.plot([0, 1], [0, 1], "k:")
    plt.tick_params(axis='both', labelsize=6)
    plt.legend()
    # múmero de ticks en los ejes
    plt.gca().xaxis.set_major_locator(MaxNLocator(nbins=12))
    plt.gca().yaxis.set_major_locator(MaxNLocator(nbins=12))
    
    # mostrar y guardar el diagrama
    plt.tight_layout()
    os.makedirs("diagramas", exist_ok=True)
    plt.savefig("diagramas/fig-1.png")
    plt.show(block=False)


def calcular_s_prima(S):
    """Calcula la masa de solvente efectivo s' a partir del solvente S."""
    return S["masa"] / (1 + S["ns"])


def calcular_M(F, S):
    s_ = calcular_s_prima(S)
    xm = (F["masa"] * F["xf"] + s_ * S["ys"]) / (F["masa"] + s_)
    nm = (F["masa"] * F["nf"] + s_ * S["ns"]) / (F["masa"] + s_)
    
    return xm, nm


def aproximar(M, X_N, Y_N):
    # interpolaciones lineales (por defecto)
    f_X_Nr = interp1d(X_N["X"], X_N["N"], fill_value="extrapolate")
    f_Y_Ne = interp1d(Y_N["Y"], Y_N["N"], fill_value="extrapolate")
    f_X_Y = interp1d(X_N["X"], Y_N["Y"], fill_value="extrapolate")
    f_X_Y_Ne = lambda x: f_Y_Ne(f_X_Y(x))  # función composición
    
    def f(x):
        x1 = x
        x2 = f_X_Y(x)
        if np.isclose(x1, x2):
            x2 += 1e-6  # o simplemente: return np.nan
        cuerda = interp1d([x1, x2], [f_X_Nr(x), f_X_Y_Ne(x)], fill_value="extrapolate")
        nm_ = cuerda(M["xm"])
        return nm_ - M["nm"]
    a = 0
    b = 0
    
    for b in np.linspace(0, 1, MUESTREO_APROXIMACION):
        if f(a) * f(b) < 0:
            break
        a = b
    try:
        x_opt = bisect(f, a, b)
    except ValueError as e:
        raise RuntimeError(f"No se pudo encontrar raíz entre {a} y {b}") from e
    return x_opt, f_X_Nr(x_opt), f_X_Y(x_opt), f_X_Y_Ne(x_opt)


def liq_liq_n_etapas(n: int, F=None, S_masa=None, solvente=None):
    # datos experimentales
    fase_oleica, fase_propano = ingesta_datos()
    
    X_oleica = fase_oleica["C"] / (fase_oleica["A"] + fase_oleica["C"])
    N_oleica = fase_oleica["B"] / (fase_oleica["A"] + fase_oleica["C"])
    X_N = pd.DataFrame({"X": X_oleica, "N": N_oleica})

    Y_propano = fase_propano["C"] / (fase_propano["A"] + fase_propano["C"])
    N_propano = fase_propano["B"] / (fase_propano["A"] + fase_propano["C"])
    Y_N = pd.DataFrame({"Y": Y_propano, "N": N_propano})

    # A: aceite, B: propano, C: ac. oleico
    # F se actualiza en cada iteración
    # S es constante en todas las iteraciones
    if F is None or S_masa is None or solvente is None:
        F, S_masa, solvente = cargar_parametros("parametros_liq_liq.txt")
    
    # validación del solvente
    assert abs(solvente["A"] + solvente["B"] + solvente["C"] - 1) < 1e-3, "Composición del solvente no suma 1"

    S_ys = solvente["C"] / (solvente["A"] + solvente["C"])
    S_ns = solvente["B"] / (solvente["A"] + solvente["C"])
    S = {"masa": S_masa, "ys": S_ys, "ns": S_ns}
    
    M_acum = []
    R_acum = []
    E_acum = []
    E_masa = []
    y_acum = []
    for i in range(n):        
        Xm, Nm = calcular_M(F, S)
        s_ = calcular_s_prima(S)
        M =  {"masa": F["masa"] + s_, "xm": Xm, "nm": Nm}
        X, Nr, Y, Ne = aproximar(M, X_N, Y_N)
        masa_r_prima = M["masa"] * (Y - M["xm"]) / (Y - X)
        masa_e_prima = M["masa"] * (M["xm"] - X) / (Y - X)
        masa_e = masa_e_prima * (1 + Ne)
        y = Y / (1 + Ne)
        x = X / (1 + Nr)
        F = {"masa": masa_r_prima, "xf": X, "nf": Nr}  # R
        R = [X, Nr]
        E = [Y, Ne]
        M_acum.append([M["xm"], M["nm"]])
        R_acum.append(R)
        E_acum.append(E)
        E_masa.append(masa_e)
        y_acum.append(y)

    # diagramas
    graficar(X_N, Y_N, M_acum, R_acum, E_acum, n)
    
    E_compuesto = sum(E_masa)
    y_compuesto = (sum([e*y for e, y in zip(E_masa, y_acum)])) / E_compuesto
    return E_compuesto, y_compuesto
  
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--etapas", type=int, default=NUMERO_ETAPAS, help="Número de etapas")
    args = parser.parse_args()
    establecer_tkinter()
    E_compuesto, y_compuesto = liq_liq_n_etapas(args.etapas)
    
    # resultados en consola
    print(f"Cantidad de etapas: {args.etapas}")
    print(f"E compuesto: {E_compuesto}")
    print(f"y compuesto: {y_compuesto}")


if __name__ == "__main__":
    main()
