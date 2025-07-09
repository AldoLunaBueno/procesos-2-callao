import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from scipy.interpolate import interp1d
from scipy.optimize import bisect

import os
import sys

def establecer_tkinter():
    os.environ["TCL_LIBRARY"] = os.path.join(sys.base_prefix, "tcl", "tcl8.6")
    os.environ["TK_LIBRARY"] = os.path.join(sys.base_prefix, "tcl", "tk8.6")

def ingesta_datos():
    fase_oleica = pd.read_table("fase_oleica.txt", decimal=",")
    fase_propano = pd.read_table("fase_propano.txt", decimal=",")
    
    return fase_oleica, fase_propano

def graficar(X_N, Y_N, M_acum, R_acum, E_acum, n):
    # Graficar X vs N y Y vs N
    plt.subplot(2, 1, 1)
    plt.plot(X_N["X"], X_N["N"], "m.-", label="X vs Nr")
    plt.plot(Y_N["Y"], Y_N["N"], "b.-", label="Y vs Ne")
    for i in range(n):
        plt.plot([R_acum[i][0], E_acum[i][0]], [R_acum[i][1], E_acum[i][1]], "go-")
        plt.plot(M_acum[i][0], M_acum[i][1], "ro")
    plt.xlabel("Fracción molar")
    plt.ylabel("N")
    plt.legend()

    # Graficar X vs Y
    plt.subplot(2, 1, 2)
    plt.plot(X_N["X"], Y_N["Y"], "c.-", label="X vs Y")
    plt.xlabel("X")
    plt.ylabel("Y")
    plt.plot([0, 1], [0, 1], "k:")
    plt.legend()
    
    # Mostrar y guardar el diagrama
    plt.tight_layout()
    os.makedirs("diagramas", exist_ok=True)
    plt.savefig("diagramas/fig-1.png") 
    plt.show()
    
def calcular_s_prima(S):
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
        cuerda = interp1d([x, f_X_Y(x)], [f_X_Nr(x), f_X_Y_Ne(x)], fill_value="extrapolate")
        nm_ = cuerda(M["xm"])
        return nm_ - M["nm"]
    
    x_opt = bisect(f, 0.1, 0.9)
    return x_opt, f_X_Nr(x_opt), f_X_Y(x_opt), f_X_Y_Ne(x_opt)


def liq_liq_n_etapas(n: int):
    # datos experimentales
    fase_oleica, fase_propano = ingesta_datos()
    X_oleica = fase_oleica["C"] / (fase_oleica["A"] + fase_oleica["C"])
    N_oleica = fase_oleica["B"] / (fase_oleica["A"] + fase_oleica["C"])
    X_N = pd.DataFrame({"X": X_oleica, "N": N_oleica})

    Y_propano = fase_propano["C"] / (fase_propano["A"] + fase_propano["C"])
    N_propano = fase_propano["B"] / (fase_propano["A"] + fase_propano["C"])
    Y_N = pd.DataFrame({"Y": Y_propano, "N": N_propano})
    
    # datos del problema
    temp = 98.3  # grados centígrados
    F = {"masa": 100, "xf": 0.5, "nf": 0}
    S = {"masa": 1500, "ys": 0.1, "ns": 49}
    # A: aceite, B: propano, C: ac. oleico
    solvente = {"A": 0.018, "B": 0.98, "C": 0.002}
    M_acum = []
    R_acum = []
    E_acum = []
    for i in range(n):        
        Xm, Nm = calcular_M(F, S)
        s_ = calcular_s_prima(S)
        M =  {"masa": F["masa"] + s_, "xm": Xm, "nm": Nm}
        X, Nr, Y, Ne = aproximar(M, X_N, Y_N)
        masa_r_prima = M["masa"] * (Y - M["xm"]) / (Y - X)
        masa_e_prima = M["masa"] * (M["xm"] - X) / (Y - X)
        masa_e = masa_e_prima * (1 + Ne)
        # y = Y / (1 + Ne)
        # x = X / (1 + Nr)
        F = {"masa": masa_r_prima, "xf": X, "nf": Nr}  # R
        R = [X, Nr]
        E = [Y, Ne]
        M_acum.append([M["xm"], M["nm"]])
        R_acum.append(R)
        E_acum.append(E)

    graficar(X_N, Y_N, M_acum, R_acum, E_acum, n)
    
  
def main():
    establecer_tkinter()
    liq_liq_n_etapas(2)


if __name__ == "__main__":
    main()
