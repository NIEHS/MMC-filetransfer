import { reactive, toRefs } from "vue"

export default function (url) {
    const state = reactive({
        response: [],
        errors: null,
        fetching: true
    })
    const fetchData = async (filters = '') => {
        try {
            let resp = await fetch(import.meta.env.VITE_API_ROOT + url + filters, {
                credentials: 'include'
            })
            state.response = await resp.json(), 
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