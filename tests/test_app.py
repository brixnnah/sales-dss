import pandas as pd
import pytest
import app

from app import (
    build_dss_recommendations,
    calculate_inventory_recommendation,
    compute_daily_metrics,
    compute_eda,
    load_data,
)


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


def test_inventory_recommendation_invariants(sample_df):
    rec = calculate_inventory_recommendation(sample_df, 'electronics')

    assert rec is not None
    assert rec['reorder_point'] >= 0
    assert rec['safety_stock'] >= 0
    assert rec['target_stock'] == rec['reorder_point'] + rec['safety_stock']


def test_inventory_recommendation_empty_category_returns_none(sample_df):
    rec = calculate_inventory_recommendation(sample_df, 'non-existent-category')
    assert rec is None


def test_inventory_recommendation_monotonic_with_lead_time_and_service_level(sample_df):
    base = calculate_inventory_recommendation(
        sample_df,
        'electronics',
        lead_time_days=7,
        service_level=0.90,
    )
    higher_lead_time = calculate_inventory_recommendation(
        sample_df,
        'electronics',
        lead_time_days=21,
        service_level=0.90,
    )
    higher_service_level = calculate_inventory_recommendation(
        sample_df,
        'electronics',
        lead_time_days=7,
        service_level=0.95,
    )

    assert base is not None
    assert higher_lead_time is not None
    assert higher_service_level is not None

    assert higher_lead_time['reorder_point'] >= base['reorder_point']
    assert higher_lead_time['target_stock'] >= base['target_stock']
    assert higher_service_level['safety_stock'] >= base['safety_stock']


def test_compute_eda_returns_visualization_series(sample_df):
    enriched_df = sample_df.copy()
    enriched_df['unique_skus'] = [3, 2, 4]

    summary = compute_eda(enriched_df)

    assert summary is not None
    assert len(summary['price_band_labels']) == 5
    assert len(summary['price_band_values']) == 5
    assert len(summary['category_mix_labels']) > 0
    assert len(summary['category_mix_revenue']) == len(summary['category_mix_labels'])
    assert len(summary['category_mix_quantity']) == len(summary['category_mix_labels'])
