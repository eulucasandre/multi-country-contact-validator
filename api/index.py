import tempfile 
import zipfile 
import sys 
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flask import Flask, render_template, request, send_file, flash, redirect, url_for

from source.pipeline import processar_arquivo, ErroProcessamento

BASE_DIR = Path(__file__).resolve().parent.parent

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static"),
)
app.secret_key = 'troque-sua-chave-em-producao'

EXTENSOES_PERMITIDAS = {'.xlsx', '.xls', '.csv'}

@app.route('/', methods=['GET'])
def index():
    return render_template('upload.html')


@app.route('/', methods=['POST'])
def processar():
    arquivo = request.files.get('arquivo')

    if arquivo is None or arquivo.filename == '':
        flash('Selecione um arquivo antes de enviar.')
        return redirect(url_for('index'))

    extensao = Path(arquivo.filename).suffix.lower()
    if extensao not in EXTENSOES_PERMITIDAS:
        flash(f'Formato {extensao} não é suportado. Por favor, envie um arquivo .xlsx, .xls ou .csv.')
        return redirect(url_for('index'))

    with tempfile.TemporaryDirectory() as pasta_temp:
        pasta_temp = Path(pasta_temp)
        caminho_arquivo = pasta_temp / arquivo.filename
        arquivo.save(caminho_arquivo)

        pasta_saida = pasta_temp / 'saida'

        try:
            resultado = processar_arquivo(caminho_arquivo, pasta_saida)
        except ErroProcessamento as erro:
            flash(str(erro))
            return redirect(url_for('index'))

        caminho_zip = pasta_temp / 'resultado.zip'
        with zipfile.ZipFile(caminho_zip, 'w') as zipf:
            zipf.write(resultado['caminho_aceitos'], arcname='dados_limpos.xlsx')

            if resultado['caminho_rejeitados']:
                zipf.write(resultado['caminho_rejeitados'], arcname='dados_rejeitados.xlsx')

            zipf.writestr('relatorio.txt', resultado['relatorio_texto'])   

        with open(caminho_zip, 'rb') as f:
            dados_zip = f.read()

    from io import BytesIO
    return send_file(
        BytesIO(dados_zip),
        as_attachment=True,
        download_name='resultado_limpeza.zip',
        mimetype='application/zip',
    )

if __name__ == '__main__':
    app.run(debug=True, port=5000)