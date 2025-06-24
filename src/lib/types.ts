
export type DiabloConfig = {
  apiBaseUrl: string,
  devAuthEnabled: boolean,
  currentTermName: string,
  currentTermId: number,
  canvasBaseUrl: string,
  kalturaMediaSpaceUrl: string,
  searchItemsPerPage: number,
  isVueAppDebugMode: boolean,
  emailCourseCaptureSupport: string,
  currentTermRecordingsBegin: any,
  currentTermRecordingsEnd: any,
  searchFilterOptions: any,
  emailTemplateTypes: any,
}

export interface Collaborator {
  csid: string,
  email: string,
  firstName: string,
  lastName: string,
  uid: string
}

export interface Instructor {
  deletedAt: string | null,
  deptCode: string,
  email: string,
  hasOptedOut: boolean,
  name: string,
  roleCode: string,
  uid: string
}

export interface OptOut {
  createdAt: string,
  instructorUid: string,
  sectionId: number | null,
  termId: number
}

export interface Room {
  capability: string,
  capabilityName: string,
  createdAt: string,
  id: number,
  isAuditorium: boolean,
  kalturaResourceId: number,
  location: string,
  recordingTypeOptions: {
    presenter_presentation_audio: string
  }
}

export interface Meeting {
  days: string,
  daysFormatted: string[],
  daysNames: string[],
  eligible: boolean,
  endDate: string,
  endTime: string,
  endTimeFormatted: string,
  recordingEndDate: string,
  recordingStartDate: string,
  room: Room,
  startDate: string,
  startTime: string,
  startTimeFormatted: string
}

export interface BaseCourse {
  courseName: string,
  courseTitle: string,
  instructionFormat: string,
  isPrimary: boolean,
  label: string,
  sectionId: number,
  sectionNum: string,
  termId: number
}

export interface ScheduledCourse {
  collaboratorUids: string[],
  collaborators: Collaborator[],
  courseDisplayName: string,
  createdAt: string,
  id: number,
  instructorUids: string[],
  kalturaScheduleId: number,
  meetingDays: string[],
  meetingDaysNames: string[],
  meetingEndDate: string,
  meetingEndTime: string,
  meetingEndTimeFormatted: string,
  meetingStartDate: string,
  meetingStartTime: string,
  meetingStartTimeFormatted: string,
  publishType: string,
  publishTypeName: string,
  recordingType: string,
  recordingTypeName: string,
  room: Room,
  sectionId: number,
  termId: number
}

export interface Course extends BaseCourse {
  allowedUnits: number,
  canvasSiteIds: number[] | null,
  collaboratorUids: string[],
  collaborators: Collaborator[],
  courseCodes: string[],
  crossListings: BaseCourse[],
  deletedAt: string | null,
  displayMeetings: Meeting[],
  hasBlanketOptedOut: boolean,
  hasOptedOut: boolean,
  instructors: Instructor[],
  meetingType: string,
  meetings: {
    eligible: Meeting[],
    ineligible: Meeting[],
  },
  nonstandardMeetingDates: boolean,
  optOuts: OptOut[],
  publishType: string,
  publishTypeName: string,
  recordingType: string,
  recordingTypeName: string,
  scheduled: ScheduledCourse[] | null,
}

export interface DiabloUser {
  courses: Course[],
  deptCode?: string,
  email?: string,
  emailAddress: string | null,
  firstName?: string,
  hasOptedOutForAllTerms: boolean,
  hasOptedOutForTerm: boolean,
  id: string | null,
  isActive: boolean,
  isAdmin: boolean,
  isAnonymous: boolean,
  isAuthenticated: boolean,
  isExpired: boolean,
  isExpiredPerLdap?: boolean,
  isTeaching: boolean,
  lastName?: string,
  name: string,
  uid: string | null
}

export type ScreenReaderAlert = {
  message: string,
  politeness: string
}
