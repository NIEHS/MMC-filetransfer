<template>
    <div class="col-12 row align-items-center">
    <h2 class="col-auto">Sessions</h2>
        <div class="col-3">
            <div class="input-group">
                <input class="form-control border" type="search" v-model="fetchArguments.session" v-on:keyup="updateSessions()">
                <!-- <span class="input-group-append"> -->
                    <button class="btn btn-outline-secondary bg-white border border-start-0" style="margin-left: -38px !important" type="button">
                        <BIconSearch></BIconSearch>
                    </button>
                <!-- </span> -->
            </div>
        </div>
    <!-- <label class="col-auto px-0"><BIconSearch></BIconSearch></label><span class="col-3 p-0"><input class="form-control" v-model="fetchArguments.session" v-on:keyup="updateSessions()"></span> -->
    </div>
    <div>
    <div  v-for="session in sessions" :key="session" class="dropdown col-auto">
            <button class="badge rounded-pill bg-primary" type="button" data-bs-toggle="dropdown" aria-expanded="false">{{session}}</button>
            <div class="dropdown-menu p-2 bg-secondary" style="width: 20vw">
                <SessionDetail :session="session"></SessionDetail>
                </div>
            </div>
    </div>
    
</template>

<script>
import fetchingAPI from '../plugins/fectchingAPI.js'
import { store } from '../store.js'
import { reactive } from 'vue'
import { BIconSearch } from 'bootstrap-icons-vue'
import SessionDetail from './SessionDetail.vue'

export default {
    name: 'SessionList',
    components: {
        BIconSearch,
        SessionDetail
    },
    setup() {
        // const newGroupElement = ref(state.newGroupMenu);
        const { response, errors, fetching, fetchData } = fetchingAPI('sessions/find/')
        // const group = reactive(store.activeGroup)
        fetchData()
        const sessions = response
        const fetchArguments = reactive({
            group: '*',
            project: '*',
            session: '',
        })
        return { fetchArguments, sessions, response, errors, fetching, fetchData }
    },
    watch: {
        group (newGroup, oldGroup) {
            console.log(oldGroup,newGroup)
            this.fetchArguments.group = newGroup
            this.updateSessions()
        }
    },
    computed: {
        group() {
            if (store.activeGroup == null) { return null}
            return store.activeGroup.name
        },
        fecthDataString() {
            var output = '?'
            if (this.fetchArguments.group !== null) {
                output += `group=${this.fetchArguments.group}&`
            }
            if (this.fetchArguments.session !== '') {
                output += `session=${this.fetchArguments.session}`
            }
            return output
        }
    },
    methods: {
        updateSessions () {
            console.log(this.fecthDataString)
            this.fetchData(this.fecthDataString)
            this.sessions = this.response
        }
    }
        // toggleAddNewGroup() {
        //     this.newGroupElement = true
        //     state.newGroupMenu = true
        //     },
        // hideAddNewGroup() {
        //     this.newGroupElement = false
        //     state.newGroupMenu = false
        //     console.log('State:', state)
        // },

    }

</script>