# seed_orders_and_sales.py

import random
import math
import requests
from datetime import datetime, timedelta

ORDER_URL           = "http://localhost:3000/api/nuevaorden"
COMPLETE_ORDER_URL  = "http://localhost:3000/api/completarorden"
SALE_URL            = "http://localhost:3000/api/vender"
HEALTHCHECK_URL     = "http://localhost:3000/api/ordenes"

TIMEOUT_ORDER       = None
TIMEOUT_COMPLETE    = None
TIMEOUT_SALE        = None
HEALTHCHECK_TIMEOUT = 5

PRODUCTOS = ["arrachera", "ribeye"]

def health_check():
    try:
        r = requests.get(HEALTHCHECK_URL, timeout=HEALTHCHECK_TIMEOUT)
        r.raise_for_status()
        print("Backend disponible.")
    except Exception:
        print(f"No puedo conectar con {HEALTHCHECK_URL}.")
        exit(1)

def clamp(value, min_value=10, max_value=300):
    return max(min_value, min(value, max_value))

def generate_sales(n_months=36, base=100, amplitude=100):
    ventas = []
    today = datetime.now()
    start = (today.replace(day=1) - timedelta(days=(n_months-1)*30)).replace(day=1)
    for i in range(n_months):
        fecha = (start + timedelta(days=30*i)).strftime("%Y-%m-%d")
        theta = 2 * math.pi * i / (n_months - 1)
        val = base + amplitude * math.cos(theta) + (amplitude / 2) * math.sin(theta)
        cantidad = clamp(round(val))
        ventas.append((fecha, cantidad))
    return ventas

def generate_orders_from_sales(sales):
    orders = []
    for fecha, qty in sales:
        producto = random.choice(PRODUCTOS)
        orders.append({
            "correo_solicita": "detallista@ejemplo.com",
            "correo_provee":   "proveedor@ejemplo.com",
            "fecha_emision":   fecha,
            "productos": [
                {
                    "producto":  producto,
                    "cantidad":  clamp(qty),
                    "precio":    8
                }
            ]
        })
    return orders

def main():
    health_check()

    # 1) Generar datos para 36 meses
    ventas = generate_sales()
    orders = generate_orders_from_sales(ventas)

    #  Este array guardará id, fecha, producto y cantidad
    created = []

    # 2) Crear órdenes
    print("\n=== Creando ordenes (36 meses) ===")
    for idx, orden in enumerate(orders, start=1):
        fecha_emision = orden["fecha_emision"]
        prod_info = orden["productos"][0]
        producto = prod_info["producto"]
        cantidad = prod_info["cantidad"]

        print(f"→ Orden #{idx}: producto={producto}, fecha_emision={fecha_emision}, qty={cantidad}")
        try:
            resp = requests.post(ORDER_URL, json=orden, timeout=TIMEOUT_ORDER)
            resp.raise_for_status()
            data = resp.json()
            oid = data.get("id_orden") or data.get("id")
            print(f"   ← Creada con ID {oid}")

            # Guardamos también producto y cantidad
            created.append({
                "id": oid,
                "fecha_emision": fecha_emision,
                "producto": producto,
                "cantidad": cantidad
            })

        except Exception as e:
            print(f"   ← ERROR creando orden: {e}")

    # 3) Completar órdenes
    print("\n=== Completando ordenes ===")
    for idx, rec in enumerate(created, start=1):
        oid = rec["id"]
        fe = datetime.strptime(rec["fecha_emision"], "%Y-%m-%d")
        delta = timedelta(days=random.randint(1, 7))
        fecha_recepcion = (fe + delta).strftime("%Y-%m-%d")

        print(f"→ Mes #{idx}: completando orden ID {oid} con fecha_recepcion={fecha_recepcion}")
        try:
            resp = requests.post(
                f"{COMPLETE_ORDER_URL}/{oid}",
                json={"fecha_recepcion": fecha_recepcion},
                timeout=TIMEOUT_COMPLETE
            )
            resp.raise_for_status()
            print(f"   ← Orden {oid} completada")
        except Exception as e:
            print(f"   ← ERROR completando orden {oid}: {e}")

    # 4) Registrar ventas usando el mismo producto y cantidad
    print("\n=== Registrando ventas ===")
    for idx, rec in enumerate(created, start=1):
        fecha = rec["fecha_emision"]
        producto = rec["producto"]
        cantidad = rec["cantidad"]

        payload = {
            "fecha_emision": fecha,
            "productos": [
                {"producto": producto, "cantidad": cantidad}
            ]
        }

        print(f"→ Venta #{idx}: producto={producto}, fecha_emision={fecha}, qty={cantidad}")
        try:
            resp = requests.post(SALE_URL, json=payload, timeout=TIMEOUT_SALE)
            resp.raise_for_status()
            print("   ← Venta registrada")
        except Exception as e:
            print(f"   ← ERROR registrando venta en {fecha}: {e}")

    print("\nProceso completado para 3 años (36 meses).")

if __name__ == "__main__":
    main()
