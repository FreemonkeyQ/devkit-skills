from app.report_builder import orders_to_csv


def test_orders_to_csv_has_header_and_rows():
    body = orders_to_csv([(1, "Acme", "PAID")])
    assert body.splitlines() == ["id,customer,status", "1,Acme,PAID"]
