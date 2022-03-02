<script setup lang="ts">
import { computed, h } from 'vue';
import { NSpace, NText, NPopover, NH5, NH6, NDescriptions, NTag, NDescriptionsItem, NEllipsis, NScrollbar, NDataTable, DataTableColumns } from 'naive-ui'
import { Distribution } from '../../models'
import { ApiEntry, CollectionEntry, ItemEntry, ClassEntry, FunctionEntry, AttributeEntry, ModuleEntry, Parameter, ParameterKind } from '../../models/description';

const props = defineProps<{
    entry: ApiEntry
}>();

const memberColumns: DataTableColumns<{ key: string, value: string }> = [
    {
        title: 'Name',
        key: 'key'
    },
    {
        title: 'Target',
        key: 'value',
    },
];

const members = computed(() => {
    if (props.entry instanceof CollectionEntry) {
        let mem = props.entry.members;
        return Object.keys(mem).map(k => { return { key: k, value: mem[k] }; });
    }
    return [];
});

const parameterColumns: DataTableColumns<Parameter> = [
    {
        title: 'Name',
        key: 'name',
        render(row) {
            return h(NText, { strong: true, underline: true }, row.name);
        }
    },
    {
        title: 'Kind',
        key: 'kind',
        render(row) {
            let kwd = h(NText, { type: "info" }, 'Keyword');
            let pos = h(NText, { type: "success" }, 'Positional');
            let va = h(NText, { type: "warning" }, 'Var');
            switch (row.kind) {
                case ParameterKind.Keyword: return kwd;
                case ParameterKind.Positional: return pos;
                case ParameterKind.PositionalOrKeyword: return h(NSpace, {}, [pos, "Or", kwd]);
                case ParameterKind.VarKeyword: return h(NSpace, {}, [va, kwd]);
                case ParameterKind.VarPositional: return h(NSpace, {}, [va, pos]);
                case ParameterKind.VarKeywordCandidate: return h(NSpace, {}, [va, kwd, "Candidate"]);
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

</script>

<template>
    <n-descriptions :column="1">
        <template #header>
            <n-popover>
                <template #trigger>
                    <n-space>
                        <n-tag type="info" round v-if="entry instanceof ModuleEntry">Module</n-tag>
                        <n-tag type="warning" round v-if="entry instanceof ClassEntry">Class</n-tag>
                        <n-tag type="success" round v-if="entry instanceof FunctionEntry">Function</n-tag>
                        <n-tag type="error" round v-if="entry instanceof AttributeEntry">Attribute</n-tag>

                        <n-text type="info">{{ entry.name }}</n-text>
                        ({{ entry.id }})
                        <n-tag
                            v-if="entry instanceof ItemEntry"
                            :type="entry.bound ? 'warning' : 'info'"
                        >{{ entry.bound ? 'Bound' : 'Unbound' }}</n-tag>
                    </n-space>
                </template>
                <n-descriptions>
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
                </n-descriptions>
            </n-popover>
        </template>
        <n-descriptions-item v-if="entry instanceof ClassEntry && entry.bases.length > 0">
            <template #label>
                <n-h6 type="info" prefix="bar">Base Classes</n-h6>
            </template>
            <n-space vertical>
                <span v-for="item in entry.bases" :key="item">{{ item }}</span>
            </n-space>
        </n-descriptions-item>
        <n-descriptions-item v-if="entry instanceof ClassEntry && entry.abcs.length > 0">
            <template #label>
                <n-h6 type="info" prefix="bar">Abstract Base Classes</n-h6>
            </template>
            <n-space vertical>
                <span v-for="item in entry.abcs" :key="item">{{ item }}</span>
            </n-space>
        </n-descriptions-item>
        <n-descriptions-item v-if="entry instanceof ClassEntry && entry.mro.length > 0">
            <template #label>
                <n-h6 type="info" prefix="bar">Method Resolution Order</n-h6>
            </template>
            <n-space vertical>
                <span v-for="item in entry.mro" :key="item">{{ item }}</span>
            </n-space>
        </n-descriptions-item>
        <n-descriptions-item v-if="entry instanceof ClassEntry && entry.slots.length > 0">
            <template #label>
                <n-h6 type="info" prefix="bar">Slots</n-h6>
            </template>
            <n-space vertical>
                <span v-for="item in entry.slots" :key="item">{{ item }}</span>
            </n-space>
        </n-descriptions-item>
        <n-descriptions-item v-if="entry instanceof FunctionEntry">
            <template #label>
                <n-h6 type="info" prefix="bar">Parameters</n-h6>
            </template>
            <n-data-table :columns="parameterColumns" :data="entry.parameters" />
        </n-descriptions-item>
        <n-descriptions-item v-if="entry instanceof CollectionEntry">
            <template #label>
                <n-h6 type="info" prefix="bar">Members</n-h6>
            </template>
            <n-data-table :columns="memberColumns" :data="members" />
        </n-descriptions-item>
    </n-descriptions>
</template>
