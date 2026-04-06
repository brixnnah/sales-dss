import pandas as pd
import pytest
import app

from app import build_dss_recommendations, compute_daily_metrics, load_data


@pytest.fixture(scope='module')
def sample_df():
    data = [
        {'order_date': '2020-10-01', 'category': 'electronics', 'qty_ordered': 2, 'price': 50},
        {'order_date': '2020-10-15', 'category': 'electronics', 'qty_ordered': 1, 'price': 50},
        {'order_date': '2020-11-05', 'category': 'apparel', 'qty_ordered': 4, 'price': 30}
    ]
    df = pd.DataFrame(data)
    df['order_date'] = pd.to_datetime(df['order_date'])
    return df


def test_compute_daily_metrics_uses_category(sample_df):
    metrics = compute_daily_metrics(sample_df, top_n=2)
    assert 'top_qty_products' in metrics
    assert metrics['top_qty_products'][0] == 'apparel' or metrics['top_qty_products'][0] == 'electronics'


def test_build_dss_recommendations(sample_df):
    metrics = compute_daily_metrics(sample_df, top_n=2)
    recs = build_dss_recommendations(metrics['top_qty_products'], metrics['top_qty_values'], buffer_months=2)
    assert len(recs) > 0
    assert recs[0]['product'] in ['electronics', 'apparel']
    assert recs[0]['recommended_reorder'] >= recs[0]['monthly_average']


def test_load_data_has_order_date(tmp_path):
    file_path = tmp_path / 'sales_test.csv'
    file_path.write_text('order_date,category,qty_ordered,price\n2020-10-01,electronics,1,50\n', encoding='utf-8')

    original_path = app.CSV_PATH
    app.CSV_PATH = str(file_path)
    df = load_data(str(file_path))
    app.CSV_PATH = original_path

    assert not df.empty
    assert 'order_date' in df.columns
