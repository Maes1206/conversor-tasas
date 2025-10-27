#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Conversor de Tasas - Efectivas y Nominales (versión mejorada e interactiva)
---------------------------------------------------------------------------
Convierte entre tasas efectivas (E*) y nominales (N*) de distintos períodos.

Novedades:
- Permite ingresar datos por teclado si no se usan argumentos.
- Muestra mensajes de error claros y repite la solicitud si hay error.
- Soporta códigos:
    A = Anual
    S = Semestral
    T = Trimestral
    Q = Quincenal
    M = Mensual
    SM = Semanal
    D = Diario
Autor: ElviejoMaes
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dataclasses import dataclass
from typing import Dict, Tuple
import argparse

# Frecuencias por año actualizadas
PERIODOS: Dict[str, int] = {
    "A": 1,     # Anual
    "S": 2,     # Semestral
    "T": 4,     # Trimestral
    "B": 6,     #Bimestral
    "Q": 24,    # Quincenal
    "M": 12,    # Mensual
    "SM": 52,   # Semanal
    "D": 365,   # Diario
}

# Tipos y Periodos Validos
VALIDOS = {
    # Tasas efectivas
    "EA": ("E", "A"), "ES": ("E", "S"), "ET": ("E", "T"), "EQ": ("E", "Q"),
    "EB": ("E", "B"),
    "EM": ("E", "M"), "ESM": ("E", "SM"), "ED": ("E", "D"),
    # Tasas nominales
    "NA": ("N", "A"), "NS": ("N", "S"), "NT": ("N", "T"), "NQ": ("N", "Q"),
    "NM": ("N", "M"), "NSM": ("N", "SM"), "ND": ("N", "D"), "NB": ("N","B"),
}


@dataclass
class Tasa:
    """Representa una tasa con tipo (Efectiva o Nominal) y periodo."""
    valor: float
    tipo: str   # 'E' o 'N'
    periodo: str  # 'A','S','T','Q','M','SM','D'

# --------------------------------------------------------------
# FUNCIONES PRINCIPALES
# --------------------------------------------------------------

def parse_codigo(codigo: str) -> Tuple[str, str]:
    """Valida y separa el código de tasa en tipo y periodo."""
    c = codigo.strip().upper()
    if c.lower() == "esm": c = "ESM"
    if c.lower() == "nsm": c = "NSM"
    if c not in VALIDOS:
        raise ValueError(
            f"Código no reconocido: '{codigo}'. "
            f"Usa uno de: {', '.join(sorted(VALIDOS.keys()))}"
        )
    return VALIDOS[c]

def parse_tasa(s: str) -> float:
    """Acepta '0.24' o '24%' y devuelve decimal (0.24)."""
    s = s.strip().replace(",", ".")
    try:
        if s.endswith("%"):
            return float(s[:-1]) / 100
        return float(s)
    except ValueError:
        raise ValueError(f"Formato inválido de tasa: '{s}.' Usa por ejemplo 24% o 0.24.")

def a_porcentaje(x: float) -> str:
    """Convierte decimal a porcentaje con 6 decimales."""
    return f"{x * 100:.6f}%"

def a_EA(t: Tasa) -> float:
    """Convierte cualquier tasa a efectiva anual (EA)."""
    m = PERIODOS[t.periodo]
    if t.tipo == "E":
        return (1 + t.valor) ** m - 1
    else:
        return (1 + t.valor / m) ** m - 1

def desde_EA(EA: float, tipo: str, periodo: str) -> float:
    """Convierte una EA a otra tasa efectiva o nominal."""
    m = PERIODOS[periodo]
    if tipo == "E":
        return (1 + EA) ** (1 / m) - 1
    else:
        return m * ((1 + EA) ** (1 / m) - 1)

def convertir(valor: float, de: str, a: str) -> float:
    """Función central de conversión entre tasas."""
    tipo_origen, per_origen = parse_codigo(de)
    tipo_dest, per_dest = parse_codigo(a)
    tasa_origen = Tasa(valor=valor, tipo=tipo_origen, periodo=per_origen)
    EA = a_EA(tasa_origen)
    return desde_EA(EA, tipo_dest, per_dest)

# --------------------------------------------------------------
# MODO INTERACTIVO
# --------------------------------------------------------------

def entrada_interactiva():
    print("\n CONVERSOR DE TASAS EFECTIVAS Y NOMINALES")
    print("------------------------------------------------")
    print("Códigos disponibles:")
    print("EA, ES, ET, EQ, EM, ESM, ED, NA, NS, NT, NQ, NM, NSM, ND\n")

    while True:
        try:
            tasa = input("Ingrese la tasa (ej: 24% o 0.24): ").strip()
            valor = parse_tasa(tasa)

            de = input("Ingrese el código de la tasa de origen (ej: NM): ").strip().upper()
            a = input("Ingrese el código de la tasa destino (ej: EA): ").strip().upper()

            resultado = convertir(valor, de, a)
            print(f"\nResultado: {a_porcentaje(resultado)}  ({de} → {a})\n")


            seguir = input("¿Desea realizar otra conversión? (si/no): ").strip().lower()
            if seguir != "si":
                print(" ¡Gracias por usar el conversor!")
                break

        except ValueError as e:
            print(f"\n Error: {e}\nPor favor, inténtelo de nuevo.\n")

# --------------------------------------------------------------
# FUNCIÓN PRINCIPAL
# --------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Convierte entre tasas efectivas y nominales.")
    parser.add_argument("--tasa", help="Ej: 0.24 o 24%")
    parser.add_argument("--de", help="Ej: NM, EM, EA, NT, NQ, etc.")
    parser.add_argument("--a", help="Código destino.")
    parser.add_argument("--porcentaje", action="store_true", help="Mostrar resultado en %")
    args = parser.parse_args()

    # Si no se pasan argumentos → modo interactivo
    if not args.tasa or not args.de or not args.a:
        entrada_interactiva()
        return

    try:
        valor = parse_tasa(args.tasa)
        resultado = convertir(valor, args.de, args.a)
        if args.porcentaje:
          print(f"Resultado: {a_porcentaje(resultado)}  ({args.de} → {args.a})")
        else:
          print(f"Resultado: {resultado:.10f}  ({args.de} → {args.a})")

    except ValueError as e:
        print(f" Error: {e}")

if __name__ == "__main__":
    main()
class Solicitud(BaseModel):
    tasa: str
    de: str
    a: str

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def home():
    return FileResponse("static/index.html")

@app.post("/convertir")
def api_convertir(data: Solicitud):
    valor = parse_tasa(data.tasa)
    resultado = convertir(valor, data.de, data.a)

    return {"resultado": f"{resultado * 100:.6f}%"}
