<template>
    <h2>
        Setup session</h2>
    <form>
        <div class="form-group position-relative">

            
            <div class="row">
                <div class="col-5">
                    <label>{{session.sample.label}}</label>
                    <input :type="session.sample.type" class="form-control" id="setupSourceDir" v-model="session.sample.value">
                </div>
                <div class="col-3">
                    <label>{{session.date.label}}</label>
                    <input :type="session.date.type" class="form-control" id="setupFilesPattern" v-model="session.date.value">
                </div>
                <div class="col-4">
                    <label>{{session.scope.label}}</label>
                    <select class="form-control" id="setupLabel" v-model="session.scope.value">
                        <option value="" disabled selected hidden>Choose a microscope</option>
                        <option v-for="choice in session.scope.choices" :key="choice">{{choice}}</option>
                    </select>
                </div>
            </div>


            <label>{{session.sourceDir.label}}</label>
            <input :type="session.sourceDir.type" class="form-control" id="setupSourceDir" @keyup="checkPaths(session.sourceDir.value, 'sourcePathList')" @keydown.tab.prevent="autoComplete('sourceDir','sourcePathList')" v-model="session.sourceDir.value">
            <div><span v-for="path in sourcePathList" :key="path" class='badge rounded-pill bg-primary'>{{path}}</span></div>
            <label>{{session.gainReference.label}}</label>
            <input :type="session.gainReference.type" class="form-control" id="setupGainReference" @keyup="checkPaths(session.gainReference.value, 'gainReferencePathList')" @keydown.tab.prevent="autoComplete('gainReference','gainReferencePathList')" v-model="session.gainReference.value">
            <div><span v-for="path in gainReferencePathList" :key="path" class='badge rounded-pill bg-primary'>{{path}}</span></div>
    
            <div class="row">
                <div class="col-4">
                    <label>{{session.filesPattern.label}}</label>
                    <input :type="session.filesPattern.type" class="form-control" id="setupFilesPattern" v-model="session.filesPattern.value">
                </div>

                <div class="col-4">
                    <label>{{session.group.label}}</label>
                    <select class="form-control" id="setupLabel" v-model="session.group.value">
                <option value="" disabled selected hidden>Choose a group</option>
                <option v-for="choice in session.group.choices" :key="choice">{{choice}}</option>
            </select>
                </div>
                <div class="col-4">
                    <label>{{session.project.label}}</label>
                    <select class="form-control" id="setupLabel" v-model="session.project.value">
                        <option value="" disabled selected hidden>Choose a project</option>
                        <option v-for="choice in projectChoices" :key="choice">{{choice}}</option>
                    </select>
                </div>
            <!-- </div>
            <div class="row"> -->
                <div class='col-4' v-for="field in [session.pixelSize]" :key="field.label">
                    <label>{{field.label}}</label>
                    <input :type="field.type" step="0.01" class="form-control" id="setupSourceDir" v-model="field.value">
                </div>
                <div class='col-4' v-for="field in [session.magnification,session.totalDose,session.detectorCounts,session.frameNumber,session.tiltAngleOrScheme,session.defocusMin,session.defocusMax,session.slitWidth]" :key="field.label">
                    <label>{{field.label}}</label>
                    <input :type="field.type" class="form-control" id="setupSourceDir" v-model="field.value">
                </div>
            
    
            <!-- <label>{{session.tiltAngleOrScheme.label}}</label>
            <input :type="session.tiltAngleOrScheme.type" class="form-control" id="setupTiltAngleOrScheme" v-model="session.tiltAngleOrScheme.value"> -->
            </div>  
            <button v-if="!submitting" class="btn btn-primary" @click="submit">Submit</button>
            
            <button v-if="submitting" class="btn btn-primary" type="button" disabled>
            <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
            <span class="sr-only">Loading...</span>
            </button>
            <div v-if="submitResponse != null" class="alert alert-success fade show position-absolute top-50 start-50 translate-middle w-50 d-flex row justify-content-between align-items-center" role="alert"> 
                <h4>Session {{submitResponse.session}} successfully created</h4>
                <p>Run the following commands to start the session</p>
                <ul class="list-group">
                    <li v-for="command in submitResponse.commands" :key="command" class="list-group-item">{{command}}</li>
                </ul>
                <div class="d-flex justify-content-end position-absolute top-0 end-0">
                    <button class="btn btn-sm btn-transparent py-0" on-click="close">&times;</button>
                </div>
            </div>
        </div>
    
    </form>
</template>

<script>
import { computed, reactive, ref } from 'vue';
import { store } from '@/store';
import fetchingAPI from '../plugins/fectchingAPI.js'
import postingAPI from '../plugins/postingAPI.js'

export default {
    name: 'SetupRun',
    setup() {
        const setToday = () => {
            let date = new Date()
            return `${date.getFullYear()}-${date.getMonth()+1}-${String(date.getDate()).padStart(2,'0')}`
        }
        const session = reactive({
            sourceDir: {
                type: 'text',
                label: 'Source Directory',
                value: ""
            },
            group: {
                type: 'choice',
                label: 'Group',
                value: "",
                choices: computed({
                    get: () => { let list = [];
                        Object.keys(store.groups).forEach(element => { console.log(element);
                            list.push(store.groups[element].name) }); return list }
                }),
            },
            project: {
                label: 'Project',
                value: "",
                choices: []
            },
            sample: {
                type: 'text',
                label: 'Sample name',
                value: "",
            },
            scope: {
                label: "Microscope",
                value: "",
                choices: [],
            },
            magnification: {
                type: 'number',
                value: 0,
                label: 'Magnification'
            },
            pixelSize: {
                type: 'number',
                value: 0,
                label: 'Pixel Size'
            },
            totalDose: {
                type: 'number',
                value: 0,
                label: 'Total Dose'
            },
            frameNumber: {
                type: 'number',
                value: 0,
                label: 'Total Frames'
            },
            detectorCounts: {
                type: 'number',
                value: 0,
                label: 'Detector Counts'
            },
            defocusMin: {
                type: 'number',
                value: 0,
                label: 'Min Defocus'
            },
            defocusMax: {
                type: 'number',
                value: 0,
                label: 'Max Defocus'
            },            
            slitWidth: {
                type: 'number',
                value: 0,
                label: 'Energy Filter Slit Width'
            },

            tiltAngleOrScheme: {
                type: 'text',
                value: '0',
                label: 'Tilt Angle or Tilt Scheme'
            },
            filesPattern: {
                type: 'text',
                value: null,
                label: 'File pattern'
            },
            gainReference: {
                type: 'text',
                value: null,
                label: 'Gain Reference'
            },
            date: {
                type: 'date',
                value: setToday(),
                label: 'Date'
            }
        })


        const { response, errors, fetching, fetchData } = fetchingAPI('scopes/')
        fetchData()
        console.log(response, errors, fetching)
        if (errors.value == null) {
            session.scope.choices = response
        }
        const sourcePathList = []
        const gainReferencePathList = []
        const submitting = ref(false)
        const submitResponse = null
        return { session, gainReferencePathList, sourcePathList, submitting, submitResponse}
    },
    methods: {
        checkPaths(value, pathListVar) {
            console.log(value, this[pathListVar])
            const { response, errors, fetching, fetchData } = fetchingAPI(`path/?value=${value}`)
            fetchData()
            console.log(response, errors, fetching)
            if (errors.value == null) {

                this[pathListVar] = response
            }
        },
        autoComplete(valueVar, pathListVar) {
            if (this[pathListVar].length == 1) {
                this.session[valueVar].value = this[pathListVar][0]
            }
        },
        async submit(e) {
            e.preventDefault()
            const { response, errors, fetching, postData } = postingAPI('session/setup/', this.sessionValues)
            this.submitting = fetching.value
            await postData()
            
            console.log(errors.value)
            if (errors.value == null) {
                console.log(response.value)
                this.submitResponse= response.value
            }
            this.submitting = fetching.value
            return { response, errors, fetching }
        },
        fakesubmit(e) {
            e.preventDefault()
            this.submitting = true
            console.log(this.submitting)
        }

    },
    computed: {
        sessionValues() {
            let session = {}

            Object.keys(this.session).forEach(element => {
                session[element] = this.session[element].value
            });
            return session
        },
        projectChoices() {
            let list = [];
            if (this.session.group.value == "") {
                return list
            }
            let projects = store.groups[this.session.group.value].projects
            console.log(this.session.group.value, projects)

            projects.forEach(element => {
                console.log(element);
                list.push(element.name)
            });
            return list
        }
    }

}
</script>