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

CREATE TYPE publish_types AS ENUM (
    'canvas',
    'kaltura_media_gallery'
);

--

CREATE TYPE recording_types AS ENUM (
    'presentation_audio',
    'presenter_audio',
    'presenter_presentation_audio'
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
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
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
    approved_by_uid VARCHAR(80) NOT NULL,
    section_id INTEGER NOT NULL,
    term_id INTEGER NOT NULL,
    room_id INTEGER NOT NULL,
    approver_type approver_types,
    publish_type publish_types NOT NULL,
    recording_type recording_types NOT NULL,
    created_at timestamp with time zone NOT NULL
);
ALTER TABLE approvals OWNER TO diablo;
ALTER TABLE approvals ADD CONSTRAINT approvals_pkey PRIMARY KEY (approved_by_uid, section_id, term_id);
CREATE INDEX approvals_approved_by_uid_idx ON approvals USING btree (approved_by_uid);
CREATE INDEX approvals_section_id_idx ON approvals USING btree (section_id);
CREATE INDEX approvals_term_id_idx ON approvals USING btree (term_id);

--

CREATE TABLE rooms (
    id INTEGER NOT NULL,
    capability room_capability_types,
    is_auditorium BOOLEAN NOT NULL,
    kaltura_resource_id INTEGER,
    location VARCHAR(255) NOT NULL,
    created_at timestamp with time zone NOT NULL
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
    section_id INTEGER NOT NULL,
    term_id INTEGER NOT NULL,
    room_id INTEGER NOT NULL,
    created_at timestamp with time zone NOT NULL
);
ALTER TABLE scheduled OWNER TO diablo;
ALTER TABLE scheduled ADD CONSTRAINT scheduled_pkey PRIMARY KEY (section_id, term_id);
CREATE INDEX scheduled_section_id_idx ON scheduled USING btree (section_id);
CREATE INDEX scheduled_term_id_idx ON scheduled USING btree (term_id);

--

ALTER TABLE ONLY approvals
    ADD CONSTRAINT approvals_room_id_fkey FOREIGN KEY (room_id) REFERENCES rooms(id);
ALTER TABLE ONLY scheduled
    ADD CONSTRAINT scheduled_room_id_fkey FOREIGN KEY (room_id) REFERENCES rooms(id);

--
