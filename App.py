from flask import Flask, render_template_string, request
import random
import sqlite3
from reportlab.platypus import SimpleDocTemplate, Paragraph

app = Flask(__name__)

# --- BASE DE DATOS ---
conn = sqlite3.connect("pesajes.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS registros (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    matricula TEXT,
    producto TEXT,
    peso_vacio INTEGER,
    peso_lleno INTEGER,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

# Diccionario temporal
data = {}

# --- IA POR HISTÓRICO ---
def obtener_producto(matricula):
    cursor.execute("""
    SELECT producto, COUNT(*) as veces
    FROM registros
    WHERE matricula=?
    GROUP BY producto
    ORDER BY veces DESC
    LIMIT 1
    """, (matricula,))
    
    resultado = cursor.fetchone()
    
    if resultado:
        return resultado[0]
    else:
        return "MATRÍCULA NUEVA"

# --- GENERAR PDF ---
def generar_pdf(matricula, producto, pv, pl):
    doc = SimpleDocTemplate(f"albaran_{matricula}.pdf")
    elementos = []

    elementos.append(Paragraph(f"Matrícula: {matricula}", None))
    elementos.append(Paragraph(f"Producto: {producto}", None))
    elementos.append(Paragraph(f"Peso vacío: {pv} kg", None))
    elementos.append(Paragraph(f"Peso lleno: {pl} kg", None))
    elementos.append(Paragraph(f"Peso neto: {pl-pv} kg", None))

    doc.build(elementos)

# --- HTML (TU DISEÑO, SIN TOCAR) ---
html = """TU HTML TAL CUAL (NO LO CAMBIES)"""

@app.route("/", methods=["GET","POST"])
def home():
    matricula = None
    producto = None
    peso_vacio = None
    peso_lleno = None

    if request.method == "POST":
        matricula = request.form.get("matricula", "").upper().strip()
        accion = request.form.get("accion")

        if accion == "detectar":
            producto = obtener_producto(matricula)
            data[matricula] = {"producto": producto}

        elif accion == "peso_vacio":
            peso_vacio = random.randint(12000, 15000)
            if matricula in data:
                data[matricula]["peso_vacio"] = peso_vacio
                producto = data[matricula].get("producto")

        elif accion == "peso_lleno":
            if matricula in data and "peso_vacio" in data[matricula]:
                peso_lleno = random.randint(25000, 32000)
                peso_vacio = data[matricula]["peso_vacio"]
                producto = data[matricula].get("producto")

                # 💾 GUARDAR EN BD
                cursor.execute("""
                INSERT INTO registros (matricula, producto, peso_vacio, peso_lleno)
                VALUES (?, ?, ?, ?)
                """, (matricula, producto, peso_vacio, peso_lleno))
                conn.commit()

                # 🧾 GENERAR PDF
                generar_pdf(matricula, producto, peso_vacio, peso_lleno)

    return render_template_string(html, 
                                matricula=matricula, 
                                producto=producto, 
                                peso_vacio=peso_vacio, 
                                peso_lleno=peso_lleno)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
