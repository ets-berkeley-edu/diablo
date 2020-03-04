<template>
  <div>
    <h1>{{ $currentUser.teachingSections.length }} Capture-enabled Rooms</h1>
    <v-data-table
      :headers="headers"
      :items="$currentUser.teachingSections"
      :items-per-page="100"
      :loading="loading"
      class="elevation-1"
    ></v-data-table>
  </div>
</template>

<script>
  export default {
    name: 'Home',
    data: () => ({
      headers: [
        {text: 'Section', value: 'sectionId'},
        {text: 'Title', value: 'courseTitle'},
        {text: 'Catalog', value: 'courseName'},
        {text: 'Format', value: 'instructionFormat'},
        {text: 'Instructor Role', value: 'instructorRoleCode'},
        {text: 'Eligible for Course Capture', value: 'isEligibleForCourseCapture'},
        {text: 'meetingDays', value: 'meetingDays'},
        {text: 'meetingEndDate', value: 'meetingEndDate'},
        {text: 'meetingEndTime', value: 'meetingEndTime'},
        {text: 'meetingLocation', value: 'meetingLocation'},
        {text: 'meetingStartDate', value: 'meetingStartDate'},
        {text: 'meetingStartTime', value: 'meetingStartTime'},
        {text: 'sectionNum', value: 'sectionNum'}
      ]
    })
  }
</script>
