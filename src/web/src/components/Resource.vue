<script setup lang="ts">
import { onMounted, watch, onBeforeUnmount } from 'vue';

const props = defineProps<{
    css?: string[],
}>();

const headElement = document.getElementsByTagName("head")[0];
const elements: Node[] = [];

function reset() {
    for (let item of elements)
        headElement.removeChild(item);
    elements.length = 0;
}

function apply() {
    reset();

    if (props.css != null) {
        for (let item of props.css) {
            let link = document.createElement("link");
            link.type = "text/css";
            link.rel = "stylesheet";
            link.href = item;
            headElement.appendChild(link);
            elements.push(link);
        }
    }
}

onMounted(apply);
watch(props, apply);
onBeforeUnmount(reset);
</script>