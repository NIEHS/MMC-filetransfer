import { reactive, toRefs } from "vue"

const API_ROOT = 'http://mri20-dtn01:8000/'

export default function (url, data, contentType='application/json') {
    const content = {
        method: 'POST',
        headers: {
            'Content-Type': contentType
        },
        credentials: 'include',
        body: JSON.stringify(data)
    }
    const state = reactive({
        response: [],
        errors: null,
        fetching: true
    })
    const postData = async () => {
        try {
            console.log(content)
            let resp = await fetch(API_ROOT + url, content)
            state.response = await resp.json()
            
        }
        catch (errors) {
            state.errors = errors
        }
        finally {
            state.fetching = false
        }
    }
    return { ...toRefs(state), postData }
}