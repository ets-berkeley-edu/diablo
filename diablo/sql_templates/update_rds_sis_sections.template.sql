/**
 * Copyright ©2020. The Regents of the University of California (Regents). All Rights Reserved.
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

DELETE FROM sis_sections WHERE term_id = '{term_id}';

--

INSERT INTO sis_sections (allowed_units, course_name, course_title, instruction_format, instructor_name,
                          instructor_role_code, instructor_uid, is_primary, meeting_days, meeting_end_date,
                          meeting_end_time, meeting_location, meeting_start_date, meeting_start_time, section_id,
                          section_num, term_id)
   (SELECT * FROM dblink('{rds_dblink_to_redshift}',$REDSHIFT$
    SELECT
       allowed_units, course_display_name, course_title, instruction_format, instructor_name, instructor_role_code,
       instructor_uid, is_primary::BOOLEAN, meeting_days, meeting_end_date::TIMESTAMP, meeting_end_time, meeting_location,
       meeting_start_date::TIMESTAMP, meeting_start_time, section_id::INTEGER, section_num, term_id::INTEGER
    FROM {redshift_schema_sis}.courses
    WHERE term_id='{term_id}'
  $REDSHIFT$)
  AS redshift_sis_sections (
    allowed_units DOUBLE PRECISION,
    course_name VARCHAR(80),
    course_title TEXT,
    instruction_format VARCHAR(80),
    instructor_name TEXT,
    instructor_role_code VARCHAR(80),
    instructor_uid VARCHAR(80),
    is_primary BOOLEAN,
    meeting_days VARCHAR(80),
    meeting_end_date VARCHAR(80),
    meeting_end_time VARCHAR(80),
    meeting_location VARCHAR(80),
    meeting_start_date VARCHAR(80),
    meeting_start_time VARCHAR(80),
    section_id INTEGER,
    section_num VARCHAR(80),
    term_id INTEGER
  )
);

-- Our source data may use blank spaces for UIDs that should be null.
UPDATE sis_sections SET instructor_uid = NULL WHERE instructor_uid = '';
