with exposed as (
    select
        distinct affiliation.campaignid as campaign_id,
        generic.device.ifa.plain as device_id
    from
        impressions
    where
        dt between '%begin_date'
        and '%end_date_targeting'
        and generic.bundleidentifier in ('%bundle_a', '%bundle_i') %campaign_ids_e
),
users as (
    select
        t.date,
        t.campaign_id,
        t.device_id,
        case when exposed.device_id is not null then 'exposed' else t.variant end as variant
    from
        bi_sandbox.%table_name_processed t
        left join exposed on t.campaign_id = exposed.campaign_id
        and exposed.device_id = t.device_id
    where 
        t.date between '%begin_date'
        and '%end_date_targeting'
        %campaign_ids_t
),
count_users as (
    select
        campaign_id,
        variant,
        count(distinct device_id) as total_unique_users
    from
        users
    where
        variant in ('control', 'targeted', 'exposed')
    group by
        1,
        2
),
ca as (
    select
        dt as date,
        generic.device.ifa.plain as device_id,
        payload.name as custom_action,
        count(distinct generic.actionid) as count_events,
        sum(payload.revenueinusd) as revenue_usd
    from
        custom_actions
    where
        dt between '%begin_date'
        and '%end_date'
        and bundle in ('%bundle_a', '%bundle_i')
    group by
        1,
        2,
        3
),
reopens as (
    select
        dt as date,
        generic.device.ifa.plain as device_id,
        'REOPEN' as custom_action,
        count(distinct generic.actionid) as count_events,
        0 as revenue_usd
    from
        reopens
    where
        dt between '%begin_date'
        and '%end_date'
        and bundle in ('%bundle_a', '%bundle_i')
    group by
        1,
        2,
        3,
        5
),
events as (
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
),
rtb as (
    select
        distinct u.device_id
    from
        user_db_last_run rtb
        inner join users u on u.device_id = rtb.device_id_plain
),
cost as (
    select
        drc.campaign_id,
        round(coalesce(sum(client_cost_usd), 0), 2) as total_cost
    from
        dsp_revenue_costs drc
        inner join dim_campaign dc on drc.campaign_id = dc.campaign_id
    where
        dt between '%begin_date'
        and '%end_date_targeting'
        and bundle_identifier in ('%bundle_a', '%bundle_i') %campaign_ids_dc
    group by
        1
),
data as (
    select
        case when rtb.device_id is not null then 'TRUE' else 'FALSE' end as rtb_active,
        case when count_percentile > 90
        or revenue_percentile > 90 then 'TRUE' else 'FALSE' end as is_outlier,
        dc.campaign_id,
        dc.os,
        coalesce(country_code_a2, region) as country,
        custom_action,
        campaign_name,
        co.variant as segment,
        total_unique_users,
        --coalesce(count(distinct users.device_id), 0) as total_unique_users,
        coalesce(
            count(
                distinct case when count_events > 0 then events.device_id end
            ),
            0
        ) as unique_users_with_custom_action,
        coalesce(sum(count_events), 0) as count,
        coalesce(sum(revenue_usd), 0) as revenue,
        total_cost
    from
        users
        inner join experimental.history_dim_campaign dc on dc.campaign_id = users.campaign_id
        and dc.partition_0 = users.date
        left join events on events.device_id = users.device_id
        left join rtb on rtb.device_id = users.device_id
        left join cost c on c.campaign_id = users.campaign_id
        inner join count_users co on co.campaign_id = users.campaign_id
        and co.variant = users.variant
    where
        date(events.date) > date(users.date)
        or events.date is null
    group by
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        13
)
select
    coalesce(rtb_active, 'all_users') as rtb_active,
    coalesce(is_outlier, 'all_users') as is_outlier,
    campaign_id,
    os,
    country,
    custom_action,
    campaign_name,
    segment,
    sum(total_unique_users) as total_unique_users,
    sum(unique_users_with_custom_action) as unique_users_with_custom_action,
    coalesce(
        sum(unique_users_with_custom_action) / nullif(sum(total_unique_users), 0),
        0
    ) as conversion_rate,
    sum(data.count) as count,
    coalesce(
        sum(data.count) / nullif(sum(total_unique_users), 0),
        0
    ) as anoapu,
    sum(revenue) as revenue,
    coalesce(
        sum(revenue) / nullif(sum(total_unique_users), 0),
        0
    ) as arpu,
    total_cost
from
    data
group by
    rollup (rtb_active),
    rollup (is_outlier),
    3,
    4,
    5,
    6,
    7,
    8,
    16