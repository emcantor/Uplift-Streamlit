select
    *
from
    (
        select
            partition_0,
            cast(campaign_id as varchar) as campaign_id,
            os,
            coalesce(country_code_a2, region) as country,
            campaign_name
        from
            experimental.history_dim_campaign dc
        where
            partition_0 between '%begin_date'
            and '%end_date_targeting'
            and bundle_identifier in ('%bundle_a', '%bundle_i') %campaign_ids_dc
        union all
        select
            partition_0,
            array_join(
                array_distinct(array_agg(cast(campaign_id as varchar))),
                ', '
            ) as campaign_id,
            os,
            array_join(
                array_distinct(array_agg(coalesce(country_code_a2, region))),
                ', '
            ) as country,
            'Android' as campaign_name
        from
            experimental.history_dim_campaign dc
        where
            partition_0 between '%begin_date'
            and '%end_date_targeting'
            and os = 'ANDROID'
            and bundle_identifier in ('%bundle_a', '%bundle_i') %campaign_ids_dc
        group by
            1,
            3,
            5
        union all
        select
            partition_0,
            array_join(
                array_distinct(array_agg(cast(campaign_id as varchar))),
                ', '
            ) as campaign_id,
            os,
            array_join(
                array_distinct(array_agg(coalesce(country_code_a2, region))),
                ', '
            ) as country,
            'IOS' as campaign_name
        from
            experimental.history_dim_campaign dc
        where
            partition_0 between '%begin_date'
            and '%end_date_targeting'
            and os = 'IOS'
            and bundle_identifier in ('%bundle_a', '%bundle_i') %campaign_ids_dc
        group by
            1,
            3,
            5
    )