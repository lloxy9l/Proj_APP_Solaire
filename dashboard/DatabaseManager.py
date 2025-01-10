from flask import Flask, request, jsonify
from search import Search  # Importando a classe Search
import mysql.connector

app = Flask(__name__)

# Criando uma instância da classe Search
search_instance = Search(host="172.67.213.34", user="dev", password="9e*s@@iCFNs#r8", database="projet_solarx")

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')
    
    if not query:
        return jsonify({"error": "Nenhum termo de pesquisa fornecido"}), 400
    
    try:
        # Usando a classe Search para realizar a busca
        results = search_instance.search_in_all_tables(query)

    except mysql.connector.Error as e:
        return jsonify({"error": f"Erro no banco de dados: {e}"}), 500
    
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)
