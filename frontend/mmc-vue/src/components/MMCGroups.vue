<template>
  <h1>Hello</h1>
  <div>
    <p v-for="project in response" :key="project.name">{{ project.name }}</p>
  </div>
</template>

<script>
import fetchingAPI from '../plugins/fectchingAPI.js'
// import { reactive, toRefs } from "vue"

export default {
  name: 'MMCGroups',
  setup() {
    const { response, errors, fetching, fetchData } = fetchingAPI()
    // const state = reactive({
    //   response: [],
    //   errors: null,
    //   fetching: true
    // })

    // const fetchData = async () => {
    //   try {
    //     let resp = await fetch('http://localhost:8000/groups/list/')
    //     state.response = await resp.json()
    //     console.log(resp)
    //   }
    //   catch (errors) {
    //     state.errors = errors
    //   }
    //   finally {
    //     state.fetching = false
    //   }
    // }
    fetchData()
    return { response, errors, fetching }
    // return { ...toRefs(state), fetchData }
  },
  // methods: {
  //   async fetchingAPI() {
  //     try {
  //       let resp = await fetch('http://localhost:8000/groups/list/')
  //       console.log(resp)
  //       return resp
  //     }
  //     catch (errors) {
  //       return errors
  //     }

  //   }
  // }
}

</script>

