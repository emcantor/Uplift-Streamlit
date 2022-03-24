select
    *
from
    (
        select
            cast(drc.campaign_id as varchar) as campaign_id,
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
        union all
        select
            array_join(
                array_distinct(array_agg(cast(drc.campaign_id as varchar))),
                ', '
            ) as campaign_id,
            round(coalesce(sum(client_cost_usd), 0), 2) as total_cost
        from
            dsp_revenue_costs drc
            inner join dim_campaign dc on drc.campaign_id = dc.campaign_id
        where
            dt between '%begin_date'
            and '%end_date_targeting'
            and os = 'ANDROID'
            and bundle_identifier in ('%bundle_a', '%bundle_i') %campaign_ids_dc
        union all
        select
            array_join(
                array_distinct(array_agg(cast(drc.campaign_id as varchar))),
                ', '
            ) as campaign_id,
            round(coalesce(sum(client_cost_usd), 0), 2) as total_cost
        from
            dsp_revenue_costs drc
            inner join dim_campaign dc on drc.campaign_id = dc.campaign_id
        where
            dt between '%begin_date'
            and '%end_date_targeting'
            and os = 'IOS'
            and bundle_identifier in ('%bundle_a', '%bundle_i') %campaign_ids_dc
    )