<script setup lang="ts">
import { NButton, NIcon } from 'naive-ui'
import { LinkIcon } from '../icons'
import { computed } from 'vue';

const props = withDefaults(defineProps<{
    url?: string,
    entry: string,
    text?: boolean,
    icon?: boolean,
}>(), { text: true, icon: false });

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
    <n-button :href="entryUrl" tag="a" text :style="{ 'user-select': 'auto' }">
        <template #icon>
            <n-icon v-if="icon" :component="LinkIcon" />
        </template>
        {{ text ? entry : "" }}</n-button>
</template>