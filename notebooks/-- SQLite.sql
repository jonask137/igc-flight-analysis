-- -- SQLite
-- SELECT id, airfield_code, date, created_at
-- FROM airfield_reports
-- where airfield_code = 'EKBH'
-- ORDER BY created_at DESC;

-- select * 
-- from flights
-- where device_address = 'D01EFB'
-- ;

select *
from flights
order by report_id desc