<template>
  <div id=main class="container">
    <div class="row">
    <div v-if="auth.isAuthenticated">
    <h1>MMC page</h1>
    
      <MMCGroups></MMCGroups>
      <GroupDetails></GroupDetails>
      <SessionList></SessionList>
      <SetupRun></SetupRun>
    
      <div v-if="sessionLog.isLog">
          <logFile></logFile>
      </div>
    </div>
    <div v-else>
      <LoginForm></LoginForm>
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
import LoginForm from './components/Login.vue';
import { sessionLog, auth } from './store';
// import { computed } from 'vue';
// import VueCookies from 'vue-cookies';

export default {
  name: 'App',
  components: {
    MMCGroups,
    GroupDetails,
    SetupRun,
    SessionList,
    LogFile,
    LoginForm
  },
  setup() {
    console.log(sessionLog)
    // const { cookies } = useCookies();
    // const isAuthenticated = computed(() => {
    //     return .get('Authorization') != null
    // })
    return {sessionLog, auth}
  },
  // computed: {
  //   isAuthenticated() {
  //       return auth.isAuthenticated()
  //   }
  // },
}
 
</script>

<style>
@import'~bootstrap/dist/css/bootstrap.css'
</style>
