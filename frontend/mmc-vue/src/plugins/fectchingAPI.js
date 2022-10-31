import { reactive, toRefs } from "vue"


export default function () {
    const state = reactive({
        response: [],
        errors: null,
        fetching: true
    })
    const fetchData = async () => {
        try {
            let resp = await fetch('http://localhost:8000/groups/list/')
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