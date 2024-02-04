<script setup lang="ts">
import { computed, h } from 'vue';
import { NSpace, NText, NPopover, NH6, NDescriptions, NButton, NTag, NDescriptionsItem, NA, NEllipsis, NScrollbar, NDataTable, DataTableColumns, NCode, NCollapse, NCollapseItem } from 'naive-ui'
import ApiEntryLink from '../metadata/ApiEntryLink.vue';
import { ApiEntry, CollectionEntry, ItemEntry, ClassEntry, FunctionEntry, AttributeEntry, ModuleEntry, Parameter, ParameterKind, ItemScope } from '../../models/description';

const props = defineProps<{
    entry: ApiEntry,
    rawUrl?: string,
    entryUrl?: string,
}>();

const memberColumns: DataTableColumns<{ key: string, value: string }> = [
    {
        title: 'Name',
        key: 'key',
        sorter: 'default',
    },
    {
        title: 'Target',
        key: 'value',
        render(row) {
            return h(ApiEntryLink, {
                entry: row.value,
                url: props.entryUrl,
            }, {});
        }
    },
];

const members = computed(() => {
    if (props.entry instanceof CollectionEntry) {
        let mem = props.entry.members;
        return Object.keys(mem).map(k => { return { key: k, value: mem[k] }; });
    }
    return [];
});

function renderParameterKind(kind: ParameterKind) {
    let kwd = h(NText, { type: "info" }, { default: () => 'Keyword' });
    let pos = h(NText, { type: "success" }, { default: () => 'Positional' });
    let va = h(NText, { type: "warning" }, { default: () => 'Var' });
    switch (kind) {
        case ParameterKind.Keyword: return kwd;
        case ParameterKind.Positional: return pos;
        case ParameterKind.PositionalOrKeyword: return h(NSpace, {}, { default: () => [pos, "Or", kwd] });
        case ParameterKind.VarKeyword: return h(NSpace, {}, { default: () => [va, kwd] });
        case ParameterKind.VarPositional: return h(NSpace, {}, { default: () => [va, pos] });
        case ParameterKind.VarKeywordCandidate: return h(NSpace, {}, { default: () => [va, kwd, "Candidate"] });
    }
}

function renderOptional(optional: boolean) {
    return optional ? h(NText, { type: "success" }, { default: () => "Optional" }) : h(NText, { type: "warning" }, { default: () => "Required" });
}

const parameterColumns = computed(() => {

    if (!(props.entry instanceof FunctionEntry)) {
        return [];
    }

    let kinds = [];
    let optionals = [];

    let params = props.entry.parameters;
    for (let p of params) {
        if (kinds.indexOf(p.kind) == -1) {
            kinds.push(p.kind);
        }
        if (optionals.indexOf(p.optional) == -1) {
            optionals.push(p.optional);
        }
    }
    let kindFilterOptions = kinds.map(kind => { return { label: renderParameterKind(kind), value: kind }; });
    let optionalFilterOptions = optionals.map(optional => { return { label: renderOptional(optional), value: optional }; });

    return [
        {
            title: 'Pos',
            key: 'position',
            width: 80,
            sorter(row1, row2) {
                if (props.entry instanceof FunctionEntry) {
                    if (row1.kind == ParameterKind.Positional || row1.kind == ParameterKind.PositionalOrKeyword) {
                        if (row2.kind == ParameterKind.Positional || row2.kind == ParameterKind.PositionalOrKeyword) {
                            return props.entry.parameters.indexOf(row1) - props.entry.parameters.indexOf(row2);
                        }
                    }
                }
                return 0;
            },
            render(row) {
                if (props.entry instanceof FunctionEntry) {
                    if (row.kind == ParameterKind.Positional || row.kind == ParameterKind.PositionalOrKeyword) {
                        return props.entry.parameters.indexOf(row) + 1;
                    }
                }
                return "";
            }
        },
        {
            title: 'Name',
            key: 'name',
            sorter: 'default',
            render(row) {
                return h(NText, { strong: true, underline: true }, { default: () => row.name });
            }
        },
        {
            title: 'Kind',
            key: 'kind',
            width: 200,
            filterOptions: kindFilterOptions,
            defaultFilterOptionValues: kinds,
            filter: "default",
            render(row) {
                return renderParameterKind(row.kind);
            }
        },
        {
            title: 'Optional',
            key: 'optional',
            width: 120,
            filterOptions: optionalFilterOptions,
            defaultFilterOptionValues: optionals,
            filter: "default",
            render(row) {
                return renderOptional(row.optional);
            }
        },
        {
            title: 'Default',
            key: 'default'
        },
        {
            title: 'Type',
            key: 'type',
            render(row) {
                if (props.entry instanceof FunctionEntry) {
                    if (row.type) {
                        let type = row.type;
                        return h(
                            NPopover,
                            {},
                            {
                                trigger: () => type.id,
                                default: () => h(NScrollbar,
                                    { style: "max-height: 500px; max-width: 500px;", "x-scrollable": true },
                                    {
                                        default: () => h(NSpace, { vertical: true }, {
                                            default: () => [
                                                h(NText, {}, { default: () => type.raw }),
                                                h(NCode, { language: "json", code: JSON.stringify(type.data, undefined, 2) }, {}),
                                            ]
                                        })
                                    }
                                ),
                            }
                        );
                    }
                }
                return "";
            }
        },
        {
            title: 'Annotation',
            key: 'annotation'
        },
        {
            title: 'Source',
            key: 'source',
            width: 120,
            render(row) {
                if (row.source != "") {
                    return h(NEllipsis, {}, {
                        default: () => h(ApiEntryLink, {
                            entry: row.source,
                            url: props.entryUrl,
                        }, {}),
                        tooltip: () => row.source,
                    })
                }
                return "";
            }
        }
    ] as DataTableColumns<Parameter>;
});
</script>

<template>
    <n-descriptions :column="1">
        <template #header>
            <n-space>
                <n-tag type="info" round v-if="entry instanceof ModuleEntry">Module</n-tag>
                <n-tag type="warning" round v-if="entry instanceof ClassEntry">Class</n-tag>
                <n-tag type="success" round v-if="entry instanceof FunctionEntry">Function</n-tag>
                <n-tag type="error" round v-if="entry instanceof AttributeEntry">Attribute</n-tag>

                <n-popover>
                    <template #trigger>
                        <n-text type="info">{{ entry.name }}</n-text>
                    </template>
                    <n-space vertical>
                        <n-text text v-if="entry.location">{{ entry.location.file }}:{{ entry.location.line }}:{{
                            entry.location.module
                        }}</n-text>
                        <n-scrollbar style="max-height: 500px; max-width: 500px;" v-if="entry.data" x-scrollable>
                            <n-code language="json" :code="JSON.stringify(entry.data, undefined, 2)"></n-code>
                        </n-scrollbar>
                    </n-space>
                </n-popover>
                ({{ entry.id }})
                <n-tag v-if="entry.private" type="error">Private</n-tag>
                <n-tag v-if="(entry instanceof ItemEntry)" :type="entry.scope != ItemScope.Static ? 'warning' : 'info'">{{
                    ItemScope[entry.scope]
                }}</n-tag>
                <n-tag v-if="(entry instanceof AttributeEntry && entry.property)" type="success">Property</n-tag>
                <n-tag v-if="(entry instanceof FunctionEntry && entry.transmitKwargs)">Transmit Kwargs</n-tag>
            </n-space>
        </template>
        <n-descriptions-item v-if="entry.parent.length > 0">
            <template #label>
                <n-h6 type="info" prefix="bar">Parent</n-h6>
            </template>
            <ApiEntryLink :entry="entry.parent" :url="entryUrl" />
        </n-descriptions-item>
        <n-descriptions-item v-if="(entry instanceof ClassEntry && entry.bases.length > 0)">
            <template #label>
                <n-h6 type="info" prefix="bar">Base Classes</n-h6>
            </template>
            <n-space vertical>
                <ApiEntryLink v-for="item in entry.bases" :key="item" :entry="item" :url="entryUrl" />
            </n-space>
        </n-descriptions-item>
        <n-descriptions-item v-if="(entry instanceof ClassEntry && entry.abcs.length > 0)">
            <template #label>
                <n-h6 type="info" prefix="bar">Abstract Base Classes</n-h6>
            </template>
            <n-space vertical>
                <ApiEntryLink v-for="item in entry.abcs" :key="item" :entry="item" :url="entryUrl" />
            </n-space>
        </n-descriptions-item>
        <n-descriptions-item v-if="(entry instanceof ClassEntry && entry.mro.length > 0)">
            <template #label>
                <n-h6 type="info" prefix="bar">Method Resolution Order</n-h6>
            </template>
            <n-space vertical>
                <ApiEntryLink v-for="item in entry.mro" :key="item" :entry="item" :url="entryUrl" />
            </n-space>
        </n-descriptions-item>
        <n-descriptions-item v-if="(entry instanceof ClassEntry && entry.slots.length > 0)">
            <template #label>
                <n-h6 type="info" prefix="bar">Slots</n-h6>
            </template>
            <n-space vertical>
                <n-text v-for="item in entry.slots" :key="item">{{ item }}</n-text>
            </n-space>
        </n-descriptions-item>
        <n-descriptions-item v-if="(entry instanceof AttributeEntry && entry.annotation.length > 0)">
            <template #label>
                <n-h6 type="info" prefix="bar">Annotation</n-h6>
            </template>
            <n-space vertical>
                <n-text>{{ entry.annotation }}</n-text>
            </n-space>
        </n-descriptions-item>
        <n-descriptions-item
            v-if="(entry instanceof ItemEntry && (entry.type || (entry instanceof AttributeEntry && entry.rawType.length > 0)))">
            <template #label>
                <n-h6 type="info" prefix="bar">Type</n-h6>
            </template>
            <n-popover>
                <template #trigger>
                    <n-space>
                        <n-text v-if="entry.type">{{ entry.type.id }}</n-text>
                        <n-text v-if="entry instanceof AttributeEntry && entry.rawType.length > 0">( {{ entry.rawType }}
                            )</n-text>
                    </n-space>
                </template>
                <n-scrollbar style="max-height: 500px; max-width: 500px;" v-if="entry.type" x-scrollable>
                    <n-space vertical>
                        <n-text>{{ entry.type.raw }}</n-text>
                        <n-code language="json" :code="JSON.stringify(entry.type.data, undefined, 2)"></n-code>
                    </n-space>
                </n-scrollbar>
            </n-popover>
        </n-descriptions-item>
        <n-descriptions-item
            v-if="(entry instanceof FunctionEntry && (entry.returnType || entry.returnAnnotation.length > 0))">
            <template #label>
                <n-h6 type="info" prefix="bar">Return Type</n-h6>
            </template>
            <n-popover>
                <template #trigger>
                    <n-space>
                        <n-text v-if="entry.returnType">{{ entry.returnType.id }}</n-text>
                        <n-text v-if="entry.returnAnnotation.length > 0">( {{ entry.returnAnnotation }} )</n-text>
                    </n-space>
                </template>
                <n-scrollbar style="max-height: 500px; max-width: 500px;" v-if="entry.returnType" x-scrollable>
                    <n-space vertical>
                        <n-text>{{ entry.returnType.raw }}</n-text>
                        <n-code language="json" :code="JSON.stringify(entry.returnType.data, undefined, 2)"></n-code>
                    </n-space>
                </n-scrollbar>
            </n-popover>
        </n-descriptions-item>
        <n-descriptions-item
            v-if="(entry instanceof FunctionEntry && (entry.callers.length > 0 || entry.callees.length > 0)) || (entry.src.length > 0) || (entry.alias.length > 0) || (entry.docs.length > 0) || (entry.comments.length > 0)">
            <template #label>
                <n-h6 type="info" prefix="bar">Code Related</n-h6>
            </template>
            <n-collapse>
                <n-collapse-item title="Aliases" v-if="entry.alias.length > 0">
                    <n-space vertical>
                        <n-text v-for="item in entry.alias" :key="item">{{ item }}</n-text>
                    </n-space>
                </n-collapse-item>
                <n-collapse-item title="Document" v-if="entry.docs.length > 0">{{ entry.docs }}</n-collapse-item>
                <n-collapse-item title="Comment" v-if="entry.comments.length > 0">{{ entry.comments }}</n-collapse-item>
                <n-collapse-item title="Callers" name="1" v-if="entry instanceof FunctionEntry && entry.callers.length > 0">
                    <n-space vertical>
                        <ApiEntryLink v-for="item in entry.callers" :key="item" :entry="item" :url="entryUrl" />
                    </n-space>
                </n-collapse-item>
                <n-collapse-item title="Callees" name="2" v-if="entry instanceof FunctionEntry && entry.callees.length > 0">
                    <n-space vertical>
                        <ApiEntryLink v-for="item in entry.callees" :key="item" :entry="item" :url="entryUrl" />
                    </n-space>
                </n-collapse-item>
                <n-collapse-item title="Code" name="3" v-if="entry.src.length > 0">
                    <n-code language="python" :code="entry.src"></n-code>
                </n-collapse-item>
            </n-collapse>
        </n-descriptions-item>

        <n-descriptions-item v-if="entry instanceof FunctionEntry">
            <template #label>
                <n-h6 type="info" prefix="bar">Parameters</n-h6>
            </template>
            <n-data-table :columns="parameterColumns" :data="entry.parameters" :pagination="{ pageSize: 20 }"
                :max-height="300" striped />
        </n-descriptions-item>
        <n-descriptions-item v-if="entry instanceof CollectionEntry">
            <template #label>
                <n-h6 type="info" prefix="bar">Members</n-h6>
            </template>
            <n-data-table :columns="memberColumns" :data="members" :pagination="{ pageSize: 20 }" striped
                :max-height="300" />
        </n-descriptions-item>
    </n-descriptions>
</template>