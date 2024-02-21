<script setup lang="ts">
import { ref, computed, onMounted, h, defineComponent, reactive } from 'vue'
import { NFlex, NText, NDivider, DataTableColumns, NDataTable, DataTableBaseColumn, NScrollbar, NCollapseTransition, NPopover, NIcon, NButton, NInputGroup, NInput, NCode } from 'naive-ui'
import { GoIcon, CountIcon, DataIcon, DistributionIcon } from '../../components/icons'
import { ApiDifference, ReleasePair } from '../../models'
import { apiUrl, changeUrl, hashedColor } from '../../services/utils'
import DistributionViewer from '../../components/products/DistributionViewer.vue'
import ApiEntryViewer from '../../components/entries/ApiEntryViewer.vue'
import { BreakingRank, DiffEntry, getRankColor } from '../../models/difference'
import CountViewer from '../metadata/CountViewer.vue'
import { DoughnutChart } from 'vue-chart-3';
import ApiEntryLink from '../metadata/ApiEntryLink.vue'
import DiffEntryLink from '../metadata/DiffEntryLink.vue'

const props = defineProps<{
    data: ApiDifference,
    showDists: boolean,
    showStats: boolean,
    entry?: string,
    entryUrl?: string,
}>();

const sortedEntries = computed(() => {
    return Object.values(props.data.entries).sort((a, b) => {
        if (props.entry) {
            if (a.id == props.entry && b.id != props.entry) {
                return -1;
            }
            if (b.id == props.entry && a.id != props.entry) {
                return 1;
            }
        }
        if (a.rank > b.rank) {
            return -1;
        }
        if (a.rank < b.rank) {
            return 1;
        }
        if (a.kind < b.kind) {
            return -1;
        }
        if (a.kind > b.kind) {
            return 1;
        }
        if (a.message < b.message) {
            return -1;
        }
        if (a.message > b.message) {
            return 1;
        }
        return 0;
    })
});

function rankViewer(rank: BreakingRank) {
    switch (rank) {
        case BreakingRank.Unknown: return h(NText, { type: 'default' }, { default: () => '❔' });
        case BreakingRank.Compatible: return h(NText, { type: 'success' }, { default: () => '🟢' });
        case BreakingRank.Low: return h(NText, { type: 'info' }, { default: () => '🟡' });
        case BreakingRank.Medium: return h(NText, { type: 'warning' }, { default: () => '🟠' });
        case BreakingRank.High: return h(NText, { type: 'error', strong: true }, { default: () => '🔴' });
    }
}

const messageFilterValue = ref("");

const columns = computed(() => {
    let kinds = props.data.kinds();
    let kindFilterOptions = kinds.sort().map(kind => { return { label: kind, value: kind }; });
    let rankFilterOptions = props.data.ranks().sort().map(rank => { return { label: rankViewer(rank), value: rank }; });

    let messageColumn = reactive<DataTableBaseColumn<DiffEntry>>({
        title: 'Message',
        key: 'message',
        width: 800,
        sorter: "default",
        filter: "default",
        filterOptionValue: "",

        render: (row) => {
            console.log(row.id, props.entry, row.id == props.entry);
            return h(
                NPopover,
                {},
                {
                    trigger: () => h(NText, {}, { default: () => (row.id == props.entry ? "⭐ " : "") + row.message }),
                    default: () => h(NScrollbar,
                        { style: "max-height: 500px; max-width: 500px;", "x-scrollable": true },
                        {
                            default: () => h(NCode, { language: "json", code: JSON.stringify(row.data, undefined, 2) }),
                        }),
                }
            )
        },
        renderFilterMenu: ({ hide }) => {
            return h(
                NInputGroup,
                {},
                {
                    default: () => [
                        h(
                            NInput,
                            {
                                onUpdateValue: (value) => {
                                    messageFilterValue.value = value;
                                },
                                value: messageFilterValue.value,
                                clearable: true,
                            },
                        ),
                        h(
                            NButton,
                            {
                                onClick: () => {
                                    if (messageFilterValue.value.length == 0) {
                                        messageColumn.filterOptionValue = null;
                                    }
                                    else {
                                        messageColumn.filterOptionValue = messageFilterValue.value;
                                    }
                                    hide();
                                }
                            },
                            {
                                default: () => h(NIcon, { component: GoIcon }, {})
                            }
                        )
                    ]
                }
            )
        }
    });

    return [
        {
            key: 'rank',
            width: 50,
            sorter: "default",
            filterOptions: rankFilterOptions,
            defaultFilterOptionValues: props.data.ranks(),
            filter: "default",
            render(row) {
                return h(NFlex, {}, {
                    default: () => rankViewer(row.rank)
                });
            }
        },
        {
            title: 'Kind',
            key: 'kind',
            width: 200,
            sorter: "default",
            filterOptions: kindFilterOptions,
            defaultFilterOptionValues: kinds,
            filter: "default",
            render: (row) => {
                return h(
                    NPopover,
                    {},
                    {
                        trigger: () => row.kind,
                        default: () => h(DiffEntryLink, { entry: row.id, url: props.entryUrl ?? changeUrl(new ReleasePair(props.data.old.release, props.data.new.release)) }, {}),
                    }
                )
            }
        },
        messageColumn,
        {
            title: 'Old',
            key: 'old',
            width: 80,
            sorter(row1, row2) {
                if ((row1.old ?? "") == (row2.old ?? ""))
                    return 0;
                return (row1.old ?? "") < (row2.old ?? "") ? -1 : 1;
            },
            render(row) {
                if (row.old) {
                    return h(
                        NPopover,
                        {},
                        {
                            trigger: () => {
                                if (row.old) {
                                    return h(ApiEntryLink, { entry: row.old.id, url: apiUrl(props.data.old.release), text: false, icon: true }, {})
                                }
                                return "";
                            },
                            default: () => {
                                if (row.old) {
                                    let old = row.old;
                                    return h(NScrollbar,
                                        { style: "max-height: 500px; max-width: 800px;", "x-scrollable": true },
                                        {
                                            default: () => h(ApiEntryViewer, {
                                                entry: old,
                                                rawUrl: props.data.old.rootPath,
                                                entryUrl: apiUrl(props.data.old.release),
                                            })
                                        });
                                }
                                return "";
                            },
                        }
                    );
                }
                return "";
            }
        },
        {
            title: 'New',
            key: 'new',
            width: 80,
            sorter(row1, row2) {
                if ((row1.new ?? "") == (row2.new ?? ""))
                    return 0;
                return (row1.new ?? "") < (row2.new ?? "") ? -1 : 1;
            },
            render(row) {
                if (row.new) {
                    return h(
                        NPopover,
                        {},
                        {
                            trigger: () => {
                                if (row.new) {
                                    return h(ApiEntryLink, { entry: row.new.id, url: apiUrl(props.data.new.release), text: false, icon: true }, {})
                                }
                                return "";
                            },
                            default: () => {
                                if (row.new) {
                                    let ne = row.new;
                                    return h(NScrollbar,
                                        { style: "max-height: 500px; max-width: 800px;", "x-scrollable": true },
                                        {
                                            default: () => h(ApiEntryViewer, {
                                                entry: ne,
                                                rawUrl: props.data.new.rootPath,
                                                entryUrl: apiUrl(props.data.new.release),
                                            })
                                        });
                                }
                                return "";
                            },
                        }
                    );
                }
                return "";
            }
        },
    ] as DataTableColumns<DiffEntry>;
});

function getRankType(rank: BreakingRank) {
    switch (rank) {
        case BreakingRank.Compatible: return 'success';
        case BreakingRank.Low: return 'info';
        case BreakingRank.Medium: return 'warning';
        case BreakingRank.High: return 'error';
        default: return 'default';
    }
}

const kindCounts = computed(() => {
    let raw = [];
    let kinds = [];
    let bgs = []
    for (let kind of props.data.kinds()) {
        let count = props.data.kind(kind).length;
        kinds.push(kind);
        raw.push(count);
        bgs.push(hashedColor(kind));
    }
    return {
        labels: kinds,
        datasets: [
            {
                data: raw,
                backgroundColor: bgs,
            },
        ],
    };
});

const bckindCounts = computed(() => {
    let raw = [];
    let kinds = [];
    let bgs = []
    for (let kind of props.data.kinds()) {
        let count = props.data.kind(kind).filter((value) => value.rank >= BreakingRank.Low).length;
        if (count > 0) {
            kinds.push(kind);
            raw.push(count);
            bgs.push(hashedColor(kind));
        }
    }
    return {
        labels: kinds,
        datasets: [
            {
                data: raw,
                backgroundColor: bgs,
            },
        ],
    };
});

const rankCounts = computed(() => {
    let raw = [];
    let ranks = [];
    let bgs = []
    for (let rank of props.data.ranks()) {
        let count = props.data.rank(rank).length;
        ranks.push(BreakingRank[rank]);
        raw.push(count);
        bgs.push(getRankColor(rank));
    }
    return {
        labels: ranks,
        datasets: [
            {
                data: raw,
                backgroundColor: bgs,
            },
        ],
    };
});

</script>

<template>
    <n-flex vertical>
        <n-collapse-transition :show="showDists">
            <n-divider>
                <n-flex :wrap="false" :align="'center'">
                    <n-icon size="large" :component="DistributionIcon" />
                    Distributions
                </n-flex>
            </n-divider>
            <n-flex>
                <DistributionViewer v-if="data.old" :data="data.old" />
                <DistributionViewer v-if="data.new" :data="data.new" />
            </n-flex>
        </n-collapse-transition>
        <n-collapse-transition :show="showStats">
            <n-divider>
                <n-flex :wrap="false" :align="'center'">
                    <n-icon size="large" :component="CountIcon" />
                    Statistics
                </n-flex>
            </n-divider>
            <n-flex>
                <CountViewer :value="data.breaking().length" label="Breaking" :total="Object.keys(data.entries).length"
                    status="warning"></CountViewer>
                <DoughnutChart :chart-data="rankCounts"
                    :options="{ plugins: { legend: { position: 'bottom' }, title: { display: true, text: 'Ranks' } } }"
                    v-if="Object.keys(data.entries).length > 0" />
                <DoughnutChart :chart-data="bckindCounts"
                    :options="{ plugins: { legend: { position: 'bottom' }, title: { display: true, text: 'Breaking Kinds' } } }"
                    v-if="Object.keys(data.entries).length > 0 && data.breaking().length > 0" />
                <DoughnutChart :chart-data="kindCounts"
                    :options="{ plugins: { legend: { position: 'bottom' }, title: { display: true, text: 'Kinds' } } }"
                    v-if="Object.keys(data.entries).length > 0" />
            </n-flex>
        </n-collapse-transition>

        <n-divider>
            <n-flex :wrap="false" :align="'center'">
                <n-icon size="large" :component="DataIcon" />
                Entries
            </n-flex>
        </n-divider>

        <n-data-table :columns="columns" :data="sortedEntries" :pagination="{ pageSize: 10 }" striped></n-data-table>
    </n-flex>
</template>
