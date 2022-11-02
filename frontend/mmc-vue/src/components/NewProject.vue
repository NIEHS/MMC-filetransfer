<template>
    <form>
        <div class="form-group">
            <label for="newProjectName">Name</label>
            <input id='newProjectName' class="form-control" v-model="project.name">
            <label for="newProjectEmails">Emails</label>
            <input id="newGroupAffiliation" class="form-control" v-model="email" @keydown="handleKeyDown">
            <div>
              <span v-for="address in project.emails" :key="address" class='badge rounded-pill bg-primary'>{{address}}</span>
            </div>

            <button class="btn btn-primary mt-2" @click="submit">Create</button>
        </div>
    </form>
</template>

<script>
import { store } from '@/store';
import { reactive, nextTick } from 'vue';
import patchingAPI from '../plugins/patchingAPI.js'

export default {
    name: 'NewProject',
    setup() {
        const project = reactive({
            name: "",
            emails: [],
        })
        const email = ""
        return { project, email }
    },
    methods: {
      submit(e) {
        e.preventDefault()
        let group = store.activeGroup
        group.projects.push(this.project)
        const { response, errors, fetching, patchData } = patchingAPI('groups/update', group)
        patchData()
        if (errors.value == null) {
          store.groups = response
          store.activeGroup = group
        }
        return {response, errors, fetching}
      },
      handleKeyDown (e) {
        
        if([',',' '].includes(e.key)){
          e.preventDefault()
          this.project.emails.push(this.email)
          nextTick(()=> {console.log('RESET!');return ''})
          this.email=''
          console.log(this.email)
        }
      },
    }
}
</script>