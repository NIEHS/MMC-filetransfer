<template>
  <div class="mt-2">

    <!-- Status badge -->
    <span class="badge"
      :class="{
        'bg-secondary': transferStatus === 'not_started',
        'bg-success':   transferStatus === 'running',
        'bg-danger':    transferStatus === 'stopped',
      }">
      Transfer: {{ statusLabel }}
    </span>

    <!-- Form (hidden while running) -->
    <div v-if="transferStatus !== 'running'" class="mt-2">
      <div class="row g-2 align-items-end">

        <div class="col-auto">
          <label class="form-label mb-0 small">Duration (h)</label>
          <input type="number" class="form-control form-control-sm" v-model.number="form.duration" min="1" max="96" style="width:80px">
        </div>

        <div class="col-auto">
          <label class="form-label mb-0 small">Email</label>
          <select class="form-select form-select-sm" v-model="form.emailLevel" style="width:90px">
            <option value="all">all</option>
            <option value="none">none</option>
          </select>
        </div>

      </div>

      <div class="mt-1">
        <div class="form-check form-check-inline">
          <input class="form-check-input" type="checkbox" id="chk-noStaging" v-model="form.noStaging">
          <label class="form-check-label small" for="chk-noStaging">noStaging</label>
        </div>
        <div class="form-check form-check-inline">
          <input class="form-check-input" type="checkbox" id="chk-noLongTerm" v-model="form.noLongTerm">
          <label class="form-check-label small" for="chk-noLongTerm">noLongTerm</label>
        </div>
        <div class="form-check form-check-inline">
          <input class="form-check-input" type="checkbox" id="chk-cluster" v-model="form.cluster">
          <label class="form-check-label small" for="chk-cluster">cluster</label>
        </div>
        <div class="form-check form-check-inline">
          <input class="form-check-input" type="checkbox" id="chk-remove" v-model="form.remove">
          <label class="form-check-label small" for="chk-remove">remove</label>
        </div>
        <div class="form-check form-check-inline">
          <input class="form-check-input" type="checkbox" id="chk-checkFiles" v-model="form.checkFiles">
          <label class="form-check-label small" for="chk-checkFiles">checkFiles</label>
        </div>
      </div>

      <button
        class="btn btn-sm btn-success mt-2"
        :disabled="transferStatus === 'running' || starting"
        @click="startTransfer">
        <span v-if="starting" class="spinner-border spinner-border-sm me-1"></span>
        Start Transfer
      </button>
    </div>

    <!-- Running info + stop button -->
    <div v-if="transferStatus === 'running'" class="mt-2">
      <div class="text-muted small">PID: {{ currentPid }} &mdash; Started: {{ startedAt }}</div>
      <button class="btn btn-sm btn-danger mt-1" @click="stopTransfer" :disabled="stopping">
        <span v-if="stopping" class="spinner-border spinner-border-sm me-1"></span>
        Stop Transfer
      </button>
    </div>

    <!-- Error -->
    <div v-if="errorMsg" class="alert alert-danger py-1 px-2 mt-2 small">{{ errorMsg }}</div>

  </div>
</template>

<script>
import { reactive, ref, computed, onMounted, onUnmounted, toRef } from 'vue'

const API_ROOT = 'http://mri20-dtn01:8000/'
const POLL_INTERVAL_MS = 10000

export default {
  name: 'TransferControl',
  props: {
    session: {
      type: String,
      required: true,
    }
  },
  setup(props) {
    const sessionName = toRef(props, 'session')

    const form = reactive({
      duration: 16,
      emailLevel: 'all',
      noStaging: false,
      noLongTerm: false,
      cluster: false,
      remove: false,
      checkFiles: false,
    })

    const transferStatus = ref('not_started')
    const currentPid = ref(null)
    const startedAt = ref(null)
    const starting = ref(false)
    const stopping = ref(false)
    const errorMsg = ref(null)

    const statusLabel = computed(() => {
      const map = { not_started: 'Not Started', running: 'Running', stopped: 'Stopped' }
      return map[transferStatus.value] ?? transferStatus.value
    })

    const refreshStatus = async () => {
      try {
        const resp = await fetch(
          `${API_ROOT}session/${sessionName.value}/transfer/status`,
          { credentials: 'include' }
        )
        if (!resp.ok) return
        const data = await resp.json()
        transferStatus.value = data.status
        currentPid.value = data.pid ?? null
        startedAt.value = data.started_at ?? null
      } catch (e) {
        console.error('Transfer status poll failed:', e)
      }
    }

    const startTransfer = async () => {
      errorMsg.value = null
      starting.value = true
      try {
        const params = new URLSearchParams({
          duration: form.duration,
          emailLevel: form.emailLevel,
          cluster: form.cluster,
          remove: form.remove,
          checkFiles: form.checkFiles,
          noStaging: form.noStaging,
          noLongTerm: form.noLongTerm,
        })
        const resp = await fetch(
          `${API_ROOT}session/${sessionName.value}/transfer?${params}`,
          { method: 'POST', credentials: 'include' }
        )
        const data = await resp.json()
        if (!resp.ok) {
          errorMsg.value = data.detail ?? 'Failed to start transfer'
        } else {
          transferStatus.value = 'running'
          currentPid.value = data.pid
          startedAt.value = data.started_at
        }
      } catch (e) {
        errorMsg.value = String(e)
      } finally {
        starting.value = false
      }
    }

    const stopTransfer = async () => {
      errorMsg.value = null
      stopping.value = true
      try {
        const resp = await fetch(
          `${API_ROOT}session/${sessionName.value}/transfer`,
          { method: 'DELETE', credentials: 'include' }
        )
        const data = await resp.json()
        if (!resp.ok) {
          errorMsg.value = data.detail ?? 'Failed to stop transfer'
        } else {
          await refreshStatus()
        }
      } catch (e) {
        errorMsg.value = String(e)
      } finally {
        stopping.value = false
      }
    }

    let pollTimer = null

    onMounted(async () => {
      await refreshStatus()
      pollTimer = setInterval(async () => {
        if (transferStatus.value === 'running') {
          await refreshStatus()
        }
      }, POLL_INTERVAL_MS)
    })

    onUnmounted(() => {
      if (pollTimer) {
        clearInterval(pollTimer)
        pollTimer = null
      }
    })

    return {
      form,
      transferStatus,
      statusLabel,
      currentPid,
      startedAt,
      starting,
      stopping,
      errorMsg,
      startTransfer,
      stopTransfer,
    }
  }
}
</script>
