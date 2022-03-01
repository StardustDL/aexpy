<script setup lang="ts">
import { ref } from 'vue'
import { NIcon, NTime, NSpace, NTooltip, NCheckbox, NSwitch } from 'naive-ui'
import { Dashboard } from '@vicons/tabler'
import { ProducerOptions } from '../../models';

const props = defineProps<{
    options: ProducerOptions,
}>();

const redo = ref(false);
const cached = ref<boolean>(false);
const onlyCache = ref(false);

function onRedo(checked: boolean) {
    if (!checked) {
        props.options.redo = undefined;
    }
    else {
        props.options.redo = false;
    }
    redo.value = checked;
}

function onSetRedo(checked: boolean) {
    props.options.redo = checked;
}

function onCached(checked: boolean) {
    if (!checked) {
        props.options.cached = undefined;
    }
    else {
        props.options.cached = true;
    }
    cached.value = checked;
}

function onSetCached(checked: boolean) {
    props.options.cached = checked;
}

function onOnlyCache(checked: boolean) {
    if (!checked) {
        props.options.onlyCache = undefined;
    }
    else {
        props.options.onlyCache = false;
    }
    onlyCache.value = checked;
}

function onSetOnlyCache(checked: boolean) {
    props.options.onlyCache = checked;
}

</script>

<template>
    <n-space>
        <n-checkbox label="Cached" @update-checked="onCached"></n-checkbox>
        <n-switch :value="options.cached" :disabled="!cached" @update-value="onSetCached"></n-switch>
        <n-checkbox label="Only cache" @update-checked="onOnlyCache"></n-checkbox>
        <n-switch :value="options.onlyCache" :disabled="!onlyCache" @update-value="onSetOnlyCache"></n-switch>
        <n-checkbox label="Redo" @update-checked="onRedo"></n-checkbox>
        <n-switch :value="options.redo" :disabled="!redo" @update-value="onSetRedo"></n-switch>
    </n-space>
</template>