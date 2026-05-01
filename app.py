from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# ─────────────────────────────────────────────
#  ENTRADAS (todas mensuales, lenguaje simple)
#  ventas         → ingresos del mes
#  costos         → costo de lo que vende
#  gastos         → gastos fijos del mes
#  caja           → dinero en caja/banco ahora
#  por_cobrar     → lo que le deben clientes
#  por_pagar      → lo que debe a proveedores
# ─────────────────────────────────────────────

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

        # 3. MARGEN BRUTO (cuánto queda antes de gastos fijos)
        if ventas > 0:
            mb = ((ventas - costos) / ventas) * 100
            indicadores.append({
                'id': 'margen_bruto',
                'nombre': 'Margen sobre ventas',
                'subtitulo': 'Lo que te queda después de pagar lo que vendiste',
                'valor': round(mb, 1),
                'valor_fmt': f"{round(mb, 1)}%",
                'unidad': '%',
                'tipo': 'porcentaje',
                'icono': '🏷️',
                'estado': 'bueno' if mb >= 40 else ('alerta' if mb >= 20 else 'critico'),
                'mensaje': _msg_margen_bruto(mb),
            })

        # 4. COBERTURA DE GASTOS (¿cuántos meses de gastos tienes en caja?)
        gastos_totales = costos + gastos
        if gastos_totales > 0:
            cobertura = caja / gastos_totales
            indicadores.append({
                'id': 'cobertura',
                'nombre': 'Reserva de emergencia',
                'subtitulo': 'Cuántos meses puede sobrevivir tu negocio sin vender',
                'valor': round(cobertura, 1),
                'valor_fmt': f"{round(cobertura, 1)} meses",
                'unidad': 'meses',
                'tipo': 'meses',
                'icono': '🛡️',
                'estado': 'bueno' if cobertura >= 2 else ('alerta' if cobertura >= 1 else 'critico'),
                'mensaje': _msg_cobertura(cobertura),
            })

        # 5. BALANCE CLIENTES vs PROVEEDORES
        balance = por_cobrar - por_pagar
        indicadores.append({
            'id': 'balance_cp',
            'nombre': 'Balance de créditos',
            'subtitulo': 'Diferencia entre lo que te deben y lo que debes',
            'valor': round(balance, 2),
            'valor_fmt': _fmt_dinero(balance),
            'unidad': '$',
            'tipo': 'dinero',
            'icono': '⚖️',
            'estado': 'bueno' if balance >= 0 else ('alerta' if balance >= -(ventas * 0.3) else 'critico'),
            'mensaje': _msg_balance(balance, por_cobrar, por_pagar),
        })

        # 6. PUNTO DE EQUILIBRIO (¿cuánto necesitas vender para no perder?)
        if ventas > 0 and (ventas - costos) > 0:
            mb_ratio = (ventas - costos) / ventas
            if mb_ratio > 0:
                pe = gastos / mb_ratio
                pct_alcanzado = (ventas / pe * 100) if pe > 0 else 100
                indicadores.append({
                    'id': 'equilibrio',
                    'nombre': 'Punto de equilibrio',
                    'subtitulo': 'Cuánto debes vender para cubrir todos tus costos',
                    'valor': round(pe, 2),
                    'valor_fmt': _fmt_dinero(pe),
                    'unidad': '$',
                    'tipo': 'dinero',
                    'icono': '🎯',
                    'estado': 'bueno' if ventas >= pe else ('alerta' if ventas >= pe * 0.8 else 'critico'),
                    'mensaje': _msg_equilibrio(ventas, pe, pct_alcanzado),
                    'extra': round(pct_alcanzado, 0),
                })

        score = _score(indicadores)
        resumen = _resumen(indicadores, ganancia if ventas > 0 else 0)

        return {'success': True, 'indicadores': indicadores, 'score': score, 'resumen': resumen}

    except Exception as e:
        return {'success': False, 'error': str(e)}


# ── Formatos ──────────────────────────────────
def _fmt_dinero(v):
    if abs(v) >= 1000:
        return f"{'−' if v < 0 else ''}${abs(v):,.0f}"
    return f"{'−' if v < 0 else ''}${abs(v):.2f}"


# ── Mensajes personalizados ───────────────────
def _msg_ganancia(g, ventas):
    if g > 0:
        pct = (g / ventas * 100) if ventas > 0 else 0
        if pct >= 20:
            return f"¡Muy bien! Tu negocio genera ${g:,.2f} de ganancia este mes — un {pct:.1f}% sobre tus ventas. Estás en una posición cómoda para reinvertir o ahorrar."
        elif pct >= 10:
            return f"Tu negocio gana ${g:,.2f} este mes ({pct:.1f}% de tus ventas). Es un margen positivo, pero hay espacio para mejorar revisando si tus gastos fijos o costos pueden reducirse."
        else:
            return f"Ganas ${g:,.2f} este mes, pero el margen es ajustado ({pct:.1f}%). Cualquier mes malo podría dejarte en cero. Analiza qué gastos podrías recortar."
    elif g == 0:
        return "Tu negocio empata exactamente: no ganas ni pierdes. Estás en el límite — cualquier gasto adicional o baja en ventas resultaría en pérdida."
    else:
        return f"Este mes tu negocio perdió ${abs(g):,.2f}. Tus costos y gastos superan lo que vendes. Es importante actuar: revisa qué puedes recortar o cómo aumentar tus ventas."

def _msg_margen(m):
    if m >= 25:
        return f"Por cada $100 que vendes, te quedan ${m:.1f} de ganancia neta. Es un margen sólido — tu negocio es eficiente y rentable."
    elif m >= 15:
        return f"Te quedan ${m:.1f} de cada $100 vendidos. Es aceptable, pero busca oportunidades para mejorar: negocia precios con proveedores o revisa gastos fijos."
    elif m >= 5:
        return f"Solo ${m:.1f} de cada $100 vendidos llegan a tu bolsillo. El margen es muy estrecho. Un pequeño imprevisto puede borrar toda la ganancia del mes."
    else:
        return f"Tu margen es crítico: ${m:.1f} por cada $100 vendidos. El negocio apenas cubre sus costos. Necesitas aumentar precios, reducir costos o ambos."

def _msg_margen_bruto(mb):
    if mb >= 50:
        return f"Después de pagar lo que vendes, te queda el {mb:.1f}% para cubrir gastos y generar ganancia. Excelente — tienes mucho margen para operar."
    elif mb >= 30:
        return f"Te queda el {mb:.1f}% de cada venta para cubrir tus gastos fijos y generar ganancia. Es un margen saludable para la mayoría de negocios."
    elif mb >= 20:
        return f"Con el {mb:.1f}% que te queda de cada venta, cubres tus gastos con poco margen de error. Considera si puedes subir precios o reducir el costo de lo que vendes."
    else:
        return f"Solo el {mb:.1f}% de tus ventas queda después de pagar lo que vendes. Es muy poco para cubrir gastos fijos y generar ganancia. Revisa urgentemente tus precios o costos."

def _msg_cobertura(c):
    if c >= 3:
        return f"Tienes dinero para {c:.1f} meses sin vender nada — excelente reserva. Tu negocio puede aguantar imprevistos sin entrar en crisis."
    elif c >= 2:
        return f"Con lo que tienes en caja, cubres {c:.1f} meses de gastos. Bien — es lo mínimo recomendado. Trata de mantener o aumentar esta reserva."
    elif c >= 1:
        return f"Tu caja alcanza para {c:.1f} mes de gastos. Es poco. Si las ventas bajan un mes, podrías tener problemas para pagar. Intenta ahorrar parte de las ganancias."
    else:
        return f"Con tu caja actual, solo cubres {c:.1f} meses de gastos — situación frágil. Una semana mala podría dejarte sin fondos para operar. Prioriza tener una reserva."

def _msg_balance(b, pc, pp):
    if b > 0:
        return f"Tus clientes te deben ${pc:,.2f} y tú debes ${pp:,.2f} a proveedores — tienes un saldo a favor de ${b:,.2f}. Buena posición: recibirás más de lo que pagarás."
    elif b == 0:
        return "Lo que te deben tus clientes es exactamente igual a lo que debes a proveedores. Estás equilibrado."
    else:
        return f"Debes ${pp:,.2f} a proveedores y solo tienes ${pc:,.2f} por cobrar. El déficit de ${abs(b):,.2f} puede presionar tu caja. Activa el cobro a clientes cuanto antes."

def _msg_equilibrio(ventas, pe, pct):
    diff = ventas - pe
    if ventas >= pe:
        return f"¡Superaste tu punto de equilibrio! Vendes ${ventas:,.2f} y solo necesitabas ${pe:,.2f}. Estás generando ganancia real con un {pct:.0f}% de cobertura."
    else:
        return f"Aún no alcanzas tu punto de equilibrio. Vendes ${ventas:,.2f} pero necesitas llegar a ${pe:,.2f} para no perder. Te faltan ${abs(diff):,.2f} más en ventas este mes."


# ── Score ─────────────────────────────────────
def _score(inds):
    mapa = {'bueno': 10, 'alerta': 5, 'critico': 0}
    if not inds:
        return 0
    total = sum(mapa.get(i['estado'], 5) for i in inds)
    return round((total / (len(inds) * 10)) * 100)


# ── Resumen ejecutivo ─────────────────────────
def _resumen(inds, ganancia):
    buenos   = [i for i in inds if i['estado'] == 'bueno']
    alertas  = [i for i in inds if i['estado'] == 'alerta']
    criticos = [i for i in inds if i['estado'] == 'critico']
    return {
        'buenos':   [i['nombre'] for i in buenos],
        'alertas':  [i['nombre'] for i in alertas],
        'criticos': [i['nombre'] for i in criticos],
    }


# ── Rutas Flask ───────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analizar', methods=['POST'])
def analizar():
    data = request.get_json()
    return jsonify(calcular(data))

if __name__ == '__main__':
    app.run()
