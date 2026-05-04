from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

def calcular(data):
    try:
        ventas     = float(data.get('ventas', 0))
        costos     = float(data.get('costos', 0))
        gastos     = float(data.get('gastos', 0))
        caja       = float(data.get('caja', 0))
        por_cobrar = float(data.get('por_cobrar', 0))
        por_pagar  = float(data.get('por_pagar', 0))

        indicadores = []

        # 1. GANANCIA DEL MES
        ganancia = ventas - costos - gastos
        indicadores.append({
            'id': 'ganancia',
            'nombre': 'Ganancia del mes',
            'subtitulo': 'Lo que te queda después de pagar todo',
            'valor': round(ganancia, 2),
            'valor_fmt': _fmt_dinero(ganancia),
            'unidad': '$',
            'tipo': 'dinero',
            'icono': '💰',
            'estado': 'bueno' if ganancia > 0 else ('alerta' if ganancia == 0 else 'critico'),
            'mensaje': _msg_ganancia(ganancia, ventas),
        })

        # 2. MARGEN DE GANANCIA
        if ventas > 0:
            margen = ((ventas - costos - gastos) / ventas) * 100
            indicadores.append({
                'id': 'margen',
                'nombre': 'Margen de ganancia',
                'subtitulo': 'De cada $100 que vendes, cuánto te queda',
                'valor': round(margen, 1),
                'valor_fmt': f"{round(margen, 1)}%",
                'unidad': '%',
                'tipo': 'porcentaje',
                'icono': '📊',
                'estado': 'bueno' if margen >= 15 else ('alerta' if margen >= 5 else 'critico'),
                'mensaje': _msg_margen(margen),
            })

        # 3. MARGEN SOBRE VENTAS
        if ventas > 0:
            mb = ((ventas - costos) / ventas) * 100
            indicadores.append({
                'id': 'margen_bruto',
                'nombre': 'Margen sobre ventas',
                'subtitulo': 'Lo que queda después de pagar solo lo que vendiste (sin arriendo, sueldos ni gastos fijos)',
                'valor': round(mb, 1),
                'valor_fmt': f"{round(mb, 1)}%",
                'unidad': '%',
                'tipo': 'porcentaje',
                'icono': '🏷️',
                'estado': 'bueno' if mb >= 40 else ('alerta' if mb >= 20 else 'critico'),
                'mensaje': _msg_margen_bruto(mb),
            })

        # 4. EFICIENCIA OPERATIVA
        if ventas > 0:
            mb_val = ((ventas - costos) / ventas) * 100
            mg_val = ((ventas - costos - gastos) / ventas) * 100
            brecha = mb_val - mg_val
            if mb_val >= 40 and mg_val >= 15:
                estado_comp = 'bueno'
            elif mb_val >= 20 and mg_val >= 5:
                estado_comp = 'alerta'
            else:
                estado_comp = 'critico'
            indicadores.append({
                'id': 'comparativa',
                'nombre': 'Eficiencia operativa',
                'subtitulo': 'Comparativa entre margen sobre ventas y margen de ganancia',
                'valor': round(brecha, 1),
                'valor_fmt': f"{round(brecha, 1)}%",
                'unidad': '%',
                'tipo': 'porcentaje',
                'icono': '🔍',
                'estado': estado_comp,
                'mensaje': _msg_comparativa(mb_val, mg_val, brecha),
                'extra_mb': round(mb_val, 1),
                'extra_mg': round(mg_val, 1),
            })

        # 5. VELOCIDAD DE COBRO
        if ventas > 0:
            dias_cobro = (por_cobrar / ventas) * 30
            pct_cobrar = (por_cobrar / ventas) * 100
            indicadores.append({
                'id': 'cobro',
                'nombre': 'Velocidad de cobro',
                'subtitulo': 'Cuánto tiempo tarda en entrar el dinero de tus ventas',
                'valor': round(dias_cobro, 1),
                'valor_fmt': f"{round(dias_cobro, 1)} días",
                'unidad': 'días',
                'tipo': 'dias',
                'icono': '⏱️',
                'estado': 'bueno' if dias_cobro <= 15 else ('alerta' if dias_cobro <= 25 else 'critico'),
                'mensaje': _msg_cobro(dias_cobro, por_cobrar, ventas, pct_cobrar),
            })

        # 6. PRESIÓN DE PROVEEDORES
        if ventas > 0:
            pct_pagar = (por_pagar / ventas) * 100
            indicadores.append({
                'id': 'proveedores',
                'nombre': 'Presión de proveedores',
                'subtitulo': 'Qué parte de tus ingresos mensuales representan tus deudas con proveedores',
                'valor': round(pct_pagar, 1),
                'valor_fmt': f"{round(pct_pagar, 1)}%",
                'unidad': '%',
                'tipo': 'porcentaje',
                'icono': '📦',
                'estado': 'bueno' if pct_pagar <= 20 else ('alerta' if pct_pagar <= 40 else 'critico'),
                'mensaje': _msg_proveedores(pct_pagar, por_pagar, ventas),
            })

        score   = _score(indicadores)
        resumen = _resumen(indicadores)

        return {'success': True, 'indicadores': indicadores, 'score': score, 'resumen': resumen}

    except Exception as e:
        return {'success': False, 'error': str(e)}


def _fmt_dinero(v):
    if abs(v) >= 1000:
        return f"{'−' if v < 0 else ''}${abs(v):,.0f}"
    return f"{'−' if v < 0 else ''}${abs(v):.2f}"


def _msg_ganancia(g, ventas):
    pct = (g / ventas * 100) if ventas > 0 else 0
    if g > 0:
        if pct >= 20:
            return f"¡Sólido! Ganas ${g:,.2f} este mes ({pct:.1f}% de tus ventas). Reinvierte o ahorra parte para seguir creciendo."
        elif pct >= 10:
            return f"Ganas ${g:,.2f} este mes ({pct:.1f}%). Hay margen para mejorar: revisa si puedes reducir algún gasto fijo o costo variable."
        else:
            return f"Ganas ${g:,.2f}, pero el margen es ajustado ({pct:.1f}%). Un mes difícil podría dejarte en cero. Actúa antes de que eso pase."
    elif g == 0:
        return "No ganas ni pierdes. Estás en el límite: cualquier gasto extra o baja en ventas se convierte en pérdida."
    else:
        return f"Perdiste ${abs(g):,.2f} este mes. Tus costos superan tus ventas. Identifica qué recortar y actúa pronto."


def _msg_margen(m):
    if m >= 25:
        return f"¡De cada $100 vendidos te quedan ${m:.1f}! Margen sólido. Considera potenciar los productos o servicios más rentables para seguir subiendo."
    elif m >= 15:
        return f"Te quedan ${m:.1f} de cada $100 vendidos. Aceptable, pero mejorable. Negocia con proveedores o revisa tus gastos fijos."
    elif m >= 5:
        return f"Solo ${m:.1f} de cada $100 llegan a tu bolsillo. Margen muy estrecho: un imprevisto puede borrar toda la ganancia del mes."
    else:
        return f"Margen crítico: ${m:.1f} por cada $100. El negocio casi no cubre sus costos. Necesitas ajustar precios o reducir gastos urgentemente."


def _msg_margen_bruto(mb):
    if mb >= 50:
        return f"¡Excelente! El {mb:.1f}% de cada venta queda después de pagar lo que vendiste. Cuida que tus gastos fijos no consuman ese margen."
    elif mb >= 30:
        return f"Saludable: te queda el {mb:.1f}% para cubrir gastos y generar ganancia. Aún puedes mejorar negociando mejores precios con proveedores."
    elif mb >= 20:
        return f"El {mb:.1f}% que te queda deja poco margen de error. Considera subir precios o reducir el costo de lo que vendes."
    else:
        return f"Solo el {mb:.1f}% queda después de cubrir lo que vendiste. Muy poco para pagar gastos fijos y ganar. Revisa precios o costos urgentemente."


def _msg_comparativa(mb, mg, brecha):
    if mb >= 40 and mg >= 15:
        return f"¡Tus números cuadran bien! Costos de producto bajos ({mb:.1f}%) y gastos fijos controlados. La brecha de {brecha:.1f}% es el peso de tus gastos fijos: intenta crecer en ventas sin subirlos proporcionalmente."
    elif mb >= 40 and mg < 15:
        return f"Tus costos de producto son eficientes ({mb:.1f}%), pero tus gastos fijos se comen el margen: solo te queda {mg:.1f}% de ganancia. Revisa arriendo, sueldos y servicios, hay espacio para negociar."
    elif mb < 30 and mg < 15:
        return f"Alerta doble: el margen sobre ventas ({mb:.1f}%) y el de ganancia ({mg:.1f}%) son bajos. Hay presión tanto en costos de producto como en gastos fijos. Ataca los dos frentes."
    elif mb >= 20 and mg >= 5:
        return f"Margen sobre ventas razonable ({mb:.1f}%), pero la ganancia final ({mg:.1f}%) aún tiene espacio para crecer. Reduce gastos fijos progresivamente para que más dinero llegue a tu bolsillo."
    else:
        return f"Margen sobre ventas de {mb:.1f}% y ganancia de {mg:.1f}%: ambos necesitan mejora. Identifica cuál frente (costos o gastos fijos) tiene más potencial de mejora y empieza por ahí."


def _msg_cobro(dias, por_cobrar, ventas, pct):
    if dias <= 10:
        return f"¡Cobras en {dias:.1f} días, excelente! Tienes ${por_cobrar:,.2f} pendientes ({pct:.1f}% de tus ventas). Considera descuentos por pago anticipado para mantener este ritmo."
    elif dias <= 15:
        return f"Cobras en {dias:.1f} días, saludable. Tienes ${por_cobrar:,.2f} por entrar. Reducir 3 o 4 días este ciclo mejoraría notablemente tu flujo de caja."
    elif dias <= 25:
        return f"Tus clientes tardan {dias:.1f} días en pagarte. Tienes ${por_cobrar:,.2f} inmovilizados ({pct:.1f}% de tus ventas). Implementa recordatorios o incentivos por pago anticipado."
    else:
        return f"Ciclo de cobro de {dias:.1f} días: riesgo alto. Tienes ${por_cobrar:,.2f} sin ingresar ({pct:.1f}% de tus ventas). Refuerza el seguimiento de cuentas y revisa tu política de crédito."


def _msg_proveedores(pct, por_pagar, ventas):
    if pct <= 10:
        return f"¡Muy baja presión! Debes a proveedores solo el {pct:.1f}% de tus ventas (${por_pagar:,.2f}). Tienes margen para negociar mejores condiciones si lo necesitas."
    elif pct <= 20:
        return f"Deuda con proveedores manejable: {pct:.1f}% de tus ventas (${por_pagar:,.2f}). Un buen historial de pago te da poder para negociar mejores precios o plazos."
    elif pct <= 40:
        return f"Debes a proveedores el {pct:.1f}% de tus ventas (${por_pagar:,.2f}). Si los clientes se demoran en pagarte, podrías tener problemas. Alinea cobros y pagos."
    else:
        return f"El {pct:.1f}% de tus ventas ya está comprometido con proveedores (${por_pagar:,.2f}). Carga alta: negocia plazos más largos y acelera el cobro a clientes."


def _score(inds):
    mapa = {'bueno': 10, 'alerta': 5, 'critico': 0}
    if not inds:
        return 0
    total = sum(mapa.get(i['estado'], 5) for i in inds)
    return round((total / (len(inds) * 10)) * 100)


def _resumen(inds):
    buenos   = [i for i in inds if i['estado'] == 'bueno']
    alertas  = [i for i in inds if i['estado'] == 'alerta']
    criticos = [i for i in inds if i['estado'] == 'critico']
    return {
        'buenos':   [i['nombre'] for i in buenos],
        'alertas':  [i['nombre'] for i in alertas],
        'criticos': [i['nombre'] for i in criticos],
    }


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analizar', methods=['POST'])
def analizar():
    data = request.get_json()
    return jsonify(calcular(data))

if __name__ == '__main__':
    app.run()
