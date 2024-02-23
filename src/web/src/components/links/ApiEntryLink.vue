<script setup lang="ts">
import { NButton, NFlex, NIcon } from 'naive-ui'
import { LinkIcon } from '../icons'
import { Component, computed } from 'vue'

const props = withDefaults(defineProps<{
    url?: string,
    entry: string,
    text?: boolean,
    icon?: boolean,
    iconComponent?: Component
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
    <span>
        <router-link :to="entryUrl" custom v-slot="{ href, navigate }">
            <n-button tag="a" :href="href" @click="navigate" text>
                <template #icon>
                    <n-icon v-if="icon" :component="iconComponent ?? LinkIcon" />
                </template>
                {{ text ? entry : "" }}
            </n-button>
        </router-link>
    </span>
</template>