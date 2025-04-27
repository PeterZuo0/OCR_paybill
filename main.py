# Revised main.py with default line_items handling
import os
import glob
import pandas as pd
from ocr_utils import extract_text_from_pdf
from parser import parse_payslip_text


def process_payslips(input_dir: str, output_excel: str) -> pd.DataFrame:
    """
    Batch process PDF payslips, ensure 'line_items' always exists,
    then extract to Excel.
    """
    current_dir = os.path.dirname(__file__)
    pdf_dir = os.path.join(current_dir, input_dir)
    # 1. 检查输入目录是否存在
    if not os.path.isdir(pdf_dir):
        raise FileNotFoundError(f"输入目录不存在：{pdf_dir}")

    records = []
    pdf_paths = glob.glob(os.path.join(pdf_dir, "*.pdf"))
    if not pdf_paths:
        raise FileNotFoundError(f"在 {pdf_dir} 中未找到任何 PDF 文件。")

    for pdf_path in pdf_paths:
        raw_text = extract_text_from_pdf(pdf_path)
        parsed = parse_payslip_text(raw_text)
        parsed.setdefault('line_items', [])
        parsed['file_name'] = os.path.basename(pdf_path)
        records.append(parsed)

    df = pd.DataFrame(records)

    # 展开 line_items 如前
    if 'line_items' in df.columns:
        df_expanded = df.explode('line_items').reset_index(drop=True)
        if not df_expanded['line_items'].isna().all():
            line_items_df = pd.DataFrame(df_expanded['line_items'].tolist())
            df_final = pd.concat([df_expanded.drop('line_items', axis=1), line_items_df], axis=1)
        else:
            df_final = df_expanded.drop('line_items', axis=1)
    else:
        df_final = df

    # 3. 导出 Excel
    df_final.to_excel(output_excel, index=False)
    print(f"成功导出到：{output_excel}")
    return df_final


if __name__ == "__main__":
    pdf_dir = r"input_pdf"
    output_excel = r"ayslips_summary.xlsx"

    df = process_payslips(pdf_dir, output_excel)
    print(df.head())
