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

DROP TABLE IF EXISTS sis_sections CASCADE;

CREATE TABLE IF NOT EXISTS sis_sections
(
    id INTEGER NOT NULL,
    sis_term_id INTEGER,
    sis_section_id INTEGER,
    is_primary BOOLEAN,
    sis_course_name VARCHAR(80),
    sis_course_title TEXT,
    sis_instruction_format VARCHAR(80),
    sis_section_num VARCHAR(80),
    allowed_units DOUBLE PRECISION,
    instructor_uid VARCHAR(80),
    instructor_name TEXT,
    instructor_role_code VARCHAR(80),
    meeting_location VARCHAR(80),
    meeting_days VARCHAR(80),
    meeting_start_time VARCHAR(80),
    meeting_end_time VARCHAR(80),
    meeting_start_date VARCHAR(80),
    meeting_end_date VARCHAR(80),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL
);
ALTER TABLE sis_sections OWNER TO diablo;
CREATE SEQUENCE sis_sections_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER TABLE sis_sections_id_seq OWNER TO diablo;
ALTER SEQUENCE sis_sections_id_seq OWNED BY sis_sections.id;
ALTER TABLE ONLY sis_sections ALTER COLUMN id SET DEFAULT nextval('sis_sections_id_seq'::regclass);
ALTER TABLE ONLY sis_sections
    ADD CONSTRAINT sis_sections_pkey PRIMARY KEY (id);
ALTER TABLE sis_sections ALTER COLUMN created_at SET DEFAULT now();

--

INSERT INTO sis_sections (
  SELECT *
  FROM dblink('{rds_dblink_to_redshift}',$REDSHIFT$
    SELECT sis_term_id::INTEGER, sis_section_id::INTEGER, is_primary, sis_course_name, sis_course_title,
      sis_instruction_format, sis_section_num, allowed_units, instructor_uid, instructor_name, instructor_role_code,
      meeting_location, meeting_days, meeting_start_time, meeting_end_time, meeting_start_date, meeting_end_date
    FROM {redshift_schema_intermediate}.sis_sections
  $REDSHIFT$)
  AS redshift_sis_sections (
    sis_term_id INTEGER,
    sis_section_id INTEGER,
    is_primary BOOLEAN,
    sis_course_name VARCHAR(80),
    sis_course_title TEXT,
    sis_instruction_format VARCHAR(80),
    sis_section_num VARCHAR(80),
    allowed_units DOUBLE PRECISION,
    instructor_uid VARCHAR(80),
    instructor_name TEXT,
    instructor_role_code VARCHAR(80),
    meeting_location VARCHAR(80),
    meeting_days VARCHAR(80),
    meeting_start_time VARCHAR(80),
    meeting_end_time VARCHAR(80),
    meeting_start_date VARCHAR(80),
    meeting_end_date VARCHAR(80)
  )
);

CREATE INDEX sis_sections_term_id_section_id_idx ON sis_sections(sis_term_id, sis_section_id);
CREATE INDEX sis_sections_instructor_uid_idx ON sis_sections USING btree (instructor_uid);
CREATE INDEX sis_sections_meeting_location_idx ON sis_sections USING btree (meeting_location);

--
