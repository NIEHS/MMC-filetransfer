import { reactive } from 'vue'

export const store = reactive({
    activeGroup: null,
    groups: null,
})

export const state = reactive({
    newGroupMenu:false
})

export const sessionLog = reactive({
    isLog: false,
    sessionName: null,
})