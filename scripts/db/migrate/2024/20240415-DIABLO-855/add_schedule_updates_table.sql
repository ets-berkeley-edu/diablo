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

CREATE TYPE schedule_update_status_types AS ENUM (
    'queued',
    'succeeded',
    'errored'
);

CREATE TABLE schedule_updates (
    id INTEGER NOT NULL,
    term_id INTEGER NOT NULL,
    section_id INTEGER NOT NULL,
    field_name VARCHAR(80) NOT NULL,
    field_value_old VARCHAR,
    field_value_new VARCHAR,
    kaltura_schedule_id INTEGER,
    requested_by_uid VARCHAR(80),
    requested_by_name VARCHAR,
    status schedule_update_status_types NOT NULL,
    requested_at TIMESTAMP WITH TIME ZONE NOT NULL,
    published_at TIMESTAMP WITH TIME ZONE
);
CREATE SEQUENCE schedule_updates_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER TABLE ONLY schedule_updates ALTER COLUMN id SET DEFAULT nextval('schedule_updates_id_seq'::regclass);
ALTER TABLE ONLY schedule_updates
    ADD CONSTRAINT schedule_updates_pkey PRIMARY KEY (id);
ALTER TABLE schedule_updates ALTER COLUMN requested_at SET DEFAULT now();

CREATE INDEX schedule_updates_status_idx ON schedule_updates USING btree (status);
CREATE INDEX schedule_updates_term_id_section_id_idx ON schedule_updates(term_id, section_id);
