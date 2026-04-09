<template>
    <form>
        <div class="form-group">
            <label for="newGroupName">Name</label>
            <input id='newGroupName' class="form-control" v-model="group.name">
            <label for="newGroupAffiliation">Affiliation</label>
            <select id="newGroupAffiliation" class="form-control" v-model="group.affiliation">
              <option v-for="aff in affiliations" :key="aff" :value="aff">{{ aff }}</option>
            </select>
            <button class="btn btn-primary" @click="submit">Create</button>
        </div>
    </form>
</template>

<script>
import { store } from '@/store';
import { reactive, ref, onMounted } from 'vue';
import postingAPI from '../plugins/postingAPI.js'
import fetchingAPI from '../plugins/fectchingAPI.js'

export default {
    name: 'NewGroup',
    setup() {
        const affiliations = ref([])
        const group = reactive({
            name: "",
            affiliation: ""
        })

        onMounted(async () => {
            const { response, fetchData } = fetchingAPI('groups/affiliations/')
            await fetchData()
            affiliations.value = response.value
            if (affiliations.value.length > 0) {
                group.affiliation = affiliations.value[0]
            }
        })

        return { group, affiliations }
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
