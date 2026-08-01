from app.services import ratios
def test_ratios():
    assert ratios('Revenue $1,000 Gross profit $400 Net income $100')=={'gross_margin_pct':40.0,'net_margin_pct':10.0}
