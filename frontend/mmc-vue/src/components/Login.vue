<template>

<div class="container">
    <div class="row align-items-center justify-content-center h-100">
        <div class=" col-4 d-flex justify-content-center">
            <article class="card-body align-middle">
                <h1 class="card-title text-center mb-1 mt-1">MMC</h1>
                    <form class="d-flex flex-column justify-content-center" method="post">
                            <input class="form-control" placeholder="Username" type="text" name="username" v-model="loginForm.username">
                            <input class="form-control" placeholder="Password" type="password" name="password" v-model="loginForm.password">
                            <button class="btn btn-primary" @click="submit">Login</button>
                    </form>
            </article>
        </div>
    </div>
</div>


</template>
  
<script>

import { auth } from '../store.js'
import { reactive } from 'vue';
import postingAPI from '@/plugins/postingAPI';

export default {
    name: 'LoginForm',
    setup() {
        const loginForm = reactive({
            username: "",
            password: ""
        })
        return { loginForm }
    },
    methods: {
      async submit(e) {
        e.preventDefault()
        const { response, errors, fetching, postData } = postingAPI('login', this.loginForm)
        await postData()
        
        if (errors.value == null) {
            auth.token = response
            console.log(auth.token)
            this.$cookies.set('Authorization', decodeURIComponent(auth.token), '1h');
            auth.isAuthenticated = true
            // auth.username = this.loginForm.username
        }
        return {response, errors, fetching}
      }
    }
}

</script>