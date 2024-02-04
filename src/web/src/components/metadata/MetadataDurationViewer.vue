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
                {{ props.duration.toFixed(2) }} s
            </n-tag>
        </template>
        Duration:&nbsp; {{ props.duration }} s
    </n-tooltip>
</template>