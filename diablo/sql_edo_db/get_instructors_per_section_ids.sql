SELECT
    DISTINCT i."campus-uid" AS ldap_uid,
    s."id" AS section_id,
    i."emailAddress" AS email_address,
    i."givenName" AS first_name,
    i."familyName" AS last_name,
    c."academicDepartment-descr" AS dept_description
FROM SISEDO.ASSIGNEDINSTRUCTORV00_VW i
JOIN SISEDO.CLASSSECTIONALLV01_MVW s ON (
    i."term-id" = s."term-id" AND
    i."session-id" = s."session-id" AND
    i."cs-course-id" = s."cs-course-id" AND
    i."offeringNumber" = s."offeringNumber" AND
    i."number" = s."sectionNumber"
)
LEFT OUTER JOIN SISEDO.DISPLAYNAMEXLATV01_MVW x ON (x."classDisplayName" = s."displayName")
LEFT OUTER JOIN SISEDO.API_COURSEV01_MVW c ON (x."courseDisplayName" = c."displayName" AND c."status-code" = 'ACTIVE')
WHERE
    i."term-id" = :term_id
    AND s."id" IN (:section_ids)
    AND i."role-code" IN ('ICNT', 'PI', 'TNIC')
    AND i."campus-uid" IS NOT NULL
    AND i."emailAddress" IS NOT NULL
    AND i."familyName" IS NOT NULL
