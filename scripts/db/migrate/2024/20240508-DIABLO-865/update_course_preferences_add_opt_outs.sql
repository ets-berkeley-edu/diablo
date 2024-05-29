/**
 * Copyright ©2024. The Regents of the University of California (Regents). All Rights Reserved.
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

ALTER TABLE course_preferences DROP COLUMN can_aprx_instructors_edit_recordings;
ALTER TABLE course_preferences ADD COLUMN collaborator_uids VARCHAR(80)[];
ALTER TABLE course_preferences ADD COLUMN publish_type publish_types;
ALTER TABLE course_preferences ADD COLUMN recording_type recording_types;
ALTER TABLE course_preferences ADD COLUMN canvas_site_id INTEGER;
UPDATE course_preferences SET publish_type = 'kaltura_my_media';
UPDATE course_preferences SET recording_type = 'presenter_presentation_audio';
ALTER TABLE course_preferences ALTER COLUMN publish_type SET NOT NULL;
ALTER TABLE course_preferences ALTER COLUMN recording_type SET NOT NULL;


CREATE TABLE opt_outs (
    id INTEGER NOT NULL,
    instructor_uid VARCHAR(80) NOT NULL,
    term_id INTEGER,
    section_id INTEGER,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL
);
CREATE SEQUENCE opt_outs_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE opt_outs_id_seq OWNED BY opt_outs.id;
ALTER TABLE ONLY opt_outs ALTER COLUMN id SET DEFAULT nextval('opt_outs_id_seq'::regclass);
ALTER TABLE ONLY opt_outs
    ADD CONSTRAINT opt_outs_pkey PRIMARY KEY (id);
