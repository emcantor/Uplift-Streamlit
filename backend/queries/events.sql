with users as (
    select
        distinct t.date,
        t.campaign_id,
        t.device_id,
        t.variant
    from
        bi_sandbox.%table_name_processed t
    where
        t.date between '%begin_date'
        and '%end_date_targeting' %campaign_ids_t
        and t.variant in ('control', 'targeted')
),
ca as (
    select
        ca.dt as date,
        generic.device.ifa.plain as device_id,
        payload.name as custom_action,
        count(distinct generic.actionid) as count_events,
        sum(payload.revenueinusd) as revenue_usd
    from
        custom_actions ca
        inner join users u on u.device_id = ca.generic.device.ifa.plain
    where
        dt between '%begin_date'
        and '%end_date'
        and bundle in ('%bundle_a', '%bundle_i')
        and date(ca.dt) > date(u.date)
    group by
        1,
        2,
        3
),
reopens as (
    select
        r.dt as date,
        generic.device.ifa.plain as device_id,
        'REOPEN' as custom_action,
        count(distinct generic.actionid) as count_events,
        0 as revenue_usd
    from
        reopens r
        inner join users u on u.device_id = r.generic.device.ifa.plain
    where
        dt between '%begin_date'
        and '%end_date'
        and bundle in ('%bundle_a', '%bundle_i')
        and date(r.dt) > date(u.date)
    group by
        1,
        2,
        3,
        5
)
select
    date,
    device_id,
    custom_action,
    sum(count_events) as count_events,
    NTILE(100) OVER (
        ORDER BY
            sum(count_events)
    ) AS count_percentile,
    sum(revenue_usd) as revenue_usd,
    NTILE(100) OVER (
        ORDER BY
            sum(revenue_usd)
    ) AS revenue_percentile
from
    (
        select
            *
        from
            ca
        union all
        select
            *
        from
            reopens
    )
group by
    1,
    2,
    3
