<template>
      <button class="btn btn-primary" @click="logs">Logs</button>
</template>

<script>
import {sessionLog } from '../store.js'
import { toRef } from 'vue'

export default {
    name: 'SessionDetail',
    props: {
        session: String,
      },
    setup(props) {
      const sessionName = toRef(props, 'session')
      console.log('SessionName', sessionName)
      return {sessionName} 
    },
    methods: {
      logs() {
        sessionLog.isLog = true
        sessionLog.sessionName = this.sessionName
      }
    }
}
</script>