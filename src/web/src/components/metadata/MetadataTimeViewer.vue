<script setup lang="ts">
import { NIcon, NTime, NFlex, NTooltip, NTag, NText } from 'naive-ui'
import { Clock } from '@vicons/tabler'

const props = defineProps<{
    creation: Date,
}>();

</script>

<template>
    <n-tooltip>
        <template #trigger>
            <n-tag>
                <template #avatar>
                    <n-icon size="medium" :component="Clock" />
                </template>
                <n-time :time="props.creation" type="relative"></n-time>
            </n-tag>
        </template>
        Creation:&nbsp;
        <n-time :time="props.creation"></n-time>
    </n-tooltip>
</template>