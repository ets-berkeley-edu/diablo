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

--

ALTER TABLE IF EXISTS ONLY public.approvals DROP CONSTRAINT IF EXISTS approvals_room_id_fkey;
ALTER TABLE IF EXISTS ONLY public.scheduled DROP CONSTRAINT IF EXISTS scheduled_room_id_fkey;

--

ALTER TABLE IF EXISTS ONLY public.admin_users DROP CONSTRAINT IF EXISTS admin_users_pkey;
ALTER TABLE IF EXISTS ONLY public.admin_users DROP CONSTRAINT IF EXISTS admin_users_uid_key;
ALTER TABLE IF EXISTS public.admin_users ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS ONLY public.approvals DROP CONSTRAINT IF EXISTS approvals_pkey;
ALTER TABLE IF EXISTS ONLY public.canvas_course_sites DROP CONSTRAINT IF EXISTS canvas_course_sites_pkey;
ALTER TABLE IF EXISTS ONLY public.course_preferences DROP CONSTRAINT IF EXISTS course_preferences_pkey;
ALTER TABLE IF EXISTS ONLY public.cross_listings DROP CONSTRAINT IF EXISTS cross_listings_pkey;
ALTER TABLE IF EXISTS ONLY public.email_templates DROP CONSTRAINT IF EXISTS email_templates_name_unique_constraint;
ALTER TABLE IF EXISTS ONLY public.email_templates DROP CONSTRAINT IF EXISTS email_templates_pkey;
ALTER TABLE IF EXISTS ONLY public.instructors DROP CONSTRAINT IF EXISTS instructors_pkey;
ALTER TABLE IF EXISTS ONLY public.queued_emails DROP CONSTRAINT IF EXISTS queued_emails_pkey;
ALTER TABLE IF EXISTS ONLY public.queued_emails DROP CONSTRAINT IF EXISTS queued_emails_section_id_template_type_unique_constraint;
ALTER TABLE IF EXISTS ONLY public.rooms DROP CONSTRAINT IF EXISTS rooms_location_unique_constraint;
ALTER TABLE IF EXISTS ONLY public.rooms DROP CONSTRAINT IF EXISTS rooms_pkey;
ALTER TABLE IF EXISTS ONLY public.scheduled DROP CONSTRAINT IF EXISTS scheduled_pkey;
ALTER TABLE IF EXISTS ONLY public.sent_emails DROP CONSTRAINT IF EXISTS sent_emails_pkey;
ALTER TABLE IF EXISTS ONLY public.sis_sections DROP CONSTRAINT IF EXISTS sis_sections_pkey;

--

DROP INDEX IF EXISTS public.rooms_location_idx;
DROP INDEX IF EXISTS public.sent_emails_section_id_idx;
DROP INDEX IF EXISTS public.sis_sections_instructor_uid_idx;
DROP INDEX IF EXISTS public.sis_sections_meeting_location_idx;
DROP INDEX IF EXISTS public.sis_sections_term_id_section_id_idx;

--

DROP TABLE IF EXISTS public.admin_users;
DROP SEQUENCE IF EXISTS public.admin_users_id_seq;
DROP TABLE IF EXISTS public.approvals;
DROP TABLE IF EXISTS public.canvas_course_sites;
DROP TABLE IF EXISTS public.course_preferences;
DROP TABLE IF EXISTS public.cross_listings;
DROP TABLE IF EXISTS public.email_templates;
DROP SEQUENCE IF EXISTS public.email_templates_id_seq;
DROP TABLE IF EXISTS public.instructors;
DROP TABLE IF EXISTS public.job_history;
DROP SEQUENCE IF EXISTS job_history_id_seq;
DROP TABLE IF EXISTS public.queued_emails;
DROP SEQUENCE IF EXISTS public.queued_emails_id_seq;
DROP TABLE IF EXISTS public.rooms;
DROP SEQUENCE IF EXISTS public.rooms_id_seq;
DROP TABLE IF EXISTS public.scheduled;
DROP TABLE IF EXISTS public.sent_emails;
DROP SEQUENCE IF EXISTS public.sent_emails_id_seq;
DROP TABLE IF EXISTS public.sis_sections;
DROP SEQUENCE IF EXISTS public.sis_sections_id_seq;

--

DROP TYPE IF EXISTS public.approver_types;
DROP TYPE IF EXISTS public.email_template_types;
DROP TYPE IF EXISTS public.publish_types;
DROP TYPE IF EXISTS public.recording_types;
DROP TYPE IF EXISTS public.room_capability_types;
DROP TYPE IF EXISTS public.user_types;

--
