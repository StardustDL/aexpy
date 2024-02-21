<script setup lang="ts">
import { computed, h, onMounted, ref, watch } from 'vue';
import { ApiDescription } from '../../models'
import { FunctionEntry } from '../../models/description';
import { Network } from 'vis-network';
import { DataSet } from 'vis-data';

const element = ref<HTMLDivElement>();

const props = defineProps<{
    api: ApiDescription,
    entry: FunctionEntry,
    entryUrl?: string,
    depth?: number,
    callee?: boolean,
    caller?: boolean,
    external?: boolean,
}>();

function show() {
    let queue: {
        id: string,
        depth: number,
    }[] = [];

    let el = element.value!;
    let nodeIds = new Map<string, number>();
    let callers = new Set();
    let callees = new Set();
    let edgeIds = new Set();
    let nodes = new DataSet<{
        id: string,
        label: string,
        group?: string,
        shape: string,
        color?: {
            background?: string,
            border?: string,
        },
    }>([{
        id: props.entry.id,
        label: props.entry.id,
        color: {
            // background: "#97c2fc",
            background: "#ff9632",
        },
        shape: "box"
    }]);
    nodeIds.set(props.entry.id, 0);
    let edges = new DataSet<{
        id: string,
        from: string,
        to: string,
        label: string,
        arrows?: {
            to: {
                enabled: boolean,
            }
        },
        length?: number,
        dashes?: boolean,
        width?: number,
    }>();

    let limit = props.depth ?? 0;

    if (props.callee) {
        queue.push({
            id: props.entry.id,
            depth: 0
        });
        while (queue.length > 0) {
            let item = queue.shift();
            if (!item) {
                continue;
            }
            let entry = props.api.entry(item.id);
            if (!(entry instanceof FunctionEntry)) {
                continue;
            }
            let depth = item.depth + 1;

            for (let callee of entry.callees) {
                callees.add(callee);
                if (!nodeIds.has(callee) || (nodeIds.get(callee) ?? 0) > depth) {
                    nodeIds.set(callee, depth);
                    if (depth < limit) {
                        queue.push({
                            id: callee,
                            depth: depth
                        });
                    }
                }
                let edgeId = `${entry.id}->${callee}`;
                if (!edgeIds.has(edgeId)) {
                    edges.add({
                        id: edgeId,
                        from: entry.id,
                        to: callee,
                        label: "",
                        arrows: {
                            to: {
                                enabled: true,
                            }
                        },
                        width: (limit - depth + 1) * 0.5,
                    });
                    edgeIds.add(edgeId);
                }
            }
        }
    }

    if (props.caller) {
        queue.push({
            id: props.entry.id,
            depth: 0
        });
        while (queue.length > 0) {
            let item = queue.shift();
            if (!item) {
                continue;
            }
            let entry = props.api.entry(item.id);
            if (!(entry instanceof FunctionEntry)) {
                continue;
            }
            let depth = item.depth + 1;

            for (let caller of entry.callers) {
                callers.add(caller);
                if (!nodeIds.has(caller) || (nodeIds.get(caller) ?? 0) > depth) {
                    nodeIds.set(caller, depth);
                    if (depth < limit) {
                        queue.push({
                            id: caller,
                            depth: depth
                        });
                    }
                }
                let edgeId = `${caller}-${entry.id}`;
                if (!edgeIds.has(edgeId)) {
                    edges.add({
                        id: edgeId,
                        from: caller,
                        to: entry.id,
                        label: "",
                        arrows: {
                            to: {
                                enabled: true,
                            }
                        },
                        dashes: true,
                        width: (limit - depth + 1) * 0.5,
                    });
                    edgeIds.add(edgeId);
                }
            }
        }
    }

    for (let id of nodeIds) {
        if (id[0] == props.entry.id) {
            continue;
        }
        let bg = "#e7f5ee";
        if (callees.has(id[0]) && callers.has(id[0])) {
            bg = "#d6cfe2";
        }
        else if (callers.has(id[0])) {
            bg = "#fff7d0";
        }
        let bd = undefined;
        if (props.api.entry(id[0]) == undefined) {
            if (props.external != true) {
                continue;
            }
            bd = "#f4f4f4";
        }
        nodes.add({
            id: id[0],
            label: id[0],
            color: {
                background: bg + Math.round(255 - (id[1] - 1) * (255 / (limit + 1))).toString(16),
                border: bd,
            },
            shape: "box"
        });
    }

    let data = {
        nodes: nodes,
        edges: edges,
    };
    let options = {
        height: "800px",
        layout: {
            randomSeed: 0,
            // hierarchical: {
            //     sortMethod: "directed"
            // }
        },
        physics: {
            enabled: true,
            // barnesHut: {
            //     gravitationalConstant: -2000,
            // }
        }
    };
    let network = new Network(el, data, options);
}

watch(props, (newVal, oldVal) => {
    show();
});

onMounted(() => {
    show();
});

</script>

<template>
    <div ref="element" />
</template>