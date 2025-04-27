import re


def normalize_text(raw_text: str) -> str:
    """做一些针对 OCR 错分的预处理，比如把 'Lu m i a' → 'Lumia'."""
    text = raw_text
    # 修复 Lumia Care 的断字
    text = re.sub(r"L\s*u\s*m\s*i\s*a", "Lumia", text, flags=re.IGNORECASE)
    text = re.sub(r"C\s*a\s*r\s*e", "Care", text, flags=re.IGNORECASE)
    # …可以根据需要继续添加其他常见错分规则
    return text


def parse_payslip_text(raw_text: str) -> dict:
    """
    从 OCR 提取的原始文本中，解析并返回以下字段：
    - 雇主信息: employer, abn
    - 结算周期: period_start, period_end, date_paid
    - 支付与时薪: base_rate, loading, hours_paid, gross_earnings, net_payment, super_payment
    - 明细工时 & 津贴: line_items 列表
    - 扣税与养老金: payg, tax_withheld, tax_rate_percent, super_guarantee
    - 银行到账: bank_account, net_paid_to_account
    """
    # 1. 文本预处理
    fixed = normalize_text(raw_text)
    text = re.sub(r"\s+", " ", fixed).strip()

    # 2. 基本字段正则
    patterns = {
        "employer":        r"^(.*?)ABN:",
        "abn":             r"ABN:\s*(\d+)",
        "period_start":    r"Period Starting:\s*([\d/]+)",
        "period_end":      r"Period Ending:\s*([\d/]+)",
        "date_paid":       r"Date Paid:\s*([\d/]+)",
        "job_title":       r"Job Title:\s*(.+?)Base Pay Rate",
        "base_rate":       r"Base Pay Rate:\s*\$(\d+\.\d+)",
        "loading":         r"includes\s*\$(\d+\.\d+)\s*loading",
        "hours_paid":      r"Hours Paid:\s*(\d+\.?\d*)",
        "gross_earnings":  r"Gross Earnings:\s*\$(\d+\.\d{2})",
        "net_payment":     r"Net Payment:\s*\$(\d+\.\d{2})",
        "super_payment":   r"Super Payments:\s*\$(\d+\.\d{2})",
        "payg":            r"PAYG\s*\$(\d+\.\d{2})",
        "super_guarantee": r"SG\s*\$(\d+\.\d{2})",
        # 银行到账
        "bank_account":    r"Ziyang Zuo\s+(\d+\s*-\s*\*+\d+)\s*\$(\d+\.\d{2})"
    }

    result = {}
    for key, pat in patterns.items():
        m = re.search(pat, text)
        if not m:
            continue
        # 银行账号和到账分两组
        if key == "bank_account":
            acct, paid = m.groups()
            result["bank_account"] = acct.strip()
            result["net_paid_to_account"] = float(paid)
        else:
            val = m.group(1).strip()
            # 转数值类型
            if key in {"base_rate", "loading", "hours_paid"}:
                result[key] = float(val)
            elif key in {"gross_earnings", "net_payment", "super_payment", "payg", "super_guarantee"}:
                result[key] = float(val)
            else:
                result[key] = val

    # 3. 明细工时 & 津贴
    item_pattern = re.compile(
        r"((?:Casual\s*-\s*[\w\s-]+|Laundry Allowance\s*-\s*\w+))\s+"
        r"(\d+\.?\d*)\s+\$(\d+\.\d+)\s+\$(\d+\.\d+)"
    )
    items = []
    for m in item_pattern.finditer(text):
        items.append({
            "item":     m.group(1).strip(),
            "hours":    float(m.group(2)),
            "rate":     float(m.group(3)),
            "this_pay": float(m.group(4))
        })
    result["line_items"] = items

    # 4. 计算税率并标明扣税金额
    if "gross_earnings" in result and "payg" in result:
        gross = result.get("gross_earnings", 0)
        payg  = result.get("payg", 0)
        result["tax_withheld"] = payg
        result["tax_rate_percent"] = round((payg / gross * 100) if gross else 0, 2)

    return result


if __name__ == "__main__":
    from ocr_utils import extract_text_from_pdf

    raw = extract_text_from_pdf("./input_pdf/PaySlip20250403.pdf")
    parsed = parse_payslip_text(raw)
    import pprint; pprint.pprint(parsed)
