import { reactive, toRefs } from "vue"

const API_ROOT = 'http://localhost:8000/'

export default function (url, data) {
    console.log('PATCH.API',url, data)
    const content = {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    }
    const state = reactive({
        response: [],
        errors: null,
        fetching: true
    })
    const patchData = async () => {
        try {
            console.log(content)
            let resp = await fetch(API_ROOT + url, content)
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
    return { ...toRefs(state), patchData }
}