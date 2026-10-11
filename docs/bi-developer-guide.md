# BI developer guide

Work in Superset as usual. The image is stock 6.1.0. Jalali labels come from a virtual dataset, and the Jalali calendar appears only on the dashboard time filter.

## A dataset with Jalali columns

Create a virtual dataset. Keep the real date column, and add the macro pair. Use a different `alias` and `prefix` for each date column.

```sql
SELECT
    o.id,
    o.amount,
    o.created_at,
    CAST(o.created_at AS DATE) AS order_date,
    r.code AS region,
    {{ jalali_columns('o.created_at') }}
FROM sales.orders o
JOIN sales.branches b ON b.id = o.branch_id
JOIN sales.regions r ON r.code = b.region_code
{{ jalali_join('o.created_at') }}
```

Mark `order_date` (and `created_at`, if you want it) as temporal. Set the dataset's main datetime column to `order_date`.

Columns you can group and display:

| Column | Example |
|---|---|
| `jalali_year` | 1403 |
| `jalali_month_num` | 7 |
| `jalali_day` | 18 |
| `jalali_date` | 1403/07/18 |
| `jalali_date_int` | 14030718 |
| `jalali_month` | 1403-07 |
| `jalali_month_name` | مهر |
| `jalali_month_label` | 1403-07 مهر |
| `jalali_season` | پاییز |
| `jalali_season_key` | 1403-3 پاییز |
| `jalali_weekday` | چهارشنبه |
| `jalali_weekday_num` | 4 (Saturday is 0) |
| `jalali_week_start` | Gregorian date of that Saturday |

`jalali_month_label` and `jalali_date` sort correctly as text because the numeric part comes first. `jalali_date_int` is the column to use when a table needs a numeric sort. Dates outside `JALALI_SQL` min/max year, and NULL dates, produce NULL Jalali columns.

`{{ jalali_to_gregorian('1403/07/01') }}` becomes `DATE '2024-09-22'`. `{{ jalali_period_sql('o.created_at', 'this_month') }}` is a predicate for this Jalali month, last month, this year, last year, or `ytd`, using today in Asia/Tehran.

Set `JALALI_SQL` `digits` to `persian` only when the text columns should be displayed with Persian digits. Numeric columns stay Latin so they aggregate.

## Charts that follow the dashboard date filter

On every chart, add a time filter:

- column: the Gregorian temporal column (`order_date`)
- range: No filter

Without that pill, the dashboard time range does not reach the chart. A dataset with no date column cannot follow the filter.

Use Jalali columns as categories (`jalali_month_label` on the x axis, `jalali_year` as pivot rows). Superset's time grain, comparison, and forecast stay Gregorian.

## The dashboard filter

Add a Time range native filter. That control is the Jalali calendar. Other filters (year, month, category) are ordinary select filters on the Jalali columns. Month can cascade from year.

For a default that should move every day, use «امروز» or «۷ روز اخیر» in the filter settings. «این ماه» and «امسال» are saved as the dates of the day you clicked them.

## Embedding

Publish the dashboard and set its embedded domains to the host origins. Guest tokens apply `region IN (...)` to every dataset, so the virtual dataset must expose `region`. Do not put a user's ad-hoc filter into the guest token.

## Explore

The chart editor still uses Superset's Gregorian time picker. The Jalali calendar is the dashboard filter bar only. The chart header shows the stored Gregorian range.
