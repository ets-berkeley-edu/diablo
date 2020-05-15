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

BEGIN;

CREATE TYPE job_schedule_types AS ENUM (
    'day_at',
    'minutes',
    'seconds'
);

CREATE TABLE jobs (
    id INTEGER NOT NULL,
    disabled BOOLEAN NOT NULL,
    job_schedule_type job_schedule_types NOT NULL,
    job_schedule_value VARCHAR(80) NOT NULL,
    key VARCHAR(80) NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);
ALTER TABLE jobs OWNER TO app_diablo;
CREATE SEQUENCE jobs_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER TABLE jobs_id_seq OWNER TO app_diablo;
ALTER SEQUENCE jobs_id_seq OWNED BY jobs.id;
ALTER TABLE ONLY jobs ALTER COLUMN id SET DEFAULT nextval('jobs_id_seq'::regclass);
ALTER TABLE ONLY jobs
    ADD CONSTRAINT jobs_pkey PRIMARY KEY (id);
ALTER TABLE ONLY jobs
    ADD CONSTRAINT jobs_key_unique_constraint UNIQUE (key);

-- Migrate data out of py config file

INSERT INTO jobs
    (disabled, job_schedule_type, job_schedule_value, key, created_at, updated_at)
VALUES
    (False, 'minutes', '120', 'admin_emails', now(), now()),
    (False, 'day_at', '06:00', 'canvas', now(), now()),
    (False, 'day_at', '09:00', 'sis_data_refresh', now(), now()),
    (False, 'minutes', '60', 'instructor_emails', now(), now()),
    (False, 'minutes', '120', 'kaltura', now(), now()),
    (False, 'minutes', '15', 'queued_emails', now(), now());

COMMIT;
