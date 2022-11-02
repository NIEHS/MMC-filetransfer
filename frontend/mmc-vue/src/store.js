import { reactive } from 'vue'

export const store = reactive({
    activeGroup: null,
    groups: null,
})

export const state = reactive({
    newGroupMenu:false
})