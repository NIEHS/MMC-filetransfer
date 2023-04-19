<template>
<div class="row w-100">
    <div  
        data-bs-toggle="tooltip"
        data-bs-placement="right"
        :title="date"
        ref="info" class="col-auto"><BIconCaretRightFill></BIconCaretRightFill></div>
    
    <small class="col-auto">{{msg}}</small>
</div>

</template>

<script>
import { BIconCaretRightFill } from 'bootstrap-icons-vue'
import { Tooltip } from 'bootstrap'
import { onMounted, ref } from 'vue'

export default {
    name: 'LogLine',
    components: {
        BIconCaretRightFill,
    },
    props: {
        line: String
    },
    setup(props) {
      let match = props.line.match(/(.*)\s\[(.*)\s-[\s]+([A-Z]+)\][\s]+(.*)/)
      const info = ref(null);
      onMounted(() => {
       new Tooltip(info.value)
      })
      
      if (match != null) {
      return {  raw:match[0],
                date:match[1],
                file:match[2],
                level: match[3],
                msg:match[4],
                info
            }
      }
      return {  raw:props.line,
                date:'',
                file:'',
                level: '',
                msg: props.line,
                info
            }
    }
}
</script>