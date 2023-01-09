<template>
  <div class="card popupCard position-absolute top-50 start-50 translate-middle d-flex justify-content-between align-items-center" style="z-index: 99;">

    <div class="row align-items-center" style="height: 10%">
      <h2 class="col-auto">{{sessionLog.sessionName}}</h2>
      <div class="form-group row col-auto">
        <label class="col-sm-6 col-form-label">Number of lines</label>
        <div class="col-sm-6">
          <input class="form-control" v-model="logData.lineNumber">
        </div>
      </div>
      <div class="row col-auto">
        <button @click="refresh" class="btn col-auto"><BIconArrowClockwise></BIconArrowClockwise></button>
        <button @click="closePopup" class="btn col-auto"><BIconXLg></BIconXLg></button>
      </div>
    </div>
    <div class="card-body d-flex w-100" style="height: 90%">
      <div class="card-text scroll-box w-100">
      <LogLine v-for="line in logData.log.log" :key="line" :line="line"></LogLine>
      <!-- <p v-for="line in logData.log.log" :key="line">{{processLogLine(line)}}</p> -->
    </div>
    </div>
  </div>
</template>

<script>
import fetchingAPI from '../plugins/fectchingAPI.js'
import {sessionLog } from '../store.js'
import { onMounted,reactive } from 'vue'
import { BIconXLg, BIconArrowClockwise } from 'bootstrap-icons-vue'
import LogLine from './LogLine.vue'

export default {
  name: 'LogFile',
  components: {
    BIconXLg,
    BIconArrowClockwise,
    LogLine
  },
  setup() {
    const logData = reactive({
      lineNumber: 200,
      log:[]
    })
    console.log(sessionLog)
    const { response, errors, fetching, fetchData } = fetchingAPI(`session/${sessionLog.sessionName}/log`)
    const fetchLog = () => {
      fetchData(`?lineNumber=${logData.lineNumber}`)
      logData.log = response
    }
    onMounted(() => {
      fetchLog()
      console.log(logData)
    })
    return { sessionLog, logData, response, errors, fetching, fetchData}
  },
  methods: {
    closePopup (e) {
      e.preventDefault();
      console.log('Closing')
      sessionLog.isLog = false
      sessionLog.sessionName = null
    },
    refresh () {
      this.fetchData(`?lineNumber=${this.logData.lineNumber}`)
    },

  }
}
</script>

<style scoped>
.popupCard {
  width: 80vw;
  height: 80vh
}
.scroll-box {
            overflow-y: scroll;
            height: 100%;
            padding: 1rem
        }

</style>