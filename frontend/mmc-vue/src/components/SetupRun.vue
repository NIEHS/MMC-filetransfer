<template>
<form>
    <div class="form-group">
        <label>Source Directory</label>    <input class="form-control" id="setupSourceDir" v-model="session.sourceDir">
        
    </div>

</form>

</template>

<script>
import { reactive } from 'vue';

export default {
    name: 'SetupRun',
    setup() {
        const session = reactive({
            sourceDir: "",
            group: "",
            project: "",
            sample: "",
        
            scope: "",
            magnification: 0,
            pixelSize: 0,
            totalDose: 0,
            frameNumber: 0,
            detectorCounts: 0,

            mode: 'spr',
            tiltAngleOrScheme: '0',
            filesPattern: null,
            gainReference: null,
            date: 'YYYYMMDD',

            status: 'created',
            startTime: null,
            endTime: null,
            durationInHours: null,
            numberOfMovies: null,
        })
        return {session}
    }
}

</script>