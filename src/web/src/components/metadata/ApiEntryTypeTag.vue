<script setup lang="ts">
import { NTag, NTooltip } from 'naive-ui'
import { ApiEntry, ModuleEntry, ClassEntry, FunctionEntry, AttributeEntry } from '../../models/description';

defineProps<{
    entry: ApiEntry,
}>();

</script>

<template>
    <n-tooltip v-if="entry instanceof ModuleEntry">
        <template #trigger>
            <n-tag type="info" round>M</n-tag>
        </template>
        Module
    </n-tooltip>
    <n-tooltip v-if="entry instanceof ClassEntry">
        <template #trigger>
            <n-tag type="warning" round>C</n-tag>
        </template>
        Class
    </n-tooltip>
    <n-tooltip v-if="entry instanceof FunctionEntry">
        <template #trigger>
            <n-tag type="success" round>F</n-tag>
        </template>
        Function
    </n-tooltip>
    <n-tooltip v-if="entry instanceof AttributeEntry">
        <template #trigger>
            <n-tag type="error" round>A</n-tag>
        </template>
        Attribute
    </n-tooltip>
</template>