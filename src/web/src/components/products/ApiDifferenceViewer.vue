<script setup lang="ts">
import { ref, computed, onMounted, h, defineComponent } from 'vue'
import { NPageHeader, NSpace, NText, NDivider, DataTableColumns, NDataTable, NBreadcrumb, NCollapseTransition, NPopover, NIcon, NLayoutContent, NAvatar, NLog, NSwitch, NStatistic, NTabs, NTabPane, NCard, NButton, useOsTheme, useMessage, NDescriptions, NDescriptionsItem, NSpin, NDrawer, NDrawerContent } from 'naive-ui'
import { HomeIcon, RootIcon, LogIcon, ReportIcon } from '../../components/icons'
import { useRouter, useRoute } from 'vue-router'
import HomeBreadcrumbItem from '../../components/breadcrumbs/HomeBreadcrumbItem.vue'
import DiffBreadcrumbItem from '../../components/breadcrumbs/DiffBreadcrumbItem.vue'
import ReleasePairBreadcrumbItem from '../../components/breadcrumbs/ReleasePairBreadcrumbItem.vue'
import { useStore } from '../../services/store'
import { ApiDifference, Distribution, ProducerOptions, Release, ReleasePair, Report } from '../../models'
import NotFound from '../../components/NotFound.vue'
import MetadataViewer from '../../components/metadata/MetadataViewer.vue'
import DistributionViewer from '../../components/products/DistributionViewer.vue'
import PaginationList from '../../components/PaginationList.vue'
import DiffEntryViewer from '../../components/entries/DiffEntryViewer.vue'
import ApiEntryViewer from '../../components/entries/ApiEntryViewer.vue'
import { BreakingRank, DiffEntry } from '../../models/difference'
import { ApiEntry } from '../../models/description'
import CountViewer from '../metadata/CountViewer.vue'

const store = useStore();
const router = useRouter();
const route = useRoute();
const message = useMessage();

const props = defineProps<{
    data: ApiDifference,
    showDists: boolean,
    showCounts: boolean,
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
        case BreakingRank.Unknown: return h(NText, { type: 'default' }, 'Unknown');
        case BreakingRank.Compatible: return h(NText, { type: 'success' }, 'Compatible');
        case BreakingRank.Low: return h(NText, { type: 'info' }, 'Low');
        case BreakingRank.Medium: return h(NText, { type: 'warning' }, 'Medium');
        case BreakingRank.High: return h(NText, { type: 'error', strong: true }, 'High');
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
            width: 200,
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
                            trigger: () => h(NText, { type: "default" }, (<any>row).new.name),
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

function getRankName(rank: BreakingRank) {
    switch (rank) {
        case BreakingRank.Compatible: return 'Compatible';
        case BreakingRank.Low: return 'Low';
        case BreakingRank.Medium: return 'Medium';
        case BreakingRank.High: return 'High';
        default: return 'Unknown';
    }
}

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
        <n-collapse-transition :show="showCounts">
            <n-divider>Counts</n-divider>
            <n-space vertical>
                <n-space>
                    <CountViewer
                        v-for="rank in data.ranks()"
                        :value="data.rank(rank).length"
                        :total="Object.keys(data.entries).length"
                        :key="rank"
                        :status="getRankType(rank)"
                    >
                        <template #label>
                            <n-text :type="getRankType(rank)">{{ getRankName(rank) }}</n-text>
                        </template>
                    </CountViewer>
                </n-space>
                <n-space>
                    <n-statistic
                        v-for="kind in data.kinds()"
                        :key="kind"
                        :label="kind"
                        :value="data.kind(kind).length"
                    ></n-statistic>
                </n-space>
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
