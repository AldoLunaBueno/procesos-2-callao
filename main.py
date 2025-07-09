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

def graficar(X_N, Y_N, M, R, E):
    # Graficar X vs N y Y vs N
    plt.subplot(2, 1, 1)
    plt.plot(X_N["X"], X_N["N"], "m.-", label="X vs Nr")
    plt.plot(Y_N["Y"], Y_N["N"], "b.-", label="Y vs Ne")
    plt.plot([R[0], E[0]], [R[1], E[1]], "go-")
    plt.plot(M[0], M[1], "ro")
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

def etapa(f, xf, nf, s, ys, ns):
    s_ = s / (1 + ns)
    xm = (f * xf + s_ * ys) / (f + s_)
    nm = (f * nf + s_ * ns) / (f + s_)
    
    return xm, nm

def aproximar(M, X_N, Y_N):
    xm, nm = M
    # interpolaciones lineales (por defecto)
    f_X_Nr = interp1d(X_N["X"], X_N["N"], fill_value="extrapolate")
    f_Y_Ne = interp1d(Y_N["Y"], Y_N["N"], fill_value="extrapolate")
    f_X_Y = interp1d(X_N["X"], Y_N["Y"], fill_value="extrapolate")
    f_X_Y_Ne = lambda x: f_Y_Ne(f_X_Y(x))  # función composición
    
    def f(x):
        cuerda = interp1d([x, f_X_Y(x)], [f_X_Nr(x), f_X_Y_Ne(x)], fill_value="extrapolate")
        nm_ = cuerda(xm)
        return nm_ - nm
    
    x_opt = bisect(f, 0.1, 0.9)
    return x_opt, f_X_Nr(x_opt), f_X_Y(x_opt), f_X_Y_Ne(x_opt)


def liq_liq_1_etapa():
    # datos experimentales
    fase_oleica, fase_propano = ingesta_datos()
    X_oleica = fase_oleica["C"] / (fase_oleica["A"] + fase_oleica["C"])
    N_oleica = fase_oleica["B"] / (fase_oleica["A"] + fase_oleica["C"])
    X_N = pd.DataFrame({"X": X_oleica, "N": N_oleica})

    Y_propano = fase_propano["C"] / (fase_propano["A"] + fase_propano["C"])
    N_propano = fase_propano["B"] / (fase_propano["A"] + fase_propano["C"])
    Y_N = pd.DataFrame({"Y": Y_propano, "N": N_propano})
    
    # datos del problema
    f = 100  # kilogramos
    xf = 0.5  # porcentaje
    nf = 0
    temp = 98.3  # grados centígrados
    
    solvente = {"propano": 0.98, "aceite": 0.018, "oleico": 0.002}
    s1 = 1500
    s2 = 1500
    
    ys1 = 0.1
    ns1 = 49
    
    xm1, nm1 = etapa(f, xf, nf, s1, ys1, ns1) # etapa 1
    M1 = [xm1, nm1]
    print(M1)
    x1, nr1, y1, ne1 = aproximar(M1, X_N, Y_N)
    R1 = [x1, nr1]
    E1 = [y1, ne1]
    graficar(X_N, Y_N, M1, R1, E1)
    
  
def main():
    establecer_tkinter()
    liq_liq_1_etapa()


if __name__ == "__main__":
    main()
