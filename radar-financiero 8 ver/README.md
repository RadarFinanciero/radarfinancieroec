# 📡 Radar Financiero

Herramienta de diagnóstico financiero para PYMES. Ingresa los datos de tu empresa y obtén un análisis automático con indicadores clave e interpretación personalizada.

---

## 🚀 Cómo ejecutar

### 1. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2. Ejecutar la aplicación
```bash
python app.py
```

### 3. Abrir en el navegador
```
http://localhost:5000
```

---

## 📊 Indicadores calculados

### Liquidez
- **Razón Corriente** — Activo Corriente / Pasivo Corriente
- **Prueba Ácida** — (Activo Corriente - Inventario) / Pasivo Corriente
- **Liquidez Inmediata** — Caja / Pasivo Corriente

### Rentabilidad
- **Margen Bruto** — (Ingresos - Costo de Ventas) / Ingresos × 100
- **Margen Operativo** — Utilidad Operativa / Ingresos × 100
- **ROA** — Utilidad Neta / Activo Total × 100
- **ROE** — Utilidad Neta / Patrimonio × 100

### Operación
- **Días Promedio de Cobro** — (CxC / Ingresos) × 365
- **Días de Inventario** — (Inventario / Costo de Ventas) × 365

### Endeudamiento
- **Nivel de Endeudamiento** — Pasivo Total / Activo Total × 100

---

## 🗂️ Estructura del proyecto
```
radar-financiero/
├── app.py              # Backend Flask con cálculos financieros
├── requirements.txt    # Dependencias
├── README.md
└── templates/
    └── index.html      # Interfaz web completa
```

---

## 💡 Próximas funcionalidades (versión premium)
- Análisis comparativo por sector/industria
- Proyecciones financieras
- Plan de mejora personalizado
- Exportación a PDF
- Reporte ejecutivo
