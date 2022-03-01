<script setup lang="ts">
import { NSpace, NDescriptions, NDescriptionsItem, NCard, NPopover } from 'naive-ui'
import { Distribution } from '../../models'
import { ApiEntry } from '../../models/description';
import { DiffEntry } from '../../models/difference';
import ApiEntryViewer from './ApiEntryViewer.vue';

const props = defineProps<{
    entry: DiffEntry
}>();

</script>

<template>
    <n-space vertical>
        <n-descriptions :title="entry.message" :column="5">
            <n-descriptions-item>
                <template #label>Kind</template>
                {{ entry.kind }}
            </n-descriptions-item>
            <n-descriptions-item>
                <template #label>Rank</template>
                {{ entry.rank }}
            </n-descriptions-item>
            <n-descriptions-item v-if="entry.old">
                <template #label>Old</template>
                <n-popover>
                    <template #trigger>{{ entry.old.id }}</template>
                    <ApiEntryViewer :entry="entry.old" />
                </n-popover>
            </n-descriptions-item>
            <n-descriptions-item v-if="entry.new">
                <template #label>New</template>
                <n-popover>
                    <template #trigger>{{ entry.new.id }}</template>
                    <ApiEntryViewer :entry="entry.new" />
                </n-popover>
            </n-descriptions-item>
            <n-descriptions-item>
                <template #label>Id</template>
                {{ entry.id }}
            </n-descriptions-item>
        </n-descriptions>
    </n-space>
</template>
