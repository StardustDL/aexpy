<script setup lang="ts">
import { NIcon, NTime, NSpace, NTooltip, NTag, NText } from 'naive-ui'
import { Dashboard } from '@vicons/tabler'

const props = defineProps<{
    duration: number,
}>();

</script>

<template>
    <n-tooltip>
        <template #trigger>
            <n-tag>
                <template #avatar>
                    <n-icon size="medium">
                        <Dashboard />
                    </n-icon>
                </template>
                <n-text>{{ props.duration.toFixed(2) }} s</n-text>
            </n-tag>
        </template>
        <n-text>Duration:</n-text>&nbsp;
        <n-text>{{ props.duration }} s</n-text>
    </n-tooltip>
</template>