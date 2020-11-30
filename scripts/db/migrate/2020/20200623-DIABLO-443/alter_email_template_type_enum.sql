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

BEGIN;

-- Rename existing TYPE
ALTER TYPE email_template_types RENAME TO email_template_types_OLD;

-- Create new TYPE
CREATE TYPE email_template_types AS ENUM (
    'admin_alert_instructor_change',
    'admin_alert_multiple_meeting_patterns',
    'admin_alert_room_change',
    'invitation',
    'notify_instructor_of_changes',
    'recordings_scheduled',
    'room_change_no_longer_eligible',
    'waiting_for_approval'
);

-- Update tables to use the new TYPE
ALTER TABLE email_templates ALTER COLUMN template_type TYPE email_template_types USING template_type::text::email_template_types;
ALTER TABLE queued_emails ALTER COLUMN template_type TYPE email_template_types USING template_type::text::email_template_types;
ALTER TABLE sent_emails ALTER COLUMN template_type TYPE email_template_types USING template_type::text::email_template_types;

-- Remove old TYPE
DROP TYPE email_template_types_OLD;

COMMIT;
