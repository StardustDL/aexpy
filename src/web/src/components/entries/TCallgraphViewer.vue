<script setup lang="ts">
import { computed, h, onMounted, ref, watch, reactive } from 'vue';
import { NSpace, NText, NPopover, NH5, NH6, NDescriptions, NButton, NTag, NDescriptionsItem, NA, NEllipsis, NScrollbar, NDataTable, DataTableColumns, NCode, NCollapse, NCollapseItem } from 'naive-ui'
import ApiEntryLink from '../metadata/ApiEntryLink.vue';
import { ApiDescription, Distribution } from '../../models'
import { ApiEntry, CollectionEntry, Location, ItemEntry, ClassEntry, FunctionEntry, AttributeEntry, ModuleEntry, Parameter, ParameterKind } from '../../models/description';
import { useStore } from '../../services/store';
import { Nodes, Edges, Layouts } from "v-network-graph";
import * as vNG from "v-network-graph"
import {
    ForceLayout,
    ForceNodeDatum,
    ForceEdgeDatum,
} from "v-network-graph/lib/force-layout"

const store = useStore();

const props = defineProps<{
    api: ApiDescription,
    entry?: FunctionEntry,
    entryUrl?: string,
    callee?: boolean,
    caller?: boolean,
    external?: boolean,
}>();

const layouts = computed<Layouts>(() => {
    if (props.entry) {
        return {
            nodes: {
                [props.entry.id]: {
                    x: 0,
                    y: 0,
                    fixed: true,
                },
            }
        };
    }
    return {
        nodes: {}
    };
});

const configs = reactive(
    vNG.defineConfigs({
        view: {
            layoutHandler: new ForceLayout(),
        },
        node: {
            label: {
                direction: "center",
            },
            normal: {
                color: (node) => node.color,
            },
            hover: {
                color: (node) => node.color,
            },
        },
        edge: {
            marker: {
                source: {
                    type: "none",
                },
                target: {
                    type: "arrow",
                },
            },
        }
    })
)

const nodes = computed<Nodes>(() => {
    let nodes: Nodes = {};

    let nodeIds = new Set<string>();
    let callers = new Set();
    let callees = new Set();
    let initial: string[] = [];
    if (props.entry) {
        nodes[props.entry.id] = {
            name: props.entry.id,
            color: "#ff9632"
        };
        initial.push(props.entry.id);
        nodeIds.add(props.entry.id);
    }
    else {
        for (let entry in props.api.funcs()) {
            nodeIds.add(entry);
            initial.push(entry);
        }
    }

    if (props.callee) {
        let queue = [...initial];
        while (queue.length > 0) {
            let item = queue.shift();
            if (!item) {
                continue;
            }
            let entry = props.api.entries[item];
            if (!(entry instanceof FunctionEntry)) {
                continue;
            }

            for (let callee of entry.callees) {
                callees.add(callee);
                if (!nodeIds.has(callee)) {
                    nodeIds.add(callee);
                    queue.push(callee);
                }
            }
        }
    }

    if (props.caller) {
        let queue = [...initial];
        while (queue.length > 0) {
            let item = queue.shift();
            if (!item) {
                continue;
            }
            let entry = props.api.entries[item];
            if (!(entry instanceof FunctionEntry)) {
                continue;
            }
            for (let caller of entry.callers) {
                callers.add(caller);
                if (!nodeIds.has(caller)) {
                    nodeIds.add(caller);
                    queue.push(caller);
                }
            }
        }
    }

    for (let id of nodeIds) {
        if (props.entry && id == props.entry.id) {
            continue;
        }
        let bg = "#e7f5ee";
        if (callees.has(id) && callers.has(id)) {
            bg = "#bb8eaf";
        }
        else if (callers.has(id)) {
            bg = "#fff7d0";
        }
        if (props.api.entries[id] == undefined) {
            if (props.external != true) {
                continue;
            }
            bg = "#f4f4f4";
        }
        nodes[id] = {
            name: id,
            color: bg,
        };
    }
    return nodes;
});

const edges = computed<Edges>(() => {
    let edgeIds = new Set();
    let edges: Edges = {}

    for (let item in nodes.value) {
        let entry = props.api.entries[item];
        if (!(entry instanceof FunctionEntry)) {
            continue;
        }
        for (let callee of entry.callees) {
            let edgeId = `${entry.id}->${callee}`;
            if (!edgeIds.has(edgeId)) {
                edges[edgeId] = {
                    source: entry.id,
                    target: callee,
                };
                edgeIds.add(edgeId);
            }
        }
    }
    return edges;
});
</script>

<template>
    <div :style="{ height: '800px' }">
        <v-network-graph :nodes="nodes" :edges="edges" :configs="configs" :layouts="layouts" />
    </div>
</template>