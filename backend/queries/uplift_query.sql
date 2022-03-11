with wl as (
    select
        distinct t.date,
        dtl.campaign_id,
        t.variant,
        t.device_id
    from
        bi_sandbox.%table_name t
        inner join experimental.history_dim_targeting_list dtl on dtl.targeting_list_id = t.targeting_list_id
        and dtl.partition_0 = t.date
        inner join experimental.history_dim_campaign dc on dc.campaign_id = dtl.campaign_id
        and dtl.partition_0 = dc.partition_0
    where
        targeting_list_type = 'white'
        and date(dtl.partition_0) between date('%begin_date')
        and date('%end_date_targeting')
        and date(dc.partition_0) between date('%begin_date')
        and date('%end_date_targeting')
        and device_id is not Null
        and bundle_identifier in ('%bundle_a', '%bundle_i') %campaign_ids
),
bl as (
    select
        distinct t.date,
        dtl.campaign_id,
        t.device_id
    from
        bi_sandbox.%table_name t
        inner join experimental.history_dim_targeting_list dtl on dtl.targeting_list_id = t.targeting_list_id
        and dtl.partition_0 = t.date
        inner join experimental.history_dim_campaign dc on dc.campaign_id = dtl.campaign_id
        and dtl.partition_0 = dc.partition_0
    where
        targeting_list_type = 'black'
        and date(dtl.partition_0) between date('%begin_date')
        and date('%end_date_targeting')
        and date(dc.partition_0) between date('%begin_date')
        and date('%end_date_targeting')
        and device_id is not Null
        and bundle_identifier in ('%bundle_a', '%bundle_i') %campaign_ids
),
users as (
    select
        wl.date,
        wl.campaign_id,
        wl.device_id,
        variant
    from
        wl
        left join bl on wl.date = bl.date
        and wl.campaign_id = bl.campaign_id
        and wl.device_id = bl.device_id
    where
        bl.device_id is Null
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
exposed as (
    select
        distinct generic.bundleidentifier as bundle_identifier,
        generic.device.os as os,
        generic.device.ifa.plain as device_id
    from
        impressions
    where
        date(dt) between date('%begin_date')
        and date('%end_date_targeting')
        and generic.bundleidentifier in ('%bundle_a', '%bundle_i') %campaign_ids_e
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
        sum(client_cost_usd) as cost
    from
        dsp_revenue_costs drc
        inner join experimental.history_dim_campaign dc on drc.campaign_id = dc.campaign_id
    where
        dt between '%begin_date'
        and '%end_date_targeting'
        and partition_0 between '%begin_date'
        and '%end_date_targeting'
        and bundle_identifier in ('%bundle_a', '%bundle_i') %campaign_ids
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
        case when exposed.device_id is not null then 'exposed' else variant end as segment,
        coalesce(count(distinct users.device_id), 0) as total_unique_users,
        coalesce(
            count(
                distinct case when count_events > 0 then events.device_id end
            ),
            0
        ) as unique_users_with_custom_action,
        coalesce(sum(count_events), 0) as count,
        coalesce(sum(revenue_usd), 0) as revenue,
        coalesce(sum(c.cost), 0) as total_cost
    from
        users
        inner join experimental.history_dim_campaign dc on dc.campaign_id = users.campaign_id
        and dc.partition_0 = users.date
        left join exposed on dc.bundle_identifier = exposed.bundle_identifier
        and dc.os = exposed.os
        and exposed.device_id = users.device_id
        left join events on events.device_id = users.device_id
        left join rtb on rtb.device_id = users.device_id
        left join cost c on c.campaign_id = users.campaign_id
    where
        date(events.date) > date(users.date)
        and variant in ('control', 'targeted')
    group by
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8
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
    sum(total_cost) as total_cost
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
    8
