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

ALTER TABLE scheduled RENAME TO old_scheduled;

CREATE TABLE scheduled (
    id SERIAL PRIMARY KEY,
    term_id INTEGER NOT NULL,
    section_id INTEGER NOT NULL,
    kaltura_schedule_id INTEGER NOT NULL,
    course_display_name VARCHAR(255) NOT NULL,
    instructor_uids VARCHAR(80)[] NOT NULL,
    collaborator_uids VARCHAR(80)[],
    room_id INTEGER NOT NULL,
    meeting_days VARCHAR(80) NOT NULL,
    meeting_start_date TIMESTAMP NOT NULL,
    meeting_start_time VARCHAR(80) NOT NULL,
    meeting_end_date TIMESTAMP NOT NULL,
    meeting_end_time VARCHAR(80) NOT NULL,
    publish_type publish_types NOT NULL,
    recording_type recording_types NOT NULL,
    alerts email_template_types[],
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE
);
CREATE INDEX scheduled_term_id_section_id_idx ON scheduled (term_id, section_id);
ALTER TABLE ONLY scheduled
    ADD CONSTRAINT scheduled_room_id_fkey FOREIGN KEY (room_id) REFERENCES rooms(id);

INSERT INTO scheduled (id, term_id, section_id, kaltura_schedule_id, course_display_name, instructor_uids, room_id, meeting_days, meeting_start_date, meeting_start_time, meeting_end_date, meeting_end_time, publish_type, recording_type, alerts, created_at, deleted_at)
SELECT id, term_id, section_id, kaltura_schedule_id, course_display_name, instructor_uids, room_id, meeting_days, meeting_start_date, meeting_start_time, meeting_end_date, meeting_end_time, publish_type, recording_type, alerts, created_at, deleted_at FROM old_scheduled;

DROP TABLE old_scheduled;
