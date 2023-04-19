import { reactive } from 'vue'
import VueCookies from 'vue-cookies';

export const auth= reactive({
    isAuthenticated:  VueCookies.get('Authorization') != null,
})

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