<script setup lang="ts">
import { NTag } from 'naive-ui'
import { ApiEntry, ModuleEntry, ClassEntry, FunctionEntry, AttributeEntry, ItemEntry, ItemScope } from '../../models/description';

defineProps<{
    entry: ApiEntry,
}>();

</script>

<template>
    <n-tag v-if="entry.private" type="error">Private</n-tag>
    <n-tag v-if="(entry instanceof ItemEntry)" :type="entry.scope != ItemScope.Static ? 'warning' : 'info'">{{
        ItemScope[entry.scope]
    }}</n-tag>
    <n-tag v-if="(entry instanceof ClassEntry && entry.abstract)" type="error">Abstract</n-tag>
    <n-tag v-if="(entry instanceof FunctionEntry && entry.abstract)" type="error">Abstract</n-tag>
    <n-tag v-if="(entry instanceof AttributeEntry && entry.property)" type="success">Property</n-tag>
    <n-tag v-if="(entry instanceof FunctionEntry && entry.override)" type="success">Override</n-tag>
    <n-tag v-if="(entry instanceof FunctionEntry && entry.coroutine)" type="error">Async</n-tag>
    <n-tag v-if="(entry instanceof FunctionEntry && entry.transmitKwargs)">Transmit Kwargs</n-tag>
</template>