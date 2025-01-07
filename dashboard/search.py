# search.py (salve esse código em um arquivo chamado search.py)

import pandas as pd

class Search:
    def __init__(self, data):
        """Inicializa a classe com os dados."""
        self.data = data

    def search_data(self, query):
        """Filtra os dados com base na consulta e retorna os resultados."""
        if query is None or query == "":
            return "Aucune donnée à afficher"  # Se a pesquisa estiver vazia
        
        filtered_df = self.data[self.data['nom'].str.contains(query, case=False, na=False)]
        
        if filtered_df.empty:
            return "Aucun résultat trouvé"  # Nenhum resultado encontrado

        # Retorna os resultados formatados
        return [
            f"Nom: {row['nom']}, Température: {row['temperature']}°C, Précipitations: {row['precipitation']}mm"
            for _, row in filtered_df.iterrows()
        ]
