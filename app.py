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
 
        # 3. MARGEN SOBRE VENTAS (solo costos de lo vendido)
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
 
        # 4. EFICIENCIA OPERATIVA (comparativa margen ventas vs margen ganancia)
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
                'mensaje': _msg_proveedores(pct_pagar, por_pagar, ventas, por_cobrar),
            })
 
        score  = _score(indicadores)
        resumen = _resumen(indicadores)
 
        return {'success': True, 'indicadores': indicadores, 'score': score, 'resumen': resumen}
 
    except Exception as e:
        return {'success': False, 'error': str(e)}
 
 
def _fmt_dinero(v):
    if abs(v) >= 1000:
        return f"{'−' if v < 0 else ''}${abs(v):,.0f}"
    return f"{'−' if v < 0 else ''}${abs(v):.2f}"
 
 
def _msg_ganancia(g, ventas):
    if g > 0:
        pct = (g / ventas * 100) if ventas > 0 else 0
        if pct >= 20:
            return f"¡Tu negocio genera ${g:,.2f} de ganancia este mes, un {pct:.1f}% sobre tus ventas. Estás en una posición cómoda para reinvertir o ahorrar. Para seguir mejorando, considera si puedes reducir costos o escalar ventas sin aumentar gastos proporcionales."
        elif pct >= 10:
            return f"Tu negocio gana ${g:,.2f} este mes ({pct:.1f}% de tus ventas). Es un margen positivo, y hay espacio real para mejorar: revisa si tus gastos fijos o costos variables pueden optimizarse para ampliar este margen."
        else:
            return f"Ganas ${g:,.2f} este mes, pero el margen es ajustado ({pct:.1f}%). Cualquier mes complicado podría dejarte en cero. Analiza qué gastos podrías reducir o si tienes oportunidad de subir precios sin perder clientes."
    elif g == 0:
        return "Tu negocio empata exactamente: no ganas ni pierdes. Estás en el límite, cualquier gasto adicional o baja en ventas resultaría en pérdida. Vale la pena buscar una palanca de mejora, aunque sea pequeña."
    else:
        return f"Este mes tu negocio perdió ${abs(g):,.2f}. Tus costos y gastos superan lo que vendes. Revisa qué puedes recortar o cómo aumentar tus ventas. Es importante actuar pronto."
 
 
def _msg_margen(m):
    if m >= 25:
        return f"Por cada $100 que vendes, te quedan ${m:.1f} de ganancia neta. Es un margen sólido, tu negocio es eficiente y rentable. Aun así, siempre hay oportunidad: ¿podrías potenciar los productos o servicios de mayor margen?"
    elif m >= 15:
        return f"Te quedan ${m:.1f} de cada $100 vendidos. Es un margen aceptable, con potencial real por aprovechar. Negocia precios con proveedores o revisa si algunos gastos fijos pueden reducirse para ampliar esta cifra."
    elif m >= 5:
        return f"Solo ${m:.1f} de cada $100 vendidos llegan a tu bolsillo. El margen es estrecho y un imprevisto puede borrar toda la ganancia del mes. Enfócate en reducir costos o aumentar precios gradualmente."
    else:
        return f"Tu margen es crítico: ${m:.1f} por cada $100 vendidos. El negocio apenas cubre sus costos. Necesitas reducir costos y gastos de manera urgente o replantear tu modelo de precios."
 
 
def _msg_margen_bruto(mb):
    if mb >= 50:
        return f"Después de pagar lo que vendiste, te queda el {mb:.1f}% para cubrir gastos fijos y generar ganancia. ¡Excelente base de producto! Aprovecha este margen asegurándote de que tus gastos fijos estén bien controlados, ya que aquí es donde puedes seguir mejorando."
    elif mb >= 30:
        return f"Te queda el {mb:.1f}% de cada venta para cubrir tus gastos fijos y generar ganancia. Es un margen saludable. Aún puedes mejorar: analiza si tus proveedores principales ofrecen condiciones más favorables."
    elif mb >= 20:
        return f"Con el {mb:.1f}% que te queda de cada venta, cubres tus gastos con poco margen de error. Considera subir precios gradualmente o reducir el costo de lo que vendes para ganar más espacio."
    else:
        return f"Solo el {mb:.1f}% de tus ventas queda después de pagar lo que vendiste. Es muy poco para cubrir gastos fijos y generar ganancia. Revisa urgentemente tus precios de venta o el costo de tus productos."
 
 
def _msg_comparativa(mb, mg, brecha):
    if mb >= 40 and mg >= 15:
        return (
            f"Tu margen sobre ventas es {mb:.1f}% y tu margen de ganancia es {mg:.1f}%. "
            f"¡Ambos son saludables! Tus costos de producto son bajos y tus gastos fijos están bien controlados. "
            f"La brecha de {brecha:.1f}% representa el peso de tus gastos fijos. "
            f"Para seguir mejorando, evalúa si puedes crecer en ventas sin incrementar proporcionalmente esos gastos."
        )
    elif mb >= 40 and mg < 15:
        return (
            f"Tu margen sobre ventas es alto ({mb:.1f}%), lo que indica que tus costos de producto son eficientes. "
            f"Sin embargo, tu margen de ganancia es solo {mg:.1f}%, lo que señala que tus gastos fijos (arriendo, sueldos, servicios) "
            f"consumen la mayor parte de ese margen. La brecha de {brecha:.1f}% es el espacio que se llevan tus gastos fijos. "
            f"Revisa si alguno puede reducirse o renegociarse."
        )
    elif mb < 30 and mg < 15:
        return (
            f"Tu margen sobre ventas es {mb:.1f}% y tu margen de ganancia {mg:.1f}%. "
            f"Ambos márgenes son bajos, lo que indica presión tanto en el costo de tus productos como en tus gastos fijos. "
            f"Es una señal de alerta doble: considera subir precios, reducir costos de producto y optimizar gastos fijos al mismo tiempo."
        )
    elif mb >= 20 and mg >= 5:
        return (
            f"Tu margen sobre ventas ({mb:.1f}%) es razonable, pero tu margen de ganancia ({mg:.1f}%) todavía tiene espacio para crecer. "
            f"Los gastos fijos representan una brecha de {brecha:.1f}%. Trabaja en optimizarlos progresivamente para que más de ese margen bruto llegue a tu bolsillo."
        )
    else:
        return (
            f"Tu margen sobre ventas es {mb:.1f}% y tu margen de ganancia {mg:.1f}%. "
            f"La situación requiere atención en ambos frentes: tanto el costo de tus productos como tus gastos fijos están presionando la rentabilidad. "
            f"Identifica cuál de los dos tiene mayor potencial de mejora y empieza por ahí."
        )
 
 
def _msg_cobro(dias, por_cobrar, ventas, pct):
    if dias <= 10:
        return (
            f"Tus clientes te pagan en promedio en {dias:.1f} días. ¡Excelente velocidad de cobro! "
            f"Tienes ${por_cobrar:,.2f} pendientes, equivalente al {pct:.1f}% de tus ventas mensuales. "
            f"Mantener este ritmo te da liquidez constante. Considera si puedes ofrecer incentivos de pago anticipado para seguir mejorando."
        )
    elif dias <= 15:
        return (
            f"Cobras en promedio en {dias:.1f} días, lo que es saludable. "
            f"Tienes ${por_cobrar:,.2f} por cobrar ({pct:.1f}% de tus ventas). "
            f"Si lograras reducir 3 o 4 días este ciclo, mejorarías notablemente tu flujo de caja disponible."
        )
    elif dias <= 25:
        return (
            f"Tus clientes demoran en promedio {dias:.1f} días en pagarte. Es un plazo elevado. "
            f"Tienes ${por_cobrar:,.2f} pendientes ({pct:.1f}% de tus ventas mensuales). "
            f"Cada día extra que tardas en cobrar es dinero que no puedes usar. Implementa recordatorios de cobro o incentivos por pago anticipado."
        )
    else:
        return (
            f"Tus clientes tardan {dias:.1f} días en pagarte, lo que representa un riesgo de liquidez alto. "
            f"Tienes ${por_cobrar:,.2f} inmovilizados ({pct:.1f}% de tus ventas). "
            f"Con este ciclo de cobro largo, podrías tener dificultades para cubrir tus propios pagos a tiempo. "
            f"Revisa tus políticas de crédito y refuerza el seguimiento de cuentas vencidas."
        )
 
 
def _msg_proveedores(pct, por_pagar, ventas, por_cobrar):
    if pct <= 10:
        return (
            f"Debes a proveedores ${por_pagar:,.2f}, apenas el {pct:.1f}% de tus ventas mensuales. "
            f"¡Muy baja presión financiera de tu cadena de compras! Esto te da flexibilidad para negociar mejores condiciones o plazos más largos si lo necesitas."
        )
    elif pct <= 20:
        return (
            f"Tus cuentas por pagar a proveedores representan el {pct:.1f}% de tus ventas (${por_pagar:,.2f}). "
            f"Es una proporción manejable. Mantener un buen historial de pago te da poder de negociación para obtener mejores precios o plazos en el futuro."
        )
    elif pct <= 40:
        return (
            f"Debes a proveedores ${por_pagar:,.2f}, equivalente al {pct:.1f}% de tus ventas mensuales. "
            f"Es una proporción que merece seguimiento. Si tus clientes demoran en pagarte, podrías tener problemas para cumplir con proveedores. "
            f"Alinea tus plazos de cobro con los de pago para evitar tensiones de caja."
        )
    else:
        return (
            f"Tus cuentas por pagar representan el {pct:.1f}% de tus ventas mensuales (${por_pagar:,.2f}). "
            f"Es una carga alta: casi la mitad de lo que vendes ya está comprometido con proveedores. "
            f"Prioriza reducir este porcentaje negociando plazos más largos y acelerando el cobro a clientes."
        )
 
 
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
 
