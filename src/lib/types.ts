
export type DiabloConfig = {
  apiBaseUrl: string,
  canvasBaseUrl: string,
  courseCapturePremiumCost: number,
  currentTermId: number,
  currentTermName: string,
  currentTermRecordingsBegin: string,
  currentTermRecordingsEnd: string,
  devAuthEnabled: boolean,
  emailCourseCaptureSupport: string,
  emailTemplateTypes: {[key: string]: string},
  isVueAppDebugMode: boolean,
  kalturaMediaSpaceUrl: string,
  publishTypeOptions: {[key: string]: string},
  searchFilterOptions: {[key: string]: string},
  searchItemsPerPage: number,
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
  name: string,
  roleCode: string,
  uid: string
}

export interface OptIn {
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

export type CanvasSite = {
  canvasSiteId: string,
  courseCode: string,
  name: string,
  sisCourseId: number | string,
  sisTermId: number | string,
  url: string
}

export interface Course extends BaseCourse {
  allowedUnits: number,
  canvasSiteIds: number[] | null,
  collaboratorUids: string[],
  collaborators: Collaborator[],
  courseCodes: string[],
  canvasSites?: CanvasSite[],
  crossListings: BaseCourse[],
  deletedAt: string | null,
  displayMeetings: Meeting[],
  hasBlanketOptedOut: boolean,
  hasOptedIn: boolean,
  instructors: CourseInstructor[],
  meetingType: string,
  meetings: {
    eligible: Meeting[],
    ineligible: Meeting[],
  },
  nonstandardMeetingDates: boolean,
  note: string | undefined,
  optIns: OptIn[],
  publishType: string,
  publishTypeName: string,
  recordingType: string,
  recordingTypeName: string,
  room: Room | undefined,
  scheduled: ScheduledCourse[] | null,
  statusLabel?: string,
  updateHistory?: ScheduleUpdate[]
}

export interface CourseInstructor extends Instructor {
  hasOptedIn: boolean,
  optedInAt: string | undefined
}

export interface CourseSortable extends Course {
  instructorNames: string[]
  isSelectable: boolean
}

export interface DiabloUser {
  id: string | null,
  courses: Course[],
  deptCode?: string,
  email?: string,
  emailAddress: string | null,
  firstName?: string,
  isActive: boolean,
  isAdmin: boolean,
  isAnonymous: boolean,
  isAuthenticated: boolean,
  isExpired: boolean,
  isExpiredPerLdap?: boolean,
  isTeaching: boolean,
  lastName?: string,
  name: string,
  uid: string | null,
  doNotEmail: boolean,
  optInNewCourses: boolean
}

export type ScheduleUpdate = {
  id: string,
  fieldName: string,
  fieldValueNew: string,
  fieldValueOld: string,
  kalturaScheduleId: string,
  publishedAt: string
  requestedAt: string,
  requestedByName: string,
  requestedByUid: string,
  sectionId: string,
  status: string,
  termId: string
}

export type ScreenReaderAlert = {
  message: string,
  politeness: string
}

export type SortBy = {
  key: string,
  order: 'asc' | 'desc'
}
