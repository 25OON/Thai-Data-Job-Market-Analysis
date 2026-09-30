SELECT * FROM jobthai.jobs_staging;

-- 1. Job Title
SELECT job_title
FROM jobthai.jobs_staging
GROUP BY job_title
ORDER BY job_title;

ALTER TABLE jobthai.jobs_staging
ADD COLUMN job_title_clean VARCHAR(255);

SET SQL_SAFE_UPDATES = 0;

-- trim
UPDATE jobthai.jobs_staging
SET job_title_clean = TRIM(job_title);

SELECT job_title_clean
FROM jobthai.jobs_staging
GROUP BY job_title_clean
ORDER BY job_title_clean;

-- Categorized
UPDATE jobthai.jobs_staging
SET job_title_clean = CASE
        WHEN job_title LIKE '%scientist%'                       THEN 'Data Scientist'
        WHEN job_title LIKE '%data engineer%'
          OR job_title LIKE '%data enineer%'                    THEN 'Data Engineer'
        WHEN job_title LIKE '%analyst%'
          OR job_title LIKE '%analytics%'
          OR job_title LIKE '%data analysis%'
          OR job_title LIKE '%business intelligence%'           THEN 'Data Analyst'
        WHEN job_title LIKE '%database%'
          OR job_title LIKE '%DBA%'                             THEN 'Database Administrator'
        ELSE 'Other'
    END;
-- check
SELECT job_title, job_title_clean
FROM jobthai.jobs_staging
ORDER BY job_title_clean;

-- 2. Salary

SELECT salary, COUNT(*) AS jobs
FROM jobthai.jobs_staging
GROUP BY salary
ORDER BY jobs DESC;

ALTER TABLE jobthai.jobs_staging
ADD COLUMN salary_type VARCHAR(20),
ADD COLUMN salary_min INT,
ADD COLUMN salary_max INT;

UPDATE jobthai.jobs_staging
SET salary_type = CASE
        WHEN salary LIKE '%(Daily)%'                   THEN 'daily'
        WHEN salary REGEXP '^[0-9,]+ - [0-9,]+ THB$'   THEN 'range'
        WHEN salary REGEXP '^[0-9,]+ THB$'             THEN 'fixed'
        ELSE 'not_specified'
    END;
    
UPDATE jobthai.jobs_staging
SET salary_min = REPLACE(REGEXP_SUBSTR(salary, '[0-9][0-9,]*', 1, 1), ',', ''),
    salary_max = REPLACE(COALESCE(REGEXP_SUBSTR(salary, '[0-9][0-9,]*', 1, 2),
                                  REGEXP_SUBSTR(salary, '[0-9][0-9,]*', 1, 1)), ',', '')
WHERE salary_type <> 'not_specified';

SELECT salary, salary_type, salary_min, salary_max
FROM jobthai.jobs_staging
ORDER BY salary_type, salary_min;

-- Analysis
SELECT job_title_clean,
       COUNT(*)                AS jobs,
       ROUND(AVG(salary_min))  AS avg_min,
       ROUND(AVG(salary_max))  AS avg_max
FROM jobthai.jobs_staging
WHERE salary_type IN ('range', 'fixed')     -- monthly salaries only
GROUP BY job_title_clean
ORDER BY jobs DESC;

-- 3.location

ALTER TABLE jobthai.jobs_staging
ADD COLUMN district VARCHAR(100),
ADD COLUMN province VARCHAR(100),
ADD COLUMN transit_station VARCHAR(255);

UPDATE jobthai.jobs_staging
SET transit_station = location,
    province = 'Bangkok'
WHERE location_is_transit = 'TRUE';

UPDATE jobthai.jobs_staging
SET district = CASE
                   WHEN location LIKE '%,%' THEN TRIM(SUBSTRING_INDEX(location, ',', 1))
                   ELSE NULL
               END,
    province = TRIM(SUBSTRING_INDEX(location, ',', -1))
WHERE location_is_transit = 'FALSE';
-- check
SELECT location, location_is_transit, district, province, transit_station
FROM jobthai.jobs_staging
ORDER BY location_is_transit, province;
-- job & province analysis
SELECT province, COUNT(*) AS jobs
FROM jobthai.jobs_staging
GROUP BY province
ORDER BY jobs DESC;

-- 4. date
UPDATE jobthai.jobs_staging
SET posted_date = STR_TO_DATE(posted_date, '%d-%b-%y');

ALTER TABLE jobthai.jobs_staging
MODIFY COLUMN posted_date DATE;

SELECT posted_date FROM jobthai.jobs_staging LIMIT 10;

SELECT * FROM jobthai.jobs_staging;