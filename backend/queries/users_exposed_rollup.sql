select
    *
from
    (
        select
            u.date,
            u.campaign_id,
            u.device_id,
            'exposed' as variant
        from
            bi_sandbox.temp_table_%uplift_key_users u
            inner join exposed e on u.campaign_id = e.campaign_id
            and e.device_id = u.device_id
        union all
        select
            *
        from
            users
    )