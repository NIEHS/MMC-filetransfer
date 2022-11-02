<template>
    <div class="col row">
        <h1>Groups Details</h1>
        <div v-if="store.activeGroup != null" class="col-12 row">
            <span class="col-6">Name:</span><input class="col-6" :value="store.activeGroup.name">
            <span class="col-6">Affiliation:</span><input class="col-6" :value="store.activeGroup.affiliation">
            <div class="dropdown col-auto">
                <button class="btn btn-outline-primary dropdown-toggle" type="button" data-bs-toggle="dropdown" aria-expanded="false">New Project</button>
                <div class="dropdown-menu p-2 bg-secondary" style="width: 20vw"  >
                      <NewProject></NewProject>
                    </div>
            </div>
            <div class="col-12 row">
                <button v-for="project in store.activeGroup.projects" :key="project.name"
                    class="btn btn-outline-primary col">{{ project.name }}</button>

            </div>
        </div>
    </div>
</template>
  
<script>

import { store } from '../store.js'
import NewProject from "./NewProject.vue" 

export default {
    name: 'GroupsDetails',
    setup() {
        return { store }
    },
    components: { NewProject }
}

</script>