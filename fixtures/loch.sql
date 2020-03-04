DROP SCHEMA IF EXISTS sis_data cascade;

CREATE SCHEMA sis_data;

CREATE TABLE sis_data.sis_sections
(
  allowed_units VARCHAR NOT NULL,
  instructor_role_code VARCHAR NOT NULL,
  instructor_uid VARCHAR NOT NULL,
  is_primary BOOLEAN NOT NULL,
  meeting_days VARCHAR NOT NULL,
  meeting_end_date VARCHAR NOT NULL,
  meeting_end_time VARCHAR NOT NULL,
  meeting_location VARCHAR NOT NULL,
  meeting_start_date VARCHAR NOT NULL,
  meeting_start_time VARCHAR NOT NULL,
  sis_course_name VARCHAR NOT NULL,
  sis_course_title VARCHAR NOT NULL,
  sis_instruction_format VARCHAR NOT NULL,
  sis_section_id VARCHAR NOT NULL,
  sis_section_num VARCHAR NOT NULL,
  sis_term_id VARCHAR NOT NULL
);

INSERT INTO sis_data.sis_sections
(
  allowed_units,
  instructor_role_code,
  instructor_uid,
  is_primary,
  meeting_days,
  meeting_end_date,
  meeting_end_time,
  meeting_location,
  meeting_start_date,
  meeting_start_time,
  sis_course_name,
  sis_course_title,
  sis_instruction_format,
  sis_section_id,
  sis_section_num,
  sis_term_id
)
VALUES
('4.0', 'PI', '8765432', true, 'TUTH', '2020-05-08 00:00:00 UTC', '10:59', 'Barrows 60', '2020-01-21 00:00:00 UTC', '10:00', 'COMPSCI C8', 'Foundations of Data Science', 'LEC', '28602', '001', '2202'),
('4.0', 'PI', '8765432', true, 'MOWEFR', '2020-05-08 00:00:00 UTC', '15:59', 'Wheeler 150', '2020-01-21 00:00:00 UTC', '15:00', 'COMPSCI 61B', 'Data Structures', 'LEC', '28165', '001', '2202')
