/**
 * Copyright ©2021. The Regents of the University of California (Regents). All Rights Reserved.
 *
 * Permission to use, copy, modify, and distribute this software and its documentation
 * for educational, research, and not-for-profit purposes, without fee and without a
 * signed licensing agreement, is hereby granted, provided that the above copyright
 * notice, this paragraph and the following two paragraphs appear in all copies,
 * modifications, and distributions.
 *
 * Contact The Office of Technology Licensing, UC Berkeley, 2150 Shattuck Avenue,
 * Suite 510, Berkeley, CA 94720-1620, (510) 643-7201, otl@berkeley.edu,
 * http://ipira.berkeley.edu/industry-info for commercial licensing opportunities.
 *
 * IN NO EVENT SHALL REGENTS BE LIABLE TO ANY PARTY FOR DIRECT, INDIRECT, SPECIAL,
 * INCIDENTAL, OR CONSEQUENTIAL DAMAGES, INCLUDING LOST PROFITS, ARISING OUT OF
 * THE USE OF THIS SOFTWARE AND ITS DOCUMENTATION, EVEN IF REGENTS HAS BEEN ADVISED
 * OF THE POSSIBILITY OF SUCH DAMAGE.
 *
 * REGENTS SPECIFICALLY DISCLAIMS ANY WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE. THE
 * SOFTWARE AND ACCOMPANYING DOCUMENTATION, IF ANY, PROVIDED HEREUNDER IS PROVIDED
 * "AS IS". REGENTS HAS NO OBLIGATION TO PROVIDE MAINTENANCE, SUPPORT, UPDATES,
 * ENHANCEMENTS, OR MODIFICATIONS.
 */

CREATE TABLE tmp_sis_sections AS SELECT * FROM sis_sections WHERE term_id = '{term_id}';

DELETE FROM sis_sections WHERE term_id = '{term_id}';

--

INSERT INTO sis_sections (allowed_units, course_name, course_title, instruction_format, instructor_name,
                          instructor_role_code, instructor_uid, is_primary, meeting_days, meeting_end_date,
                          meeting_end_time, meeting_location, meeting_start_date, meeting_start_time, section_id,
                          section_num, term_id)
   (SELECT * FROM dblink('{data_loch_dblink}',$REDSHIFT$
    SELECT
       allowed_units, sis_course_name, sis_course_title, sis_instruction_format, instructor_name, instructor_role_code,
       instructor_uid, is_primary, meeting_days, meeting_end_date::TIMESTAMP, meeting_end_time, meeting_location,
       meeting_start_date::TIMESTAMP, meeting_start_time, sis_section_id::INTEGER, sis_section_num, sis_term_id::INTEGER
    FROM {data_loch_sis_schema}.sis_sections
    WHERE sis_term_id='{term_id}'
  $REDSHIFT$)
  AS data_loch_sis_sections (
    allowed_units DOUBLE PRECISION,
    course_name VARCHAR(80),
    course_title TEXT,
    instruction_format VARCHAR(80),
    instructor_name TEXT,
    instructor_role_code VARCHAR(80),
    instructor_uid VARCHAR(80),
    is_primary BOOLEAN,
    meeting_days VARCHAR(80),
    meeting_end_date TIMESTAMP,
    meeting_end_time VARCHAR(80),
    meeting_location VARCHAR(80),
    meeting_start_date TIMESTAMP,
    meeting_start_time VARCHAR(80),
    section_id INTEGER,
    section_num VARCHAR(80),
    term_id INTEGER
  )
);

-- Our source data may use blank spaces for UIDs that should be null.
UPDATE sis_sections SET instructor_uid = NULL WHERE instructor_uid = '';

-- Restore deleted sections, with deleted_at set to now().
INSERT INTO sis_sections (allowed_units, course_name, course_title, deleted_at, instruction_format, instructor_name,
                          instructor_role_code, instructor_uid, is_primary, meeting_days, meeting_end_date,
                          meeting_end_time, meeting_location, meeting_start_date, meeting_start_time, section_id,
                          section_num, term_id)
(
  SELECT
    t.allowed_units, t.course_name, t.course_title, now(), t.instruction_format, t.instructor_name,
    t.instructor_role_code, t.instructor_uid, t.is_primary, t.meeting_days, t.meeting_end_date, t.meeting_end_time,
    t.meeting_location, t.meeting_start_date, t.meeting_start_time, t.section_id, t.section_num, t.term_id
  FROM tmp_sis_sections t
  LEFT JOIN sis_sections s2 ON s2.section_id = t.section_id AND s2.term_id = t.term_id
  WHERE t.term_id = {term_id} AND s2.section_id IS NULL AND s2.term_id IS NULL
);

DROP TABLE tmp_sis_sections;
