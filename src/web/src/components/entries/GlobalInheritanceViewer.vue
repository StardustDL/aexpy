<script setup lang="ts">
import { computed, h, onMounted, ref, watch } from 'vue';
import { ApiDescription } from '../../models'
import { ClassEntry } from '../../models/description';
import { Network } from 'vis-network';
import { DataSet } from 'vis-data';
import { hashedColor } from '../../services/utils';

const element = ref<HTMLDivElement>();

const props = defineProps<{
    api: ApiDescription,
    entries?: ClassEntry[],
    external?: boolean,
    entryUrl?: string,
}>();

function show() {
    let el = element.value!;
    let entryIds = new Set();
    let nodeIds = new Map<string, number>();
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
        font?: {
            size?: number,
        }
    }>();
    let entries = props.entries ?? Object.values(props.api.classes);
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
        color?: {
            color?: string,
        }
        length?: number,
        dashes?: boolean,
        width?: number,
    }>();
    for (let entry of entries) {
        entryIds.add(entry.id);
        nodeIds.set(entry.id, 0);
    }
    for (let entry of entries) {
        for (let base of entry.bases) {
            if (entryIds.has(base) || props.external) {
                let edgeId = `${entry.id}:${base}`;
                nodeIds.set(base, (nodeIds.get(base) ?? 0) + 1);
                if (!edgeIds.has(edgeId)) {
                    edges.add({
                        id: edgeId,
                        from: entry.id,
                        to: base,
                        label: "",
                        arrows: {
                            to: {
                                enabled: true,
                            }
                        },
                        color: {
                            color: hashedColor(base),
                        }
                    });
                    edgeIds.add(edgeId);
                }
            }
        }
    }

    for (let id of nodeIds.keys()) {
        if (entryIds.has(id)) {
            nodes.add({
                id: id,
                label: `${id}`,
                color: {
                    background: "#e7f5ee",
                },
                shape: "box",
                font: {
                    size: 14 + (nodeIds.get(id) ?? 0) * 1.5,
                }
            });
        }
        else if (props.external) {
            nodes.add({
                id: id,
                label: `${id}`,
                color: {
                    background: "#e7f5ee",
                    border: "#f4f4f4",
                },
                shape: "box",
                font: {
                    size: 14 + (nodeIds.get(id) ?? 0) * 1.5,
                }
            });
        }
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