<script setup lang="ts">
import { defineModel } from 'vue';
import { NIcon, NTooltip, NSwitch } from 'naive-ui';
import { LogIcon } from '../icons';

const value = defineModel({ default: false });
const emit = defineEmits<{
    update: [value: boolean]
}>();

function onUpdateValue(newVal: boolean) {
    emit('update', newVal)
}

</script>

<template>
    <n-tooltip>
        <template #trigger>
            <n-switch v-model:value="value" @update-value="onUpdateValue">
                <template #checked>
                    <n-icon size="large" :component="LogIcon" />
                </template>
                <template #unchecked>
                    <n-icon size="large" :component="LogIcon" />
                </template>
            </n-switch>
        </template>
        Log
    </n-tooltip>
</template>
