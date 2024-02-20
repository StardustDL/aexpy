<script setup lang="ts">
import { defineModel } from 'vue';
import { NIcon, NTooltip, NSwitch } from 'naive-ui';
import { DistributionIcon } from '../icons';

const value = defineModel({ default: false });

</script>

<template>
    <n-tooltip>
        <template #trigger>
            <n-switch v-model:value="value">
                <template #checked>
                    <n-icon size="large" :component="DistributionIcon" />
                </template>
                <template #unchecked>
                    <n-icon size="large" :component="DistributionIcon" />
                </template>
            </n-switch>
        </template>
        Distribution
    </n-tooltip>
</template>
