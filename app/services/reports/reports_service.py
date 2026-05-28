import base64
from datetime import date
import io

from jinja2 import Environment, FileSystemLoader
from sqlalchemy.orm import Session
import matplotlib

from app.models.dimensions.dim_date import DimDate
from app.models.dimensions.operation_type import OperationType
from app.models.fact.fact_operation import FactOperation
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from scipy.interpolate import make_interp_spline
import os

from weasyprint import HTML

from app.services.datasets.calculate_metrics import calculate_metrics_by_period, get_product_evolution, get_products_record


TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")

def generar_reporte_pdf(
        db: Session,
        empresa: str,
        usuario: str,
        company_id: int,
        fecha_inicio: date,
        fecha_fin: date
) -> bytes:
    
    # Obtener datos 
    datos = calculate_metrics_by_period(db, company_id, fecha_inicio, fecha_fin)

    kpis = datos["kpis"]
    insights = datos["insights"]
    productos = datos["productos"][:10] 
    chart_data = datos["chart"]["data"]

    # Insights automáticos
    insights_texto = _generar_insights(kpis, insights, chart_data)

    # Generar gráficos
    grafico_ventas = _grafico_area_ventas(chart_data) if chart_data else None
    grafico_egresos = _grafico_torta_egresos(kpis)

    # Renderizar plantilla
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    template = env.get_template("reporte_base.html")

    def _limpiar_nombre(valor):
        if not valor:
            return None
        if str(valor).strip().lower() in ("sin nombre", "none", ""):
            return None
        return valor

    html_renderizado = template.render(
        empresa=empresa,
        usuario=usuario,
        fecha_inicio=fecha_inicio.strftime("%d/%m/%Y"),
        fecha_fin=fecha_fin.strftime("%d/%m/%Y"),
        kpis=kpis,
        insights_texto=insights_texto,
        top_producto=insights.get("top_producto"),
        top_proveedor=insights.get("top_proveedor"),
        top_gasto=insights.get("top_gasto"),
        productos=productos,
        chart_data=chart_data,
        grafico_ventas=grafico_ventas,
        grafico_egresos=grafico_egresos
    )

    return HTML(string=html_renderizado, base_url=TEMPLATES_DIR).write_pdf()

def _generar_insights(kpis: dict, insights: dict, chart_data: list) -> list:
    textos = []

    #Margen 

    margen = kpis.get("margen_ganancia_pct")
    if margen is not None:
        if margen >= 20:
            textos.append({
                "texto": f"El margen operativo del {margen}% refleja una operación saludable.",
                "tipo": "positivo"
            })
        elif margen >=10: 
            textos.append({
                "texto": f"El margen operativo del {margen}% es moderado. Se recomienda revisar costos.",
                "tipo": "neutral"
            })
        elif margen >=0: 
            textos.append({
                "texto": f"El margen operativo del {margen}% es bajo. Revisa la estructura de compras y gastos.",
                "tipo": "negativo"
            })

        else: textos.append({
            "texto": "El margen operativo presenta valores negativos. La empresa se encuentra en estado de crítico.",
            "tipo": "negativo"
        })

    
    # utilidad operativa
    utilidad = kpis.get("utilidad_operativa")
    ventas = kpis.get("total_ventas")
    if utilidad is not None and ventas:
        if utilidad < 0: 
            textos.append({
                "texto": "La utilidad operativa es negativa: los egresos superaron los ingresos de ventas en este período.",
                "tipo": "negativo"
            })

        else: 
            textos.append({
                "texto": f"La utilidad operativa fue de ${utilidad:,.0f}, lo cual indica que el negocio generó utilidades operativas",
                "tipo": "positivo"
            })

     # Ticket promedio
    ticket = kpis.get("ticket_promedio")
    if ticket:
        textos.append({
            "texto":f"El ticket promedio de venta fue de ${ticket:,.0f}.",
            "tipo": "neutral"
        })

    # Top producto
    top_p = insights.get("top_producto")
    if top_p and top_p.strip().lower() not in ("sin nombre", "", "none"):
        textos.append({
            "texto": f"El producto más vendido fue '{top_p}', liderando en volumen de unidades.",
            "tipo": "positivo"
        })

    # Tendencia: comparar primer y último punto del chart
    if len(chart_data) >= 2:
        primera = chart_data[0].get("ventas", 0)
        ultima = chart_data[-1].get("ventas", 0)
        if primera and ultima:
            if ultima > primera:
                textos.append({
                    "texto": "Las ventas mostraron una tendencia creciente durante el período.",
                    "tipo": "positivo"
                })
            
            elif ultima < primera:
                textos.append({
                    "texto":"Las ventas mostraron una tendencia decreciente durante el período.",
                    "tipo": "negativo"
                })
            
            else:
                textos.append({
                    "texto": "Las ventas se mantuvieron estables durante el período.",
                    "tipo": "neutral"
                })

    return textos

def generar_reporte_productos(
        db: Session, 
        empresa: str,
        usuario: str,
        company_id: int,
        fecha_inicio: date,
        fecha_fin: date
) -> bytes: 
    
    productos = calculate_metrics_by_period(db, company_id, fecha_inicio, fecha_fin)

    productos = productos["productos"]

    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    template = env.get_template("reporte_productos.html")

    html_renderizado = template.render(
        empresa=empresa,
        usuario=usuario,
        fecha_inicio=fecha_inicio.strftime("%d/%m/%Y"),
        fecha_fin=fecha_fin.strftime("%d/%m/%Y"),
        productos=productos
    )

    return HTML(string=html_renderizado, base_url=TEMPLATES_DIR).write_pdf()

def _grafico_area_ventas(chart_data: list) -> str:

    periodos = [d["period"] for d in chart_data]
    ventas = [d.get("ventas", 0) for d in chart_data]

    fig, ax = plt.subplots(figsize=(7, 3.2))
    ax.fill_between(range(len(periodos)), ventas, alpha=0.3, color="#1e40af")
    ax.plot(range(len(periodos)), ventas, color="#1e40af", linewidth=2)

    step = max(1, len(periodos) // 8)
    ax.set_xticks(range(0, len(periodos), step))
    ax.set_xticklabels(
        [periodos[i] for i in range(0, len(periodos), step)],
        rotation=30, ha='right', fontsize=7
    )

    ax.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, _: f"${x:,.0f}")
    )
    ax.tick_params(axis='y', labelsize=7)
    ax.set_title("Tendencia de ventas", fontsize=12, fontweight='bold', color="#1e293b", pad=8)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', linestyle='--', alpha=0.4)

    plt.tight_layout()
    return _fig_to_base64(fig)


def _grafico_torta_egresos(kpis: dict) -> str | None:
    """Genera gráfico de torta de egresos y retorna base64."""
    labels, valores, colores = [], [], []

    if kpis.get("total_compras"):
        labels.append("Compras")
        valores.append(kpis["total_compras"])
        colores.append("#dc2626")

    if kpis.get("total_costos"):
        labels.append("Gastos")
        valores.append(kpis["total_costos"])
        colores.append("#f97316")

    if not valores:
        return None

    fig, ax = plt.subplots(figsize=(4, 2.8))
    wedges, texts, autotexts = ax.pie(
        valores,
        labels=None,
        autopct="%1.1f%%",
        colors=colores,
        startangle=90,
        pctdistance=0.75,
        wedgeprops={"edgecolor": "white", "linewidth": 1.5}
    )
    for t in autotexts:
        t.set_fontsize(8)
        t.set_color("white")
        t.set_fontweight("bold")

    ax.legend(
        wedges, [f"{l}: ${v:,.0f}" for l, v in zip(labels, valores)],
        loc="lower center",
        bbox_to_anchor=(0.5, -0.15),
        fontsize=7,
        frameon=False,
        ncol=2
    )
    ax.set_title("Distribución de Egresos", fontsize=10, fontweight='semibold', color="#1e293b", pad=8)

    plt.tight_layout()
    return _fig_to_base64(fig)


def _fig_to_base64(fig) -> str:
    """Convierte figura matplotlib a string base64."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def generar_reporte_producto_pdf(
    db: Session,
    empresa: str,
    usuario: str,
    company_id: int,
    product_id: int,
    nombre_producto: str,
    fecha_inicio: date,
    fecha_fin: date
) -> bytes:

    # 1. Obtener evolución del producto
    evolucion = get_product_evolution(db, company_id, product_id, fecha_inicio, fecha_fin)
    chart_data = evolucion["data"]

    # 2. Calcular KPIs del producto
    total_ventas = sum(d.get("ventas", 0) for d in chart_data)
    total_compras = sum(d.get("compras", 0) for d in chart_data)
    total_utilidad = sum(d.get("utilidad", 0) for d in chart_data)
    margen = round((total_utilidad / total_ventas * 100), 2) if total_ventas > 0 else 0

    # 3. Generar gráfico
    grafico = _grafico_evolucion_producto(chart_data, nombre_producto) if chart_data else None

    # 4. Obtener registros raw
    registros = db.query(
        DimDate.full_date.label("fecha"),
        FactOperation.operation_type.label("tipo"),
        FactOperation.concept.label("concepto"),
        FactOperation.quantity.label("cantidad"),
        FactOperation.unit_price.label("precio_unitario"),
        FactOperation.total_amount.label("valor_total"),
    ).join(
        DimDate, FactOperation.dim_date_id == DimDate.id
    ).filter(
        FactOperation.company_id == company_id,
        FactOperation.dim_product_id == product_id,
        DimDate.full_date >= fecha_inicio,
        DimDate.full_date <= fecha_fin,
    ).order_by(DimDate.full_date.desc()).all()

    registros_data = [
        {
            "fecha": r.fecha.strftime("%d/%m/%Y"),
            "tipo": "Venta" if r.tipo == OperationType.sale else "Compra",
            "concepto": r.concepto or "—",
            "cantidad": r.cantidad or 0,
            "precio_unitario": r.precio_unitario or 0,
            "valor_total": r.valor_total or 0,
        }
        for r in registros
    ]

    # 5. Renderizar plantilla
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    template = env.get_template("reporte_evolucion_producto.html")

    html_renderizado = template.render(
        empresa=empresa,
        usuario=usuario,
        nombre_producto=nombre_producto,
        fecha_inicio=fecha_inicio.strftime("%d/%m/%Y"),
        fecha_fin=fecha_fin.strftime("%d/%m/%Y"),
        total_ventas=total_ventas,
        total_compras=total_compras,
        total_utilidad=total_utilidad,
        margen=margen,
        grafico=grafico,
        registros=registros_data,
    )

    return HTML(string=html_renderizado, base_url=TEMPLATES_DIR).write_pdf()


def _grafico_evolucion_producto(chart_data: list, nombre_producto: str) -> str:
    periodos = [d["period"] for d in chart_data]
    ventas = [d.get("ventas", 0) for d in chart_data]
    utilidad = [d.get("utilidad", 0) for d in chart_data]
    compras = [d.get("compras", 0) for d in chart_data]

    x = np.arange(len(periodos))

    fig, ax = plt.subplots(figsize=(7, 2.8))

    # Suavizar solo si hay suficientes puntos
    if len(x) >= 4:
        x_smooth = np.linspace(x.min(), x.max(), 300)
        ventas_smooth   = make_interp_spline(x, ventas, k=3)(x_smooth)
        utilidad_smooth = make_interp_spline(x, utilidad, k=3)(x_smooth)
        compras_smooth  = make_interp_spline(x, compras, k=3)(x_smooth)
    else:
        x_smooth = x
        ventas_smooth, utilidad_smooth, compras_smooth = ventas, utilidad, compras

    ax.fill_between(x_smooth, compras_smooth, alpha=0.2, color="#dc2626")
    ax.plot(x_smooth, compras_smooth, color="#dc2626", linewidth=2, label="Compras")

    ax.fill_between(x_smooth, ventas_smooth, alpha=0.2, color="#1e40af")
    ax.plot(x_smooth, ventas_smooth, color="#1e40af", linewidth=2, label="Ventas")

    ax.fill_between(x_smooth, utilidad_smooth, alpha=0.2, color="#16a34a")
    ax.plot(x_smooth, utilidad_smooth, color="#16a34a", linewidth=2, label="Utilidad")


    # Eje X con etiquetas originales
    step = max(1, len(periodos) // 8)
    ax.set_xticks(np.linspace(0, len(periodos) - 1, min(8, len(periodos))))
    ax.set_xticklabels(
        [periodos[int(i)] for i in np.linspace(0, len(periodos) - 1, min(8, len(periodos)))],
        rotation=30, ha='right', fontsize=7
    )

    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    ax.tick_params(axis='y', labelsize=7)
    ax.set_title(f"Evolución — {nombre_producto}", fontsize=9, color="#1e293b", pad=8)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', linestyle='--', alpha=0.4)
    ax.legend(fontsize=7, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.25), ncol=3)

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.25)
    return _fig_to_base64(fig)