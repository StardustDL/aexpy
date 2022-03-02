<script setup lang="ts">
import { ref } from 'vue'
import { NIcon, NTime, NSpace, NTooltip, NCheckbox, NSwitch } from 'naive-ui'
import { Dashboard, File, FileOff, Refresh } from '@vicons/tabler'
import { ProducerOptions } from '../../models';

const props = defineProps<{
    options: ProducerOptions,
}>();

const redo = ref(false);
const cached = ref(false);
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
        <n-checkbox @update-checked="onCached">Cached</n-checkbox>
        <n-switch :value="options.cached != undefined ? options.cached : true" :disabled="!cached" @update-value="onSetCached">
            <template #unchecked>
                <n-icon>
                    <FileOff />
                </n-icon>
            </template>
        </n-switch>

        <n-checkbox @update-checked="onOnlyCache">Only cache</n-checkbox>
        <n-switch :value="options.onlyCache" :disabled="!onlyCache" @update-value="onSetOnlyCache">
            <template #checked>
                <n-icon>
                    <File />
                </n-icon>
            </template>
        </n-switch>

        <n-checkbox @update-checked="onRedo">Redo</n-checkbox>
        <n-switch :value="options.redo" :disabled="!redo" @update-value="onSetRedo">
            <template #checked>
                <n-icon>
                    <Refresh />
                </n-icon>
            </template>
        </n-switch>
    </n-space>
</template>