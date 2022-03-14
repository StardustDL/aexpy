<script setup lang="ts">
import { NIcon, NStatistic, NProgress, NSpace, NTooltip, NTag, NAvatar, NText } from 'naive-ui'
import { FaceId, FaceIdError } from '@vicons/tabler'
import { computed } from 'vue';

const props = defineProps<{
    value: number,
    total?: number,
    label?: string,
    status?: 'default' | 'success' | 'error' | 'warning' | 'info'
}>();

const rate = computed(() => {
    if (props.total) {
        return Math.round(props.value / props.total * 100);
    }
    return 0;
})

</script>

<template>
    <n-statistic :value="value">
        <template #label>
            <n-text v-if="label">{{ label }}</n-text>
            <slot name="label"></slot>
        </template>
        <template #prefix>
            <n-progress :percentage="rate" v-if="total" :status="status ?? 'default'" indicator-placement="inside"/>
        </template>
        <template #suffix>
            <n-text v-if="total">/ {{ total }}</n-text>
        </template>
    </n-statistic>
</template>