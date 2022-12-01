<template>
    <div class="col">
        <div class="col-12 row align-items-center">
            <h2 class="col-auto pr-0 mr-0">Groups</h2>
            <div class="dropdown col-auto">
                <button class="btn btn-outline-primary dropdown-toggle" type="button" data-bs-toggle="dropdown" aria-expanded="false">New Group</button>
                <div class="dropdown-menu p-2 bg-secondary" style="width: 20vw"  >
                      <NewGroup></NewGroup>
                    </div>
            </div>
        </div>
        <div class="col-12 row p-2">
        <div v-for="group in store.groups" :key="group.name" class="col-auto p-0">
            <button class="btn btn-outline-primary" type="button" v-on:click="selectGroup(group)">
                      {{ group.name }}
                    </button>
        </div>
    </div>
    </div>
</template>

<script>
import fetchingAPI from '../plugins/fectchingAPI.js'
import { store } from '../store.js'
// import { ref, watch} from 'vue'
import NewGroup from './NewGroup.vue'

export default {
    name: 'MMCGroups',
    components: {
        NewGroup
    },
    setup() {
        // const newGroupElement = ref(state.newGroupMenu);
        const { response, errors, fetching, fetchData } = fetchingAPI('groups/list/')
        fetchData()
        console.log(errors)
        if (errors.value == null) {store.groups = response}
        // watch(state.newGroupMenu, () => {
        //     if (state.newGroupMenu == true)
        //     {this.hideAddNewGroup()}
        // })
        return { store, response, errors, fetching }
    },
    methods: {
        selectGroup(group) {
            store.activeGroup = group
            console.log(store.activeGroup)
        },
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
}
</script>

