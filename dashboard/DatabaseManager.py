from flask import Flask, request, jsonify
import mysql.connector

app = Flask(__name__)

# Função para conexão com o banco de dados
def get_db_connection():
    return mysql.connector.connect(
        host="projet-idu.hqbr.win",
        user="dev",
        password="9e*s@@iCFNs#r8",
        database="projet_solarx"
    )

# Rota para filtrar os resultados da pesquisa
@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')
    
    if not query:
        return jsonify({"error": "Nenhum termo de pesquisa fornecido"}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Obter todas as tabelas no banco de dados
        cursor.execute("SHOW TABLES")
        tables = [table['Tables_in_projet_solarx'] for table in cursor.fetchall()]
        
        results = []
        for table in tables:
            # Garantir que o nome da tabela é seguro
            if not table.isidentifier():
                continue
            
            # Fazer a busca na tabela
            query_sql = f"SELECT * FROM `{table}` WHERE nome LIKE %s"
            cursor.execute(query_sql, ('%' + query + '%',))
            results.extend(cursor.fetchall())
    
    except mysql.connector.Error as e:
        return jsonify({"error": f"Erro no banco de dados: {e}"}), 500
    
    finally:
        # Certifique-se de fechar a conexão
        cursor.close()
        conn.close()
    
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)


