import mysql.connector

class Search:
    def __init__(self, host, user, password, database):
        self.host = host
        self.user = user
        self.password = password
        self.database = database

    def get_db_connection(self):
        """Conectar ao banco de dados MySQL."""
        return mysql.connector.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database
        )

    def search_in_all_tables(self, query):
        """Pesquisar nas tabelas do banco de dados."""
        conn = self.get_db_connection()
        cursor = conn.cursor()

        # Pegando todas as tabelas do banco de dados
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        all_results = []

        # Iterando sobre todas as tabelas
        for (table,) in tables:
            # Gerando a consulta dinâmica para procurar o texto em todas as colunas
            search_query = f"SELECT * FROM {table} WHERE "
            cursor.execute(f"DESCRIBE {table}")
            columns = cursor.fetchall()
            
            # Criando condição para cada coluna da tabela (assumindo que sejam colunas de texto)
            conditions = []
            for (column, _, data_type, _, _, _) in columns:
                if 'char' in data_type or 'text' in data_type:
                    conditions.append(f"{column} LIKE %s")
            
            # Se houver alguma coluna do tipo texto, prosseguir com a pesquisa
            if conditions:
                query_str = search_query + " OR ".join(conditions)
                search_params = ['%' + query + '%'] * len(conditions)
                cursor.execute(query_str, search_params)
                results = cursor.fetchall()
                all_results.extend(results)
        
        # Fechando a conexão com o banco
        cursor.close()
        conn.close()

        return all_results
