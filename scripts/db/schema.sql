/**
 * Copyright ©2023. The Regents of the University of California (Regents). All Rights Reserved.
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

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;
SET search_path = public, pg_catalog;
SET default_tablespace = '';
SET default_with_oids = false;


--

CREATE TYPE approver_types AS ENUM (
    'admin',
    'instructor'
);

--

CREATE TYPE email_template_types AS ENUM (
    'admin_alert_date_change',
    'admin_alert_instructor_change',
    'admin_alert_multiple_meeting_patterns',
    'admin_alert_room_change',
    'invitation',
    'notify_instructor_of_changes',
    'recordings_scheduled',
    'room_change_no_longer_eligible',
    'waiting_for_approval'
);

--

CREATE TYPE job_schedule_types AS ENUM (
    'day_at',
    'minutes',
    'seconds'
);

--

CREATE TYPE publish_types AS ENUM (
    'kaltura_media_gallery',
    'kaltura_my_media'
);

--

CREATE TYPE recording_types AS ENUM (
    'presentation_audio',
    'presenter_audio',
    'presenter_presentation_audio',
    'presenter_presentation_audio_with_operator'
);

--

CREATE TYPE room_capability_types AS ENUM (
    'screencast',
    'screencast_and_video'
);

--

CREATE TABLE admin_users (
    id integer NOT NULL,
    uid character varying(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE
);
ALTER TABLE admin_users OWNER TO diablo;
CREATE SEQUENCE admin_users_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER TABLE admin_users_id_seq OWNER TO diablo;
ALTER SEQUENCE admin_users_id_seq OWNED BY admin_users.id;
ALTER TABLE ONLY admin_users ALTER COLUMN id SET DEFAULT nextval('admin_users_id_seq'::regclass);
ALTER TABLE ONLY admin_users
    ADD CONSTRAINT admin_users_pkey PRIMARY KEY (id);
ALTER TABLE ONLY admin_users
    ADD CONSTRAINT admin_users_uid_key UNIQUE (uid);

--

CREATE TABLE approvals (
    id SERIAL PRIMARY KEY,
    approved_by_uid VARCHAR(80) NOT NULL,
    approver_type approver_types,
    course_display_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE,
    publish_type publish_types NOT NULL,
    recording_type recording_types NOT NULL,
    room_id INTEGER NOT NULL,
    section_id INTEGER NOT NULL,
    term_id INTEGER NOT NULL
);
ALTER TABLE approvals OWNER TO diablo;
CREATE UNIQUE INDEX approvals_unique_idx ON approvals (approved_by_uid, section_id, term_id) WHERE deleted_at IS NULL;

--

CREATE TABLE blackouts (
    id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    end_date TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);
ALTER TABLE blackouts OWNER TO diablo;
CREATE SEQUENCE blackouts_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER TABLE blackouts_id_seq OWNER TO diablo;
ALTER SEQUENCE blackouts_id_seq OWNED BY blackouts.id;
ALTER TABLE ONLY blackouts ALTER COLUMN id SET DEFAULT nextval('blackouts_id_seq'::regclass);
ALTER TABLE ONLY blackouts
    ADD CONSTRAINT blackouts_pkey PRIMARY KEY (id);
ALTER TABLE ONLY blackouts
    ADD CONSTRAINT blackouts_name_unique_constraint UNIQUE (name);

--

CREATE TABLE canvas_course_sites (
    canvas_course_site_id INTEGER NOT NULL,
    section_id INTEGER NOT NULL,
    term_id INTEGER NOT NULL,
    canvas_course_site_name TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL
);
ALTER TABLE canvas_course_sites OWNER TO diablo;
ALTER TABLE canvas_course_sites ADD CONSTRAINT canvas_course_sites_pkey PRIMARY KEY (canvas_course_site_id, section_id, term_id);

--

CREATE TABLE course_preferences (
    term_id INTEGER NOT NULL,
    section_id INTEGER NOT NULL,
    can_aprx_instructors_edit_recordings BOOLEAN DEFAULT FALSE NOT NULL,
    has_opted_out BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL
);
ALTER TABLE course_preferences OWNER TO diablo;
ALTER TABLE course_preferences ADD CONSTRAINT course_preferences_pkey PRIMARY KEY (section_id, term_id);

--

CREATE TABLE cross_listings (
    term_id INTEGER NOT NULL,
    section_id INTEGER NOT NULL,
    cross_listed_section_ids INTEGER[] NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL
);
ALTER TABLE cross_listings OWNER TO diablo;
ALTER TABLE cross_listings ADD CONSTRAINT cross_listings_pkey PRIMARY KEY (section_id, term_id);

--

CREATE TABLE email_templates (
    id INTEGER NOT NULL,
    template_type email_template_types NOT NULL,
    name VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    subject_line VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);
ALTER TABLE email_templates OWNER TO diablo;
CREATE SEQUENCE email_templates_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER TABLE email_templates_id_seq OWNER TO diablo;
ALTER SEQUENCE email_templates_id_seq OWNED BY email_templates.id;
ALTER TABLE ONLY email_templates ALTER COLUMN id SET DEFAULT nextval('email_templates_id_seq'::regclass);
ALTER TABLE ONLY email_templates
    ADD CONSTRAINT email_templates_pkey PRIMARY KEY (id);
ALTER TABLE ONLY email_templates
    ADD CONSTRAINT email_templates_name_unique_constraint UNIQUE (name);

--

CREATE TABLE instructors (
    uid character varying(255) NOT NULL,
    dept_code VARCHAR(80),
    email VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);
ALTER TABLE instructors OWNER TO diablo;
ALTER TABLE ONLY instructors
    ADD CONSTRAINT instructors_pkey PRIMARY KEY (uid);

--

CREATE TABLE job_history (
    id INTEGER NOT NULL,
    job_key VARCHAR(80) NOT NULL,
    failed BOOLEAN DEFAULT FALSE,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    finished_at TIMESTAMP WITH TIME ZONE
);
ALTER TABLE job_history OWNER TO diablo;
CREATE SEQUENCE job_history_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER TABLE job_history_id_seq OWNER TO diablo;
ALTER SEQUENCE job_history_id_seq OWNED BY job_history.id;
ALTER TABLE ONLY job_history ALTER COLUMN id SET DEFAULT nextval('job_history_id_seq'::regclass);
ALTER TABLE ONLY job_history
    ADD CONSTRAINT job_history_pkey PRIMARY KEY (id);

--

CREATE TABLE job_runner (
    ec2_instance_id VARCHAR(80) NOT NULL
);

--

CREATE TABLE jobs (
    id INTEGER NOT NULL,
    disabled BOOLEAN NOT NULL,
    is_schedulable BOOLEAN NOT NULL,
    job_schedule_type job_schedule_types NOT NULL,
    job_schedule_value VARCHAR(80) NOT NULL,
    key VARCHAR(80) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);
ALTER TABLE jobs OWNER TO diablo;
CREATE SEQUENCE jobs_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER TABLE jobs_id_seq OWNER TO diablo;
ALTER SEQUENCE jobs_id_seq OWNED BY jobs.id;
ALTER TABLE ONLY jobs ALTER COLUMN id SET DEFAULT nextval('jobs_id_seq'::regclass);
ALTER TABLE ONLY jobs
    ADD CONSTRAINT jobs_pkey PRIMARY KEY (id);
ALTER TABLE ONLY jobs
    ADD CONSTRAINT jobs_key_unique_constraint UNIQUE (key);

--

CREATE TABLE queued_emails (
    id INTEGER NOT NULL,
    subject_line VARCHAR(255),
    message TEXT,
    recipient JSONB,
    section_id INTEGER NOT NULL,
    template_type email_template_types,
    term_id INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL
);
ALTER TABLE queued_emails OWNER TO diablo;
CREATE SEQUENCE queued_emails_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER TABLE queued_emails_id_seq OWNER TO diablo;
ALTER SEQUENCE queued_emails_id_seq OWNED BY queued_emails.id;
ALTER TABLE ONLY queued_emails ALTER COLUMN id SET DEFAULT nextval('queued_emails_id_seq'::regclass);
ALTER TABLE ONLY queued_emails
    ADD CONSTRAINT queued_emails_pkey PRIMARY KEY (id);

--

CREATE TABLE rooms (
    id INTEGER NOT NULL,
    capability room_capability_types,
    is_auditorium BOOLEAN NOT NULL,
    kaltura_resource_id INTEGER,
    location VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL
);
ALTER TABLE rooms OWNER TO diablo;
CREATE SEQUENCE rooms_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER TABLE rooms_id_seq OWNER TO diablo;
ALTER SEQUENCE rooms_id_seq OWNED BY rooms.id;
ALTER TABLE ONLY rooms ALTER COLUMN id SET DEFAULT nextval('rooms_id_seq'::regclass);
ALTER TABLE ONLY rooms
    ADD CONSTRAINT rooms_pkey PRIMARY KEY (id);
ALTER TABLE ONLY rooms
    ADD CONSTRAINT rooms_location_unique_constraint UNIQUE (location);
CREATE INDEX rooms_location_idx ON rooms USING btree (location);

--

CREATE TABLE scheduled (
    id SERIAL PRIMARY KEY,
    alerts email_template_types[],
    course_display_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE,
    instructor_uids VARCHAR(80)[] NOT NULL,
    kaltura_schedule_id INTEGER NOT NULL,
    meeting_days VARCHAR(80) NOT NULL,
    meeting_end_date TIMESTAMP NOT NULL,
    meeting_end_time VARCHAR(80) NOT NULL,
    meeting_start_date TIMESTAMP NOT NULL,
    meeting_start_time VARCHAR(80) NOT NULL,
    publish_type publish_types NOT NULL,
    recording_type recording_types NOT NULL,
    room_id INTEGER NOT NULL,
    section_id INTEGER NOT NULL,
    term_id INTEGER NOT NULL
);
ALTER TABLE scheduled OWNER TO diablo;
CREATE UNIQUE INDEX scheduled_unique_idx ON scheduled (section_id, term_id) WHERE deleted_at IS NULL;

--

CREATE TABLE sent_emails (
    id INTEGER NOT NULL,
    recipient_uid VARCHAR(80) NOT NULL,
    section_id INTEGER,
    template_type email_template_types,
    term_id INTEGER NOT NULL,
    sent_at TIMESTAMP WITH TIME ZONE NOT NULL
);
ALTER TABLE sent_emails OWNER TO diablo;
CREATE SEQUENCE sent_emails_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER TABLE sent_emails_id_seq OWNER TO diablo;
ALTER SEQUENCE sent_emails_id_seq OWNED BY sent_emails.id;
ALTER TABLE ONLY sent_emails ALTER COLUMN id SET DEFAULT nextval('sent_emails_id_seq'::regclass);
ALTER TABLE ONLY sent_emails
    ADD CONSTRAINT sent_emails_pkey PRIMARY KEY (id);
CREATE INDEX sent_emails_section_id_idx ON sent_emails USING btree (section_id);

--

CREATE TABLE sis_sections (
    id INTEGER NOT NULL,
    allowed_units VARCHAR(80),
    course_name VARCHAR(80),
    course_title TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE,
    instruction_format VARCHAR(80),
    instructor_name TEXT,
    instructor_role_code VARCHAR(80),
    instructor_uid VARCHAR(80),
    is_primary BOOLEAN,
    is_principal_listing BOOLEAN DEFAULT TRUE NOT NULL,
    meeting_days VARCHAR(80),
    meeting_end_date TIMESTAMP,
    meeting_end_time VARCHAR(80),
    meeting_location VARCHAR(80),
    meeting_start_date TIMESTAMP,
    meeting_start_time VARCHAR(80),
    section_id INTEGER NOT NULL,
    section_num VARCHAR(80),
    term_id INTEGER NOT NULL
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

CREATE INDEX sis_sections_instructor_uid_idx ON sis_sections USING btree (instructor_uid);
CREATE INDEX sis_sections_meeting_location_idx ON sis_sections USING btree (meeting_location);
CREATE INDEX sis_sections_term_id_section_id_idx ON sis_sections(term_id, section_id);

--

ALTER TABLE ONLY approvals
    ADD CONSTRAINT approvals_room_id_fkey FOREIGN KEY (room_id) REFERENCES rooms(id);
ALTER TABLE ONLY scheduled
    ADD CONSTRAINT scheduled_room_id_fkey FOREIGN KEY (room_id) REFERENCES rooms(id);

--
