<script setup lang="ts">
import { defineModel } from 'vue';
import { NIcon, NTooltip, NSwitch } from 'naive-ui';
import { CountIcon } from '../icons';

const value = defineModel({ default: false });

</script>

<template>
    <n-tooltip>
        <template #trigger>
            <n-switch v-model:value="value">
                <template #checked>
                    <n-icon size="large" :component="CountIcon" />
                </template>
                <template #unchecked>
                    <n-icon size="large" :component="CountIcon" />
                </template>
            </n-switch>
        </template>
        Statistics
    </n-tooltip>
</template>
