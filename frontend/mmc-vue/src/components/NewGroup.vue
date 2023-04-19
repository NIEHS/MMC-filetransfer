<template>
    <form>
        <div class="form-group">
            <label for="newGroupName">Name</label>
            <input id='newGroupName' class="form-control" v-model="group.name">
            <label for="newGroupAffiliation">Affiliation</label>
            <select id="newGroupAffiliation" class="form-control" v-model="group.affiliation">
              <option>NIEHS</option>
              <option>NICE</option>
              <option>Collaborations</option>
            </select>
            <button class="btn btn-primary" @click="submit">Create</button>
        </div>
    </form>
</template>

<script>
// import fetchingAPI from '../plugins/fectchingAPI.js'

import { store } from '@/store';
import { reactive } from 'vue';
import postingAPI from '../plugins/postingAPI.js'

export default {
    name: 'NewGroup',
    // props: {
    //     newGroupElement: String,
    //   },
    setup() {
        const group = reactive({
            name: "",
            affiliation: "NIEHS"
        })
        // const GroupElement =  ref(props.newGroupElement)
        return { group }
    },
    methods: {
      submit(e) {
        e.preventDefault()
        const { response, errors, fetching, postData } = postingAPI('groups/add', this.group)
        postData()
        if (errors.value == null) {
          store.groups = response}
      
        return {response, errors, fetching}
      }
    }
}
</script>