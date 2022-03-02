<script setup lang="ts">
import { NIcon, NTime, NSpace, NTooltip, NTag } from 'naive-ui'
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
                <span>{{ props.duration.toFixed(2) }} s</span>
            </n-tag>
        </template>
        <span>Duration:</span>&nbsp;
        <span>{{ props.duration }} s</span>
    </n-tooltip>
</template>