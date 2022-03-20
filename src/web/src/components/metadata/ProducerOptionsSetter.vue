<script setup lang="ts">
import { ref } from 'vue'
import { NIcon, NTime, NSpace, NTooltip, NCheckbox, NSwitch } from 'naive-ui'
import { Dashboard, File, FileOff, Refresh } from '@vicons/tabler'
import { ProducerOptions } from '../../models';

const props = defineProps<{
    options: ProducerOptions,
}>();

const redo = ref(false);
const nocache = ref(false);
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

function onNocache(checked: boolean) {
    if (!checked) {
        props.options.nocache = undefined;
    }
    else {
        props.options.nocache = false;
    }
    nocache.value = checked;
}

function onSetCached(checked: boolean) {
    props.options.nocache = checked;
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
        <n-checkbox @update-checked="onNocache" size="large">No Cache</n-checkbox>
        <n-switch :value="options.nocache != undefined ? options.nocache : false" :disabled="!nocache" @update-value="onSetCached">
            <template #checked>
                <n-icon>
                    <FileOff />
                </n-icon>
            </template>
        </n-switch>

        <n-checkbox @update-checked="onOnlyCache" size="large">Only cache</n-checkbox>
        <n-switch :value="options.onlyCache" :disabled="!onlyCache" @update-value="onSetOnlyCache">
            <template #checked>
                <n-icon>
                    <File />
                </n-icon>
            </template>
        </n-switch>

        <n-checkbox @update-checked="onRedo" size="large">Redo</n-checkbox>
        <n-switch :value="options.redo" :disabled="!redo" @update-value="onSetRedo">
            <template #checked>
                <n-icon>
                    <Refresh />
                </n-icon>
            </template>
        </n-switch>
    </n-space>
</template>