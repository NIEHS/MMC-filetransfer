<template>
  <div id=main class="container">
    <div class="row">
    <h1>MMC page</h1>
    <MMCGroups></MMCGroups>
    <GroupDetails></GroupDetails>
    <SessionList></SessionList>
    <SetupRun></SetupRun>
    <div v-if="sessionLog.isLog">
        <logFile></logFile>
    </div>
    </div>
  </div>
</template>

<script>
import MMCGroups from './components/MMCGroups.vue'
import GroupDetails from './components/GroupDetails.vue';
import SetupRun from './components/SetupRun.vue'
import SessionList from './components/SessionList.vue'
import LogFile from './components/LogFile.vue';
import { sessionLog } from './store';

export default {
  name: 'App',
  components: {
    MMCGroups,
    GroupDetails,
    SetupRun,
    SessionList,
    LogFile
  },
  setup() {
    console.log(sessionLog)
    return {sessionLog}
  },
}
</script>

<style>
@import'~bootstrap/dist/css/bootstrap.css'
</style>
