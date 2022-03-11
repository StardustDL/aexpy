<script setup lang="ts">
import { ref, computed, onMounted, h, defineComponent } from 'vue'
import { NPageHeader, NSpace, NText, NDivider, DataTableColumns, NDataTable, NBreadcrumb, NCollapseTransition, NPopover, NIcon, NLayoutContent, NAvatar, NLog, NSwitch, NStatistic, NTabs, NTabPane, NCard, NButton, useOsTheme, useMessage, NDescriptions, NDescriptionsItem, NSpin, NDrawer, NDrawerContent } from 'naive-ui'
import { HomeIcon, RootIcon, LogIcon, ReportIcon } from '../../components/icons'
import { useRouter, useRoute } from 'vue-router'
import HomeBreadcrumbItem from '../../components/breadcrumbs/HomeBreadcrumbItem.vue'
import DiffBreadcrumbItem from '../../components/breadcrumbs/DiffBreadcrumbItem.vue'
import ReleasePairBreadcrumbItem from '../../components/breadcrumbs/ReleasePairBreadcrumbItem.vue'
import { useStore } from '../../services/store'
import { ApiDifference, Distribution, hashedColor, ProducerOptions, Release, ReleasePair, Report } from '../../models'
import NotFound from '../../components/NotFound.vue'
import MetadataViewer from '../../components/metadata/MetadataViewer.vue'
import DistributionViewer from '../../components/products/DistributionViewer.vue'
import PaginationList from '../../components/PaginationList.vue'
import DiffEntryViewer from '../../components/entries/DiffEntryViewer.vue'
import ApiEntryViewer from '../../components/entries/ApiEntryViewer.vue'
import { BreakingRank, DiffEntry, getRankColor } from '../../models/difference'
import { ApiEntry } from '../../models/description'
import CountViewer from '../metadata/CountViewer.vue'
import { DoughnutChart } from 'vue-chart-3';

const store = useStore();
const router = useRouter();
const route = useRoute();
const message = useMessage();

const props = defineProps<{
    data: ApiDifference,
    showDists: boolean,
    showStats: boolean,
}>();

const sortedEntries = computed(() => {
    return Object.values(props.data.entries).sort((a, b) => {
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
        return 0;
    })
});

function rankViewer(rank: BreakingRank) {
    switch (rank) {
        case BreakingRank.Unknown: return h(NText, { type: 'default' }, { default: () => 'Unknown' });
        case BreakingRank.Compatible: return h(NText, { type: 'success' }, { default: () => 'Compatible' });
        case BreakingRank.Low: return h(NText, { type: 'info' }, { default: () => 'Low' });
        case BreakingRank.Medium: return h(NText, { type: 'warning' }, { default: () => 'Medium' });
        case BreakingRank.High: return h(NText, { type: 'error', strong: true }, { default: () => 'High' });
    }
}

const columns = computed(() => {
    let kinds = props.data.kinds();
    let kindFilterOptions = kinds.map(kind => { return { label: kind, value: kind }; });
    let rankFilterOptions = props.data.ranks().map(rank => { return { label: rankViewer(rank), value: rank }; });
    return <DataTableColumns<DiffEntry>>[
        {
            title: 'Rank',
            key: 'rank',
            width: 110,
            sorter: "default",
            filterOptions: rankFilterOptions,
            filter: "default",
            render(row) {
                return rankViewer(row.rank);
            }
        },
        {
            title: 'Kind',
            key: 'kind',
            width: 240,
            sorter: "default",
            filterOptions: kindFilterOptions,
            filter: "default",
            render: (row) => {
                return h(
                    NPopover,
                    {},
                    {
                        trigger: () => row.kind,
                        default: () => row.id,
                    }
                )
            }
        },
        {
            title: 'Message',
            key: 'message',
            sorter: "default",
            render: (row) => {
                return h(
                    NPopover,
                    {},
                    {
                        trigger: () => row.message,
                        default: () => h("pre", {}, { default: () => JSON.stringify(row.data, undefined, 2) }),
                    }
                )
            }
        },
        {
            title: 'Old',
            key: 'old',
            sorter(row1, row2) {
                if ((row1.old ?? "") == (row2.old ?? ""))
                    return 0;
                return (row1.old ?? "") < (row2.old ?? "") ? -1 : 1;
            },
            render(row) {
                if (row.old) {
                    return h(
                        NPopover,
                        {
                            style: { 'max-width': '800px', 'max-height': '800px' }
                        },
                        {
                            trigger: () => (<any>row).old.name,
                            default: () => h(<any>ApiEntryViewer, {
                                entry: row.old,
                                rawUrl: props.data.old.wheelDir
                            })
                        }
                    );
                }
                return "";
            }
        },
        {
            title: 'New',
            key: 'new',
            sorter(row1, row2) {
                if ((row1.new ?? "") == (row2.new ?? ""))
                    return 0;
                return (row1.new ?? "") < (row2.new ?? "") ? -1 : 1;
            },
            render(row) {
                if (row.new) {
                    return h(
                        NPopover,
                        {
                            style: { 'max-width': '800px', 'max-height': '800px' }
                        },
                        {
                            trigger: () => h(NText, { type: "default" }, { default: () => (<any>row).new.name }),
                            default: () => h(<any>ApiEntryViewer, {
                                entry: row.new,
                                rawUrl: props.data.new.wheelDir
                            })
                        }
                    );
                }
                return "";
            }
        },
    ];
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
    <n-space vertical>
        <n-collapse-transition :show="showDists">
            <n-divider>Distributions</n-divider>
            <n-space>
                <DistributionViewer v-if="data.old" :data="data.old" />
                <DistributionViewer v-if="data.new" :data="data.new" />
            </n-space>
        </n-collapse-transition>
        <n-collapse-transition :show="showStats">
            <n-divider>Statistics</n-divider>
            <n-space>
                <CountViewer :value="Object.keys(data.entries).length" label="Entries"></CountViewer>
                <DoughnutChart
                    :chart-data="rankCounts"
                    :options="{ plugins: { legend: { position: 'bottom' }, title: { display: true, text: 'Ranks' } } }"
                    v-if="Object.keys(data.entries).length > 0"
                />
                <DoughnutChart
                    :chart-data="kindCounts"
                    :options="{ plugins: { legend: { position: 'bottom' }, title: { display: true, text: 'Kinds' } } }"
                    v-if="Object.keys(data.entries).length > 0"
                />
            </n-space>
        </n-collapse-transition>

        <n-divider>Entries</n-divider>

        <n-data-table
            :columns="columns"
            :data="sortedEntries"
            :pagination="{ pageSize: 10 }"
            striped
        ></n-data-table>
    </n-space>
</template>
