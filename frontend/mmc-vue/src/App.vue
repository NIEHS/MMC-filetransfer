<template>
  <div id=main class="container-fluid">
    <h1>MMC page</h1>
    <MMCGroups></MMCGroups>
  </div>
</template>

<script>
import MMCGroups from './components/MMCGroups.vue'

export default {
  name: 'App',
  components: {
    MMCGroups
  }
}
</script>

<style>
@import'~bootstrap/dist/css/bootstrap.css'
</style>
