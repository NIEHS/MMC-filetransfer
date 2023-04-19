import { createApp } from 'vue'
import App from './App.vue'
import VueCookies from 'vue-cookies';
import 'bootstrap'


var app = createApp(App)


app.mount('#app')
app.use(VueCookies)
