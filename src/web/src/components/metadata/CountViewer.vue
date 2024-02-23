<script setup lang="ts">
import { NStatistic, NFlex, NProgress, NText } from 'naive-ui'
import { computed } from 'vue';

const props = defineProps<{
    value?: number,
    total?: number,
    label?: string,
    inline?: boolean,
    status?: 'default' | 'success' | 'error' | 'warning' | 'info'
}>();

const rate = computed(() => {
    if (props.value && props.total) {
        if (props.total > 0) {
            return Math.round(props.value / props.total * 100);
        }
    }
    return 0;
})

</script>

<template>
    <n-flex v-if="inline">
        <n-progress :percentage="rate" :status="status ?? 'default'" indicator-placement="inside">
            {{ (label ?? "") + " " + value + (total ? ` / ${total} ( ${rate} % )` : '') }}
        </n-progress>
    </n-flex>
    <n-statistic :value="value" v-else>
        <template #label>
            <n-text v-if="label">{{ label }}</n-text>
            <slot name="label"></slot>
        </template>
        <template #prefix>
            <n-progress :percentage="rate" v-if="total" :status="status ?? 'default'" indicator-placement="inside" />
        </template>
        <template #suffix>
            <n-text v-if="total">/ {{ total }}</n-text>
        </template>
    </n-statistic>
</template>