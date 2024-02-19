<script setup lang="ts">
import { NTag } from 'naive-ui'
import { ApiEntry, ModuleEntry, ClassEntry, FunctionEntry, AttributeEntry } from '../../models/description';

defineProps<{
    entry: ApiEntry,
}>();

</script>

<template>
    <n-tag type="info" round v-if="entry instanceof ModuleEntry">Module</n-tag>
    <n-tag type="warning" round v-if="entry instanceof ClassEntry">Class</n-tag>
    <n-tag type="success" round v-if="entry instanceof FunctionEntry">Function</n-tag>
    <n-tag type="error" round v-if="entry instanceof AttributeEntry">Attribute</n-tag>
</template>