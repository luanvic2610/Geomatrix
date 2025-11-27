import pandas as pd
import os

class IOSystem:
    @staticmethod
    def ler_csv_inteligente(caminho_arquivo):
        """Tenta ler CSV com diferentes separadores e encodings."""
        try:
            # Tenta UTF-8 com ponto e vírgula
            df = pd.read_csv(caminho_arquivo, sep=';', encoding='utf-8')
            if len(df.columns) < 2:
                # Tenta UTF-8 com vírgula
                df = pd.read_csv(caminho_arquivo, sep=',', encoding='utf-8')
            return df
        except:
            # Tenta Latin-1 (Excel antigo)
            try:
                df = pd.read_csv(caminho_arquivo, sep=';', encoding='latin1')
                if len(df.columns) < 2:
                    df = pd.read_csv(caminho_arquivo, sep=',', encoding='latin1')
                return df
            except Exception as e:
                raise Exception(f"Erro ao ler arquivo: {e}")

    @staticmethod
    def achar_coluna(df, lista_possiveis):
        """Procura o nome real da coluna baseado em apelidos."""
        colunas_limpas = [c.upper().strip() for c in df.columns]
        for possivel in lista_possiveis:
            if possivel in colunas_limpas:
                index = colunas_limpas.index(possivel)
                return df.columns[index]
        return None

    @staticmethod
    def remover_duplicatas(df, col_id):
        """Remove linhas duplicadas baseado numa coluna ID."""
        antes = len(df)
        df_limpo = df.drop_duplicates(subset=[col_id], keep='first')
        removidos = antes - len(df_limpo)
        return df_limpo, removidos

    @staticmethod
    def salvar_excel(dataframe, caminho_saida):
        """Salva o DataFrame final em Excel."""
        dataframe.to_excel(caminho_saida, index=False)
        return os.path.basename(caminho_saida)