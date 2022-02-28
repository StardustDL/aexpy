<script setup lang="ts">
import { NIcon, NTime, NSpace, NTooltip } from 'naive-ui'
import { Clock } from '@vicons/tabler'

const props = defineProps<{
    creation: Date,
}>();

</script>

<script lang="ts">
export default {
    components: {
        Clock,
    }
}
</script>

<template>
    <n-tooltip>
        <template #trigger>
            <n-space size="small">
                <n-icon size="large">
                    <clock />
                </n-icon>
                <n-time :time="props.creation" type="relative"></n-time>
            </n-space>
        </template>
        <span>Creation:</span>&nbsp;
        <n-time :time="props.creation"></n-time>
    </n-tooltip>
</template>