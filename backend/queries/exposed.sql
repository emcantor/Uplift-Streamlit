select
    distinct affiliation.campaignid as campaign_id,
    generic.device.ifa.plain as device_id
from
    impressions
where
    dt between '%begin_date'
    and '%end_date_targeting'
    and generic.bundleidentifier in ('%bundle_a', '%bundle_i') %campaign_ids_e