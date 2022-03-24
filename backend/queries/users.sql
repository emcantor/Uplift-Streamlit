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