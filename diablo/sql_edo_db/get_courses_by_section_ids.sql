SELECT
    DISTINCT s."id" AS section_id,
    c."academicDepartment-descr" as dept_description,
    c."catalogNumber-formatted" AS catalog_id,
    c."subjectArea" AS dept_name,
    c."title" AS course_title,
    m."endTime" AS end_time,
    m."location-descr" AS location,
    m."meetsDays" AS days_of_week,
    m."startTime" AS start_time,
    s."component-code" AS instruction_format,
    s."displayName" AS display_name,
    s."sectionNumber" AS section_num
FROM SISEDO.MEETINGV00_VW m
    JOIN SISEDO.CLASSSECTIONALLV01_MVW s ON (
        m."cs-course-id" = s."cs-course-id" AND
        m."offeringNumber" = s."offeringNumber" AND
        m."sectionNumber" = s."sectionNumber" AND
        m."session-id" = s."session-id" AND
        m."term-id" = s."term-id"
    )
    JOIN SISEDO.ENROLLMENT_UIDV00_VW e ON (
        e."CLASS_SECTION_ID" = s."id" AND
        e."SESSION_ID" = s."session-id" AND
        e."TERM_ID" = s."term-id" AND
        s."status-code" = 'A'
    )
    LEFT OUTER JOIN SISEDO.DISPLAYNAMEXLATV01_MVW xlat ON (xlat."classDisplayName" = s."displayName")
    LEFT OUTER JOIN SISEDO.API_COURSEV01_MVW c ON (xlat."courseDisplayName" = c."displayName" AND c."status-code" = 'ACTIVE')
WHERE
    s."id" IN (:section_ids)
    AND m."endTime" != '00:00'
    AND m."endTime" IS NOT NULL
    AND m."location-descr" IS NOT NULL
    AND m."meetsDays" != 'SA'
    AND m."meetsDays" IS NOT NULL
    AND m."startDate" != m."endDate"
    AND m."startTime" != '00:00'
    AND m."startTime" IS NOT NULL
    AND s."primary" = 'true'
    AND s."term-id" = :term_id
    AND s."printInScheduleOfClasses" = 'Y'
ORDER BY s."displayName"
