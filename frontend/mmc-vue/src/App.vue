<template>
  <div id=main class="container">
    <div class="row">
    <h1>MMC page</h1>
    <MMCGroups></MMCGroups>
    <GroupDetails></GroupDetails>
    <SetupRun></SetupRun>
    </div>
  </div>
</template>

<script>
import MMCGroups from './components/MMCGroups.vue'
import GroupDetails from './components/GroupDetails.vue';
import SetupRun from './components/SetupRun.vue'

export default {
  name: 'App',
  components: {
    MMCGroups,
    GroupDetails,
    SetupRun
  }
}
</script>

<style>
@import'~bootstrap/dist/css/bootstrap.css'
</style>
