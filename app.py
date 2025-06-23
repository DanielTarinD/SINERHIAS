from flask import Flask, render_template, request, redirect, url_for, send_file, session
import pandas as pd
import os
import shutil
import tempfile
import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'clave-segura'
UPLOAD_FOLDER = 'uploads'
BACKUP_FOLDER = 'backups'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(BACKUP_FOLDER, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        archivo = request.files['archivo']
        if archivo.filename == '':
            return "No seleccionaste ningún archivo", 400

        filename = secure_filename(archivo.filename)
        path = os.path.join(UPLOAD_FOLDER, filename)
        archivo.save(path)
        session['archivo'] = path
        return redirect(url_for('buscar'))

    return render_template('index.html')

@app.route('/buscar', methods=['GET', 'POST'])
def buscar():
    archivo = session.get('archivo')
    if not archivo or not os.path.exists(archivo):
        return redirect(url_for('index'))

    df = pd.read_excel(archivo)
    query = request.form.get('query', '').lower()
    resultados = df[df.apply(
        lambda row: query in str(row["CLUES"]).lower() or query in str(row["NOMBRE UNIDAD"]).lower(), axis=1
    )] if query else df

    resultados = resultados[["CLUES", "NOMBRE UNIDAD"]].reset_index()
    return render_template('buscar.html', resultados=resultados.to_dict(orient='records'), query=query)

@app.route('/detalle/<int:idx>', methods=['GET', 'POST'])
def detalle(idx):
    archivo = session.get('archivo')
    if not archivo or not os.path.exists(archivo):
        return redirect(url_for('index'))

    df = pd.read_excel(archivo)

    if request.method == 'POST':
        for clave in request.form:
            df.at[idx, clave] = request.form[clave]

        now = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(BACKUP_FOLDER, f'respaldo_{now}.xlsx')
        shutil.copyfile(archivo, backup_path)

        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            temp_path = tmp.name
        df.to_excel(temp_path, index=False)
        shutil.copyfile(temp_path, archivo)
        os.remove(temp_path)

        return redirect(url_for('buscar'))

    row = df.loc[idx]
    campos = {col: row[col] for col in df.columns if col not in ["CLUES", "NOMBRE UNIDAD", "JURISDICCION", "NOMBRE JURISDICCION", "TIPOLOGIA"]}
    titulo = f"{row['CLUES']} - {row['NOMBRE UNIDAD']}"
    subtitulo = f"{row['JURISDICCION']} - {row['NOMBRE JURISDICCION']}"
    tipologia = row["TIPOLOGIA"]

    return render_template('detalle.html', idx=idx, campos=campos, titulo=titulo, subtitulo=subtitulo, tipologia=tipologia)

@app.route('/descargar')
def descargar():
    archivo = session.get('archivo')
    if not archivo or not os.path.exists(archivo):
        return redirect(url_for('index'))
    return send_file(archivo, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
