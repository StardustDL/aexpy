<script setup lang="ts">
import { h } from 'vue';
import { NSpace, NText,NDescriptions, NDescriptionsItem, NEllipsis, NScrollbar, NDataTable, DataTableColumns } from 'naive-ui'
import { Distribution } from '../../models'
import { ApiEntry, CollectionEntry, ItemEntry, ClassEntry, FunctionEntry, AttributeEntry, ModuleEntry, Parameter, ParameterKind } from '../../models/description';

const props = defineProps<{
    entry: ApiEntry
}>();


const columns: DataTableColumns<Parameter> = [
    {
        title: 'Name',
        key: 'name'
    },
    {
        title: 'Kind',
        key: 'kind',
        render(row) {
            switch (row.kind) {
                case ParameterKind.Keyword: return 'Keyword';
                case ParameterKind.Positional: return 'Positional';
                case ParameterKind.PositionalOrKeyword: return 'PositionalOrKeyword';
                case ParameterKind.VarKeyword: return 'VarKeyword';
                case ParameterKind.VarPositional: return 'VarPositional';
                case ParameterKind.VarKeywordCandidate: return 'VarKeywordCandidate';
            }
        }
    },
    {
        title: 'Optional',
        key: 'optional',
        render(row) {
            return row.optional ? h(NText, { type: "success" }, "Optional") : h(NText, { type: "warning" }, "Required");
        }
    },
    {
        title: 'Default',
        key: 'default'
    },
    {
        title: 'Type',
        key: 'type'
    },
    {
        title: 'Annotation',
        key: 'annotation'
    },
    {
        title: 'Source',
        key: 'source',
    }
];

console.log(props.entry);

</script>

<template>
    <n-descriptions :title="entry.id" :column="1">
        <n-descriptions-item>
            <template #label>Name</template>
            {{ entry.name }}
        </n-descriptions-item>
        <n-descriptions-item v-if="entry.docs.length > 0">
            <template #label>Document</template>
            {{ entry.docs }}
        </n-descriptions-item>
        <n-descriptions-item v-if="entry.comments.length > 0">
            <template #label>Comment</template>
            {{ entry.comments }}
        </n-descriptions-item>
        <n-descriptions-item v-if="entry.location">
            <template #label>Location</template>
            {{ entry.location.file }}:{{ entry.location.line }}:{{ entry.location.module }}
        </n-descriptions-item>
        <n-descriptions-item v-if="entry instanceof ItemEntry">
            <template #label>Bound</template>
            {{ entry.bound }}
        </n-descriptions-item>
        <n-descriptions-item v-if="entry instanceof ClassEntry">
            <template #label>Base Classes</template>
            <n-space vertical>
                <span v-for="item in entry.bases" :key="item">{{ item }}</span>
            </n-space>
        </n-descriptions-item>
        <n-descriptions-item v-if="entry instanceof ClassEntry">
            <template #label>Abstract Base Classes</template>
            <n-space vertical>
                <span v-for="item in entry.abcs" :key="item">{{ item }}</span>
            </n-space>
        </n-descriptions-item>
        <n-descriptions-item v-if="entry instanceof ClassEntry">
            <template #label>Method Resolution Order</template>
            <n-space vertical>
                <span v-for="item in entry.mro" :key="item">{{ item }}</span>
            </n-space>
        </n-descriptions-item>
        <n-descriptions-item v-if="entry instanceof ClassEntry">
            <template #label>Slots</template>
            <n-space vertical>
                <span v-for="item in entry.slots" :key="item">{{ item }}</span>
            </n-space>
        </n-descriptions-item>
        <n-descriptions-item v-if="entry instanceof FunctionEntry">
            <template #label>Parameters</template>
            <n-data-table :columns="columns" :data="entry.parameters" />
        </n-descriptions-item>
        <n-descriptions-item v-if="entry instanceof CollectionEntry">
            <template #label>Members</template>
            <n-scrollbar style="max-height: 200px;">
                <n-space vertical>
                    <span v-for="item, key in entry.members" :key="key">{{ key }}: {{ item }}</span>
                </n-space>
            </n-scrollbar>
        </n-descriptions-item>
    </n-descriptions>
</template>
