import { reactive, toRefs } from "vue"

const API_ROOT = 'http://localhost:8000/'

export default function (url) {
    const state = reactive({
        response: [],
        errors: null,
        fetching: true
    })
    const fetchData = async () => {
        try {
            let resp = await fetch(API_ROOT + url)
            state.response = await resp.json()
            console.log(resp)
        }
        catch (errors) {
            state.errors = errors
        }
        finally {
            state.fetching = false
        }
    }
    return { ...toRefs(state), fetchData }
}