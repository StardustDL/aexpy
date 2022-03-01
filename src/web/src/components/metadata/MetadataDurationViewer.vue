<script setup lang="ts">
import { NIcon, NTime, NSpace, NTooltip } from 'naive-ui'
import { Dashboard } from '@vicons/tabler'

const props = defineProps<{
    duration: number,
}>();

</script>

<template>
    <n-tooltip>
        <template #trigger>
            <n-space size="small">
                <n-icon size="large">
                    <Dashboard />
                </n-icon>
                <span>{{ props.duration }} s</span>
            </n-space>
        </template>
        <span>Duration:</span>&nbsp;
        <span>{{ props.duration }} s</span>
    </n-tooltip>
</template>