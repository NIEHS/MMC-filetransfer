<template>
  <div id=main class="container row">
    <h1>MMC page</h1>
    <MMCGroups></MMCGroups>
    <GroupDetails></GroupDetails>
    <SetupRun></SetupRun>
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
