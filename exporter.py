# hikvision_analyzer/exporter.py

from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils.dataframe import dataframe_to_rows


def export_to_excel(df, path):
    """Exporta DataFrame para Excel com estilização condicional."""
    wb = Workbook()
    ws = wb.active

    # Adicionar cabeçalhos e dados
    for r_idx, row in enumerate(dataframe_to_rows(df, index=False, header=True), 1):
        for c_idx, value in enumerate(row, 1):
            cell = ws.cell(row=r_idx, column=c_idx, value=value)
            # Se for a coluna de detalhes e tiver "precisa ser corrigida", pintar vermelho
            if df.columns[c_idx - 1] == "Detalhes da Configuração" and isinstance(value, str) and "precisa ser corrigida" in value:
                cell.font = Font(color="FF0000")

    wb.save(path)