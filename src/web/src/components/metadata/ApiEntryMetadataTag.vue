<script setup lang="ts">
import { NTag } from 'naive-ui'
import { ApiEntry, ModuleEntry, ClassEntry, FunctionEntry, AttributeEntry, ClassFlag, ItemEntry, ItemScope, FunctionFlag } from '../../models/description';

defineProps<{
    entry: ApiEntry,
}>();

</script>

<template>
    <n-tag v-if="entry.private" type="error">Private</n-tag>
    <n-tag v-if="(entry instanceof ItemEntry)" :type="entry.scope != ItemScope.Static ? 'warning' : 'info'">{{
        ItemScope[entry.scope]
    }}</n-tag>
    <n-tag v-if="(entry instanceof ClassEntry && entry.flags | ClassFlag.Abstract)" type="error">Abstract</n-tag>
    <n-tag v-if="(entry instanceof ClassEntry && entry.flags | ClassFlag.Final)" type="warning">Final</n-tag>
    <n-tag v-if="(entry instanceof ClassEntry && entry.flags | ClassFlag.Generic)" type="info">Generic</n-tag>
    <n-tag v-if="(entry instanceof ClassEntry && entry.flags | ClassFlag.Dataclass)" type="info">Dataclass</n-tag>
    <n-tag v-if="(entry instanceof FunctionEntry && entry.flags | FunctionFlag.Abstract)" type="error">Abstract</n-tag>
    <n-tag v-if="(entry instanceof FunctionEntry && entry.flags | FunctionFlag.Final)" type="warning">Final</n-tag>
    <n-tag v-if="(entry instanceof FunctionEntry && entry.flags | FunctionFlag.Generic)" type="info">Generic</n-tag>
    <n-tag v-if="(entry instanceof FunctionEntry && entry.flags | FunctionFlag.Override)" type="success">Override</n-tag>
    <n-tag v-if="(entry instanceof FunctionEntry && entry.flags | FunctionFlag.Async)" type="error">Async</n-tag>
    <n-tag v-if="(entry instanceof FunctionEntry && entry.flags | FunctionFlag.TransmitKwargs)">Transmit Kwargs</n-tag>
    <n-tag v-if="(entry instanceof AttributeEntry && entry.property)" type="success">Property</n-tag>
</template>