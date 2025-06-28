-- -- SQLite
-- SELECT id, airfield_code, date, created_at
-- FROM airfield_reports
-- where airfield_code = 'EKBH'
-- ORDER BY created_at DESC;

-- select * 
-- from flights
-- where max_height = 323
-- ;

-- select device_address, start_tsp, stop_tsp, count(*) as n
-- from flights
-- group by device_address, start_tsp, stop_tsp
-- order by n desc
-- ;

--     DELETE FROM flights
--     WHERE id NOT IN (
--         SELECT MAX(id)
--         FROM flights
--         GROUP BY device_address, start_tsp, stop_tsp
--         )

delete from airfield_reports;
delete from devices;
delete from flights;
delete from igc_files;
