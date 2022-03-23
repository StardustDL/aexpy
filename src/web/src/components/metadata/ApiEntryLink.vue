<script setup lang="ts">
import { NIcon, NStatistic, NProgress, NSpace, NTooltip, NTag, NAvatar, NText, NButton } from 'naive-ui'
import { FaceId, FaceIdError } from '@vicons/tabler'
import { computed } from 'vue';

const props = defineProps<{
    url?: string,
    entry: string,
}>();

const entryUrl = computed(() => {
    if (props.url == undefined) {
        return "";
    }
    if (props.url.indexOf("?") > 0) {
        return `${props.url}&entry=${props.entry}`;
    }
    return `${props.url}?entry=${props.entry}`;
});

</script>

<template>
    <n-button
        :href="entryUrl"
        tag="a"
        target="_blank"
        text
        :style="{ 'user-select': 'auto' }"
    >{{ entry }}</n-button>
</template>