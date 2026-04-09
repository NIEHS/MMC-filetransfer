<template>
  <div class="d-flex flex-column gap-2">
    <button class="btn btn-sm btn-primary" @click="logs">Logs</button>
    <TransferControl :session="sessionName"></TransferControl>
  </div>
</template>

<script>
import { toRef } from 'vue'
import { sessionLog } from '../store.js'
import TransferControl from './TransferControl.vue'

export default {
    name: 'SessionDetail',
    components: {
      TransferControl,
    },
    props: {
        session: String,
      },
    setup(props) {
      const sessionName = toRef(props, 'session')
      return { sessionName }
    },
    methods: {
      logs() {
        sessionLog.isLog = true
        sessionLog.sessionName = this.sessionName
      }
    }
}
</script>